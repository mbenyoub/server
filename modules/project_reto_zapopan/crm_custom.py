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
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class crm_custom_calendar_activity(osv.Model):
    _name = "crm.custom.calendar.activity"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get')
        return links._links_get(cr, uid, context=context)
    
    _columns = {
        'name': fields.char('Lista', size=128, required=True, readonly=True),
        'category': fields.char('Categoria', size=64, readonly=True),
        'date' : fields.datetime('Fecha', required=True, readonly=True, select=True),
        'user_id' : fields.many2one('res.users', 'Responsable', readonly=True),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
        'project_id': fields.related('reference', 'project_id', type="many2one", relation="project.project", store=True, string="Proyecto", readonly=True),
        'user_ids': fields.related('reference', 'user_ids', type="text", store=True, string="Usuarios", readonly=True),
    }
    
crm_custom_calendar_activity()