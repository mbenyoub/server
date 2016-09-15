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
from openerp import netsvc

# ---------------------------------------------------------
# Account generation from template wizards
# ---------------------------------------------------------

class account_account_category(osv.Model):
    _name='account.account.category'

    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32, required=True),
        'description': fields.text('Descripcion'),
        'active': fields.boolean('Activo'),
        'exclude_deduction': fields.boolean('Excluir deducciones por flujo'),
        'exclude_cum_income': fields.boolean('Excluir Ingresos Acumulados por flujo'),
        'account_ids': fields.many2many('account.account', 'account_account_category_rel', 'category_id', 'account_id', string='Cuentas contables', help="Cuentas donde se aplica el rubro fiscal"),
    }
    
    _defaults = {
        'active': True
    }
    
    _sql_constraints = [
        (
            'code_unique', 
            'UNIQUE(code)', 
            'El codigo debe ser unico para cada rubro fiscal'
        ),
    ]
    
    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        """
            Le agrega el valor de copy al codigo sobre el registro a duplicar
        """
        default = {} if default is None else default.copy()
        if context is None:
            context = []
        account = self.browse(cr, uid, id, context=context)
        if default.get('name',False):
            default['name'] = '%s (copy)'%(default.get('name',''),)
        if default.get('code',False):
            default['code'] = '%s (copy)'%(default.get('code',''),)
        return super(account_account, self).copy(cr, uid, id, default, context=context, done_list=done_list, local=local)
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no este relacionado con un codigo fiscal
        """
        #Recorre los registros a eliminar
        for id in ids:
            reference = 'account.account.category,' + str(id)
            #~ Valida que el rubro fiscal a borrar no se encuentre entre los codigos fiscales
            cr.execute("""
                        select id 
                        from account_fiscal_code
                        where reference ='%s'"""%(reference,))
            if cr.fetchone():
                raise osv.except_osv(_('Error!'),_("No se puede eliminar el rubro fiscal porque esta relacionado con codigos fiscales!"))
            #~ Valida que el rubro fiscal no se utilice en las cuentas
            cr.execute("""
                        select category_id 
                        from account_account_category_rel
                        where category_id ='%s'"""%(id,))
            if cr.fetchone():
                raise osv.except_osv(_('Error!'),_("No se puede eliminar el rubro fiscal porque esta relacionado con el plan de cuentas!"))
        return super(account_account_category, self).unlink(cr, uid, ids, context=context)

account_account_category()

class account_account_type(osv.Model):
    _inherit='account.account.type'

    _columns = {
        'name': fields.char('Tipo de cuenta', size=64, required=True),
        'active': fields.boolean('Activo'),
    }
    
    _defaults = {
        'active': True
    }
    
    _sql_constraints = [
        (
            'code_unique', 
            'UNIQUE(code)', 
            'El codigo debe ser unico para cada tipo de cuenta'
        ),
    ]
    
    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        """
            Le agrega el valor de copy al codigo sobre el registro a duplicar
        """
        default = {} if default is None else default.copy()
        if context is None:
            context = []
        account = self.browse(cr, uid, id, context=context)
        if default.get('code',False):
            default['code'] = '%s (copy)'%(default.get('code',''),)
        return super(account_account, self).copy(cr, uid, id, default, context=context, done_list=done_list, local=local)
    
account_account_type()

class account_account(osv.Model):
    _inherit='account.account'

    _columns = {
        'category_id': fields.many2many('account.account.category', 'account_account_category_rel', 'account_id', 'category_id', string='Rubros Fiscales', help="Rubros fiscales de la cuenta"),
        'user_type': fields.many2one('account.account.type', 'Tipo de cuenta', domain=[('active','=',True)]),
    }
    
    _defaults = {
        'reconcile': True
    }

    def _check_allow_type_change(self, cr, uid, ids, new_type, context=None):
        restricted_groups = ['consolidation']
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            old_type = account.type
            account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])])
            if line_obj.search(cr, uid, [('account_id', 'in', account_ids)]):
                #Check for 'Closed' type
                if old_type == 'closed' and new_type !='closed':
                    raise osv.except_osv(_('Warning!'), _("You cannot change the type of account from 'Closed' to any other type as it contains journal items!"))
                # Forbid to change an account type for restricted_groups as it contains journal items (or if one of its children does)
                if (new_type in restricted_groups):
                    raise osv.except_osv(_('Warning!'), _("You cannot change the type of account to '%s' type as it contains journal items!") % (new_type,))

        return True
    
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])], context=context)
            #if line_obj.search(cr, uid, [('account_id', 'in', account_ids)], context=context):
            #    raise osv.except_osv(_('Warning !'), _("You cannot change the code of account which contains journal items!"))
        return True
    
    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        default = {} if default is None else default.copy()
        if done_list is None:
            done_list = []
        if context is None:
            context = []
        account = self.browse(cr, uid, id, context=context)
        
        if context.get('done_list',False):
            return False
        
        if account:
            # Hace que se omitan las cuentas hijas relacionadas con la cuenta a duplicar
            for child in account.child_id:
                done_list.append(child.id)
            context['done_list'] = done_list
            #print "**************** done list ******** ", done_list
        return super(account_account, self).copy(cr, uid, id, default, context=context, done_list=done_list, local=local)

account_account()

class account_move_reconcile(osv.osv):
    _inherit = "account.move.reconcile"
    
    # Look in the line_id and line_partial_ids to ensure the partner is the same or empty
    # on all lines. We allow that only for opening/closing period
    def _check_same_partner(self, cr, uid, ids, context=None):
        for reconcile in self.browse(cr, uid, ids, context=context):
            move_lines = []
            print "**************** not reconcile.opening_reconciliation ********* ", not reconcile.opening_reconciliation
            if not reconcile.opening_reconciliation:
                print "************** reconcile.line_id *************** ", reconcile.line_id
                print "************** reconcile.line_partial_ids ************ ", reconcile.line_partial_ids
                if reconcile.line_id:
                    first_partner = reconcile.line_id[0].partner_id.id
                    move_lines = reconcile.line_id
                elif reconcile.line_partial_ids:
                    first_partner = reconcile.line_partial_ids[0].partner_id.id
                    move_lines = reconcile.line_partial_ids
                
                # Valida que las lineas no esten con un diario para aplicacion de facturas globales
                for line in move_lines:
                    if line.move_id.journal_id.paid_invoice_global:
                        return True
                
                if any([(line.account_id.type in ('receivable', 'payable') and line.partner_id.id != first_partner) for line in move_lines]):
                    return False
        return True

    _constraints = [
        (_check_same_partner, 'You can only reconcile journal items with the same partner.', ['line_id']),
    ]

account_move_reconcile()

# ---------------------------------------------------------
# Account period - Periodos contables
# ---------------------------------------------------------

class account_period(osv.Model):
    """
        Modificacion cierre de periodo
    """
    _inherit='account.period'
    
    def create_move_id_close(self, cr, uid, data, context=None):
        """ 
            Crea la poliza de cierre
        """
        # Asignacion inicial de variables
        cur_obj = self.pool.get('res.currency')
        journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        date = time.strftime('%Y-%m-%d')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.period', 'Period', context=None)
        
        # Inicializa las variables para generar el movimiento
        mov_lines = []
        
        # Obtiene el numero de la secuencia del movimiento
        mov_number = '/'
        journal = journal_obj.browse(cr, uid, data['journal_id'], context=context)
        mov_number = obj_seq.next_by_id(cr, uid, journal.sequence_id.id, context=context)
        
        period = period_obj.browse(cr, uid, data['period_id'], context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        
        # Genera el asiento contable
        mov = {
            'name': mov_number,
            'ref': 'Cierre periodo %s'%(period.name,),
            'journal_id': data['journal_id'],
            'period_id': data['period_id'],
            'date': date,
            'narration': '',
            'company_id': company.id,
            'to_check': False,
            'reference': 'account.period,' + str(period.id)
        }
        move_id = move_obj.create(cr, uid, mov, context=context)
        
        # Genera las lineas de movimiento
        move_line = {
            'journal_id': data['journal_id'],
            'period_id': data['period_id'],
            'name': '/',
            'account_id': data['account_credit_id'],
            'move_id': move_id,
            'partner_id': company.partner_id.id or False,
            'credit': data['credit'],
            'debit': data['debit'],
            'date': date,
            'ref': mov_number,
            'reference': 'account.period,' + str(data['period_id'])
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        move_line = {
            'journal_id': data['journal_id'],
            'period_id': data['period_id'],
            'name': mov_number or '/',
            'account_id': data['account_debit_id'],
            'move_id': move_id,
            'partner_id': company.partner_id.id or False,
            'credit': data['debit'],
            'debit': data['credit'],
            'date': date,
            'ref': mov_number,
            'reference': 'account.period,' + str(data['period_id'])
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        
        # Asenta el movimiento
        move_obj.button_validate(cr, uid, [move_id], context=context)
        
        return move_id
    
    def action_draft(self, cr, uid, ids, context=None):
        """
            Vuelve a abrir el periodo
        """
        move_obj = self.pool.get('account.move')
        
        # Ejecuta la funcion original
        res = super(account_period, self).action_draft(cr, uid, ids)
        
        # Elimina el periodo creado
        for period in self.browse(cr, uid, ids, context=context):
            # Valida si se genero un asiento sobre el periodo
            if not period.move_id:
                continue
            
            move_id = period.move_id.id
            
            # Elimina el asiento contable
            move_obj.button_cancel(cr, uid, [move_id], context=context)
            move_obj.unlink(cr, uid, [move_id], context=context)
        
        return res
    
    _columns = {
        'move_id': fields.many2one('account.move', 'Asiento de cierre', ondelete='set null')
    }

account_period()

# ---------------------------------------------------------
# Account journal - Diarios contables
# ---------------------------------------------------------

class account_journal(osv.Model):
    """
        Modificacion series sobre creacion de diarios
    """
    _inherit='account.journal'
    
    def action_get_balance(self, cr, uid, journal_id, date=False, context=None):
        """
            Obtiene el saldo de un diario en base a una fecha
        """
        balance_obj = self.pool.get('account.bank.statement.balance')
        amount = 0.0
        values = [('journal_id','=',journal_id)]
        # Valida que reciba una fecha para aplicar sobre la busqueda del saldo
        if date:
            values.append(('date','<=',date))
        
        # Obtiene el saldo real del banco registrado por conciliaciones
        bal_ids = balance_obj.search(cr, uid, values, context=context)
        if bal_ids:
            # Recorre los movmientos obtenidos
            for balance in balance_obj.browse(cr, uid, bal_ids, context=context):
                amount += balance.amount
        return amount
    
    def _balance_bank(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        """
            Obtiene el monto del saldo que tiene que tener el banco, segun las conciliaciones
        """
        res = {}
        # Recorre los registros
        for journal in self.browse(cr, uid, ids):
            res[journal.id] = 0.0
            # Valida que el diario sea un diario de banco
            if journal.type == 'bank':
                # Obtiene el saldo del diario
                res[journal.id] = self.action_get_balance(cr, uid, journal.id)
        return res
    
    _columns = {
        'type': fields.selection([
            ('sale', 'Sale'),
            ('sale_refund','Sale Refund'),
            ('sale_debit','Notas de cargo ventas'),
            ('purchase', 'Purchase'),
            ('purchase_refund','Purchase Refund'),
            ('purchase_debit','Notas de cargo proveedor'),
            ('cash', 'Cash'),
            ('bank', 'Bank and Checks'),
            ('general', 'General'),
            ('period', 'Apertura/Cierre Periodo'),
            ('situation', 'Opening/Closing Situation')], 'Type', size=32, required=True,
                                 help="Select 'Sale' for customer invoices journals."\
                                 " Select 'Purchase' for supplier invoices journals."\
                                 " Select 'Cash' or 'Bank' for journals that are used in customer or supplier payments."\
                                 " Select 'General' for miscellaneous operations journals."\
                                 " Select 'Opening/Closing Situation' for entries generated for new fiscal years."),
        'amount_limit': fields.float('Limite sobre el pago', digits_compute=dp.get_precision('Account'), help="Indica el limite del monto con el que se puede pagar con este diario de banco o efectivo"),
        #'note_sale': fields.boolean('Generar nota de venta', help="Maque esta opcion para que al momento de la facturacion con este diario se le de un trato de nota de venta en base a la gestion de las cuentas"),
        'balance_bank': fields.function(_balance_bank, string='Saldo Bancario', type="float", readonly=True, digits_compute= dp.get_precision('Account')),
        #'paid_invoice_global': fields.boolean('Aplicacion de Nota de Venta sobre Factura Global')
    }
    
    _defaults = {
        'amount_limit': 0.0
    }
    
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
# Account move - Tabla de impuestos
# ---------------------------------------------------------

class account_move(osv.Model):
    _inherit = "account.move"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    _columns = {
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
    }
    
account_move()

class account_move_line(osv.Model):
    _inherit = "account.move.line"
    
    def action_view_move(self, cr, uid, ids, context=None):
        """
            Muestra la poliza generada sobre los pagos
        """
        # Obtiene el objeto a cargar
        line = self.browse(cr, uid, ids[0], context=context)
        res_id = line.move_id.id or False
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_form')
        
        return {
            'name':_("Poliza"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            'res_id': res_id
        }

    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    def _get_currency_rate(self, cr, uid, ids, name, args, context):
        """
            Obtiene el tipo de cambio de la moneda
        """
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 1.0
            if line.currency_id:
                res[line.id] = line.currency_id.rate
        #print "*********** res ************* ", res
        return res
    
    def _get_currency_line(self, cr, uid, ids, name, args, context):
        """
            Obtiene la moneda utilizada en la linea
        """
        if context is None:
            context = {}
        res = {}
        currency_id = self._get_company_currency(cr, uid, context=context)
        #print "*********** currency ********** ", currency_id
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = currency_id
            if line.currency_id:
                res[line.id] = line.currency_id.id
        #print "************** res ************ ", res
        return res
    
    def _get_company_currency(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        company_pool = self.pool.get('res.company')
        user = user_pool.browse(cr, uid, uid, context=context)
        company_id = user.company_id
        company_currency = False
        if company_id:
            if user.company_id.currency_id:
                company_currency = user.company_id.currency_id.id
            return company_currency
        else:
            company_id = company_pool.search(cr, uid, [])
            currency = company_pool.browse(cr, uid, company_id).currency_id
            if currency:
                company_currency = currency.id
        return company_currency
    
    def _check_statement(self, cr, uid, ids, field, arg, context=None):
        """
            Indica True si ya fue conciliado con los movimientos del banco
        """
        result = {}
        # Recorre los registros
        for line in self.browse(cr, uid, ids, context=context):
            # Obtiene la base del impuesto
            result[line.id] = True if line.statement_id else False
        return result
    
    _columns = {
        'tax_ids': fields.one2many('account.move.tax', 'move_line_id', 'Tax lines'),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
        'currency_rate': fields.function(_get_currency_rate, string="Tipo de Cambio", type='float', store=True),
        'currency_id2': fields.function(_get_currency_line, string="Moneda", type='many2one', relation='res.currency', store=True),
        #'balance': fields.function(_balance, fnct_search=_balance_search, string='Balance', type="float", store=False),
        'concilie_bank': fields.function(_check_statement, type="boolean", store=True, string="Conciliado"),
        'statement_id': fields.many2one('account.bank.statement', 'Statement', select=True, ondelete='restrict', help="conciliacion sobre cuentas bancarias"),
        'account_tax_id': fields.many2one('account.tax', 'Referencia Impuesto')
    }

    _defaults = {
        'base': 0.0,
        'balance': 0.0,
        'concilie_bank': False
    }
    
    def _default_get(self, cr, uid, fields, context=None):
        """
            Si el movimiento es de forma manual, omite el proceso 
        """
        if context is None:
            context = {}
        if context.get('manual',False):
            data = {
                'credit': 0.0,
                'state': 'draft',
                'base': 0.0,
                'debit': 0.0
            }
        else:
            data = super(account_move_line, self)._default_get(cr, uid, fields, context=context)
        return data
    
    def reconcile_partial(self, cr, uid, ids, type='auto', context=None, writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
        move_rec_obj = self.pool.get('account.move.reconcile')
        merges = []
        unmerge = []
        total = 0.0
        merges_rec = []
        company_list = []
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)

        for line in self.browse(cr, uid, ids, context=context):
            if line.account_id.currency_id:
                currency_id = line.account_id.currency_id
            else:
                currency_id = line.company_id.currency_id
            if line.reconcile_id:
                raise osv.except_osv(_('Warning'), _("Journal Item '%s' (id: %s), Move '%s' is already reconciled!") % (line.name, line.id, line.move_id.name)) 
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    if not line2.reconcile_id:
                        if line2.id not in merges:
                            merges.append(line2.id)
                        if line2.account_id.currency_id:
                            total += line2.amount_currency
                        else:
                            total += (line2.debit or 0.0) - (line2.credit or 0.0)
                merges_rec.append(line.reconcile_partial_id.id)
            else:
                unmerge.append(line.id)
                if line.account_id.currency_id:
                    total += line.amount_currency
                else:
                    total += (line.debit or 0.0) - (line.credit or 0.0)
            #print "****************** line.name - rec.part ********************** ", line.id, "-", line.name
        #print "****************** currency ", currency_id, ", total - rec.part ********************** ", total
        if self.pool.get('res.currency').is_zero(cr, uid, currency_id, total):
            #print "*************** merge ******************** ", merges
            #print "************** unmerge ******************* ", unmerge
            
            res = self.reconcile(cr, uid, merges+unmerge, context=context, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id)
            return res
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_partial_ids': map(lambda x: (4,x,False), merges+unmerge)
        }, context=context)
        move_rec_obj.reconcile_partial_check(cr, uid, [r_id] + merges_rec, context=context)
        return True
    
    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        if context is None:
            context = {}
        company_list = []
        for line in self.browse(cr, uid, ids, context=context):
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)
            
            #print "******************* line.id ************************** ", line.id,"-", line.name, " - ", line.credit, ", ", line.debit, "  - ", line.account_id.name

        for line in unrec_lines:
            if line.state <> 'valid':
                raise osv.except_osv(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            #print "********************* cuenta **************************** ", line['account_id']['id']
            #print "********************* cuenta **************************** ", line['account_id']['name']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit

        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')
        
        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s and reconcile_id is not NULL '\
                   'GROUP BY account_id,reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #print "*************************** len r *********************  ", len(r)
        
        #TODO: move this check to a constraint in the account_move_reconcile object
        #if len(r) < 1 or len(r) > 2:
        if len(r) < 0 or len(r) > 2:
            raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        if not unrec_lines:
            raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        account = account_obj.browse(cr, uid, account_id, context=context)
        if not account.reconcile:
            raise osv.except_osv(_('Error'), _('The account is not defined to be reconciled !'))
        # Valida que se hayan retornado registros
        if len(r) > 0:
            if r[0][1] != None:
                raise osv.except_osv(_('Error!'), _('Some entries are already reconciled.'))
        if (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
           (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):
            if not writeoff_acc_id:
                raise osv.except_osv(_('Warning!'), _('You have to provide an account for the write off/exchange difference entry.'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle = context['comment']
            else:
                libelle = _('Write-Off')

            cur_obj = self.pool.get('res.currency')
            cur_id = False
            amount_currency_writeoff = 0.0
            if context.get('company_currency_id',False) != context.get('currency_id',False):
                cur_id = context.get('currency_id',False)
                for line in unrec_lines:
                    if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                        amount_currency_writeoff += line.amount_currency
                    else:
                        tmp_amount = cur_obj.compute(cr, uid, line.account_id.company_id.currency_id.id, context.get('currency_id',False), abs(line.debit-line.credit), context={'date': line.date})
                        amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount

            writeoff_lines = [
                (0, 0, {
                    'name': libelle,
                    'debit': self_debit,
                    'credit': self_credit,
                    'account_id': account_id,
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and -1 * amount_currency_writeoff or (account.currency_id.id and -1 * currency or 0.0)
                }),
                (0, 0, {
                    'name': libelle,
                    'debit': debit,
                    'credit': credit,
                    'account_id': writeoff_acc_id,
                    'analytic_account_id': context.get('analytic_id', False),
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and amount_currency_writeoff or (account.currency_id.id and currency or 0.0)
                })
            ]

            writeoff_move_id = move_obj.create(cr, uid, {
                'period_id': writeoff_period_id,
                'journal_id': writeoff_journal_id,
                'date':date,
                'state': 'draft',
                'line_id': writeoff_lines
            })

            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            if account_id == writeoff_acc_id:
                writeoff_line_ids = [writeoff_line_ids[1]]
            ids += writeoff_line_ids
        
        move_rec = {
            'type': type,
            'line_id': map(lambda x: (4, x, False), ids),
            'line_partial_ids': map(lambda x: (3, x, False), ids)
        }
        #print "******************** move rec *************** ", move_rec
        
        r_id = move_rec_obj.create(cr, uid, move_rec)
        wf_service = netsvc.LocalService("workflow")
        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            wf_service.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id

account_move_line()

class account_move_tax(osv.Model):
    _name = "account.move.tax"
    _description = "Move Tax"

    _columns = {
        'move_line_id': fields.many2one('account.move.line', 'Move Line', ondelete='cascade', select=True),
        'name': fields.char('Tax Description', size=64),
        'tax_id': fields.many2one('account.tax', 'Tax'),
        'base_tax': fields.float('Base Impuestos', digits_compute=dp.get_precision('Account')),
        'amount_tax': fields.float('Monto impuestos pagado', digits_compute=dp.get_precision('Account')),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Monto Base pagado', digits_compute=dp.get_precision('Account')),
        'percent': fields.float('Percent', digits=(16,4)),
        'account_id': fields.many2one('account.account', 'Account payment'),
        'invoice_total': fields.float('Total Factura'),
        'tax_code_id': fields.many2one('account.tax.code', 'Codigo Impuestos', ondelete='set null')
    }

    _defaults = {
        'base_tax': 0.0,
        'amount_tax': 0.0,
        'base': 0.0,
        'amount': 0.0,
        'percent': 0.0,
        'invoice_total': 0.0,
    }

account_move_tax()

# ---------------------------------------------------------
# Account financial - Configuracion Informes contables
# ---------------------------------------------------------

class account_financial_report(osv.Model):
    _inherit='account.financial.report'

    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
    }
    
account_financial_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
