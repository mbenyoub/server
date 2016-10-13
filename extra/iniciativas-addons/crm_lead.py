# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class crm_lead(osv.osv):
    _inherit = 'crm.lead'

    _columns = {
	'project_estimate': fields.char('Presupuesto del Proyecto',size=124),
	'recognized_company' : fields.boolean('Empresa reconocida?'),
	'company': fields.many2one('res.partner', string='Empresa'),
        'branch': fields.many2one('pant.branch', string='Ramo'),
        'capacity': fields.selection([('CH','Chica'),('M','Mediana'),('G','Grande')],select=True, string='Tamanio'),
        'corporate_culture': fields.many2one('pant.culture', string='Cultura'),

        'required_aut': fields.boolean('Contacto requiere autorizacion'),
        'name_contact': fields.char('Nombre del contacto objetivo', size=124),
	'email': fields.char('Email', size=124),
	'funcion': fields.char('Funcion', size=124),
	'telefono': fields.char('Telefono', size=124),

	'required_need': fields.boolean('Existe una necesidad real?'),
	'category_id': fields.many2one('pant.category', string='Categorias'),
        'why_our_products': fields.text('Porque busca los productos?'),
        'about_us': fields.text('Como se entero de CDS?'),
        'required_our_products': fields.text('Porque no requiere los productos CDS'),

	'date_start': fields.date('Fecha de Arranque'),
	'duration': fields.char('Duracion',size=124),

	'character_client': fields.many2one('pant.character', string='Caracter'),
        'attitude_client': fields.many2one('pant.attitude', string='Actitud'),
        'customer_treatment': fields.many2one('pant.treatment', string='Trato'),
        'characteristic_1': fields.many2one('pant.feature', string='Caracteristica 1'),
        'characteristic_2': fields.many2one('pant.feature', string='Caracteristica 2'),

	'calling_ids': fields.one2many('pant.phonecall', 'lead_id','Llamadas'),

	#'type_form_id': fields.many2one('pant.form', string='Tipo'),
	'type_form_id': fields.many2one('email.template', string='Tipo'),
	'status': fields.selection([('no_sent','No enviado'),('sent','Enviado'),('responded','Respondido')],select=True, string='Estado'),
	'questions': fields.html('Preguntas'),
        'answers': fields.text('Respuestas'),

	'reprogram_date': fields.datetime('Fecha Prevista'),

	#Oportunidades
	'cotizacion': fields.date('Cotizacion', required=True),
        'cotizacion_r': fields.date('Cotizacion Recepcion', required=True),
	#Reunion
	'meeting_ids': fields.one2many('op.meeting', 'lead_id','Reuniones'),

	#Cancelacion iniciativa
	'reason_cancell': fields.text('Motivo de cancelacion'),

	#Negociacion
	'project_type': fields.many2one('op.project', string='Tipo de Proyecto'),
	'estimate_active': fields.boolean('Activar presupuesto'),
	'agreements': fields.text('Acuerdos con el cliente'),
	'promises': fields.text('Promesas'),
	'additional_note': fields.text('Descripcion adicionales al proyecto'),
	'description_project': fields.text('Descripciones Basicas'), 
    }



    _defaults = {       
        'status' : 'no_sent',
    }


    def write(self, cr, uid, ids, vals, context=None):
	if vals.get('answers') is not None:
		vals['status']='responded'
    	return super(crm_lead,self).write(cr, uid, ids, vals, context=context)

    #def create(self, cr, uid, vals, context=None):
	#vals['state']='draft'
	#vals.update({'state':'draft'})
	#logging.info(vals)
	#return super(crm_lead,self).create(cr, uid, vals, context=context)

    def case_cancel(self, cr, uid, ids, context=None):
	view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'iniciativas-addons', 'w_cancel_lead_view')
	super(crm_lead,self).case_cancel(cr, uid, ids, context=context)
  	return {'name':_("Solicitud de Cancelacion"),'view_mode': 'form','view_id': [view_id and view_id[1] or False] , 'view_type': 'form','res_model': 'w.cancel.lead','type': 'ir.actions.act_window','target': 'new',}
	

    def change_form(self,cr,uid,ids,form_id,context=None):
	vals={}
       	if form_id:
       	     obj=self.pool.get('email.template').browse(cr,uid,form_id)
       	     vals.update({'questions':obj.body_html})
       	return {'value':vals}

    def change_project_type(self,cr,uid,ids,project_type,context=None):
        vals={}
        if project_type:
             obj=self.pool.get('op.project').browse(cr,uid,project_type)
             vals.update({'description_project':obj.description})
        return {'value':vals}	

    def change_category(self,cr,uid,ids,category_id,context=None):
        vals={}
        if category_id:
        	obj=self.pool.get('pant.category').browse(cr,uid,category_id)
        	form_pool= self.pool.get('email.template')
        	condicion=[('name','=',obj.name)]
		form_ids=form_pool.search(cr, uid,condicion,context=None)
		if len(form_ids)>0:
			obj_form=form_pool.browse(cr,uid,form_ids[0])
			vals.update({'questions':obj_form.body_html,'type_form_id':obj_form.id})

	return {'value':vals}

    def sent_request(self, cr, uid, ids, context=None):
        #self.write(cr,uid,ids,{'status':'sent'})
        return True

    def sent_form(self, cr, uid, ids, context=None):
	obj=self.pool.get('crm.lead').browse(cr,uid,ids[0])
	self.pool.get('email.template').send_mail(cr, uid, obj.type_form_id, ids[0] ,True, context=context)
	self.write(cr,uid,ids,{'status':'sent'})

	return True

    def print_letter(self, cr, uid, ids, context=None):
        logging.info('print_letter')
        datas = {
                     'model': 'crm.lead',
                     'ids': ids,
                     'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'carta.compromiso.report', 'datas': datas, 'nodestroy': True}


crm_lead()
