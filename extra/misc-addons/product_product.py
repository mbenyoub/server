# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
       	'is_maintenance_parts': fields.boolean('Producto para Refacciones de Mantenimiento'),
        }
    _defaults = {
        'is_maintenance_parts': False,
    }
product_product()
