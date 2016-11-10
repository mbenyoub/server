# -*- coding: utf-8 -*-

from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)

class stock_move(osv.osv):
    _inherit = 'stock.move'
    def create(self, cr, uid, vals, context=None):
	picking_id = vals.get('picking_id')
	product_id = vals.get('product_id') 
	obj_stock = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
	if obj_stock.origin is not None and obj_stock.name is not None:
		if 'EST' in  obj_stock.origin and 'INT' in obj_stock.name:
			product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			tpl= product.product_tmpl_id
			if tpl is not None:
				if tpl.supply_method == 'produce' and tpl.procure_method == 'make_to_order':
					return False
				else:	
                                	vals['location_id']=14
                                	vals['location_dest_id']=12

	return super(stock_move,self).create(cr, uid, vals, context=context)
        

stock_move()
