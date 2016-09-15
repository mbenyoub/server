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

class product_product(osv.osv):
    """ Inherits partner and add extra information product """
    _inherit = 'product.product'

    def _get_default_currency(self, cr, uid, context=None):
        """
            Regresa el id de la moneda por default
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.currency_id.id

    def _get_custom_tax_id(self, cr, uid, context=None):
        """
            Obtiene los ids de los impuestos por default para el producto
        """
        ids = self.pool.get('account.tax').search(cr, uid, [('name','ilike','IVA(16%) VENTAS')], context=context)
        print "********************* ids *********************** ", ids
        return ids

    _columns = {
        'description2': fields.text('Descripcion2'),
        'group_value': fields.char('Grupo', size=128),
        'category': fields.char('Categoria', size=128),
        'family': fields.char('Familia', size=128),
        'status': fields.selection([
                                    ('ALTA', 'Alta'),
                                    ('BAJA', 'Baja'),
                                    ('BLOQUEADO', 'Bloqueado'),
                                    ('DESCONTINUADO', 'Descontinuado')], 'Estatus'),
        'price2': fields.float('Precio2', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price3': fields.float('Precio3', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price4': fields.float('Precio4', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price5': fields.float('Precio5', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price6': fields.float('Precio6', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price7': fields.float('Precio7', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price8': fields.float('Precio8', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price9': fields.float('Precio9', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'price10': fields.float('Precio10', digits_compute=dp.get_precision('Product Price'), help="Lista de precio para el producto."),
        'have_mov': fields.boolean('Tiene Movimientos', readonly=1),
        'type2': fields.char('Tipo de producto'),
         # Campos para webservice
        'ws_id': fields.char('Id webservice', size=64),
    }
    
    _defaults = {
        'category': 'ACTIVOS',
        'family': 'NACIONALES',
        'status': 'ALTA',
        'have_mov': False,
        'price2': 0.0,
        'price3': 0.0,
        'price4': 0.0,
        'price5': 0.0,
        'price6': 0.0,
        'price7': 0.0,
        'price8': 0.0,
        'price9': 0.0,
        'price10': 0.0,
        'taxes_id': _get_custom_tax_id,
    }
    
product_product()

class product_list_price(osv.Model):
    _name = "product.list.price"
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'currency_id': fields.many2one('res.currency', 'Moneda'),
        'product_id': fields.many2one('product.product', 'Articulo'),
        'list_price': fields.float('Precio', digits_compute=dp.get_precision('Product Price'), help="Precio que aplica sobre el producto."),
        'status': fields.char('Estatus', size=64),
        # Campos para webservice
        'ws_id': fields.char('Id webservice', size=64),
    }
    
product_list_price()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
