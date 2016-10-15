# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta, date, time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logging.basicConfig(level=logging.INFO)


class stock_picking_out(osv.osv):
    _name = 'stock.picking.out'
    _inherit = ["stock.picking.out", "ir.needaction_mixin"]

    def _needaction_domain_get(self, cr, uid, context=None):
       	d=datetime.now()
       	n_format = '%Y-%m-%d'
       	fecha = d.strftime(n_format)
       	fecha = fecha+ ' 00:00:00'
        return ['&',('state','=','assigned'),('min_date','>=',fecha) ]

stock_picking_out()
