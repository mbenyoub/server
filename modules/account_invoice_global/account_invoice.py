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
    
    def generate_voucher_invoice_global(self, cr, uid, note_ids=[], context=None):
        """
            Gestion de pagos para notas de venta sobre facturas globales
        """
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        journal_obj = self.pool.get('account.journal')
        
        # Asignacion inicial de variables
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        obj_seq = self.pool.get('ir.sequence')
        date = time.strftime('%Y-%m-%d')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        note_list = []
        
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
        
        # Recorre las notas de venta
        for note in self.browse(cr, uid, note_ids, context=context):
            # Valida que la nota de venta no este pagada
            if not note.note_sale and note.note_paid == True and not note.global_invoice_id:
                continue
            # Valida que la nota este pagada
            if not note.state == 'paid':
                continue
            
            # Obtiene el total de la factura para registrar sobre cuentas por cobrar
            amount = note.amount_total
            # Inicializa las variables para generar el movimiento
            mov_lines = []
            # Inicializa variable para conciliaciones
            rec_ids = []
            
            # Obtiene el numero de la secuencia del movimiento
            mov_number = '/'
            mov_number = obj_seq.next_by_id(cr, uid, journal.sequence_id.id, context=context)
            
            # Referencia de la poliza sobre factura global
            reference = 'account.invoice,' + str(note.global_invoice_id.id)
            
            # Genera la poliza del pago de la nota de cargo a la factura
            mov = {
                'name': mov_number,
                'ref': 'Pago factura Global %s'%(note.global_invoice_id.number,),
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
                'account_id': note.global_invoice_id.account_id.id,
                'move_id': move_id,
                'partner_id': note.partner_id.id or False,
                'credit': amount,
                'debit': 0.0,
                'date': date,
                'ref': mov_number,
                'reference': reference
            }
            move_line_id = move_line_obj.create(cr, uid, move_line, context=context)
            mov_lines.append(move_line_id)
            rec_ids.append(move_line_id)
            
            # Crea los movimientos por los detalles de la nota de venta
            for line in note.invoice_line:
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': note.number or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': note.partner_id.id or False,
                    'credit': 0.0,
                    'debit': line.price_subtotal,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                
            # Crea los movimientos sobre los impuestos
            for tax in note.tax_line:
                tax_ids = []
                
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': note.number or '/',
                    'account_id': tax.account_id.id,
                    'move_id': move_id,
                    'partner_id': note.partner_id.id or False,
                    'credit': 0.0,
                    'debit': tax.amount,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                tax_ids.append(new_id)
                
                # Valida que los impuestos se trasladen al pago
                if not tax.account_tax_id.account_collected_id_apply:
                    continue
                
                # Realiza la aplicacion de los impuestos trasladados
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': note.number or '/',
                    'account_id': tax.account_tax_id.account_collected_id.id,
                    'move_id': move_id,
                    'partner_id': note.partner_id.id or False,
                    'credit': tax.amount,
                    'debit': 0.0,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                    #'account_tax_id': tax.account_tax_id.id or False,
                    'base': tax.base,
                    'tax_amount': tax.amount
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                tax_ids.append(new_id)
                move_line = {
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'name': note.number or '/',
                    'account_id': tax.account_tax_id.account_collected_id_apply.id,
                    'move_id': move_id,
                    'partner_id': note.partner_id.id or False,
                    'credit': 0.0,
                    'debit': tax.amount,
                    'date': date,
                    'ref': mov_number,
                    'reference': reference,
                    #'account_tax_id': tax.account_tax_id.id or False,
                    'base': tax.base,
                    'tax_amount': tax.amount,
                    'tax_code_id': tax.tax_code_id.id or False
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                tax_ids.append(new_id)
                
            # Asenta el movimiento
            move_obj.button_validate(cr, uid, [move_id], context=context)
            
            # Concilia el apunte con la factura global
            movelines = note.global_invoice_id.move_id.line_id
            for line in movelines:
                # Si la linea es la principal donde se carga el monto facturado la pasa a los valores a conciliar
                if line.account_id.id == note.global_invoice_id.account_id.id:
                    rec_ids.append(line.id)
            # Concilia los movimientos generados con la factura global
            reconcile = False
            if len(rec_ids) >= 2:
                reconcile = move_line_obj.reconcile_partial(cr, uid, rec_ids,
                                                writeoff_acc_id=note.global_invoice_id.account_id.id,
                                                writeoff_period_id=period_id,
                                                writeoff_journal_id=journal_id)
            
            # Agrega la nota a la lista de notas de venta pagadas
            note_list.append(note.id)
        
        #Indica que la nota de venta fue pagada
        self.write(cr, uid, note_list, {'note_paid': True}, context=context)
        return True
    
    def confirm_paid(self, cr, uid, ids, context=None):
        """
            Valida si la factura es de nota de venta y si no esta pagada y aplica el pago a la factura global
        """
        if context is None:
            context = {}
        
        # Funcion original de confirmar pago
        res = super(account_invoice, self).confirm_paid(cr, uid, ids, context=context)
        
        # Busca notas de venta que deben a plicar el pago a la factura global
        inv_ids = self.search(cr, uid, [('note_sale','=',True),('global_invoice_id','!=',False),('note_paid','=',False),('id','in',ids)], context=context)
        if inv_ids:
            self.generate_voucher_invoice_global(cr, uid, inv_ids, context=context)
        return True
    
    def get_account_product(self, cr, uid, product_id, journal_id=False, context=None):
        """
            Obtiene la cuenta del producto
        """
        product_obj = self.pool.get('product.product')
        journal_obj = self.pool.get('account.journal')
        note_sale = False
        account_id = False
        
        # Verifica si el diario es de nota de venta o es un diario de venta
        if journal_id:
            journal = journal_obj.browse(cr, uid, journal_id, context=context)
            if journal.note_sale:
                note_sale = True
        
        # Obtiene el producto
        product = product_obj.browse(cr, uid, product_id, context=context)
        if note_sale:
            if product.categ_id.property_account_income_note_categ:
                account_id = product.categ_id.property_account_income_note_categ.id or False
        # Si no tiene una cuenta asignada obtiene la cuenta que corresponde sobre el producto
        if not account_id:
            # Busca si hay una cuenta relacionada al producto
            if product.property_account_income:
                account_id = product.property_account_income.id or False
            else:
                # Obtiene la cuenta de ingresos de la categoria del producto
                account_id = product.categ_id.property_account_income_categ.id or False
        return account_id
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """
            Actualiza la informacion del cliente sobre la factura
        """
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids,
            type, partner_id, date_invoice, payment_term, partner_bank_id,
            company_id)
        # Actualiza valor de campo check_global para ejecutar funcion onchange
        res['value']['check_global'] = True
        return res
    
    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        """
            Actualiza la informacion relacionad al diario contable
        """
        # Funcion original de onchange
        result = super(account_invoice, self).onchange_journal_id(cr, uid, ids, journal_id, context)
        # Actualiza valor de campo check_global para ejecutar funcion onchange
        result['value']['check_global'] = True
        return result
    
    def onchange_check_global(self, cr, uid, ids, type, partner_id, journal_id, account_id, invoice_line, check_global, global_invoice=False, context=None):
        """
            Actualiza el resultado de los registros en base al diario
        """
        res = {}
        inv_line = []
        line_obj = self.pool.get('account.invoice.line')
        
        # Valida que check_global sea verdadero
        if check_global == True and type == 'out_invoice' and not global_invoice:
            # Valida que haya un diario seleccionado
            if not journal_id:
                return res
            # Valida si el diario es de nota de venta
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            if journal.note_sale:
                res['note_sale'] = True
                # Obtiene la cuenta del cliente
                if partner_id:
                    partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
                    if partner.property_account_receivable_note:
                        res['account_id'] = partner.property_account_receivable_note.id
            elif partner_id:
                # Actualiza la cuenta de la factura en base al cliente
                partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
                if type in ['out_invoice', 'out_refund']:
                    res['account_id'] = partner.property_account_receivable.id
                else:
                    res['account_id'] = partner.property_account_payable.id
            # Actualiza las cuentas del detalle de las lineas de factura
            for line in invoice_line:
                reg = {}
                reg = line[2]
                num = line[0]
                reg_id = line[1]
                if reg is None or reg == False:
                    reg = {}
                line_acc_id = False
                # Valida si es un nuevo registro
                if num == 0 or num == False:
                    # Valida si hay un producto relacionado
                    if reg.get('product_id',False):
                        # Obtiene la cuenta que corresponde al producto
                        line_acc_id =  self.get_account_product(cr, uid, reg['product_id'], journal_id, context=context)
                # Valida si es un registro modificado
                elif num == 1 or num == 4:
                    # Si es 4 lo cambia a 1 porque 4 solo indica la relacion
                    if num == 4:
                        num = 1
                    # Valida si hay un producto relacionado
                    if reg.get('product_id',False):
                        # Obtiene la cuenta que corresponde al producto
                        line_acc_id =  self.get_account_product(cr, uid, reg.get('product_id',False), journal_id, context=context)
                    else:
                        # Obtiene la linea del producto y obtiene la cuenta
                        line_data = line_obj.browse(cr, uid, reg_id, context=context)
                        if line_data.product_id:
                            line_acc_id =  self.get_account_product(cr, uid, line_data.product_id.id, journal_id, context=context)
                
                # Actualiza la cuenta sobre el registro
                if line_acc_id:
                    reg['account_id'] = line_acc_id
                
                # Agrega el registro sobre la lista tal cual esta
                inv_line.append([num, reg_id, reg])
            # Actualiza los registros
            res['invoice_line'] = inv_line
            
        # Cambia check_global a falso
        res['check_global'] = False
        return {'value': res}
    
    _columns = {
        # Indica que es una factura global
        'global_invoice': fields.boolean('Factura Global'),
        'note_sale': fields.boolean('Nota de venta'),
        'note_paid': fields.boolean('Pagada sobre factura global'),
        'check_global': fields.boolean('Registro generico', store=False),
        'global_invoice_id': fields.many2one('account.invoice', 'Factura global'),
        'global_ids': fields.one2many('account.invoice', 'global_invoice_id', 'Notas de Venta', domain=[('global_invoice','=',False)])
    }
    
    _defaults = {
        'global_invoice': False
    }
    
account_invoice()

class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"
    
    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        """
            Actualiza la cuenta del producto en base a si es nota de venta o factura global
        """
        invoice_obj = self.pool.get('account.invoice')
        if context is None:
            context = {}
        
        # Proceso original para obtencion de la informacion del producto
        res = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
        # Valida que sea una factura de venta y que traiga al diario en los parametros
        if type == 'out_invoice' and context.get('journal_id',False):
            # Actualiza la cuenta del producto en base al diario de la factura
            account_id = invoice_obj.get_account_product(cr, uid, product, journal_id=context.get('journal_id',False), context=context)
            if account_id:
                res['value']['account_id'] = account_id
        return res
    
account_invoice_line()


class account_invoice_tax(osv.Model):
    _inherit = "account.invoice.tax"
    
    def compute(self, cr, uid, invoice_id, context=None):
        """
            Calcula los impuestos de la factura, Agrega parametro de account_tax_id en el key
        """
        tax_grouped = {}
        compute_all = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        for line in inv.invoice_line:
            #if inv.type in ['out_refund','in_refund'] or inv.debit_note == True:
            #    compute_all = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_subtotal), 1, line.product_id, inv.partner_id)['taxes']
            #else:
            #    compute_all = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, line.product_id, inv.partner_id)['taxes']
            #for tax in compute_all:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_subtotal), 1, line.product_id, inv.partner_id)['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
                val['account_tax_id'] = tax['id']
                
                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                    # Si es una nota de venta pone la cuenta de la factura de notas de venta
                    if inv.type == 'out_invoice' and inv.note_sale:
                        # Pone en la cuenta del puesto la cuenta de nota de venta
                        tax_data = tax_obj.browse(cr, uid, tax['id'], context=context)
                        if tax_data.account_collected_note_id:
                            val['account_id'] = tax_data.account_collected_note_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['account_tax_id'], val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                #print "***************** key compute tax **************** ", key
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
        
        #print "**************** tax grouped ************* ", tax_grouped
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
            
        #print "**************** tax grouped ************* ", tax_grouped
        return tax_grouped
    
    _columns = {
        'account_tax_id': fields.many2one('account.tax', 'Tax', select=True)
    }

account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
