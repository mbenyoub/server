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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class product_product(osv.Model):
    """ Inherits product - Añadir funcionalidad para identificarlo como activo """
    _inherit = 'product.product'
    
    def _default_category_asset(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'categ_id' in context and context['categ_id']:
            return context['categ_id']
        md = self.pool.get('ir.model.data')
        res = False
        try:
            res = md.get_object_reference(cr, uid, 'product', 'product_category_asset_1')[1]
        except ValueError:
            res = False
        return res
    
    def _default_category(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'categ_id' in context and context['categ_id']:
            return context['categ_id']
        md = self.pool.get('ir.model.data')
        res = False
        try:
            res = md.get_object_reference(cr, uid, 'product', 'product_category_all')[1]
        except ValueError:
            res = False
        return res
    
    def onchange_is_asset(self, cr, uid, ids, is_asset, context=None):
        """
            Valida si es un activo y actualiza la categoria del producto
        """
        if is_asset == True:
            categ_id = self._default_category_asset(cr, uid, context)
        else:
            categ_id = self._default_category(cr, uid, context)
        return {'value': {'categ_id': categ_id}}
    
    _columns = {
        'is_asset': fields.boolean('Es Activo'),
        'default_asset_category_id': fields.many2one('account.asset.category', 'Categoria de activo', change_default=True),
    }
    
    _defaults = {
        'is_asset': False
    }
    
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
