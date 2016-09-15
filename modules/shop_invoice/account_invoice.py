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

class account_invoice(osv.Model):
    _inherit='account.invoice'
    
    def _get_number_invoice(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            #print"************ invoice ************* ", invoice
            number = ''
            number = invoice.number if invoice.number else ''
            #print"*********** number ************ ", number
            # Verifica si es una factura electronica
            if invoice.invoice_sequence_id.approval_id:
                if invoice.invoice_sequence_id.approval_id.type == 'cfdi32':
                    if invoice.journal_id.prefix2:
                        number = '%s-%s'%(invoice.journal_id.prefix2,number)
            res[invoice.id] = number
        return res
    
    _columns = {
        'shop_id': fields.many2one('sale.shop', 'Tienda', select=1, ondelete='restrict'),
        'number2': fields.function(_get_number_invoice, type="char", size=128, string="Numero")
    }
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.number2
            
            res.append((record.id,name ))
        return res
    
    def onchange_shop_id(self, cr, uid, ids, shop_id, type, context=None):
        """
            Actualiza el diario de la Tienda
        """
        context = context or {}
        if type != 'out_invoice':
            return {}
        if not shop_id:
            return {}
        value = {
            'journal_id': self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context).journal_id.id
        }
        
        return {'value': value}
    
    def _get_default_shop(self, cr, uid, context=None):
        """
            Obtiene la tienda por default
        """
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            raise osv.except_osv(_('Error!'), _('No hay tienda predeterminada para la actual compañia del usuario!'))
        return shop_ids[0]
    
    _defaults = {
        'shop_id': _get_default_shop
    }
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
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
        product_obj = self.pool.get('product.product')
        res = {}
        shop_id = False
        
        #Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context) :
            # Obtiene el id de la tienda
            if not shop_id and line.invoice_id.shop_id:
                shop_id = line.invoice_id.shop_id.id or False
            
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                #Asigna la stock virtual del producto a la linea del pedido de compra.
                res[line.id] = self._get_product_available(cr, uid, line.product_id.id, shop_id=shop_id, location_id=False, context=context)
        return res
    
    _columns = {
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
    }
    
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
