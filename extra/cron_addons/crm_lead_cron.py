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
	#Buscar los templates
	con = [('name','=','Iniciativa no atendida')]
	ini_id = self.pool.get('email.template').search(cr, uid,con,context=None)

	###### Iniviciativa Nueva #####
	d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%Y-%m-%d %H:%M:%S'
        fecha = d.strftime(n_format)
	dd= datetime.strptime(fecha, n_format)
	condicion=[('state','=','draft')]
	condicion+=[('type','=','lead')]
	ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
	if len(ids)>0:
		for id in ids:
			obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
			fecha_lead=obj.create_date
			fecha_lead2 = datetime.strptime(fecha_lead, n_format)
			var = self.get_days(dd,fecha_lead2)

			if var==1: #24 Horas
				logging.info('24 horas')
				self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==2:
				#logging.info('48 horas')
                                con_user=[('user_id','=',obj.user_id.id)]
                                hr_ids = self.pool.get('hr.employee').search(cr, uid,con_user,context=None)
                                hr_obj = self.pool.get('hr.employee').browse(cr,uid,hr_ids[0],context=context)
                                hr_parent = hr_obj.department_id.parent_id
                                if hr_parent is not None:
                                        con_parent=[('department_id','=',hr_parent.id)]
                                        hr_parent_ids = self.pool.get('hr.employee').search(cr, uid,con_parent,context=None)
                                        hr_parent_obj = self.pool.get('hr.employee').browse(cr,uid,hr_parent_ids[0],context=context)
                                        self.pool.get('crm.lead').write(cr, uid, obj.id, {'user_id':hr_parent_obj.user_id.id}, context=context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==3:
				#logging.info('72 horas')
                                con_user=[('user_id','=',obj.user_id.id)]
                                hr_ids = self.pool.get('hr.employee').search(cr, uid,con_user,context=None)
				hr_obj = self.pool.get('hr.employee').browse(cr,uid,hr_ids[0],context=context)
				hr_parent = hr_obj.department_id.parent_id
				if hr_parent is not None:
					con_parent=[('department_id','=',hr_parent.id)]
					hr_parent_ids = self.pool.get('hr.employee').search(cr, uid,con_parent,context=None)
					hr_parent_obj = self.pool.get('hr.employee').browse(cr,uid,hr_parent_ids[0],context=context)
					self.pool.get('crm.lead').write(cr, uid, obj.id, {'user_id':hr_parent_obj.user_id.id}, context=context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
				
        return True



    def get_days(self, date_a, date_b):
	resta = date_a-date_b
	dias = resta.days
	return dias
