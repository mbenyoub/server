# -*- coding: utf-8 -*-
from osv import osv,fields
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)


class pant_phonecall(osv.osv):
	_name = 'pant.phonecall'

        _columns = {
		'action':  fields.selection([('plan','Planificar una llamada'),('reg','Registrar una llamada')],select=True, string='Accion', required=True),
		'summary': fields.char('Resumen de la llamada',size=300,required=True),
		'type': fields.selection([('in','Entrante'),('out','Saliente')],select=True, string='Tipo',required=True),
                'description': fields.text('Descripcion'),
		'date_plan': fields.datetime('Fecha prevista'),	
		'company_id': fields.many2one('res.partner', string='Empresa'),
		'phone': fields.char('Telefono',size=50),
                'assign_id': fields.many2one('res.users', string='Asignar a'),
		'team_id': fields.many2one('crm.case.section', string='Equipo de ventas'),
		'lead_id': fields.many2one('crm.lead', string='Llamadas'),
                }


        def create(self, cr, uid, vals, context=None):
	    logging.info(vals)
	    if vals.get('action')=='plan':
		#Validar que fecha tengo datos
		if vals.get('date_plan') is False:
			raise osv.except_osv(('Error'), ('El campo Fecha Prevista esta vacio') )
		categoria = False
		if vals.get('type') is not None:
			if vals.get('type')=='in':
				categoria=9
			if vals.get('type')=='out':
				categoria=10	
		
	    	phone_pool=self.pool.get('crm.phonecall')
	    	phone_pool.create(cr, uid, {'description':vals.get('description',False), 'state': 'open', 'section_id':vals.get('team_id'), 'active':True, 'opportunity_id': vals.get('lead_id'), 'name': vals.get('summary',False), 'priority':'3', 'date': vals.get('date_plan',False),'alarm_id':7,'categ_id':categoria,'user_id':vals.get('assign_id'),'partner_phone': vals.get('phone') }, context=context)
	    	return super(pant_phonecall,self).create(cr, uid, vals, context=context)
	    else:
		return super(pant_phonecall,self).create(cr, uid, vals, context=context)

pant_phonecall()
