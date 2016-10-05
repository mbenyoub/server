# -*- coding: utf-8 -*-
from osv import osv,fields
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)


class op_meeting(osv.osv):
	_name = 'op.meeting'
	_inherit = "mail.thread"
        _columns = {
		'name': fields.char('Objetivo de la Reunion', size=128, required=True),
		'user_id': fields.many2one('res.users', string='Responsable',required=True),
		'partner_ids': fields.many2many('res.partner', 'op_meeting_partner_rel', 'meeting_id', 'partner_id', string='Asistentes'),
		'date': fields.datetime('Fecha prevista', required=True),
		'date_deadline' : fields.datetime('Termina', required=True),
		'assistant_client': fields.boolean('Asistente Adicional Cliente'),
		'assistant_client_name': fields.char('Nombre de Contacto',size=300),
        	'assistant_client_email': fields.char('Email',size=300),
        	'assistant_client_function': fields.char('Funcion',size=300),
        	'assistant_client_phone': fields.char('Telefono',size=300),	
        	'assistant_client_confirm': fields.boolean('Confirmacion del Cliente'),
		'lead_id': fields.many2one('crm.lead', string='Llamadas'),

		'alarm_id': fields.many2one('res.alarm',string='Recordatorio'),
		'note': fields.text('Acontecimientos de Reunion'),
                }


        def create(self, cr, uid, vals, context=None):
       	    date1= vals.get('date')
	    date1= datetime.strptime(date1, '%Y-%m-%d %H:%M:%S')
	    date2= vals.get('date_deadline')
            date2= datetime.strptime(date2, '%Y-%m-%d %H:%M:%S')
	    date3= date2-date1
            h_str= str(date3)[0]
	    horas=int(h_str)
	    alam = vals.get('alarm_id') 
       	    if alam is False:
       	    	alam=7

	    crm_meeting_pool=self.pool.get('crm.meeting')
	    crm_meeting_pool.create(cr, uid, {'name':vals.get('name'), 'state': 'open','allday':False,'duration':horas,'user_id':vals.get('user_id'),'date': vals.get('date'),'alarm_id':alam,'state_meeting': 'draft','date_deadline': vals.get('date_deadline'), 'partner_ids': vals.get('partner_ids') }, context=context)	
	    return super(op_meeting,self).create(cr, uid, vals, context=context)


op_meeting()
