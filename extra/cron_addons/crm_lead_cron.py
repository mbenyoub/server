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

        con = [('name','=','Aviso 24 Horas antes')]
        ini_after_id = self.pool.get('email.template').search(cr, uid,con,context=None)

        con = [('name','=','Oportunidad no atendida')]
        opp_id = self.pool.get('email.template').search(cr, uid,con,context=None)

	d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%Y-%m-%d %H:%M:%S'
        fecha = d.strftime(n_format)
	dd= datetime.strptime(fecha, n_format)

	###### Iniviciativa Nueva #####

	condicion=[('state','=','draft')]
	condicion+=[('type','=','lead')]
	ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
	if len(ids)>0:
		for id in ids:
			obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
			fecha_lead=obj.create_date
			fecha_lead2 = datetime.strptime(fecha_lead, n_format)
			var = self.get_days(dd,fecha_lead2)

			if var==1:
				logging.info('24 horas draft')
				self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==2:
				logging.info('48 horas draft')
				self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==3:
				logging.info('72 horas draft')
				self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)

	###### Iniviciativa Formulario #####
	condicion=[('state','=','form')]
	condicion+=[('type','=','lead')]
	ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
	if len(ids)>0:
		for id in ids:
			obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
			fecha_lead=obj.write_date #debe ser la fecha de la ultima actualizacion 
			fecha_lead2 = datetime.strptime(fecha_lead, n_format)
			var = self.get_days(dd,fecha_lead2)

			if var==1:
				logging.info('24 horas form')
				self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==2:
				logging.info('48 horas form')
				self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)
			elif var==3:
				logging.info('72 horas form')
				self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, ini_id[0], obj.id ,True, context=context)

        ###### Noticacion 24 horas antes de reprogramacion #####

	condicion=[('state','!=','cancel')]
        condicion+=[('state','!=','done')]
	condicion+=[('type','=','lead')]
        condicion+=[('reprogram_date','!=', False)]

	ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
	if len(ids)>0:
		for id in ids:
			obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
			fecha_lead=obj.create_date
			fecha_lead3 = datetime.strptime(fecha_lead, n_format)
			var = self.get_days(fecha_lead3,dd)
			if var==1:
				#logging.info('24 horas antes')
				self.pool.get('email.template').send_mail(cr, uid, ini_after_id[0], obj.id ,True, context=context)


        ###### Oportunidad Nueva #####
        condicion=[('state','=','draft')]
        condicion+=[('type','=','opportunity')]
        ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
        if len(ids)>0:
                for id in ids:
                        obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
                        fecha_lead=obj.create_date
                        fecha_lead_new = datetime.strptime(fecha_lead, n_format)
                        var = self.get_days(dd,fecha_lead_new)
                        if var==1:
                                logging.info('24 horas draft opportunity')
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==2:
                                logging.info('48 horas draft opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==3:
                                logging.info('72 horas draft opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)

        ###### Oportunidad Calificacion #####
        condicion=[('state','=','score')]
        condicion+=[('type','=','opportunity')]
        ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
        if len(ids)>0:
                for id in ids:
                        obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
                        fecha_lead=obj.write_date
                        fecha_lead_new = datetime.strptime(fecha_lead, n_format)
                        var = self.get_days(dd,fecha_lead_new)
                        if var==1:
                                logging.info('24 horas score opportunity')
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==2:
                                logging.info('48 horas score opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==3:
                                logging.info('72 horas score opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)



        ###### Oportunidad Propuesta #####
        condicion=[('state','=','proposal')]
        condicion+=[('type','=','opportunity')]
        ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
        if len(ids)>0:
                for id in ids:
                        obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
                        fecha_lead=obj.write_date
                        fecha_lead_new = datetime.strptime(fecha_lead, n_format)
                        var = self.get_days(dd,fecha_lead_new)
                        if var==1:
                                logging.info('24 horas proposal opportunity')
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==2:
                                logging.info('48 horas proposal opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==3:
                                logging.info('72 horas proposal opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)


        ###### Oportunidad Negociacion #####
        condicion=[('state','=','open')]
        condicion+=[('type','=','opportunity')]
        ids=self.pool.get('crm.lead').search(cr, uid,condicion,context=None)
        if len(ids)>0:
                for id in ids:
                        obj=self.pool.get('crm.lead').browse(cr,uid,id,context=context)
                        fecha_lead=obj.write_date
                        fecha_lead_new = datetime.strptime(fecha_lead, n_format)
                        var = self.get_days(dd,fecha_lead_new)
                        if var==1:
                                logging.info('24 horas open opportunity')
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==2:
                                logging.info('48 horas open opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)
                        elif var==3:
                                logging.info('72 horas open  opportunity')
                                self.escalado(obj,cr,uid,context)
                                self.pool.get('email.template').send_mail(cr, uid, opp_id[0], obj.id ,True, context=context)




        return True



    def get_days(self, date_a, date_b):
	resta = date_a-date_b
	dias = resta.days
	return dias

    def escalado(self,obj,cr,uid,context):
        con_user=[('user_id','=',obj.user_id.id)]
	hr_ids = self.pool.get('hr.employee').search(cr, uid,con_user,context=None)
	hr_obj = self.pool.get('hr.employee').browse(cr,uid,hr_ids[0],context=context)
	hr_parent = hr_obj.department_id.parent_id
	if hr_parent is not None:
		con_parent=[('department_id','=',hr_parent.id)]
		hr_parent_ids = self.pool.get('hr.employee').search(cr, uid,con_parent,context=None)
		hr_parent_obj = self.pool.get('hr.employee').browse(cr,uid,hr_parent_ids[0],context=context)
		self.pool.get('crm.lead').write(cr, uid, obj.id, {'user_id':hr_parent_obj.user_id.id}, context=context)
	return True
