# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
from openerp.osv import osv, fields


class stock_move_consume(osv.osv_memory):
    _inherit = 'stock.move.consume'
    
    def default_get(self, cr, uid, fields, context=None):
        move_obj = self.pool.get('stock.move')
        production_obj = self.pool.get('mrp.production')
        
        res = super(stock_move_consume, self).default_get(cr, uid, fields, context=context)
        if context is None:
            context = {}
        move = move_obj.browse(cr, uid, context['active_id'], context=context)
        if 'move_id' in fields:
            res.update({'move_id': move.id or False})
        if 'production_id' in fields:
            production_srch = production_obj.search(cr, uid, [('name', '=', move.name)], context=context)
            production = production_obj.browse(cr, uid, production_srch[0], context=context)
            res.update({'production_id': production.id or False})
        
        return res
    
    def do_move_consume(self, cr, uid, ids, context=None):
        mrp_monitoring_obj = self.pool.get('mrp.monitoring.product')
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.monitoring_product:
               res = {
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'name': 'monitoreo' + '-' + move.product_id.name,
                'move_id': move.move_id.id or False,
                'production_id': move.production_id.id or False,
                }
               monitoring_id = mrp_monitoring_obj.create(cr, uid, res, context=context)
               
               print "*****MONITORING_ID****: ", monitoring_id
        
        return super(stock_move_consume, self).do_move_consume(cr, uid, ids, context=context)
    
    _columns = {
        'monitoring_product': fields.boolean('Monitorear'),
        'move_id': fields.many2one('stock.move', 'Movimiento'),
        'production_id': fields.many2one('mrp.production', 'Orden de produccion'),
    }
    
    _defaults = {
        'monitoring_product': True,
    }