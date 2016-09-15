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

class sale_order(osv.Model):
    _inherit = "sale.order"
    
    def onchange_partner_shipping_id(self, cr, uid, ids, part, context=None):
        """
            Modifica la direccion de factura
        """
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}
        
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            'partner_invoice_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'order_line': []
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        
        return {'value': val}
    
    def onchange_partner_id(self, cr, uid, ids, part, partner_shipping, context=None):
        """
            Limpia las lineas de pedido
        """
        if not part:
            return {'value': {'partner_id': False, 'fiscal_position': False}}
        
        val = {
            'partner_shipping_id': part
        }
        
        return {'value': val}
    
    def onchange_partner_address_id(self, cr, uid, ids, part, partner_id, context=None):
        """
            Modifica la direccion de envio del cliente
        """
        if not part:
            return {'value': {'partner_shipping_id': partner_id}}
        
        val = {
            'partner_shipping_id': part,
            'order_line': []
        }
        
        return {'value': val}
    
    _columns = {
        'partner_address_id': fields.many2one('res.partner', 'Direccion de Envio'),
    }
    
    def _check_order_lines(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            # Recorre las lineas de la venta
            for line in order.order_line:
                print "************* precio unitario de venta *************** ", line.price_unit
                if line.price_unit == 0.0:
                    return False
        return True
    
    _constraints = [(_check_order_lines, "Las lineas de pedido no pueden tener productos sin costo!",    ['order_line','order_line']),]
    
    _defaults = {
        'order_policy': 'picking'
    }
        
class sale_order_line(osv.Model):
    _inherit = "sale.order.line"
    
    def _get_info_product(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Regresa el valor del descuento y precio unitario del producto
        """
        res = {}
        
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'discount2': line.discount,
                'price_unit2': line.price_unit
            }
        return res
    
    _columns = {
        'discount': fields.float('Descuento (%)', digits_compute= dp.get_precision('Discount')),
        'discount2': fields.function(_get_info_product, string='Descuento (%)', type="float", multi="product", digits_compute= dp.get_precision('Account')),
        'price_unit2': fields.function(_get_info_product, string='Precio Unidad', type="float", multi="product", digits_compute= dp.get_precision('Account')),
        'tax_id': fields.many2many('account.tax', 'sale_order_tax', 'order_line_id', 'tax_id', 'Taxes', readonly=True, states={'draft': [('readonly', False)]}),
    }
    
    _defaults = {
        'tax_id': lambda self, cr, uid, c: self.pool.get('account.tax').search(cr, uid, [('name','like','16'),('type_tax_use','=','sale')], context=None)
    }
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        print "********** reemplazo funcion original product_id_change ******************** "
        return True
    
    def product_id_change_kober(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False, partner_shipping_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        """
            Actualiza la informacion de la linea del pedido segun el producto seleccionado
        """
        print "*************** product_change_id kober ****************** "
        context = context or {}
        lang = lang or context.get('lang',False)
        if not  partner_id:
            raise osv.except_osv(_('Cliente no definido!'), _('Before choosing a product,\n select a customer in the sales form.'))
        # Si hay una direccion en la cotizacion la utiliza para obtener el costo del producto
        if partner_shipping_id:
            partner_id = partner_shipping_id
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        list_price_obj = self.pool.get('product.list.price')
        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        
        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
            print "****************** result tax ****************** ", result['tax_id']
            # Si no trae los impuestos, agrega el 16% por default
            if not result['tax_id']:
                result['tax_id'] = self.pool.get('account.tax').search(cr, uid, [('name','like','16'),('type_tax_use','=','sale')], context=context)
                print "****************** impuestos default ****************** ", result['tax_id']

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        
        # Obtiene la lista de precio de la cual se va a buscar
        partner = partner_obj.browse(cr, uid, partner_shipping_id, context=context)
        
        # Aplica el descuento sobre el producto segun el cliente
        if partner.discount:
            result['discount'] = partner.discount
            result['discount2'] = partner.discount
            print "***************** descuento ***************** ", result['discount']
        
        print "***************** sucursal ****************** ", int(partner.branch_id.code), ' - ', partner.branch_id.name
        
        # Ve de donde va a tomar el precio del producto
        if not partner.branch_id:
            # Si no contiene una sucursal seleccionada muestra el precio del articulo
            type_list = 'product'
        elif int(partner.branch_id.code) < 3:
            type_list = 'product'
        else:
            type_list = 'list_price'
        
        print "****************** producto_id ********************* ", product
        print "****************** type list ********************* ", type_list
        print "****************** lista de precio especial ************** ", partner.price_list_esp
        
        # Valida que el cliente tenga una lista de precio especial
        if not partner.price_list_esp:
            raise osv.except_osv(_('Lista de Precio Invalida!'), _('El cliente no tiene una lista de precio especial asignada.'))
        
        # Revisa si tiene que buscar el precio del producto o en las listas de precios
        if type_list == 'product':
            # Valida si hay una lista de precio especial para el producto
            if partner.price_list_esp:
                # Obtiene el precio del producto segun su lista de precio
                if partner.price_list_esp == '(Precio 2)':
                    price = product_obj.price2
                    print "*************** producto - precio 2 *************** "
                elif partner.price_list_esp == '(Precio 3)':
                    price = product_obj.price3
                    print "*************** producto - precio 3 *************** "
                elif partner.price_list_esp == '(Precio 4)':
                    price = product_obj.price4
                    print "*************** producto - precio 4 *************** "
                elif partner.price_list_esp == '(Precio 5)':
                    price = product_obj.price5
                    print "*************** producto - precio 5 *************** "
                elif partner.price_list_esp == '(Precio 6)':
                    price = product_obj.price6
                    print "*************** producto - precio 6 *************** "
                elif partner.price_list_esp == '(Precio 7)':
                    price = product_obj.price7
                    print "*************** producto - precio 7 *************** "
                elif partner.price_list_esp == '(Precio 8)':
                    price = product_obj.price8
                    print "*************** producto - precio 8 *************** "
                elif partner.price_list_esp == '(Precio 9)':
                    price = product_obj.price9
                    print "*************** producto - precio 9 *************** "
                elif partner.price_list_esp == '(Precio 10)':
                    price = product_obj.price10
                    print "*************** producto - precio 10 *************** "
                else:
                    # Si no es ninguna de las opciones regresa el precio de lista
                    price = product_obj.list_price
                    print "*************** producto - list_price *************** "
            else:
                # Utiliza el precio de lista del producto
                print "************* producto - no lista precio especial ************ "
                price = product_obj.list_price
        else:
            print "************* busca lista de precio ******************** "
            # Busca sobre las listas de precios
            list_price_ids = list_price_obj.search(cr, uid, [('name','=',partner.price_list_esp),('product_id','=',product)], context=None)
            
            if not list_price_ids:
                price = 0.0
                raise osv.except_osv(_('Lista de Precio Invalida!'), _('No se puede utilizar el producto para este cliente porque no tiene una lista de precio asignada.'))
                print "*********** lista precio - no encontrada ********** "
            else:
                price = list_price_obj.browse(cr, uid, list_price_ids[0], context=context).list_price
                print "************ lista precio - Encontrada *************** "
        
        print "*************** precio *************** ", price
        
        # Si encontro el precio del producto lo agrega sino muestra un error
        if price is False or price == 0.0:
            warn_msg = "1. " + _("Cannot find a pricelist line matching this product and quantity.\n"
                    "You have to change either the product, the quantity or the pricelist.")

            warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
        else:
            result.update({'price_unit': price, 'price_unit2': price})
        
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}
    