# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, timedelta, date, time
import logging
logging.basicConfig(level=logging.INFO)

class w_reschedule_lead(osv.osv_memory):
    _name = 'w.reschedule.lead'
    _columns = {
       	'date': fields.datetime('Fecha',required=True),
	'user_id': fields.many2one('res.users'),
	'lead_id': fields.many2one('crm.lead', string='Iniciativa'),
        }

    def default_get(self, cr, uid, fields, context=None):
        opp_obj = self.pool.get('crm.lead')
        record_ids = context and context.get('active_ids', []) or []
        res = {}
        for opp in opp_obj.browse(cr, uid, record_ids, context=context):
            if 'date' in fields:
		res.update({'date': opp.reprogram_date})
        return res


    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}


    def action_reschedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

	lead_id = context.get('active_ids')[0]
	crm = self.pool.get('crm.lead').browse(cr, uid, lead_id, context=context)
       	self.write(cr,uid,ids,{'lead_id':lead_id,'user_id':crm.user_id.id})
	
	data = self.browse(cr, uid, ids, context=context)[0]
	self.pool.get('crm.lead').write(cr,uid,lead_id,{'create_date':data.date})


        return {'type': 'ir.actions.act_window_close'}

w_reschedule_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
