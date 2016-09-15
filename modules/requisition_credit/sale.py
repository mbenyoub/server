# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Saldaña (riss_600@hotmail.com)
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
#
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.base_status.base_stage import base_stage
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class sale_order(osv.Model):
    _inherit = "sale.order"
    
    def action_requisition_credit_new(self, cr, uid, ids, context=None):
        """
            Permite realizar una solicitud de credito
        """
        if context is None:
            context = {}
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'requisition_credit', 'requisition_credit_credit_new_form_view')
        
        sale = self.browse(cr, uid, ids[0], context=context)
        
        # Obtiene los parametros que van por default
        context['default_partner_id'] = sale.partner_id.id or False
        context['default_rfc'] = sale.partner_id.rfc
        context['default_current_credit'] = sale.partner_id.credit_limit
        context['default_user_id'] = uid
        context['default_state'] = 'open'
        
        return {
            'name':_("Solicitud de credito"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'requisition.credit.credit',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context
        }
    
sale_order()

