# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import logging
logging.basicConfig(level=logging.INFO)

class w_reprogram_lead(osv.osv_memory):
    _name = 'w.reprogram.lead'
    _columns = {
       	'reprogram_date': fields.datetime('Fecha prevista',required=True),
	'description': fields.text('Descripcion',required=True),
	'lead_id': fields.many2one('crm.lead', string='Iniciativa'),
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}


    def action_reprogram(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

	lead_id = context.get('active_ids')[0]
       	self.write(cr,uid,ids,{'lead_id':lead_id})
        data = self.browse(cr, uid, ids, context=context)[0]
	self.pool.get('crm.lead').write(cr,uid,lead_id,{'reprogram_date':data.reprogram_date})
        return {'type': 'ir.actions.act_window_close'}

w_reprogram_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
