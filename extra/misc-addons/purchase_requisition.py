# -*- coding: utf-8 -*-
from datetime import datetime, date, time
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logging.basicConfig(level=logging.INFO)


class purchase_requisition(osv.osv):
    _name = 'purchase.requisition'
    _inherit = ["purchase.requisition", "ir.needaction_mixin"]

    _columns = {
       	'read': fields.boolean('No revisado'),
        }

    _defaults = {
        'read' : True,
    }

    def _needaction_domain_get(self, cr, uid, context=None):
       	"""d=datetime.now()
       	n_format = '%Y-%m-%d'
	fecha = d.strftime(n_format)
	fecha = fecha+ ' 00:00:00'"""
        return ['&',('read','=',True),('user_id', '=', uid)]

purchase_requisition()
