# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)
from openerp import netsvc

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
       	'project': fields.char('Proyecto',size=300),
        'proposal': fields.char('Propuesta',size=300),
        }


    def print_quotation(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'quotation_sent', cr)

        datas = {
                     'model': 'sale.order',
                     'ids': ids,
                     'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'sale.order.report', 'datas': datas, 'nodestroy': True}

sale_order()
