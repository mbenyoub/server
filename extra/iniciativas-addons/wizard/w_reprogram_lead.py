# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import logging
logging.basicConfig(level=logging.INFO)

class w_reprogram_lead(osv.osv_memory):
    _name = 'w.reprogram.lead'
    _columns = {
       	'reprogram_date': fields.datetime('Fecha prevista'),
	'description': fields.text('Descripcion'),
	'lead_id': fields.many2one('crm.lead', string='Iniciativa'),
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}


    def action_reprogram(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

	logging.info(ids)
	logging.info(context.get('active_ids'))
        #phonecall = self.pool.get('crm.phonecall')
        #opportunity_ids = context and context.get('active_ids') or []
        #opportunity = self.pool.get('crm.lead')
        #data = self.browse(cr, uid, ids, context=context)[0]
        #call_ids = opportunity.schedule_phonecall(cr, uid, opportunity_ids, data.date, data.name, \
        #        data.note, data.phone, data.contact_name, data.user_id and data.user_id.id or False, \
        #        data.section_id and data.section_id.id or False, \
        #        data.categ_id and data.categ_id.id or False, \
        #        action=data.action, context=context)

        return {'type': 'ir.actions.act_window_close'}

w_reprogram_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
