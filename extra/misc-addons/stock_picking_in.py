# -*- coding: utf-8 -*-
from datetime import datetime, date, time
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logging.basicConfig(level=logging.INFO)


class stock_picking_in(osv.osv):
    _name = 'stock.picking.in'
    _inherit = ["stock.picking.in", "ir.needaction_mixin"]

    def _needaction_domain_get(self, cr, uid, context=None):
        return [('state','=','assigned')]

stock_picking_in()
