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
	'title_id': fields.many2one('pant.title', string='Objetivo'),
        'name_contact': fields.char('Nombre del contacto', size=124),
	'email': fields.char('Email', size=124),
	'funcion': fields.char('Funcion', size=124),
	'telefono': fields.char('Telefono', size=124),

	'required_need': fields.boolean('Existe una necesidad real?'),
	'category_id': fields.many2one('pant.category', string='Categorias'),
        'why_our_products': fields.char('Porque busca los productos?',size=300),
        'about_us': fields.char('Como se entero de CDS?',size=300),
        'required_our_products': fields.char('Porque no requiere los productos CDS',size=300),

	'date_start': fields.date('Fecha de Arranque'),
	'duration': fields.char('Duracion',size=124),

	'character_client': fields.many2one('pant.character', string='Caracter'),
        'attitude_client': fields.many2one('pant.attitude', string='Actitud'),
        'customer_treatment': fields.many2one('pant.treatment', string='Trato'),
        'characteristic_1': fields.many2one('pant.feature', string='Caracteristica 1'),
        'characteristic_2': fields.many2one('pant.feature', string='Caracteristica 2'),

	'calling_ids': fields.one2many('pant.phonecall', 'lead_id','Llamadas'),

	'type_form_id': fields.many2one('pant.form', string='Tipo'),
	'status': fields.selection([('no_sent','No enviado'),('sent','Enviado'),('responded','Respondido')],select=True, string='Estado'),

    }


crm_lead()
