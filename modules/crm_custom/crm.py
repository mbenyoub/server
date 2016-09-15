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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import pytz
from openerp import tools, pooler, SUPERUSER_ID

class crm_case_section(osv.Model):
    _inherit = "crm.case.section"
    
    def button_update_users(self, cr, uid, ids, context=None):
        """
            Abre el formulario para actualizar los equipos de ventas
        """
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm_custom', 'wizard_update_serction_user_view')
        
        user_ids = []
        # Obtiene los usuarios que se mostraran sobre el equipo de ventas
        section = self.browse(cr, uid, ids[0], context=context)
        if section.user_id:
            user_ids.append(section.user_id.id or False)
        for member in section.member_ids:
            try:
                user_ids.index(member.id)
            except:
                user_ids.append(member.id or False)
        
        return {
            'name': "Actualizar equipo de Ventas por default",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'update.section.user.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_section_id': section.id or False,
                'user_ids': user_ids
            }
        }
    
crm_case_section()

