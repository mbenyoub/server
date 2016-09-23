# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
       	'project': fields.char('Proyecto',size=300),
        'proposal': fields.char('Propuesta',size=300),
        }
sale_order()
