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

from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from Tkinter import *

class sale_order(osv.Model):
    _inherit = "sale.order"
    
    def action_view_invoice_partner(self, cr, uid, ids, context=None):
        """
            Redirecciona a la vista formulario de las facturas del cliente seleccionado
        """
        # Obtiene el id del cliente seleccionado
        order = self.browse(cr, uid, ids[0], context=context)
        customer_id = order.partner_id.id or False
        
        # Actualiza los valores de retorno para el context con el filtrado de los datos a mostrar
        context['search_default_partner_id'] = customer_id
        context['default_type'] = 'out_invoice'
        context['type'] = 'out_invoice'
        context['journal_type'] = 'sale'
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_tree')
        
        # Obtiene la vista de busqueda
        search_dummy, search_view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_account_invoice_filter')
        
        return {
            'name':_("Facturas Cliente"),
            'view_mode': 'tree',
            'search_view_id': search_view_id,
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('type','=','out_invoice')]",
            'context': context
        }
    
    def button_print_payments(self, cr, uid, ids, context=None):
        """
            Manda llamar el boton original de imprimir pagos que se encuentra en account_followup
        """
        partner_obj = self.pool.get('res.partner')
        # Recorre los registros
        for order in self.browse(cr, uid, ids, context=context):
            # Valida que se haya seleccionado un partner para poder imprimir
            if not order.partner_id:
                raise osv.except_osv(_('Warning!'),_("No se ha seleccionado ningun cliente!"))
            else:
                partner_obj.do_button_print(cr, uid, [order.partner_id.id], context=context)
        return True
    
    def _get_credit(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el credito disponible del cliente
        """
        res = {}
        # Recorre las ventas recibidas en el parametro
        for sale in self.browse(cr, uid, ids, context=context):
            res[sale.id] = 0.0
            # Valida si hay una relacion con una oportunidad
            if sale.partner_id:
                res[sale.id] = sale.partner_id.credit_available
        return res
    
    def _compute_discount(self, cr, uid, ids, context=None):
        """
            Actualiza los descuentos del producto
        """
        line_obj = self.pool.get('sale.order.line')
        line_ids = []
        # Recorre los registros
        for order in self.browse(cr, uid, ids, context=context):
            # Recorre las lineas del pedido de venta
            for line in order.order_line:
                print "************* line discount change *************** ", line.price_unit
                print "************* line discount change *************** ", line.discount_change
                price = line.price_unit_original
                vals = {}
                
                # Valida que haya algun cambio en el descuento
                if order.pricelist_change == False and line.discount_change == True and line.price_change == True:
                    #print "**********+ no aplica *********+"
                    continue
                
                # Si se cambio la lista de precio debe quitar el indicador que dice si se modifico un descuento
                if order.pricelist_change == True:
                    # agrega el id al arreglo para despues modificar el objeto line_obj
                    line_ids.append(line.id)
                    # Obtiene el nuevo precio del producto
                    if line.product_id:
                        price = line_obj._get_price_product(cr, uid, line.product_id.id, order.pricelist_id.id, line.product_uom_qty, order.partner_id.id, line.product_uom.id, order.date_order, context=context)
                
                # Pone el valor original de los descuentos
                if line.discount_change != True:
                    vals = {
                        's_discount_com': line.discount_com,
                        's_discount_vol': line.discount_vol,
                        's_discount_mez': line.discount_mez,
                    }
                
                # Valida si se modifico el precio del producto, sino pone el precio original
                if line.price_change != True:
                    vals['price_unit'] = price
                
                # Valida si se modifico l
                if order.pricelist_change == True:
                    vals['discount_change'] = False
                    vals['price_change'] = False
                
                #print "************* update vals *********************", vals
                line_obj.write(cr, uid, [line.id], vals, context=context)
                #print "*************line_id*********************", line.id
            #cambia el valor de discount_change
            #line_obj.write(cr, uid, line_ids, {'discount_change': False, 'price_change':False}, context=context)
            #print "*************line_ids*********************", line_ids
        return True
    
    def _compute_mix(self, cr, uid, ids, context=None):
        """
            Calcula el total de las mezclas sobre el pedido
        """
        mix_obj = self.pool.get('sale.order.mix')
        
        # Recorre los registros
        for order in self.browse(cr, uid, ids, context=context):
            # Obtiene el total de conceptos cargados sobre el pedido de venta
            cr.execute("""
                select l.order_id, sum(l.product_uom_qty), sum(l.weight * l.product_uom_qty) as Peso
                from sale_order_line as l
                where l.order_id = %s
                group by l.order_id"""%(order.id))
            quantity_order = 0.0
            weight_order = 0.0
            for value in cr.fetchall():
                print "************ value ************* ", value
                quantity_order = float(value[1])
                weight_order = float(value[2])
                break
            #print "************ quantity order *********** ", quantity_order
            
            # Elimina las mezclas calculadas anteriormente sobre el pedido de venta
            mix_ids = mix_obj.search(cr, uid, [('order_id','=',order.id)], context=context)
            mix_obj.unlink(cr, uid, mix_ids, context=context)
            
            # Valida que haya registrados productos sobre la venta
            if quantity_order == 0.0:
                return True
            
            # Si se encontraron productos en el pedido de venta, obtiene los resultados por categoria
            cr.execute("""
                select
                    l.order_id, t.categ_id, sum(l.product_uom_qty), sum(t.weight * l.product_uom_qty)
                from
                    sale_order_line as l
                    inner join product_product as p on l.product_id=p.id
                    inner join product_template as t on t.id=p.product_tmpl_id
                where
                    order_id = %s
                group by l.order_id,t.categ_id"""%(order.id))
            for value in cr.fetchall():
                quantity = 0
                weight = 0
                if value[2]:
                    quantity = int(value[2])
                    weight = int(value[3])
                vals = {
                    'order_id': value[0] or False,
                    'categ_id': value[1] or False,
                    'quantity': quantity,
                    'weight': weight,
                    'percent': 0.0
                }
                
                # Calcula el porcentaje sobre las mezclas
                if weight_order != 0:
                    print "**************** "
                    vals['percent'] = (weight * 100.0)/weight_order
                # Crea el nuevo registro de mezcla
                mix_id = mix_obj.create(cr, uid, vals, context=context)
        return True
    
    def action_button_confirm(self, cr, uid, ids, context=None):
        """
            Genera la factura en borrador despues de confirmar el pedido, solo si esta en la politica bajo demanda
        """
        # Funcion original
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        
        # Recorre los registros
        for sale in self.browse(cr, uid, ids, context=context):
            # Valida si la politica de facturacion es bajo demanda
            if sale.order_policy == 'manual':
                result = self.manual_invoice(cr, uid, [sale.id], context)
        return res
    
    def button_dummy(self, cr, uid, ids, context=None):
        """
            Actualiza informacion de pedido de venta
        """
        # Manda actualizar las mezclas del pedido
        self._compute_mix(cr, uid, ids, context=context)
        self._compute_discount(cr, uid, ids, context=context)
        self.write(cr,uid,ids,{'pricelist_change':False, 'created':True},context=context)
        
        return super(sale_order, self).button_dummy(cr, uid, ids, context=context)
    
    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        """
            Actualiza el diario segun la tienda que este seleccionada
        """
        res = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, context=context)
        # validamos que se reciba un tipo de tarifa sobre el registro
        
        if shop_id:
            res['value']['journal_id'] = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context).journal_id.id or False
        
        return res
    
    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
        """
            Cambia verdadero el cambio de precio para modificar los precios mostrados
        """
        res = super(sale_order, self).onchange_pricelist_id(cr, uid, ids, pricelist_id, order_lines, context=context)
        # validamos que se reciba un tipo de tarifa sobre el registro
        
        if pricelist_id:
            # Modificmos la variable pricelist_change a verdadero
            #print "**************** onchage pricelist **************", pricelist_change
            res['value']['pricelist_change'] = True
            if res.get('warning',False):
                # Actualizar mensaje que se muestra al cambiar la tarifa
                warning = {
                    'title': _('Lista de precio modificada!'),
                    'message' : _('Si se cambia la lista de precio del Cliente, pasara el pedido por una previa autorizacion antes de ser confirmado.')
                }
                res['warning'] = warning
        return res
    
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        """
            Agrega los campos de credito al modulo de ventas
        """
        warning_msgs = ""
        partner_obj = self.pool.get('res.partner')
        res = super(sale_order,self).onchange_partner_id(cr, uid, ids, part, context=context)
        if part:
            partner = partner_obj.browse(cr, uid, part, context=context)
            if partner:
                res['value']['credit'] = partner.credit
                res['value']['credit_available'] = partner.credit_available
                res['value']['journal_id'] = partner.journal_id.id or False
            
            if not res.get('domain',False):
                res['domain'] = {}
            
            # Dominio para filtrar los clientes para el envio
            domain = ['|',('branch_id.user_ids','in',(uid)),('branch_id','=',False),('type','=','delivery')]
            domain.append('|')
            domain.append(('id','=',part))
            domain.append(('parent_id','=',part))
            res['domain']['partner_shipping_id'] = domain
            
            #--------------- modifique lo que sigue-----------------
            if (partner.credit_available <= 0.0):
                warning_msgs += _("El cliente no cuenta con credito, para pedir credito ir a solicitud de credito .") + "\n\n"
            
            if warning_msgs:
                res['warning'] = {
                           'title': _('Advertencia!'),
                           'message' : warning_msgs
                        }
        
        return res
    
    #def create(self, cr, uid, vals, context=None):
    #    if vals.get('name','/')=='/':
    #        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
    #    return super(sale_order, self).create(cr, uid, vals, context=context)
    
    #def _create_invoices(self, cr, uid, inv_values, sale_id, context=None):
    #    inv_obj = self.pool.get('account.invoice')
    #    sale_obj = self.pool.get('sale.order')
    #    inv_id = inv_obj.create(cr, uid, inv_values, context=context)
    #    inv_obj.button_reset_taxes(cr, uid, [inv_id], context=context)
    #    # add the invoice to the sales order's invoices
    #    sale_obj.write(cr, uid, sale_id, {'invoice_ids': [(4, inv_id)]}, context=context)
    #    return inv_id
    
    def create_invoice(self, cr, uid, ids, context=None):
        """
            Crea la factura del pedido
        """
        res = self.manual_invoice(cr, uid, ids, context)
        return res
    
    def create_order(self, cr, uid, ids, context=None):
        """
            Manda actualizar el registro para que se guarde el documento
        """
        self.button_dummy(cr, uid, ids, context=context)
        return True
    
    def notify_message(self, cr, uid, res_id, model, subject, body, context=None):
        """
            Agrega una nota para los seguidores del pedido de venta
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        email_from = user.email
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'body': body,
            'email_from': email_from,
            'partner_ids': [],
            #'attachment_ids': [(6, 0, attachments)],
            'res_id': res_id,
            'model': model,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'author_id': uid
        }
        mail_message_id = self.pool.get('mail.message').create(cr, uid, values_message, context=context)
        
        return True
    
    def action_button_validate(self, cr, uid, ids, context=None):
        """
            Revisa si se realizo algún cambio de precio de lista o de descuento en algun producto y
            si es asi pide autorización
        """
        msgs = []
        msgs2 = ""
        pending = ""
        product_obj = self.pool.get('product.product')
        
        for order in self.browse(cr, uid, ids, context=context):
            res = True
            
            # Si se deja solo order.pricelist_id te regresa ids y no puedes recorrerlo con un for por eso se pone .id
            if (order.pricelist_id.id or False) != (order.partner_id.property_product_pricelist.id or False):
                res = False
                msgs.append("Se ha cambiado la tarifa predeterminada (Tarifa:%s)."%(order.partner_id.property_product_pricelist.name,))
                #raise osv.except_osv(_('Warning!'),_("La cotización tendra que ser autorizada porque se ha cambiado la tarifa predeterminada!"))
                pending = "discount"
            for line in order.order_line:
                # Revisa si hubo algun cambio de descuento
                if line.discount_change:
                    if (line.s_discount_com > line.discount_com) or (line.s_discount_vol > line.discount_vol) or (line.s_discount_mez > line.discount_mez):
                        res =  False
                        msgs.append("Se han modificado los descuentos permitidos en la linea %s."%(line.name,))
                        pending = "discount"
                
                # Valida que no disminuya el precio original del producto
                if line.price_unit < line.price_unit_original:
                    res =  False
                    msgs.append("Se ha modificado el precio unitario original en la linea %s."%(line.name))
                    #print "****************** precio producto ************* ", line.price_unit
                    #print "******************* precio original ************ ", line.price_unit_original
                # Valida que el precio protegido sea menor al precio total del producto 
                if line.product_id:
                    # Obtiene el descuento aplicado sobre el producto
                    discount = line.price_unit * (line.s_discount_com + line.s_discount_vol + line.s_discount_mez)/100
                    
                    protected_price = line.product_id.protected_price
                    product_price = line.price_unit - discount
                    #Valida que el producto tenga protected_price
                    if protected_price == 0:
                        continue
                    # Valida que el precio de venta del producto sea mayor al precio protegido
                    if protected_price >= product_price:
                        raise osv.except_osv(_('Error!'),_("El producto %s es menor que el precio protegido permitido para poder confirmar la venta!"%(line.product_id.name,)))
                
                #for price in products:
                #    if line.price_unit < price.protected_price:
                #        res =  False
                #        warning_msgs += _("El precio del producto es menor al precio protegido .") + "\n\n"
            
            #if (order.credit > 0):
            #    res = False
            #    msgs.append("El cliente tiene adeudo pendiente (Adeudo: %s)."%(order.credit,))
            #    pending = "credit"
            # Valida que el cliente tenga credito disponible para que le generen la factura
            if (order.credit_available < order.amount_total):
                # Valida que el mentodo de pago de la factura no sea por pago inmediato
                payment_days = 0.0
                # Obtiene la cantidad de dias sobre el credito
                if order.payment_term:
                    for line in order.payment_term.line_ids:
                        payment_days += line.days
                # Si hay un plazo de pago verifica si tiene credito disponible
                if payment_days > 0.0:
                    res = False
                    credit = 0.0
                    if order.credit_available:
                        credit = order.credit_available
                    msgs.append("El cliente no cuenta con el credito disponible (Credito disponible: %s)."%(credit,))
                    pending = "credit"
            # Valida que res sea verdadero y si es asi es que se hizo alguna modificacion
            if res:
                return self.action_button_confirm(cr, uid, ids, context=context)
            else:
                # Pasa a por autorizar si no se cumplieron todas las validaciones
                if pending == "discount":
                    self.write(cr, uid, ids, {'state': 'pending_discount'}, context=context)
                else:
                    self.write(cr, uid, ids, {'state': 'pending_credit'}, context=context)
                    
                msgs2 += _("      Para realizar este pedido tendra que pasar por previa Autorizacion por las siguientes razones: .") + "\n\n"
                for msg in msgs:
                    msgs2 += "           -" + msg + "\n"
                
                # Registra una nota sobre el mensaje de error
                subject = "Autorizacion de Pedido de Venta"
                body_mail = """
                                <h3>Autorizacion de Pedido de venta %s</h3>
                                <div>Para realizar este pedido tendra que pasar por previa Autorizacion por las siguientes razones:
                                    <ul>
                            """%(order.name,)
                for msg in msgs:
                    body_mail += "<li type='disc'>" + msg + "</li>"
                body_mail += "</ul></div>"
                # Registra mensaje sobre pedido de venta
                self.notify_message(cr, uid, order.id, order._name, subject, body_mail, context=context)
                
        return self.pool.get('warning').error(cr, uid, title='Advertencia!', message=_(msgs2))
    
    def _amount_line_discount_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_import, 1, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        """
            Agrega el descuento en los subtotales y lo resta
        """
        cur_obj = self.pool.get('res.currency')
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'discount_total': 0.0,
                'amount_discount': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_import': 0.0
            }
            val = 0.0
            amount_discount = 0.0
            discount_total = 0.0
            amount_untaxed = 0.0
            amount_tax = 0.0
            cur = order.pricelist_id.currency_id
            #Recorro linea por linea del pedido de venta
            for line in order.order_line:
                # Calcula los impuestos de la linea del pedido
                tax = self._amount_line_tax(cr, uid, line, context=context)
                discount_tax = self._amount_line_discount_tax(cr, uid, line, context=context)
                #print "************** discount_tax ************* ", discount_tax
                discount = cur_obj.round(cr, uid, cur, line.price_import) - cur_obj.round(cr, uid, cur, line.price_subtotal)
                #print "******************* discount ************* ", discount
                # Informacion del resultado para la obtencion del total
                amount_tax += discount_tax
                amount_untaxed += line.price_subtotal
                amount_discount += discount
                discount_total += tax - discount_tax - discount
                
            #print "************ discount total ************ ", discount_total
            res[order.id]['discount_total'] = cur_obj.round(cr, uid, cur, discount_total)
            res[order.id]['amount_discount'] = cur_obj.round(cr, uid, cur, amount_discount)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, amount_tax)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, amount_untaxed)
            res[order.id]['amount_import'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_discount']
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['amount_discount']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def _get_total_weight(self, cr, uid, ids, field_name, args, context=None):
        """
            Calcula el peso total de todo el pedido de venta
        """
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            total = 0
            for line in move.order_line:
                # Sumando el peso de cada producto en la linea del pedido de venta
                total += line.weight_import
            res[move.id] = total
            
        return res
    
    _columns = {
        'mix_ids': fields.one2many('sale.order.mix', 'order_id', 'Mezclas'),
        'partner_credit': fields.function(_get_credit, method=True, string='Saldo disponible', digits_compute= dp.get_precision('Account'), readonly=True, type='float', store=True, help="Saldo disponible del cliente sobre los creditos."),
        
        'amount_import': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Base',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="descuento aplicado sobre lineas de pedido."),
        'amount_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Descuento',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="descuento aplicado sobre lineas de pedido."),
        'discount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Descuento',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="descuento aplicado sobre lineas de pedido."),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        
        'pricelist_change': fields.boolean('cambio precio de lista'),
        'credit': fields.related('partner_id', 'credit', type="float", digits_compute=dp.get_precision('Account'), string="Adeudo pendiente", store=False, readonly=True),
        'credit_available': fields.related('partner_id', 'credit_available', type="float", digits_compute=dp.get_precision('Account'), string="Credito disponible", store=False, readonly=True),
        #'journal_id': fields.many2one('account.journal', 'Account Journal', help="Este diario sera creado automaticamente para la cuenta del cliente activo cuando confirme el pedido", required=True),
        'journal_id': fields.many2one('account.journal', 'Documento', domain=[('type','in',['sale'])], context={'type': 'sale'}, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Este diario sera creado automaticamente para la cuenta del cliente activo cuando confirme el pedido"),
        'state': fields.selection([
            ('draft', 'Presupuesto borrador'),
            ('sent', 'Cotizaciones enviadas'),
            ('cancel', 'Cancelado'),
            ('waiting_date', 'Waiting Schedule'),
            ('pending_credit', 'Autorizacion por Credito'),
            ('pending_discount', 'Autorizacion por Descuento'),
            ('progress', 'Pedido de Venta'),
            ('manual', 'Venta a Facturar'),
            ('invoice_except', 'Exepcion de Factura'),
            ('shipping_except', 'Excepcion de Envio'),
            ('done', 'Realizado'),
            ], 'Estado', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
        'created': fields.boolean('creado'),
        'branch_id': fields.related('user_id', 'branch_id', type="many2one", relation="access.branch", store=True, string="Acceso", readonly=True),
        'weight_total': fields.function(_get_total_weight, type="float", string="Peso total vendido", store=False,
            digits_compute=dp.get_precision('Account')),
    }
    #def onchange_partner_id(self, cr, uid, ids, field, context=None):
    #    """
    #        Actualiza la sucursal y pone la sucursal del cliente en el partner
    #    """
    #    # Obtiene el valor de la sucursal del padre
    #    partner = self.pool.get('res.partner').browse(cr, uid, field, context=context)
    #    return {'value':{'branch_id': partner.branch_id.id}}
    
    def _get_branch_default_id(self, cr, uid, context=None):
        """
            Obtiene la sucursal del usuario y la pone por default para el cliente
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.branch_id.id or False
    
    _defaults = {
        'pricelist_change': False,
        'created': False,
        'branch_id': _get_branch_default_id,
        #'order_policy': 'prepaid'
    }
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """
            Agrega a la informacion de la factura el precio de lista aplicado sobre el pedido de venta
        """
        if context is None:
            context = {}
        # Ejecuta funcion original
        invoice_vals = res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)

        # Agrega la informacion del precio de lista al diccionario de retorno
        invoice_vals['pricelist_id'] = order.pricelist_id.id or False
        invoice_vals['discount_sale'] = order.discount_total or 0.0
        if order.journal_id:
            invoice_vals['journal_id'] = order.journal_id.id or False
        return invoice_vals
    
sale_order()

class sale_order_mix(osv.osv):
    _name = "sale.order.mix"
    _description = "Mezclas producto por categoria"

    _columns = {
         'order_id': fields.many2one('sale.order', 'Venta', ondelete='cascade', help="Pedido de venta."),
         'categ_id': fields.many2one('product.category', 'Categoria', ondelete='restrict', help="Categoria de producto sobre pedido de venta."),
         'weight': fields.float('Peso Total', digits_compute= dp.get_precision('Account')),
         'quantity': fields.float('Cantidad', digits_compute= dp.get_precision('Account')),
         'percent': fields.float('Porcentaje', digits_compute= dp.get_precision('Account')),
    }

sale_order_mix()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    def _get_price_product(self, cr, uid, product_id, pricelist, qty, partner_id, uom, date_order, context=None): 
        """
            Obtiene el precio del producto sobre la linea de pedido
        """
        # Obtiene el precio del producto
        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                        product_id, qty or 1.0, partner_id, {
                            'uom': uom,
                            'date': date_order,
                            })[pricelist]
        # Valida que haya un producto sobre la lista de precio
        if price is False:
            product = self.pool.get('product.product').browse(cr, uid, [product_id], context=context)
            raise osv.except_osv(_('Error!'),_("No se ha encontrado un precio disponible para el producto sobre la lista de precio seleccionada. (producto: %s)!"%(product.name,)))
            
        return price
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        """
            Agrega al retorno el valor del precio unitario al campo de precio unitario original
        """
        # Funcion original
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
                        uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                        lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        #print "********************* res product_change ************* ", res
        
        # Agrega el valor nuevo al retorno
        res['value']['price_unit_original'] = res['value'].get('price_unit',0.0)
        
        # Agrega el valor del peso del producto
        if product:
            product = self.pool.get('product.product').browse(cr, uid, product, context=context)
            res['value']['weight'] = product.weight
        return res
    
    def _get_discount_pricelist(self, cr, uid, ids, name, arg, context=None):
        """
            Obtiene los descuentos por lista de precio
        """
        # Inicializa variables
        product_obj = self.pool.get('product.product')
        disc_obj = self.pool.get('product.pricelist.discount')
        mix_obj = self.pool.get('sale.order.mix')
        res = {}
        discount = {}
        apply_discount = False
        weight_total = 0.0
        
        # Obtiene la tarifa que aplica sobre el pedido de venta
        pricelist = False
        line = self.browse(cr, uid, ids[0], context=context)
        if line:
            pricelist = line.order_id.pricelist_id.id
            weight_total = line.order_id.weight_total
        
        # Obtiene los descuentos disponibles en donde se aplican sobre los productos
        type_ids = self.pool.get('product.pricelist.discount.type').search(cr, uid, [('to_mix','=',False),('to_paid','=',False),('to_quantity','=',True)], context=context) 
        # Obtiene los descuentos que se deben aplicar sobre los productos
        discount_ids = disc_obj.search(cr, uid, [('type_id','in',type_ids),('pricelist_id','=',pricelist)])
        if discount_ids:
            # Recorre los descuentos que aplican sobre el volumen
            for disc in disc_obj.browse(cr, uid, discount_ids, context=context):
                # Valida que el descuento tenga un codigo
                if not disc.type_id.key:
                    continue
                
                # Recorre las reglas aplicadas sobre el descuento
                for item in disc.item_ids:
                    # Valida si aplica el descuento sobre el pedido
                    if item.min_quantity <= weight_total:
                        # Valida que exista sobre el diccionario el datos, sino lo inicializa 
                        if not discount.get(disc.type_id.key):
                            discount[disc.type_id.key] = {
                                'val': 0.0,
                                'field': disc.type_id.key
                            }
                        # Actualiza el descuento aplicado por volumen
                        discount[disc.type_id.key]['val'] += item.discount
                        break
        
        # Obtiene los descuentos disponibles en donde se aplican mezclas
        type_ids = self.pool.get('product.pricelist.discount.type').search(cr, uid, [('to_mix','=',True)], context=context) 
        # Valida si se debe aplicar un descuento sobre las mezclas
        discount_ids = disc_obj.search(cr, uid, [('type_id','in',type_ids),('pricelist_id','=',pricelist)])
        if discount_ids:
            # Recorre los descuentos sobre mezclas y valida si se aplican en alguna de las reglas
            for disc in disc_obj.browse(cr, uid, discount_ids, context=context):
                print "****DISC.NAME****: ", disc.name
                #print "************** descuento ", disc.type_id.key, " - ", disc.name, "  *************** "
                
                # Valida que el descuento tenga un codigo
                if not disc.type_id.key:
                    continue
                
                # Recorre las reglas aplicadas sobre el descuento
                for item in disc.item_ids:
                    print"*****ITEM.NAME****: ", item.name
                    apply_discount = True
                    # Valida que se apliquen mezclas sobre el descuento
                    if item.to_mix == False:
                        continue
                    
                    #print "************** regla ", item.name, "  *************** ", item.sequence
                    
                    # Recorre las categorias de la mezcla
                    for mx in item.mix_ids:
                        print"*****MX.NAME****: ", mx.categ_id
                        # Total porcentaje sobre la mezcla
                        mix_percent = 0.0
                        mix_quantity = 0.0
                        
                        # Valida si se encuentra la categoria sobre las mezclas del descuento y que se encuentre dentro del rango del porcentaje de la mezcla
                        mix_ids = mix_obj.search(cr, uid, [('order_id','=',line.order_id.id),'|',('categ_id','=',mx.categ_id.id),('categ_id.parent_id','=',mx.categ_id.id)])
                        #print "***** mix ids ********* ", mix_ids
                        # Valida que la mezcla se aplique sobre los descuentos
                        if mix_ids:
                            # Obtiene el total del porcentaje y cantidad sobre la mezcla
                            for mix in mix_obj.browse(cr, uid, mix_ids, context=context):
                                mix_percent += mix.percent
                                mix_quantity += mix.weight
                                
                            #print "************ percent ******** ", mix_percent
                            #print "*********MIX_QUANTITY*******: ", mix_quantity
                            #
                            ##print "************ quantity ******** ", mix_quantity
                            #print "*********MIN_PROPORTION******: ", mx.min_proportion
                            #print "*********MAX_PROPORTION*******: ", mx.max_proportion
                            #print "*********MIN_QUANTITY********: ", item.min_quantity
                            
                            # Valida que los descuentos del producto den a la suma
                            if mix_percent >= mx.min_proportion and mix_percent <= mx.max_proportion and mix_quantity >= item.min_quantity:
                                print "**********APLICANDO DESCUENDO DE MEZCLA*************"
                                apply_discount = True
                            else:
                                #print "**********NO SE HA APLICADO DESCUENTO DE MEZCLA**********"
                                apply_discount = False
                                break
                        else:
                            apply_discount = False
                            break
                        
                    # Si se cumple la regla termina la busqueda
                    if apply_discount == True:
                        # Valida que exista sobre el diccionario el datos, sino lo inicializa 
                        if not discount.get(disc.type_id.key):
                            discount[disc.type_id.key] = {
                                'val': 0.0,
                                'field': disc.type_id.key
                            }
                        #print "****** actualiza descuento ************* ", item.discount
                        discount[disc.type_id.key]['val'] += item.discount
                        break
        
        #print "**************** discount ************ ", discount
        
        # Obtiene los descuentos disponibles en donde se aplican sobre los productos
        type_ids = self.pool.get('product.pricelist.discount.type').search(cr, uid, [('to_mix','=',False),('to_paid','=',False),('to_quantity','=',False)], context=context) 
        # Obtiene los descuentos que se deben aplicar sobre los productos
        discount_ids = disc_obj.search(cr, uid, [('type_id','in',type_ids),('pricelist_id','=',pricelist)])
        
        # Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context):
            # Inicializa descuentos sobre la regla
            res[line.id] = {
                'discount_com': 0.0,
                'discount_vol': 0.0,
                'discount_mez': 0.0
            }
            
            # Actualiza el resultado sobre la mezcla
            for dis in discount:
                #print "************** descuento ************** ", dis
                #print "************** get descuento ************** ", res[line.id].get(dis, False)
                #print "************** valor descuento ************** ", discount[dis]['val']
                #print "************** validacion descuento x ************** ", 0.0 != False
                #print "************** validacion descuento ************** ", res[line.id].get(dis, None) is not None
                
                # Valida que la columna del descuento exista
                if res[line.id].get(dis, None) is not None:
                    res[line.id][dis] += discount[dis]['val']
                    #print "******** res ****** ", res[line.id]
            
            # Valida que haya descuentos por aplicar sobre los otros conceptos
            if not discount_ids:
                continue
            
            # Recorre los descuentos disponibles sobre las tarifas
            for disc in disc_obj.browse(cr, uid, discount_ids, context=context):
                # Valida que el descuento tenga un codigo
                if not disc.type_id.key:
                    continue
                
                # Valida si alguna regla del descuento aplica sobre el producto
                for item in disc.item_ids:
                    apply_discount = True
                    
                    # Valida la cantidad sobre la linea del producto
                    if line.weight_import < item.min_quantity:
                        apply_discount = False
                        continue
                    
                    # Valida si tiene seleccionado un producto sobre el detalle
                    if item.product_id:
                        # Valida que haya seleccionado un producto sobre la linea de pedido
                        if not line.product_id:
                            #print "********* no producto ********* "
                            apply_discount = False
                            continue
                        
                        # Valida que el producto sea el mismo que el de la regla
                        if line.product_id.id != item.product_id.id:
                            #print "********* producto dif a la regla ************* "
                            apply_discount = False
                            continue
                    
                    # Valida si tiene seleccionada una categoria sobre el detalle
                    if item.categ_id:
                        # Valida que haya seleccionado un producto sobre la linea de pedido
                        if not line.product_id:
                            #print "************* no producto en categoria *********** "
                            apply_discount = False
                            continue
                        
                        # Valida que el producto tenga seleccionada una categoria
                        if not line.product_id.categ_id:
                            #print "********* no categoria ******* "
                            apply_discount = False
                            continue
                        
                        # Valida que la categoria del producto sea la misma que la categoria de la regla
                        if line.product_id.categ_id.id != item.categ_id.id:
                            #print "********* categoria dif a la regla ********* "
                            
                            # Valida que haya una categoria padre en el arbol
                            if not line.product_id.categ_id.parent_id:
                                #print "********* no categoria padre ********* "
                                apply_discount = False
                                continue
                            
                            # Valida si coincide con la categoria padre
                            if line.product_id.categ_id.parent_id.id  != item.categ_id.id:
                                #print "********* categoria padre dif a la regla ********* "
                                apply_discount = False
                                continue
                    
                    # Si la regla se cumple detiene el proceso
                    if apply_discount == True:
                        
                        #print "************* registro sobre descuento ***** ", res[line.id].get(disc.type_id.key, False)
                        # Valida que la columna del descuento exista
                        if res[line.id].get(disc.type_id.key, None) is not None:
                            #print "******** valor descuento ****************** ", item.discount
                            # Actualiza el resultado
                            res[line.id][disc.type_id.key] += item.discount
                        break
                
                #print "********* descuento lista ********* ", disc.type_id.key
                #print "********** descuento texto ********* ", res[line.id].get(disc.type_id.key)
                #print "********** aplica descuento ******** ", apply_discount
                
        #print "********** res ******** ", res
            
        return res
    
    def onchange_discount_change(self, cr, uid, ids, s_discount_com, s_discount_vol, s_discount_mez, discount_com, discount_vol, discount_mez, context=None):
        """
            Cambia verdadero el cambio de precio para modificar los precios mostrados
        """
        #inicializamos las variables
        res = {}
        msgs = ""
        # Asignamos los valores actuales a mi diccionario
        res['discount_change'] = True
        # Actualiza variable de retorno
        res = {'value':res}
        # Valida que el descuento no sea mayor al descuento aplicado originalmente
        if s_discount_com != discount_com or s_discount_vol != discount_vol or s_discount_mez != discount_mez:
            msgs += _("Se ha modificado el descuento a un descuento mayor del permitido, su pedido se enviara a un proceso de autorizacion.") + "\n\n"
        
        # Valida si tiene que retornar un mensaje
        if msgs != '':
            res['warning'] = {
                'title': _('Advertencia!'),
                'message' : msgs
            }
        return res
    
    def onchange_price_unit(self, cr, uid, ids, price_unit_original, price_unit, context=None):
        """
            Indica que se cambio el precio unitario sobre el producto
        """
        #inicializamos las variables
        res = {}
        msgs = ""
        
        print "**************** precio original ***************** ", price_unit_original, " - precio ", price_unit
        # Recorre los registros sobre el precio unitario 
        if price_unit_original > price_unit:
            msgs += _("Se ha modificado el precio unitario a un precio menor del permitido, su pedido se enviara a un proceso de autorizacion.") + "\n\n"
        # Asignamos los valores actuales a mi diccionario
        if price_unit_original != price_unit:
            res['price_change'] = True
        # Actualiza variable de retorno
        res = {'value':res}

        # Valida si tiene que retornar un mensaje
        if msgs != '':
            res['warning'] = {
                'title': _('Advertencia!'),
                'message' : msgs
            }
        return res
    
    def action_refresh_line(self, cr, uid, ids, context=None):
        """
            Actualiza los precios con los valores predefinidos por la tarifa del cliente
        """
        #print "*************** action_refresh **************"
        # Obtiene el objeto a cargar
        for line in self.browse(cr, uid, ids, context=context):
        
            vals = {
                'price_unit': line.price_unit_original,
                's_discount_com': line.discount_com,
                's_discount_vol': line.discount_vol,
                's_discount_mez': line.discount_mez,
                'discount_change': False,
                'price_change': False
            }
            #print "*************** valores refresh **************", vals
            self.write(cr, uid, [line.id], vals, context=context)
        return True
        
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """
            Agrega la informacion de los descuentos para actualizar sobre el detalle de la factura
        """
        # Funcion original
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)
        # Valida que traiga el dato de facturado
        if not line.invoiced:
            res['discount_com'] = line.s_discount_com
            res['discount_vol'] = line.s_discount_vol
            res['discount_mez'] = line.s_discount_mez
            
        return res
    
        #no sirve esta funcion
    #def _get_tax_line(self, cr, uid, line, context=None):
    #    
    #    """
    #        Obtiene el descuento del producto sobre la linea de pedido
    #    """
    #    # Obtiene el decuento del producto
    #    if line:
    #        tax_line = self.pool.get('sale.order')._amount_line_tax(cr, uid, line, context=context)
    #    return tax_line
    
    def _get_import(self, cr, uid, ids, fields_names, arg, context=None):
        """
            Obtiene el importe del producto con el descuento aplicado
        """
        # Inicializa variables
        product_obj = self.pool.get('product.product')
        disc_obj = self.pool.get('product.pricelist.discount')
        mix_obj = self.pool.get('sale.order.mix')
        res = {}
        
        # Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context):
            # Inicializa el importe del producto en cero
            res[line.id] = {
                'price_import': 0.0,
                'weight_import': 0.0
            }
            
            # Calcula los impuestos de la linea del pedido
            price = line.price_subtotal
            # Aplica al subtotal el descuento comercial y al impuesto
            if line.s_discount_com > 0:
                price = price * ((100 - line.s_discount_com)/100)
            # Aplica al subtotal el descuento de mezcla y al impuesto
            if line.s_discount_mez > 0:
                price = price * ((100 - line.s_discount_mez)/100)
            # Aplica al subtotal el descuento de volumen y al impuesto
            if line.s_discount_vol > 0:
                price = price * ((100 - line.s_discount_vol)/100)
            # Informacion del resultado para la obtencion del total
            res[line.id] = {
                'weight_import': line.weight * line.product_uom_qty,
                'price_import': price
            }
        return res    
    
    _columns = {
        'discount_com': fields.function(_get_discount_pricelist, type='float', string='Descuento Comercial', multi='discount'),
        'discount_vol': fields.function(_get_discount_pricelist, type='float', string='Descuento Volumen', multi='discount'),
        'discount_mez': fields.function(_get_discount_pricelist, type='float', string='Descuento Mezcla', multi='discount'),
        's_discount_com': fields.float('Comercial', digits_compute= dp.get_precision('Account')),
        's_discount_vol': fields.float('Volumen', digits_compute= dp.get_precision('Account')),
        's_discount_mez': fields.float('Mezcla', digits_compute= dp.get_precision('Account')),
        'price_change': fields.boolean('Cambio precio'),
        'discount_change': fields.boolean('Cambio descuento'),
        'state_order': fields.related('order_id','state', type='char', required=False, readonly=True, store=False, string='Estado cotizacion'),
        'price_unit_original': fields.float('Precio unitario original', digits_compute= dp.get_precision('Product Price')),
        'price_import': fields.function(_get_import, type='float', string='Importe', store=True, digits_compute= dp.get_precision('Product Price'), multi="import"),
        'weight_import': fields.function(_get_import, type='float', string='Peso', store=True, digits_compute= dp.get_precision('Product Price'), multi="import"),
        #'tax_line': fields.function(_get_tax_line, type='float', string='Descuento x linea'),
        'product_uom_qty': fields.integer('Cantidad', required=True),
        'weight': fields.float('Peso Producto'),
    }
    
    _defaults = {
        'discount_change': False
    }
    
sale_order_line()
