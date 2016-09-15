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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_fiscal_balance_return(osv.osv_memory):
    """ Aplicar Devolucion de saldo """
    _name = 'account.fiscal.balance.return'
    _description = 'Aplicar Devolucion de Saldo'
    
    def action_balance_return(self, cr, uid, ids, context=None):
        """
            Genera un egreso sobre la devolucion del saldo
        """
        #print "***************** devolver saldo ***************** "
        inc_obj = self.pool.get('account.fiscal.statement')
        inc_tax_obj = self.pool.get('account.fiscal.statement.tax')
        bline_obj = self.pool.get('account.fiscal.balance.line')
        link_obj = self.pool.get('links.get.request')
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.fiscal.statement', 'Income/Expense', context=None)
        
        # Obtiene el tipo de ingreso a aplicar
        type_id = self.pool.get('account.fiscal.balance').get_config_type_statement_id(cr, uid, context=context)
        
        # Valida que este registrado el tipo de ingreso
        if not type_id or type_id == 0:
            raise osv.except_osv('Error Validacion', 'El tipo de ingreso no esta configurado, debe ir a la configuracion de codigos fiscales y completar la informacion.')
        
        type_statement = self.pool.get('account.fiscal.statement.type').browse(cr, uid, type_id, context=context)
        #print "*********** type statement ***************** ", type_statement
        
        percent_total = 1
        # Obtiene el porcentaje total del total del importe mas impuestos
        for tax in type_statement.tax_ids:
            percent_total += tax.amount
        
        # Recorre los registros
        for ret in self.browse(cr, uid, ids, context=context):
            
            if ret.journal_id.default_debit_account_id.currency_id.id:
                currency_id = ret.journal_id.default_debit_account_id.currency_id.id
            else:
                currency_ids = self.pool.get('res.currency').search(cr, uid, [('name', '=', 'MXN'),])
                if currency_ids:
                    currency_id = currency_ids[0]
            
            # Genera un ingreso en estado borrador
            inc_id = inc_obj.create(cr, uid, {
                'type_statement_id': type_id,
                'journal_id': ret.journal_id.id,
                'period_id': ret.period_id.id,
                'date': ret.date,
                'amount': ret.amount,
                'account_id': type_statement.account_id.id,
                'state': 'draft',
                'currency_id': currency_id
                }, context=context)
            # Obtiene los impuestos y los agrega
            for tax in type_statement.tax_ids:
                # Genera los impuestos para el modelo
                base = ret.amount/percent_total
                amount_tax = (ret.amount * tax.amount)/percent_total
                values = {
                    'statement_id': inc_id,
                    'name': tax.name,
                    'tax_id': tax.id,
                    'percent': tax.amount,
                    'account_id': tax.account_collected_id_apply.id,
                    'base': base,
                    'amount': amount_tax}
                tax_id = inc_tax_obj.create(cr, uid, values, context=context)
            
            reference = 'account.fiscal.statement,' + str(inc_id)
            
            # Agrega un registro en las lineas del saldo fiscal
            bline_id = bline_obj.create(cr, uid, {
                'balance_id': ret.balance_id.id,
                'period_id': ret.period_id.id,
                'balance_before': ret.balance_id.balance,
                'amount': ret.amount,
                'type': 'dev',
                'next_inpc_id': ret.balance_id.next_inpc_id.id,
                'last_inpc_id': ret.balance_id.last_inpc_id.id,
                'inpc': ret.balance_id.inpc.id,
                'state': 'pending',
                'reference': reference,
                'reference2': reference}, context=context)
            #print "**************** bline_id ***************** ", bline_id
            #print "**************** balance id ***************** ", ret.balance_id
            
            # Actualiza el ingreso con la informacion del saldo
            inc_obj.write(cr, uid, [inc_id], {'balance_id': ret.balance_id.id, 'balance_line_id': bline_id}, context=context)
        return True
    
    _columns = {
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account'), help="Monto a Devolver"),
        'update_amount': fields.float('Saldo actual', digits_compute=dp.get_precision('Account'), help="Saldo disponible"),
        'journal_id': fields.many2one('account.journal', 'Diario', required=True, domain=[('partner_bank_ids','!=',None)]),
        'date': fields.date('Fecha'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo Fiscal'),
    }
    
    def _get_period(self, cr, uid, context=None):
        """
            Obtiene el periodo actual
        """
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    
    _defaults = {
        'period_id': _get_period,
        'date': fields.datetime.now,
        'amount': 0.0,
        'update_amount': 0.0
    }

account_fiscal_balance_return()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
