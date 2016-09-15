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
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
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
from openerp import netsvc
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account generation from template wizards
# ---------------------------------------------------------

class account_voucher(osv.Model):
    _inherit='account.voucher'
    _description = 'Accounting Voucher'
    
    _columns = {
        'invoice_amount':fields.float('Monto Factura', digits_compute=dp.get_precision('Account')),
        'discount': fields.float('Descuento', digits_compute=dp.get_precision('Account')),
        'apply_discount': fields.boolean('Aplicar descuento')
    }
    
    _defaults = {
        'apply_discount': True
    }
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de los impuestos sobre los pagos del voucher,
            Si hay deducciones elimina el valor aplicado
        """
        move_tax_obj = self.pool.get('account.move.tax')
        vapply_tax_obj = self.pool.get('account.voucher.apply.tax')
        deduction_obj = self.pool.get('account.fiscal.deduction')
        
        # Recorre los registros
        for voucher in self.browse(cr, uid, ids, context=context):
            tax_ids = []
            if voucher.tax_ids:
                for tax in voucher.tax_ids:
                    # Actualiza la tabla de impuesto con el total pagado y su base pagada
                    move_tax_obj.write(cr, uid, [tax.move_tax_id.id], {'amount_tax': tax.move_tax_id.amount_tax - tax.amount_apply, 'amount': tax.move_tax_id.amount - tax.base_apply})
                    tax_ids.append(tax.move_tax_id.id)
                # Elimina los registros
                vapply_tax_obj.unlink(cr, uid, tax_ids, context=context)
        
        # Busca en los registros de deducciones si haya algo relacionado al pago
        deduction_ids = deduction_obj.search(cr, uid, [('voucher_id','in',ids)],context=context)
        if deduction_ids:
            deduction_obj.unlink(cr, uid, deduction_ids, context=context)
        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)
    
    def _create_refund_to_payment(self, cr, uid, invoice, context=None):
        """
            Crea la nota de credito donde se aplica el descuento sobre el pago
        """
        obj_journal = self.pool.get('account.journal')
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
        if invoice['type'] == 'in_invoice':
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')], context=context)
        else:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')], context=context)
        
        date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            #'tax_line': tax_lines,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
            'invoice_id': invoice.id
        })
        
        # Agrega el campo de tipo de nota de credito si lo trae entre los parametros
        if context.get('default_filter_refund',False):
            invoice_data['filter_refund'] = context.get('default_filter_refund',False)
        
        invoice_id = inv_obj.create(cr, uid, invoice_data, context=context)
        
        # Recorre las lineas de la factura
        for line in invoice.invoice_line:
            # Obtiene el monto del descuento de venta por la linea
            subtotal = line.price_subtotal
            amount_discount = 0.0
            # Aplica al subtotal el descuento comercial y al impuesto
            if line.discount_com > 0:
                subtotal = subtotal * ((100 - line.discount_com)/100)
            # Aplica al subtotal el descuento de mezcla y al impuesto
            if line.discount_mez > 0:
                subtotal = subtotal * ((100 - line.discount_mez)/100)
            # Aplica al subtotal el descuento de volumen y al impuesto
            if line.discount_vol > 0:
                subtotal = subtotal * ((100 - line.discount_vol)/100)
            
            # Obtiene el descuento sobre la linea del producto
            amount_discount = (line.discount_fin / 100) * subtotal
            # Trunca el descuento a dos digitos
            amount_discount = float(int(amount_discount * 100.0))/100.0
            
            vals = {
                'product_id': line.product_id.id or False,
                'name': 'Descuento (Financiero: %s %%) - %s '%(line.discount_fin,line.name),
                'quantity': 1,
                'uos_id': line.uos_id.id,
                'price_unit': amount_discount,
                'account_id': line.account_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.invoice_line_tax_id])],
                'invoice_id': invoice_id
            }
            inv_line_obj.create(cr, uid, vals, context=context)
        
        # Actualiza los totales de la factura
        inv_obj.write(cr, uid, [invoice_id], {}, context=context)
        
        return invoice_id
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        """
            Crea las notas de credito en donde aplican descuentos por pronto pago
        """
        vline_obj = self.pool.get('account.voucher.line')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        wf_service = netsvc.LocalService("workflow")
        
        # Recorre los pagos y genera las notas de credito donde se aplican descuentos por pronto pago
        for voucher in self.browse(cr, uid, ids, context=context):
            # Recorre las lineas del voucher
            for line in voucher.line_cr_ids:
                # Valida si hay un descuento y si se esta reconciliando completo el pago
                if line.to_paid != line.amount:
                    print "************ pago no completo **************** "
                    continue
                    
                if line.to_paid == 0.0:
                    print "********* pago en cero *************** "
                    continue
                
                if line.invoice_id:
                    # actualiza el valor del descuento sobre las lineas de la factura
                    line_ids = inv_line_obj.search(cr, uid, [('invoice_id','=',line.invoice_id.id)])
                    inv_line_obj.write(cr, uid, line_ids, {'discount_fin': line.discount}, context=context)
                    
                    # Crea la nota de credito con la informacion del descuento financiero
                    refund_id = self._create_refund_to_payment(cr, uid, line.invoice_id, context=context)
                    
                    # Pasa la factura a abierto
                    wf_service.trg_validate(uid, 'account.invoice', \
                                                 refund_id, 'invoice_open', cr)
                    # Salda la nota de credito con la factura
                    inv_obj.generate_voucher_invoice(cr, uid, line.invoice_id.id, refund_id, context=context)
                    
                    # Obtiene el resultado obtenido del descuento aplicado sobre la factura
                    refund = inv_obj.browse(cr, uid, refund_id, context=context)
                    
                    # Actualiza el total del descuento financiero sobre la factura
                    inv_obj.write(cr, uid, [line.invoice_id.id], {'discount_fin': refund.amount_total}, context=context)
                    
                    # Agrega a la linea del pago el id de la nota de credito y actualiza el monto real pagado sobre el descuento
                    to_paid = line.amount_unreconciled - refund.amount_total
                    vline_obj.write(cr, uid, [line.id], {'refund_id':refund_id, 'discount_fin': refund.amount_total, 'to_paid': to_paid, 'amount':to_paid}, context=context)
        
        # Funcion original para crear el movimiento sobre la factura
        super(account_voucher, self).action_move_line_create(cr, uid, ids, context=context)
        return True
    
    def _get_date_notify(self, cr, uid, date, days, context=None):
        """
            Obtiene la fecha de notificacion
        """
        if days:
            date_notify = date_notify + timedelta(days=days)
            return date_notify.strftime('%Y-%m-%d')
        return date

#En este metodo hize modificaciones
    
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
        inv_obj = self.pool.get('account.voucher.line')
        disc_obj = self.pool.get('product.pricelist.discount')
        item_obj = self.pool.get('product.pricelist.discount.item')
        cur_date = time.strftime('%Y-%m-%d')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }
        
        # Obtiene los descuentos disponibles en donde se aplican pagos
        type_ids = self.pool.get('product.pricelist.discount.type').search(cr, uid, [('to_paid','=',True)], context=context) 
        
        # Obtiene el valor del descuento si va a dar descuento sobre el cobro
        print "*********** ids ********************* ", ids
        discount_voucher = context.get('apply_discount',True)
        
        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue
            
            inv_id = False
            inv_date = ''
            discount = 0.0
            discount_amount = 0.0
            
            # Agrega a la informacion del movimiento, si tiene una referencia agrega el descuento
            if line.move_id.reference:
                invoice = line.move_id.reference
                # Valida que la referencia sea una factura
                if invoice._name == 'account.invoice':
                    # Valida que la factura sea una factura de cliente y que tenga un precio de lista
                    if invoice.type == 'out_invoice' and invoice.pricelist_id:
                        # Obtiene los datos de la factura
                        inv_date = invoice.date_invoice
                        pricelist = invoice.pricelist_id.id
                        discount = 0.0
                        # Obtiene el numero de dias en relacion al pago contra la factura
                        days = disc_obj.get_number_days(cr, uid, inv_date, date, context=context) - 1
                        
                        # Valida que la factura no tenga pagos registrados
                        #if round(invoice.amount_total,0) == round(invoice.residual + invoice.discount_sale,0):
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
                                    if item_obj.validate_exception_categ(cr, uid, item.id, invoice.id, context=context):
                                        continue
                                    
                                    # Valida que los dias de la factura al pago correspondan al descuento
                                    #if item.min_quantity >= days and invoice.amount>=invoice.amount_total:
                                    #    discount += item.discount
                                    #else:
                                    #    discount = 0.0
                                    #    break
                                    if item.min_quantity >= days:
                                        discount += item.discount
                                        break
                    
                        #print "************ descuento ************* ", discount
                        # Si el descuento es mayor a cero obtiene el valor de la factura
                        if discount > 0.0:
                            discount_amount = (invoice.amount_total - invoice.discount_sale) * (discount / 100)
                            # Trunca el descuento a dos digitos
                            discount_amount = float(int(discount_amount * 100.0))/100.0
                            inv_id = invoice.id
            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #print "********* line amount residual *********** ", line.amount_residual
                #print "********* price *********** ", price
                #otherwise treatments is the same but with other field names
                if line.amount_residual - discount_amount == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                #print "********* line.amount_residual_currency *********** ", line.amount_residual_currency
                #print "********* price *********** ", price
                if line.amount_residual_currency - discount_amount == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            
            inv_id = False
            inv_date = False
            discount = 0.0
            discount_amount = 0.0
            
            # Agrega a la informacion del movimiento, si tiene una referencia agrega el descuento
            if line.move_id.reference:
                #print "***************** referencia movimiento ********** ", line.move_id.reference
                invoice = line.move_id.reference
                #print "***************** nombre factura ***************** ", invoice._name
                # Valida que la referencia sea una factura
                if invoice._name == 'account.invoice':
                    #print "******************** tipo factura *************** ", invoice.type
                    #print "************************ lista de precio ********** ", invoice.pricelist_id
                    # Valida que la factura sea una factura de cliente y que tenga un precio de lista
                    if invoice.type == 'out_invoice' and invoice.pricelist_id:
                        # Obtiene los datos de la factura
                        inv_date = invoice.date_invoice
                        pricelist = invoice.pricelist_id.id
                        discount = 0.0
                        # Obtiene el numero de dias en relacion al pago contra la factura
                        days = disc_obj.get_number_days(cr, uid, inv_date, date, context=context) - 1
                        
                        #print "*********************** dias ********************* ", days
                        # Valida que la factura no tenga pagos registrados
                        #if round(invoice.amount_total,0) == round(invoice.residual + invoice.discount_sale,0):
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
                                    if item_obj.validate_exception_categ(cr, uid, item.id, invoice.id, context=context):
                                        continue
                                    
                                    if item.min_quantity >= days:
                                        discount += item.discount
                                        break
                        
                        #print "************ descuento ************* ", discount
                        # Si el descuento es mayor a cero obtiene el valor de la factura
                        if discount > 0.0:
                            discount_amount = (invoice.amount_total - invoice.discount_sale) * (discount / 100)
                            # Trunca el descuento a dos digitos
                            discount_amount = float(int(discount_amount * 100.0))/100.0
                            inv_id = invoice.id
                        #if discount > 0.0:
                        #    if invoice.amount>=invoice.amount_total:
                        #        discount_amount = invoice.amount_total * (discount / 100)
                        #    else:
                        #        discount_amount = 0.0
                        #    inv_id = invoice.id
            # Obtiene el monto a pagar
            to_paid = amount_unreconciled 
            if discount_voucher:
                to_paid = amount_unreconciled - discount_amount
            amount_apply = (move_line_found == line.id) and min(abs(price), abs(to_paid)) or 0.0
            #print "*************** amount_apply ******************* ", amount_apply
            # Diccionario con la informacion del registro
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': amount_apply,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
                'invoice_id': inv_id,
                'date_invoice': inv_date,
                'discount_fin': discount_amount,
                'discount': discount,
                'to_paid': to_paid,
                'apply_discount': discount_voucher
            }
            
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_line_found:
                if currency_id == line_currency_id:
                    #print "*************** amount_unreconciled ******************* ", amount_unreconciled
                    #print "*************** discount ******************* ", discount_amount
                    #print "*************** total_debit ******************* ", total_debit
                    #print "*************** total_credit ******************* ", total_credit
                    
                    if line.credit:
                        amount = min(amount_unreconciled - discount_amount, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled - discount_amount, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if (rs['amount_unreconciled'] - rs['discount_fin']) == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        """
            Calcula el descuento financiero sobre los apuntes en los que aplica
        """
        #print "***************** funcion onchange_partner_id ******************* "
        
        # Funcion original
        res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
        
        #print "************** res onchange partner ******************** ", res
        
        return res
    
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, apply_discount= True, context=None):
        """
            Agrega sobre la funcion el context de si aplica descuento o no
        """
        if context is None:
            context = {}
        context['apply_discount'] = apply_discount
        # Funcion original
        res = super(account_voucher, self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=context)
        
        return res
    
    #def button_proforma_voucher(self, cr, uid, ids, context=None):
    #    context = context or {}
    #    res = super(account_voucher, self).button_proforma_voucher(cr, uid, ids,context=context)
    #    
    #    return 
    
    def onchange_date_voucher(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        """
            Actualiza la informacion del voucher
        """
        # Funcion onchange de contacto para actualizar los conceptos de los pagos
        res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
        # Funcion original de onchange date
        res_date = self.onchange_date(cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context=context)
        
        # Combina los resultados de los onchange en uno solo
        for value in res_date['value']:
            res['value'][value] = res_date['value'][value]
        return res
    
    def onchange_date_voucher_invoice(self, cr, uid, ids, partner_id, journal_id, amount, invoice_amount, apply_discount, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        """
            Actualiza la informacion del voucher
        """
        inv_obj = self.pool.get('account.invoice')
        
        # Funcion original de onchange date
        res = self.onchange_date(cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context=context)
        
        print "*********** date ************* ", date
        print "*********** invoice_id ************* ", context.get('invoice_id',False)
        print "*********** apply discount ************* ", apply_discount
        # Recalcula el descuento sobre la factura
        if context.get('invoice_id',False) and apply_discount == True:
            discount_amount, amount = inv_obj.get_discount_payment_invoice(cr, uid, context.get('invoice_id',False), date, context=context)
            res['value']['discount'] = discount_amount
            res['value']['amount'] = amount
        else:
            res['value']['discount'] = 0.0
            res['value']['amount'] = invoice_amount
        return res
    
account_voucher()

class account_voucher_line(osv.Model):
    _inherit = 'account.voucher.line'
    
    def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, apply_discount, discount, context=None):
        """
            Valida si aplica el descuento sobre la linea del cobro
        """
        to_paid = amount_unreconciled
        if apply_discount:
            to_paid = amount_unreconciled - discount
        vals = {'amount': 0.0, 'to_paid': to_paid}
        if reconcile:
            vals = { 'amount': to_paid}
        return {'value': vals}

    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, apply_discount, discount, context=None):
        vals = {}
        to_paid = amount_unreconciled
        
        # Valida si tiene que aplicar descuento
        if apply_discount:
            to_paid = amount_unreconciled - discount
        print "****** apply_discount ************** ", apply_discount
        print "******* to_paid *********** ", to_paid
        print "******* amount ********** ", amount
        
        # Actualiza el resultado del monto a pagar
        if amount:
            vals['reconcile'] = (round(amount,2) == (round(to_paid,2)))
            vals['to_paid'] = to_paid
        return {'value': vals}
    
    _columns = {
        'date_invoice':fields.date('Fecha Factura'),
        'invoice_id': fields.many2one('account.invoice','Factura'),
        'refund_id': fields.many2one('account.invoice','Nota de credito'),
        'discount_fin': fields.float('Des. Financiero', digits_compute=dp.get_precision('Account')),
        'discount': fields.float('Descuento', digits_compute=dp.get_precision('Account')),
        'to_paid': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        'apply_discount': fields.boolean('Aplica descuento')
    }
    
    _defaults = {
        'date_invoice': lambda *a: time.strftime('%Y-%m-%d'),
        'apply_discount': True
    }
    
account_voucher_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
