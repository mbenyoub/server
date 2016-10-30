# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)

class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'


mrp_production_workcenter_line()
