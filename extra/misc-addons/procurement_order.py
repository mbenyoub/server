# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta, date, time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logging.basicConfig(level=logging.INFO)


class procurement_order(osv.osv):
    _name = 'procurement.order'
    _inherit = ["procurement.order", "ir.needaction_mixin"]
    _order = "date_planned desc"
   

    def _needaction_domain_get(self, cr, uid, context=None):
	d=datetime.now()
       	n_format = '%Y-%m-%d'
       	fecha = d.strftime(n_format)
       	fecha = fecha+ ' 00:00:00'
        return ['&',('state','=','exception'),('date_planned', '>=',fecha), ('procure_method','=', 'make_to_stock')]

procurement_order()
