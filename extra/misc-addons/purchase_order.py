# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta, date, time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logging.basicConfig(level=logging.INFO)


class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = ["purchase.order", "ir.needaction_mixin"]

    _columns = {
       	'read': fields.boolean('No revisado'),
        }

    _defaults = {       
        'read' : True,
    }

    def _needaction_domain_get(self, cr, uid, context=None):
	#n_format = '%Y-%m-%d'
        return [('read','=',True)]

    def create(self, cr, uid, vals, context=None):
	d=datetime.now()
	date=d.strftime('%Y-%m-%d %H:%M:%S')
	date_end = datetime.now() + timedelta(days=1)
	date_end_str = date_end.strftime('%Y-%m-%d %H:%M:%S')

	vals.update({'date_order':date,'minimum_planned_date':date_end_str})

	return super(purchase_order,self).create(cr, uid, vals, context=context)


purchase_order()
