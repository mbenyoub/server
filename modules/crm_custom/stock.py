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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import logging
logging.basicConfig(level=logging.INFO)

class stock_picking(osv.osv):
    """
        Inherit from stock
    """
    _inherit = "stock.picking"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = invoice_obj = self.pool.get('links.get')
        return links._links_get(cr, uid, context=None)
    
    def _prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
        """
            Inherit from stock.picking
        """
        valor = super(stock_picking, self)._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'stock.picking'),])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Almacen', 'object': 'stock.picking', })
        
        #~ Relaciona el documento origen con la factura 
        invoice_obj = self.pool.get('account.invoice')
        #print "**************** valor es igual a", valor
        valor['ref'] = 'stock.picking,' + str(picking.id)
        valor['ref2'] = 'sale.order,' + str(picking.reference.id)
        return valor
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        valor = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        """
            Inherit from stock.picking
        """
        valor = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'stock.picking'),])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Almacen', 'object': 'stock.picking', })
        
        #~ Relaciona el documento origen con la factura 
        invoice_obj = self.pool.get('account.invoice')  
        valor['ref'] = 'stock.picking,' + str(picking.id)
        valor['ref2'] = 'sale.order,' + str(picking.reference.id)
        #print "**************** VALOR ES IGUAL A ****", valor
        return valor
    
    def _have_reference(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si hay una relacion con una venta en la referencia del albaran de salida
        """
        res = {}
        # Recorre los albaranes recibidos en el parametro
        for stock in self.browse(cr, uid, ids, context=context):
            res[stock.id] = False
            # Valida si hay una relacion en el documento
            if stock.reference.id:
                res[stock.id] = True
        return res
    
    _columns = {
        'reference' : fields.reference('Documento Origen', selection=_links_get, size=128, readonly=True),
        'have_reference': fields.function(_have_reference, method=True, string='Documento origen?', readonly=True, type='boolean', help="Indica si hay una referencia con una venta."),
    }
    
class stock_picking_out(osv.osv):
    """
        Inherit from stock
    """
    _name = "stock.picking.out"
    _inherit = ["stock.picking", "stock.picking.out" ]
    _table = "stock_picking"
    
stock_picking_out()
    
class stock_move(osv.osv):
    """
        Inherit from stock
    """
    _inherit = "stock.move"
    
    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Retorna el producto disponible sobre la tienda
        """

        product_obj = self.pool.get('product.product')
        res = {}
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
        #Recorre las lineas del producto

        for line in self.browse(cr, uid, ids, context=context):
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                # Obtiene el id de la ubicacion origen
                if line.location_id:
                    #ctx['location'] = line.location_id.id
		    ctx['location'] = False
		    ctx['shop'] = False
                # Asigna la stock virtual del producto a la linea del pedido de venta.

                stock = product_obj.get_product_available(cr, uid, [line.product_id.id], context=ctx)
                res[line.id] = stock.get(line.product_id.id, 0.0)

        return res
    


    _columns ={
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
    }
    
stock_move()
