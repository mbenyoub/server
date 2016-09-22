# -*- coding: utf-8 -*-
from osv import osv,fields
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)


class pant_phonecall(osv.osv):
	_name = 'pant.phonecall'

        _columns = {
		'action':  fields.selection([('plan','Planificar una llamada'),('reg','Registrar una llamada')],select=True, string='Accion'),
		'summary': fields.char('Resumen de la llamada',size=300),
		'type': fields.selection([('in','Entrante'),('out','Saliente')],select=True, string='Tipo'),
                'description': fields.text('Descripcion'),
		'date_plan': fields.datetime('Fecha prevista'),	
		'company_id': fields.many2one('res.partner', string='Empresa'),
		'phone': fields.char('Telefono',size=50),
                'assign_id': fields.many2one('res.partner', string='Asignar a'),
		'team_id': fields.many2one('crm.case.section', string='Equipo de ventas'),
		'lead_id': fields.many2one('crm.lead', string='Llamadas'),
                }

pant_phonecall()
