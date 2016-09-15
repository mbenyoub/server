# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import tools
from openerp.osv import osv, fields

class mail_compose_message(osv.Model):
    _inherit = 'mail.compose.message'

    def onchange_template_id(self, cr, uid, ids, template_id, composition_mode, model, res_id, context=None):
        """
            Si trae parametros default con adjuntos no agrega los de la plantilla
        """
        result = super(mail_compose_message, self).onchange_template_id(cr, uid, ids, template_id, composition_mode, model, res_id, context=context)
        
        #print"*************** context onchange_template_id ***************** ", context
        #print"*************** context onchange_template_id ***************** ", context
        #print"**************** result ************************ ", result
        
        if context == None:
            context = {}
        
        if context.get('default_attachment_ids'):
            result['value']['attachment_ids'] = context['default_attachment_ids'] or []
            #print"*********** attachment_ids ************ ", result['value']['attachment_ids']
        
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
