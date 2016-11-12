# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, timedelta, date, time
import logging
logging.basicConfig(level=logging.INFO)

class w_reallocate_agent(osv.osv_memory):
    _name = 'w.reallocate.agent'
    _columns = {
       	'date': fields.datetime(),
	'user_from': fields.many2one('res.users'),
	'user_to': fields.many2one('res.users', string='Asignar a:', required=True),
	'lead_id': fields.many2one('crm.lead', string='Iniciativa'),
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}


    def action_reallocate(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

	lead_id = context.get('active_ids')[0]
	crm = self.pool.get('crm.lead').browse(cr, uid, lead_id, context=context)
       	self.write(cr,uid,ids,{'lead_id':lead_id,'date':datetime.now(),'user_from':crm.user_id.id})
	
	
	data = self.browse(cr, uid, ids, context=context)[0]
	self.pool.get('crm.lead').write(cr,uid,lead_id,{'user_id':data.user_to.id})

	#Se envia correo
        con = [('name','=','Iniciativa Asignada')]
        tmpl_id = self.pool.get('email.template').search(cr, uid,con,context=None)
	self.pool.get('email.template').send_mail(cr, uid, tmpl_id[0], lead_id ,True, context=context)

        return {'type': 'ir.actions.act_window_close'}

w_reallocate_agent()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
