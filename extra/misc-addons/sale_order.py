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
        #'lead_id': fields.many2one('crm.lead', string='Presupuestos', required=False),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('signed', 'Cotizacion Firmada'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),

        }

    def action_signed(self, cr, uid, ids, context=None):
    	res = self.write(cr, uid, ids, {'state': 'signed'}, context=context)    
    	return res

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
