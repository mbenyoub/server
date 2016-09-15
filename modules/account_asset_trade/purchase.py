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
from openerp.tools.translate import _

class purchase_order(osv.Model):
    _inherit = "purchase.order"
    
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """
            Agrega al retorno de la linea de la factura a crear el campo de categoria de activo en los casos que requiera
        """
        print "****************** agrega categoria de activo a linea ****************** "
        #raise osv.except_osv(_('Warning!'),_("Prueba exepcion!"))
        
        # Ejecuta proceso original de funcion
        result = super(purchase_order, self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        
        print "******************** result ************************** ", result
        
        # Si hay producto valida si es un activo
        if result['product_id']:
            product = self.pool.get('product.product').browse(cr, uid, result['product_id'], context=context)
            # Si el producto es activo agrega al retorno el valor de su categoria
            if product.is_asset:
                result['asset_category_id'] = product.default_asset_category_id.id or False
        
        print "**************** resultado linea ***************** ", result
        return result
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
