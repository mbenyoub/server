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
from openerp.tools.translate import _

class admon_active_user(osv.osv_memory):
    """
        Solicita el tiempo que va a estar activo el usaurio
    """
    _name = "admon.active.user.wizard"

    _columns = {
        'user_id': fields.many2one('admon.database.user', 'Usuario BD', select=True, ondelete='cascade', required=True),
        'date': fields.date('Fecha de Vencimiento', required=True),
    }
    
    def _get_date_default(self, cr, uid, ids, context=None):
        """
            Obtiene la fecha de vencimiento por default 30 dias
        """
        date = time.strftime('%Y-%m-%d')
        date = self.pool.get('admon.database.user')._get_date_end(cr, uid, date, 30, context=context)
        return date
    
    _defaults = {
        'date': _get_date_default,
    }
    
    def action_active_user(self, cr, uid, ids, context=None):
        """
            Pone como activo al usuario y con la fecha de vencimiento tecleada
        """
        user_obj = self.pool.get('admon.database.user')
        data = self.browse(cr, uid, ids, context=context)[0]
        ctx = context.copy()
        ctx['date_end'] = data.date
        
        # Crea al usuario
        user_obj.action_active_user(cr, uid, [data.user_id.id], context=ctx)
        return True

admon_active_user()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
