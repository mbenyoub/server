#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: Juan Carlos Funes(juan@vauxoo.com)
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from openerp.osv import osv, fields, orm
import decimal_precision as dp
from openerp.tools.translate import _

from datetime import datetime
from dateutil.relativedelta import relativedelta

class stock_location_product(osv.osv_memory):
    _inherit = "stock.location.product"

    def action_location_print(self, cr, uid, ids, context=None):
        '''
            Esta funcion imprime el reporte de el inventario sobre la locacion actual
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        
        print "*********** active id ******** ", context['active_id']
        
        datas = {
             'ids': [context['active_id']],
             'model': 'stock.location',
             'form': self.pool.get('stock.location').read(cr, uid, context['active_id'], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'lot.stock.overview',
            'datas': datas,
            'nodestroy' : True
        }
    
    defaults = {
        'type': 'inventory'
    }
    
stock_location_product()

class stock_location(osv.osv):
    _inherit = "stock.location"
    
    _columns = {
        'name': fields.char('Nombre ubicacion', size=64, required=True),
    }
    
stock_location()