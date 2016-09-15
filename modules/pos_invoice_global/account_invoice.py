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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import pytz

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_invoice(osv.Model):
    _inherit='account.invoice'
    
    def pos_generate_voucher_invoice_global(self, cr, uid, order_ids=[], context=None):
        """
            Gestion de pagos para notas de venta sobre facturas globales
        """
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        journal_obj = self.pool.get('account.journal')
        
        # Asignacion inicial de variables
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        tax_obj = self.pool.get('account.tax')
        order_obj = self.pool.get('pos.order')
        obj_seq = self.pool.get('ir.sequence')
        date = time.strftime('%Y-%m-%d')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        order_list = []
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.invoice', 'Factura', context=None)
        
        # Obtiene el periodo actual y la compañia
        periods = self.pool.get('account.period').find(cr, uid, context=context)
        period_id = periods and periods[0] or False
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id or False
        
        # Obtiene el dario donde se va a generar la poliza
        journal_ids = journal_obj.search(cr, uid, [('type','=','general'),('paid_invoice_global','=',True)], context=context)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),_("No hay un diario para aplicar los pagos sobre la factura global: (Diario tipo general). Revise en la configuracion de diarios para modificar la configuracion.!"))
        journal_id = journal_ids[0]
        journal = journal_obj.browse(cr, uid, journal_id, context=context)
        
        # Recorre los pedidos de venta
        for order in order_obj.browse(cr, uid, order_ids, context=context):
            # Valida que el pedido este pagado
            if order.global_invoice_paid == True or not order.global_invoice_id or order.state != 'paid':
                continue
            
            # Obtiene el total del pedido para registrar sobre cuentas por cobrar
            amount = order.amount_total
            # Inicializa las variables para generar el movimiento
            mov_lines = []
            # Inicializa variable para conciliaciones
            rec_ids = []
            
            # Obtiene el numero de la secuencia del movimiento
            mov_number = '/'
            mov_number = obj_seq.next_by_id(cr, uid, journal.sequence_id.id, context=context)
            
            # Referencia de la poliza sobre factura global
            reference = 'account.invoice,' + str(order.global_invoice_id.id)
            
            # Genera la poliza del pago de la nota de cargo a la factura
            mov = {
                'name': mov_number,
                'ref': 'Pago factura Global %s'%(order.global_invoice_id.number,),
                'journal_id': journal_id,
                'period_id': period_id,
                'date': date,
                'narration': '',
                'company_id': company_id,
                'to_check': False,
                'reference': reference
            }
            move_id = move_obj.create(cr, uid, mov, context=context)
            
            # Genera las lineas de movimiento de CXC
            move_line = {
                'journal_id': journal_id,
                'period_id': period_id,
                'name': mov_number or '/',
                'account_id': order.global_invoice_id.account_id.id,
                'move_id': move_id,
                'partner_id': order.partner_id.id or False,
                'credit': amount,
                'debit': 0.0,
                'date': date,
                'ref': mov_number,
                'reference': reference
            }
            move_line_id = move_line_obj.create(cr, uid, move_line, context=context)
            mov_lines.append(move_line_id)
            rec_ids.append(move_line_id)
            
            group_tax = {}
            
            # Crea los movimientos por los detalles de la nota de venta
            for line in order.lines:
                income_account = False
                # Cuenta de nota de venta para producto
                if line.product_id.categ_id.property_account_income_note_categ:
                    income_account = line.product_id.categ_id.property_account_income_note_categ.id
                elif  line.product_id.property_account_income:
                    income_account = line.product_id.property_account_income.id
                elif line.product_id.categ_id.property_account_income_categ:
                    income_account = line.product_id.categ_id.property_account_income_categ.id
                
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': order.name or '/',
                    'account_id': income_account,
                    'move_id': move_id,
                    'partner_id': order.partner_id.id or False,
                    'credit': 0.0,
                    'debit': line.price_subtotal,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                
                tax_amount = 0
                taxes = [t for t in line.product_id.taxes_id]
                computed_taxes = account_tax_obj.compute_all(cr, uid, taxes, line.price_unit * (100.0-line.discount) / 100.0, line.qty)['taxes']
                
                for tax in computed_taxes:
                    tax_amount += cur_obj.round(cr, uid, cur, tax['amount'])
                    
                    group_tax.setdefault(tax['id'], 0)
                    group_tax[tax['id']] += tax_amount
                
            for key, tax_amount in group_tax.items():
                insert_data('tax', {
                    'name': _('Tax') + ' ' + tax.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': key[account_pos] or income_account,
                    'credit': ((tax_amount>0) and tax_amount) or 0.0,
                    'debit': ((tax_amount<0) and -tax_amount) or 0.0,
                    'tax_code_id': key[tax_code_pos],
                    'tax_amount': tax_amount,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                })
            
            # Crea los movimientos sobre los impuestos
            for tax_id in group_tax:
                tax = self.pool.get('account.tax').browse(cr, uid, key[tax_id], context=context)
                
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': order.name or '/',
                    'account_id': tax.account_collected_id.id or False,
                    'move_id': move_id,
                    'partner_id': order.partner_id.id or False,
                    'credit': 0.0,
                    'debit': group_tax[tax_id],
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                
                # Valida que los impuestos se trasladen al pago
                if not tax.account_tax_id.account_collected_id_apply:
                    continue
                
                # Realiza la aplicacion de los impuestos trasladados
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': order.name or '/',
                    'account_id': tax.account_collected_id.id,
                    'move_id': move_id,
                    'partner_id': order.partner_id.id or False,
                    'credit': group_tax[tax_id]['amount'],
                    'debit': 0.0,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                    #'account_tax_id': tax.account_tax_id.id or False,
                    'base': group_tax[tax_id]['base'],
                    'tax_amount': group_tax[tax_id]['amount']
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': order.name or '/',
                    'account_id': tax.account_collected_id_apply.id,
                    'move_id': move_id,
                    'partner_id': order.partner_id.id or False,
                    'credit': 0.0,
                    'debit': group_tax[tax_id]['amount'],
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                    #'account_tax_id': tax.account_tax_id.id or False,
                    'base': group_tax[tax_id]['base'] * tax.tax_sign,
                    'tax_amount': group_tax[tax_id]['amount'] * tax.tax_sign,
                    'tax_code_id': tax.tax_code_id.id or False
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                
            # Asenta el movimiento
            move_obj.button_validate(cr, uid, [move_id], context=context)
            
            # Concilia el apunte con la factura global
            movelines = order.global_invoice_id.move_id.line_id
            for line in movelines:
                # Si la linea es la principal donde se carga el monto facturado la pasa a los valores a conciliar
                if line.account_id.id == order.global_invoice_id.account_id.id:
                    rec_ids.append(line.id)
            # Concilia los movimientos generados con la factura global
            reconcile = False
            if len(rec_ids) >= 2:
                reconcile = move_line_obj.reconcile_partial(cr, uid, rec_ids,
                                                writeoff_acc_id=order.global_invoice_id.account_id.id,
                                                writeoff_period_id=period_id,
                                                writeoff_journal_id=journal_id)
            
            # Agrega la nota a la lista de notas de venta pagadas
            order_list.append(order.id)
        
        #Indica que el pedido de venta fue pagado
        self.write(cr, uid, order_list, {'global_invoice_paid': True}, context=context)
        return True
    
    _columns = {
        # Indica que es una factura global
        'pos_global_invoice': fields.boolean('Factura Global POS'),
        'pos_global_ids': fields.one2many('pos.order', 'global_invoice_id', 'Pedidos de Venta', readonly=True)
    }
    
    _defaults = {
        'pos_global_invoice': False
    }
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
