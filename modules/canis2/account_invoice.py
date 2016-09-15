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
    
    def get_discount_payment_invoice(self, cr, uid, invoice_id, date, context=None):
        """
            Obtiene el descuento que corresponde sobre la factura
        """
        disc_obj = self.pool.get('product.pricelist.discount')
        item_obj = self.pool.get('product.pricelist.discount.item')
        
        inv = self.browse(cr, uid, invoice_id, context=context)
        amount = inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual
        
        # Obtiene el descuento que se debe aplicar por pronto pago
        discount = 0.0
        discount_amount = 0.0
        
        # Valida que la factura sea una factura de cliente y que tenga un precio de lista
        if inv.type == 'out_invoice' and inv.pricelist_id:
            # Obtiene los datos de la factura
            inv_date = inv.date_invoice
            pricelist = inv.pricelist_id.id
            
            # Obtiene los descuentos disponibles en donde se aplican pagos
            type_ids = self.pool.get('product.pricelist.discount.type').search(cr, uid, [('to_paid','=',True)], context=context) 
            
            # Obtiene el numero de dias en relacion al pago contra la factura
            days = disc_obj.get_number_days(cr, uid, inv_date, date, context=context) - 1
            
            # Valida si se debe aplicar un descuento sobre pronto pago
            discount_ids = disc_obj.search(cr, uid, [('type_id','in',type_ids),('pricelist_id','=',pricelist)])
            if discount_ids:
                # Recorre los descuentos sobre pagos y valida si se aplican en alguna de las reglas
                for disc in disc_obj.browse(cr, uid, discount_ids, context=context):
                    # Valida que el descuento tenga un codigo
                    if not disc.type_id.key:
                        continue
                    
                    # Recorre las reglas aplicadas sobre el descuento
                    for item in disc.item_ids:
                        apply_discount = False
                        
                        # Valida si hay categorias que excluyen el descuento
                        if item_obj.validate_exception_categ(cr, uid, item.id, inv.id, context=context):
                            continue
                        
                        # Valida que los dias de la factura al pago correspondan al descuento
                        if item.min_quantity >= days:
                            discount += item.discount
                            break
            
            # Si el descuento es mayor a cero obtiene el valor de la factura
            if discount > 0.0:
                # Obtiene el monto del descuento
                discount_amount = (inv.amount_total - inv.discount_sale) * (discount / 100)
                # Trunca el descuento a dos digitos
                discount_amount = float(int(discount_amount * 100.0))/100.0
                amount += inv.type in ('out_refund', 'in_refund') and discount_amount or -discount_amount
        return discount_amount, amount
    
    def generate_voucher_invoice(self, cr, uid, invoice_id, refund_id, context=None):
        """
            Genera el cobro automatico de una factura sobre una nota de credito
        """
        inv_obj = self.pool.get('account.invoice')
        v_obj = self.pool.get('account.voucher')
        v_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        type_line = 'receipt'
        
        # Obtiene la informacion de la factura
        inv = inv_obj.browse(cr, uid, invoice_id, context=context)
        
        if inv.type in ['in_invoice','in_refund']:
            account_type = 'payable'
            type_line = 'payment'
        else:
            account_type = 'receivable'
            type_line = 'receipt'
        
        reconcile = 0
        to_reconcile_ids = []
        # Recorre las lineas de la factura y obtiene los movimientos a pagar de la factura
        movelines = inv.move_id.line_id
        for line in movelines:
            # Si la factura origen ya esta pagada en su totalidad se omite el proceso
            if (line.account_id.id == inv.account_id.id) and (type(line.reconcile_id) == osv.orm.browse_null):
                to_reconcile_ids.append(line.id)
                reconcile += 1
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
        
        # Si no se encontraron lineas para conciliar termina el proceso
        if reconcile == 0:
            return True
        
        # Obtiene la informacion de la nota de credito
        refund = inv_obj.browse(cr, uid, refund_id, context=context)
        reconcile = 0
        # Recorre las lineas de la nota de credito y obtiene los movimientos a pagar de la factura
        movelines = refund.move_id.line_id
        for line in movelines:
            # Si la factura origen ya esta pagada en su totalidad se omite el proceso
            if (line.account_id.id == refund.account_id.id) and (type(line.reconcile_id) == osv.orm.browse_null):
                to_reconcile_ids.append(line.id)
                reconcile += 1
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
        # Si no se encontraron lineas para conciliar termina el proceso
        if reconcile == 0:
            return True
        
        # Obtiene la cuenta que se va a aplicar para el voucher
        account_id = inv.partner_id.property_account_receivable.id
        
        line_cr_ids = []
        line_dr_ids = []
        voucher_line = []
        concilie = 0
        # Recorre las lineas de movimiento y crea las lineas del voucher
        for line in move_line_obj.browse(cr, uid, to_reconcile_ids, context=context):
            amount_unreconciled = abs(line.amount_residual_currency)
            reconcile = False
            if line.credit:
                amount = min(amount_unreconciled, abs(total_debit))
                total_debit -= amount
            else:
                amount = min(amount_unreconciled, abs(total_credit))
                total_credit -= amount
            line_type = line.credit and 'dr' or 'cr'
            
            # Revisa si se esta conciliando el movimiento completo
            if amount_unreconciled == amount and concilie == 0:
                reconcile = True
                if total_credit == 0 or total_debit == 0:
                    concilie = 1
            # Genera un arreglo con la informacion de la linea a generar
            rs = {
                'name':line.move_id.name,
                'type': line_type,
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': abs(line.amount_currency),
                'amount': amount,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': inv.currency_id.id,
                'reconcile': reconcile
            }
            
            # Agrega la informacion a los cargos o abonos
            if rs['type'] == 'cr':
                line_cr_ids.append(rs)
            else:
                line_dr_ids.append(rs)
            voucher_line.append(rs)
        
        writeoff_amount = v_obj._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, 0.0, type_line)
        
        vals = {
            'invoice_id': inv.id,
            'partner_id': inv.partner_id.id,
            'currency_id': inv.currency_id.id,
            'type': type_line,
            'pre_line': 1,
            'writeoff_amount': writeoff_amount,
            'account_id': account_id
        }
        
        # Crea el nuevo voucher para la factura
        v_id = v_obj.create(cr, uid, vals)
        
        # Crea las lineas del voucher
        for line in voucher_line:
            line['voucher_id'] = v_id
            v_line_obj.create(cr, uid, line, context=context)
        
        # Aplica el pago sobre los movimientos
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.voucher', v_id, 'proforma_voucher', cr)
        return v_id
    
    def _create_refund_to_discount(self, cr, uid, invoice, context=None):
        """
            Crea la nota de credito donde se aplica el descuento comercial, volumen y mezcla
        """
        obj_journal = self.pool.get('account.journal')
        cur_obj = self.pool.get('res.currency')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        if context is None:
            context = {}
        type_dict = {
            'out_invoice': 'out_refund', # Customer Invoice
            'in_invoice': 'in_refund',   # Supplier Invoice
            'out_refund': 'out_invoice', # Customer Refund
            'in_refund': 'in_invoice',   # Supplier Refund
        }
        invoice_data = {}
        
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False
        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = inv_obj._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        
        # Obtenemos el diario para la nota de debito
        refund_journal = invoice.journal_id.journal_refund_id
        # Valida que exista
        if not refund_journal:
            raise osv.except_osv(_('Error!'),_("Diario automatico para nota de debito, no configurado, configure el diario sobre diario de credito"))
        if refund_journal.type not in ('sale_refund','purchase_refund'):
            raise osv.except_osv(_('Error!'),_("Configurar el diario de nota de debito con: credito de compra o credito de venta"))
        
        date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            #'tax_line': tax_lines,
            'journal_id': refund_journal.id or False,
            'invoice_id': invoice.id
        })
        
        # Agrega el campo de tipo de nota de credito si lo trae entre los parametros
        if context.get('default_filter_refund',False):
            invoice_data['filter_refund'] = context.get('default_filter_refund',False)
        
        invoice_id = inv_obj.create(cr, uid, invoice_data, context=context)
        cur = invoice.currency_id
        
        # Recorre las lineas de la factura
        for line in invoice.invoice_line:
            # Obtiene el monto del descuento de venta por la linea
            price = line.price_subtotal
            amount_discount = 0.0
            discount_sale = 0.0
            # Aplica al subtotal el descuento comercial y al impuesto
            if line.discount_com > 0:
                discount_sale = price * (line.discount_com/100)
                price = price - discount_sale
                amount_discount += discount_sale
            # Aplica al subtotal el descuento de mezcla y al impuesto
            if line.discount_mez > 0:
                discount_sale = price * (line.discount_mez/100)
                price = price - discount_sale
                amount_discount += discount_sale
            # Aplica al subtotal el descuento de volumen y al impuesto
            if line.discount_vol > 0:
                discount_sale = price * (line.discount_vol/100)
                price = price - discount_sale
                amount_discount += discount_sale
            
            # Valida que el descuento no sea cero
            if amount_discount == 0.0:
                continue
            #tax = line.
            amount_discount = cur_obj.round(cr, uid, cur, amount_discount)
            vals = {
                'product_id': line.product_id.id or False,
                'name': 'Descuento (Comercial: %s %%, Volumen: %s %%, Mezcla: %s %%) - %s '%(line.discount_com,line.discount_vol,line.discount_mez,line.name),
                'quantity': 1,
                'uos_id': line.uos_id.id,
                'price_unit': amount_discount,
                #'tax_line': tax_lines,
                'account_id': line.account_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.invoice_line_tax_id])],
                'invoice_id': invoice_id
            }
           #print "****************** vals despues de agregar tax de create refund *************",vals
            
            inv_line_obj.create(cr, uid, vals, context=context)
        
        # Actualiza los totales de la factura
        inv_obj.write(cr, uid, [invoice_id], {}, context=context)
        
        return invoice_id
    
    def invoice_validate(self, cr, uid, ids, context=None):
        """
            Si la factura tiene descuentos genera la nota de credito
        """
        wf_service = netsvc.LocalService('workflow')
        
        # Funcion original de validar factura
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        
        # Revisa si alguna factura es de nota de credito y ve si tiene que aplicar una modificacion sobre la factura origen
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.amount_total == 0.0 and inv.type in ['out_refund','in_refund']:
                raise osv.except_osv(_('Error!'),_("No puede validar notas de credito en cero: '%s'!")%(inv.number,))
            
            # Valida que sea una nota de credito generada para el cliente
            if inv.type in ['out_invoice']:
                # Valida si hay descuento sobre la factura
                if inv.discount_sale:
                    # Crea la nota de credito con la informacion del descuento financiero
                    refund_id = self._create_refund_to_discount(cr, uid, inv, context=context)
                    
                    # Pasa la factura a abierto
                    wf_service.trg_validate(uid, 'account.invoice', \
                                                 refund_id, 'invoice_open', cr)
                    # Salda la nota de credito con la factura
                    self.generate_voucher_invoice(cr, uid, inv.id, refund_id, context=context)
                    
                    # Actualiza el total de descuento sobre la venta obtenido por la nota de credito
                    refund = self.browse(cr, uid, refund_id, context=context)
                    self.write(cr, uid, [inv.id], {'discount_sale': refund.amount_total})
        return res
    
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        """
            Abre el formulario para los cobros desde  la factura
        """
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
        date = time.strftime('%Y-%m-%d')
        
        inv = self.browse(cr, uid, ids[0], context=context)
        # Obtiene el descuento sobre la factura
        discount_amount, amount = self.get_discount_payment_invoice(cr, uid, inv.id, date, context=context)
        
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': amount,
                'default_discount': discount_amount,
                'default_invoice_amount': inv.residual,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """
            Cuando se modifique el cliente tiene que actualizar el precio de lista que contenga
        """
        # Funcion original onchange
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids,
            type, partner_id, date_invoice, payment_term, partner_bank_id,
            company_id)
        
        #~ # Si no esta el metodo de pago relacionado con el cliente pone el metodo de no identificado
        #~ if partner_id:
            #~ partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            #~ # Si el cliente tiene una lista de precio relacionada, actualiza el valor en la factura
            #~ if partner.property_product_pricelist:
                #~ res['value']['pricelist_id'] = partner.property_product_pricelist.id
        return res
    
    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', 'Tarifa'),
        'discount_fin': fields.float('Descuento', digits_compute=dp.get_precision('Account')),
        'discount_sale': fields.float('Descuento', digits_compute=dp.get_precision('Account')),
        'tax_line': fields.one2many('account.invoice.tax', 'invoice_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
account_invoice()

class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"
    
    def _amount_line_tax(self, cr, uid, line, price, context=None):
        """
            Calculando el subtotal con impuestos
        """
        val = 0.0

        # Se llama para redondear la cantindad
        cur_obj = self.pool.get('res.currency')

        # Calculando impuestos
        for c in self.pool.get('account.tax').compute_all(cr, uid,
            line.invoice_line_tax_id, price, 1, line.product_id,
                line.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        cur = line.invoice_id.currency_id or 0.0

        print """"""""""""""""cur:  """, cur

        if cur:
            # Regresando el valor de los impuestos redondeado
            return cur_obj.round(cr, uid, cur, val)
        else:
            return 0.0        
        
    def _compute_tax_all(self, cr, uid, ids, field_names, args, context=None):
        """
            Calculando importe con descuentos: comercial, volumen, mezcla; además del cálculo del total neto con
            descuento financiero
        """
        res = {}
        amount_subtotal_desc = 0.0
        discount_subtotal_sale = 0.0
        price_discount = 0.0
        imprt_discount = 0.0
        dif = 0.0
        utility_c = 0.0
        utility_div = 0.0
        utility_p = 0.0
        
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'price_unit_discount': 0.0,
                'price_subtotal2': 0.0,
                'diference': 0.0,
                'total_cost': 0.0,
                'utility': 0.0,
                'utility_percent': 0.0,
            }
            
            # Se obtiene el importe o subtotal
            price = line.price_subtotal
            
            # Aplica al subtotal el descuento comercial
            if line.discount_com > 0:
                discount_sale = price * (line.discount_com/100)
                price = price - discount_sale
            # Aplica al subtotal el descuento de mezcla
            if line.discount_mez > 0:
                discount_sale = price * (line.discount_mez/100)
                price = price - discount_sale
            # Aplica al subtotal el descuento de volumen
            if line.discount_vol > 0:
                discount_sale = price * (line.discount_vol/100)
                price = price - discount_sale
            # Aplica al subtotal el descuento de financiero
            if line.discount_fin > 0:
                discount_sale = price * (line.discount_fin/100)
                price = price - discount_sale
            
            print "********** PRICE ********* ", price
            # Se agrega el nuevo importe con los descuentos (comercial, volumen, mezcla) al diccionario
            res[line.id]['price_subtotal2'] = price
            
            # Calculamos el precio del producto con descuentos aplicados
            res[line.id]['price_unit_discount'] = (price / line.quantity)
            
            # Calculamos la diferencia de importes
            res[line.id]['diference'] = line.price_subtotal - res[line.id]['price_subtotal2']
            
            # Obtiene el costo total
            res[line.id]['total_cost'] = line.standard_price * line.quantity
            
            # Calcula la utilidad
            utility = price - res[line.id]['total_cost']
            res[line.id]['utility'] = utility
            res[line.id]['utility_percent'] = (utility/price)*100 if utility != 0 and price!=0 else 0.0
        return res
    
    _columns = {
        # Descuentos aplicados sobre la linea
        'discount_com': fields.float('Comercial', digits_compute= dp.get_precision('Account'), readonly=True),
        'discount_vol': fields.float('Volumen', digits_compute= dp.get_precision('Account'), readonly=True),
        'discount_mez': fields.float('Mezcla', digits_compute= dp.get_precision('Account'), readonly=True),
        'discount_fin': fields.float('Financiero', digits_compute= dp.get_precision('Account'), readonly=True),
        
        # Campos para reporte de ventas
        'price_unit_discount': fields.function(_compute_tax_all, type='float',
            digits_compute=dp.get_precision('Account'), string='Precio C/Desc (unitario)', method=True, store=True,
            multi='amount_all'),
        'price_subtotal2':fields.function(_compute_tax_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Importe C/Desc', method=True, store=True, multi='amount_all'),
        'diference':fields.function(_compute_tax_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Diferencia', method=True, store=True, multi='amount_all'),
        'total_cost': fields.function(_compute_tax_all, type='float', digits_compute= dp.get_precision('Account'),
            store=True, string='Total costo', method=True, multi="amount_all"),
        'utility':fields.function(_compute_tax_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Utilidad', store=True, method=True, multi="amount_all"),
        'utility_percent':fields.function(_compute_tax_all, type='float', digits_compute=dp.get_precision('Account'),
            string='%Utilidad', method=True, store=True, multi='amount_all'),
    }
    
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
