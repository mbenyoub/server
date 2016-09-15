# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class email_template(osv.osv):
    _inherit = 'email.template'

    _sql_constraints = [('email_template_name_unique', 'unique(name)', 'Ya existe otra plantilla con el mismo nombre')]



email_template()
