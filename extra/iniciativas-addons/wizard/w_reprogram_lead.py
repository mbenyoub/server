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
	#Buscamos template
	crm_obj = self.pool.get('crm.lead').browse(cr, uid, lead_id, context=context)
        con = [('name','=','Reprogramar Iniciativa')]
        ini_id = self.pool.get('email.template').search(cr, uid,con,context=None)
	#Escalado
	user_old = crm_obj.user_id.id
        con_user=[('user_id','=',user_old)]
        hr_ids = self.pool.get('hr.employee').search(cr, uid,con_user,context=None)
        hr_obj = self.pool.get('hr.employee').browse(cr,uid,hr_ids[0],context=context)
        hr_parent = hr_obj.department_id.parent_id
        if hr_parent is not None:
                con_parent=[('department_id','=',hr_parent.id)]
                hr_parent_ids = self.pool.get('hr.employee').search(cr, uid,con_parent,context=None)
                hr_parent_obj = self.pool.get('hr.employee').browse(cr,uid,hr_parent_ids[0],context=context)
                self.pool.get('crm.lead').write(cr, uid, crm_obj.id, {'user_id':hr_parent_obj.user_id.id}, context=context)
	#Enviar correo
	self.pool.get('email.template').send_mail(cr, uid, ini_id[0], lead_id ,True, context=context)
	#Regresar user
	self.pool.get('crm.lead').write(cr, uid, crm_obj.id, {'user_id':user_old}, context=context)

        return {'type': 'ir.actions.act_window_close'}

w_reprogram_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
