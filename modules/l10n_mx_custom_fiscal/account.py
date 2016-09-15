# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Saldaña (riss_600@hotmail.com)
#
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account journal - Modificacion de Diarios
# ---------------------------------------------------------

class account_journal(osv.Model):
    """
        Modificacion series sobre creacion de diarios
    """
    _inherit='account.journal'

    def create_sequence(self, cr, uid, vals, context=None):
        """
            Crea una secuencia para un diario
        """
        # in account.journal code is actually the prefix of the sequence
        # whereas ir.sequence code is a key to lookup global sequences.
        prefix = vals['code'].upper()

        seq = {
            'name': vals['name'],
            'implementation':'no_gap',
            'prefix': prefix + "/%(year)s/%(month)s/",
            'padding': 4,
            'number_increment': 1
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.pool.get('ir.sequence').create(cr, uid, seq)

account_journal()

# ---------------------------------------------------------
# Account generation from template wizards
# ---------------------------------------------------------

class wizard_multi_charts_accounts(osv.Model):
    """
        Herencia para modificar el plan de cuentas para realizar los pagos de banco
    """
    _inherit='wizard.multi.charts.accounts'

    def execute(self, cr, uid, ids, context=None):
        '''
        This function is called at the confirmation of the wizard to generate the COA from the templates. It will read
        all the provided information to create the accounts, the banks, the journals, the taxes, the tax codes, the
        accounting properties... accordingly for the chosen company.
        '''
        obj_data = self.pool.get('ir.model.data')
        ir_values_obj = self.pool.get('ir.values')
        obj_wizard = self.browse(cr, uid, ids[0])
        company_id = obj_wizard.company_id.id
        
        self.pool.get('res.company').write(cr, uid, [company_id], {'currency_id': obj_wizard.currency_id.id})
        
        # When we install the CoA of first company, set the currency to price types and pricelists
        if company_id==1:
            for ref in (('product','list_price'),('product','standard_price'),('product','list0'),('purchase','list0')):
                try:
                    tmp2 = obj_data.get_object_reference(cr, uid, *ref)
                    if tmp2: 
                        self.pool.get(tmp2[0]).write(cr, uid, tmp2[1], {
                            'currency_id': obj_wizard.currency_id.id
                        })
                except ValueError, e:
                    pass
        
        # If the floats for sale/purchase rates have been filled, create templates from them
        self._create_tax_templates_from_rates(cr, uid, obj_wizard, company_id, context=context)
        
        # Install all the templates objects and generate the real objects
        acc_template_ref, taxes_ref, tax_code_ref = self._install_template(cr, uid, obj_wizard.chart_template_id.id, company_id, code_digits=obj_wizard.code_digits, obj_wizard=obj_wizard, context=context)
        
        # write values of default taxes for product as super user
        if obj_wizard.sale_tax and taxes_ref:
            ir_values_obj.set_default(cr, SUPERUSER_ID, 'product.product', "taxes_id", [taxes_ref[obj_wizard.sale_tax.id]], for_all_users=True, company_id=company_id)
        if obj_wizard.purchase_tax and taxes_ref:
            ir_values_obj.set_default(cr, SUPERUSER_ID, 'product.product', "supplier_taxes_id", [taxes_ref[obj_wizard.purchase_tax.id]], for_all_users=True, company_id=company_id)
        
        #print "****************** create bank journals *********************** "
        
        # Create Bank journals
        self._create_bank_journals_from_o2m(cr, uid, obj_wizard, company_id, acc_template_ref, context=context)
        return {}

    def _prepare_bank_journal(self, cr, uid, line, current_num, default_account_id, company_id, context=None):
        '''
        This function prepares the value to use for the creation of a bank journal created through the wizard of
        generating COA from templates.

        :param line: dictionary containing the values encoded by the user related to his bank account
        :param current_num: integer corresponding to a counter of the already created bank journals through this wizard.
        :param default_account_id: id of the default debit.credit account created before for this journal.
        :param company_id: id of the company for which the wizard is running
        :return: mapping of field names and values
        :rtype: dict
        '''
        obj_data = self.pool.get('ir.model.data')
        obj_journal = self.pool.get('account.journal')
        

        # we need to loop again to find next number for journal code
        # because we can't rely on the value current_num as,
        # its possible that we already have bank journals created (e.g. by the creation of res.partner.bank)
        # and the next number for account code might have been already used before for journal
        for num in xrange(current_num, 100):
            # journal_code has a maximal size of 5, hence we can enforce the boundary num < 100
            journal_code = _('BNK')[:3] + str(num)
            ids = obj_journal.search(cr, uid, [('code', '=', journal_code), ('company_id', '=', company_id)], context=context)
            if not ids:
                break
        else:
            raise osv.except_osv(_('Error!'), _('Cannot generate an unused journal code.'))
        
        #print "********************** prepare account journal *************************** "
        
        vals = {
                'name': line['acc_name'],
                'code': journal_code,
                'type': line['account_type'] == 'cash' and 'cash' or 'bank',
                'company_id': company_id,
                'analytic_journal_id': False,
                'currency': False,
                'default_credit_account_id': default_account_id,
                'default_debit_account_id': default_account_id,
        }
        if line['currency_id']:
            vals['currency'] = line['currency_id']
            
        #print "******************* vals journal ************************** ", vals
        
        return vals

    def _prepare_bank_account(self, cr, uid, line, new_code, acc_template_ref, ref_acc_bank, company_id, context=None):
        '''
        This function prepares the value to use for the creation of the default debit and credit accounts of a
        bank journal created through the wizard of generating COA from templates.

        :param line: dictionary containing the values encoded by the user related to his bank account
        :param new_code: integer corresponding to the next available number to use as account code
        :param acc_template_ref: the dictionary containing the mapping between the ids of account templates and the ids
            of the accounts that have been generated from them.
        :param ref_acc_bank: browse record of the account template set as root of all bank accounts for the chosen
            template
        :param company_id: id of the company for which the wizard is running
        :return: mapping of field names and values
        :rtype: dict
        '''
        obj_data = self.pool.get('ir.model.data')

        # Get the id of the user types fr-or cash and bank
        tmp = obj_data.get_object_reference(cr, uid, 'account', 'data_account_type_cash')
        cash_type = tmp and tmp[1] or False
        tmp = obj_data.get_object_reference(cr, uid, 'account', 'data_account_type_bank')
        bank_type = tmp and tmp[1] or False
        return {
                'name': line['acc_name'],
                'currency_id': line['currency_id'],
                'code': new_code,
                'type': 'liquidity',
                'user_type': line['account_type'] == 'cash' and cash_type or bank_type,
                'parent_id': acc_template_ref[ref_acc_bank.id] or False,
                'company_id': company_id,
        }

    def _create_bank_journals_from_o2m(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):
        '''
        This function creates bank journals and its accounts for each line encoded in the field bank_accounts_id of the
        wizard.

        :param obj_wizard: the current wizard that generates the COA from the templates.
        :param company_id: the id of the company for which the wizard is running.
        :param acc_template_ref: the dictionary containing the mapping between the ids of account templates and the ids
            of the accounts that have been generated from them.
        :return: True
        '''
        
        #print "******************** create_bank_journals_from_02m ************************* "
        
        #print "******************* parametro obj_wizard **************** ", obj_wizard
        #print "******************* parametro company_id **************** ", company_id
        #print "******************* parametro acc_template_ref **************** ", acc_template_ref
        
        obj_acc = self.pool.get('account.account')
        obj_journal = self.pool.get('account.journal')
        code_digits = obj_wizard.code_digits
        
        #print "***************** code digits ********************* ", code_digits
        
        currency_usd_id = self.pool.get('res.currency').search(cr, uid, [('name', '=', 'USD'),])[0]
        #print "**************** currency_usd_id***************** ", currency_usd_id
        
        journal_data = [
            {
                'acc_name': u'Efectivo',
                'account_type': u'cash',
                'currency_id': False
            },
            {
                'acc_name': u'Santander MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Scotiabank MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Banorte MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Banamex MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Bancomer MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'HSBC MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Banco del Bajio MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'IXE MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Banco Azteca MXN',
                'account_type': u'bank',
                'currency_id': False
            },
            {
                'acc_name': u'Santander USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
            {
                'acc_name': u'Scotiabank USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
            {
                'acc_name': u'Banorte USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
            {
                'acc_name': u'Banamex USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
            {
                'acc_name': u'Bancomer USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
            {
                'acc_name': u'HSBC USD',
                'account_type': u'bank',
                'currency_id': currency_usd_id
            },
        ]
        
        # Build a list with all the data to process
        #journal_data = []
        #if obj_wizard.bank_accounts_id:
        #    for acc in obj_wizard.bank_accounts_id:
        #        vals = {
        #            'acc_name': acc.acc_name,
        #            'account_type': acc.account_type,
        #            'currency_id': acc.currency_id.id,
        #        }
        #        journal_data.append(vals)
        #        
        #        #print "********************** journal ******************************* ", vals
        #print "******************** journal data *************** ", journal_data
        
        ref_acc_bank = obj_wizard.chart_template_id.bank_account_view_id
        if journal_data and not ref_acc_bank.code:
            raise osv.except_osv(_('Configuration Error!'), _('You have to set a code for the bank account defined on the selected chart of accounts.'))
        
        #print "********************** ref_acc_bank ********************* ", ref_acc_bank
        
        current_num = 1
        for line in journal_data:
            # Seek the next available number for the account code
            while True:
                new_code = str(ref_acc_bank.code.ljust(code_digits-len(str(current_num)), '0')) + str(current_num)
                ids = obj_acc.search(cr, uid, [('code', '=', new_code), ('company_id', '=', company_id)])
                if not ids:
                    break
                else:
                    current_num += 1
            # Create the default debit/credit accounts for this bank journal
            vals = self._prepare_bank_account(cr, uid, line, new_code, acc_template_ref, ref_acc_bank, company_id, context=context)
            
            #print "******************* cuentas ******************** ",vals['code'], vals['name']
            default_account_id  = obj_acc.create(cr, uid, vals, context=context)
            
            #create the bank journal
            vals_journal = self._prepare_bank_journal(cr, uid, line, current_num, default_account_id, company_id, context=context)
            obj_journal.create(cr, uid, vals_journal)
            current_num += 1
            
        #raise osv.except_osv('bank_journal', 'excepcion agregada para bloquear proceso')
            
        return True

wizard_multi_charts_accounts()

class account_bank_accounts_wizard(osv.Model):
    _inherit='account.bank.accounts.wizard'

    _columns = {
        'acc_name': fields.char('Account Name.', size=64, required=True),
        'bank_account_id': fields.many2one('wizard.multi.charts.accounts', 'Bank Account', required=True, ondelete='cascade'),
        'currency_id': fields.many2one('res.currency', 'Secondary Currency', help="Forces all moves for this account to have this secondary currency."),
        'account_type': fields.selection([('cash','Cash'), ('check','Check'), ('bank','Bank')], 'Account Type', size=32),
    }

account_bank_accounts_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
