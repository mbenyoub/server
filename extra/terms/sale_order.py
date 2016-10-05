# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class sale_order(osv.osv):
    _inherit = 'sale.order'


    _columns = {
		'terms_line': fields.many2many('t.terms','t_terms_rel','sale_id','terms_id','Terminos y Condiciones'),
    }



sale_order()
