# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)

class stock_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = ['stock.picking','ir.needaction_mixin']

    def _needaction_domain_get(self, cr, uid, context=None):
	d=datetime.now()
       	n_format = '%Y-%m-%d'
       	fecha = d.strftime(n_format)
       	fecha = fecha+ ' 00:00:00'
        return ['&',('state','in',('assigned','confirmed')),('date', '>=',fecha)]


stock_picking()
