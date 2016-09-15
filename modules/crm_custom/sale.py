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
#              Ivan Macias (ivanfallen@gmail.com)
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
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get')
        return links._links_get(cr, uid, context=context)
    
    def _have_crm_lead(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si hay una relacion con una oportunidad del crm
        """
        res = {}
        # Recorre las ventas recibidas en el parametro
        for sale in self.browse(cr, uid, ids, context=context):
            res[sale.id] = False
            #print "*************** crm_lead_id *********** ", sale.crm_lead_id
            # Valida si hay una relacion con una oportunidad
            if sale.crm_lead_id.id:
                res[sale.id] = True
        return res
    
    def _progress_invoice(self, cr, uid, ids, field_name, arg, context=None):
        """
            Esta funcion obtiene el porcentaje facturado del pedido de venta
        """
        invoice_obj = self.pool.get('account.invoice')
        res = {}
        invoice_total = 0.0
        if context is None:
            context = {}
        # Recorre los pedidos de venta
        for order in self.browse(cr, uid, ids, context=context):
            invoice_total = 0.0
            # Recorre las facturas
            for invoice in order.invoice_ids:
                #print "***************** invoice *********************** ",  invoice.id, "  ", invoice.state, "  ", invoice.amount_total
                # Si el estado es diferente de cancelado actualiza el total facturado
                if invoice.state != 'cancel':
                    invoice_total += invoice.amount_total
                    #print "************* invoice total *********** ", invoice_total
            # Agrega el porcentaje facturado al valor de retorno
            #print "************** total venta ************** ", order.amount_total
            # Valida que el total de la venta no sea cero
            if not order.amount_total:
                porcent_invoice = 0.0
            else:
                # Calcula el porcentaje facturado
                total = order.amount_total
                porcent_invoice = round(100.0 * invoice_total / total, 2)
            #print "****************** porcentaje facturado ********************** ",  porcent_invoice
            res[order.id] = porcent_invoice
        return res
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """
            Inherit from sale prepare_invoice 
        """
        #print"***********Crea factura desde venta*************\m/"
        valor = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'sale.order'),])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Ventas', 'object': 'sale.order', })
        
        #~ Relaciona el documento origen con la factura 
        invoice_obj = self.pool.get('account.invoice')
        #print "**************** valor es igual a", valor
        valor['ref'] = 'sale.order,' + str(order.id)
        #print "***************************", valor
        return valor
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        """
            Inherit from sale_stock 
        """
        # Funcion de SUPER para heredar la funcionalidad anterior
        valor = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)
        # Revisa si ya existe una relacion sobre el objeto si no no funciona
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'sale.order'),])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Ventas', 'object': 'sale.order', })
        
        #~ Relaciona el documento origen con el albaran 
        valor['reference'] = 'sale.order,' + str(order.id)
        #print "*************PREPARE ORDER LINE MOVE**********",valor
        return valor
    
    _columns = {
        'crm_lead_id': fields.reference('Oportunidad', selection=_links_get, size=128, readonly=True),
        'have_crm_lead': fields.function(_have_crm_lead, method=True, string='Proviene de oportunidad?', readonly=True, type='boolean', help="Indica si se origina de una oportunidad."),
        'progress_invoice': fields.function(_progress_invoice, string='Porcentaje Facturado', type='float',  help="Porcentaje facturado del pedido de venta."),
    }
    
class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    def _get_product_available(self, cr, uid, product_id, shop_id=False, location_id=False, context=None):
        """
            Obtiene el producto disponible del almacen
        """
        product_obj = self.pool.get('product.product')
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
        if shop_id:
            ctx['shop'] = shop_id
        if location_id:
            ctx['location'] = location_id
        stock = product_obj.get_product_available(cr, uid, [product_id], context=ctx)
        return stock.get(product_id, 0.0)

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Retorna el producto disponible sobre la tienda
        """
        res = {}
        shop_id = False
        #Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context):
            # Obtiene el id de la tienda
            if not shop_id:
                shop_id = line.order_id.shop_id.id or False
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                # Asigna la stock virtual del producto a la linea del pedido de venta.
                res[line.id] = self._get_product_available(cr, uid, line.product_id.id, shop_id=shop_id, location_id=False, context=context)
        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        """
            Retorna la cantidad disponible del producto junto con la informacion que ya obtenia
        """
        # Funcion de SUPER para heredar la funcionalidad anterior
        ret = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
                uom=uom, qty_uos=qty_uos, uos=uos, name='', partner_id=partner_id,
                lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        
        # Obtiene la cantidad disponible del producto
        if product:
            product_obj = self.pool.get('product.product')
            product_available = self._get_product_available(cr, uid, product, location_id=False, context=context)
            ret['value']['virtual_available'] = product_available
        return ret
        
    _columns = {
         'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
    }
    