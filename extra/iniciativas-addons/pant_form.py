# -*- coding: utf-8 -*-
from osv import osv,fields
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)


class pant_form(osv.osv):
	_name = 'pant.form'

        _columns = {
		'name': fields.char('Nombre',size=300,required=True),
                'html': fields.html('Html Body',required=True),
                }

pant_form()
