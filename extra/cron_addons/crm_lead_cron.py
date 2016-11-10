# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp import tools
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)


class crm_lead_cron(osv.osv):
    _name = 'crm.lead.cron'

    _columns = {
        'name':fields.char('Name', size=256, required=False),
    }



    def sent_notification(self, cr, uid, ids=False, context=None):
	logging.info('sent_notification')
	d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%Y-%m-%d %H:%M:%S'
        fecha = d.strftime(n_format)
	dd= datetime.strptime(fecha, n_format)

	condicion=[('state','=','draft')]
	ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
	if len(ids)>0:
		for id in ids:
			obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
			fecha_lead=obj.create_date
			fecha_lead2 = datetime.strptime(fecha_lead, n_format)
			var = self.get_days(dd,fecha_lead2)
			if var==1:
				#Extraer el nombre del template para enviar el id
				self.pool.get('email.template').send_mail(cr, uid, 36, obj.id ,True, context=context)

        return True

    def get_days(self, date_a, date_b):
	resta = date_a-date_b
	dias = resta.days
	return dias
