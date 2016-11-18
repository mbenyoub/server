# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'lead_id': fields.many2one('crm.lead', string='Presupuestos', required=False),
    }


sale_order()
