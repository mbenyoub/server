# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class crm_lead(osv.osv):
    _inherit = 'crm.lead'

    _columns = {
	'company': fields.char('Empresa',size=124),
        'branch': fields.char('Ramo',size=124),
        'capacity': fields.char('Tamanio',size=124),
        'corporate_culture': fields.char('Cultura Empresarial',size=124),
        'required_aut': fields.boolean('Contacto requiere autorizacion'),
        'name_contact': fields.char('Nombre del contacto', size=124),
	'email': fields.char('Email', size=124),
	'funcion': fields.char('Funcion', size=124),
	'telefono': fields.char('Telefono', size=124),
	'required_need': fields.boolean('Existe necesidad?'),
        'why_our_products': fields.text('Porque busca los productos?'),
        'about_us': fields.text('Como se entero de nosotros?'),
        'required_our_products': fields.text('Porque requiere los productos CDS'),
	'date_start': fields.date('Fecha de Arranque'),
	'duration': fields.char('Duracion',size=124),
	'character_client': fields.text('Caracter del cliente'),
        'attitude_client': fields.text('Actitud del cliente'),
        'customer_treatment': fields.text('Trato del cliente'),
        'characteristic_1': fields.text('Caracteristica 1 del cliente'),
        'characteristic_2': fields.text('Caracteristica 2 del cliente'),

    }


crm_lead()
