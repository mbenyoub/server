# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class t_terms(osv.osv):
    _name = 't.terms'


    _columns = {
		'name': fields.char('Marca',size=150,required=True),
		'description': fields.text('Descripcion',required=True),
    }
