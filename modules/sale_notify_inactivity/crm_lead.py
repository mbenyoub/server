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

import time
from datetime import datetime, timedelta
from openerp.osv import fields,osv

class crm_lead(osv.Model):
    """ Model for Crm lead """
    _inherit = 'crm.lead'
    
    def _get_date_notify(self, cr, uid, date, days, context=None):
        """
            Obtiene la fecha de notificacion
        """
        if days:
            date_notify = datetime.strptime(date, '%Y-%m-%d')
            date_notify = date_notify + timedelta(days=days)
            return date_notify.strftime('%Y-%m-%d')
        return date
    
    def _get_date_notify_default(self, cr, uid, ids, context=None):
        """
            Obtiene la fecha de notificacion por default a 10 dias
        """
        date = time.strftime('%Y-%m-%d')
        date_notify = self._get_date_notify(cr, uid, date, 10, context=context)
        return date_notify
    
    def _get_user_notify_default(self, cr, uid, ids, context=None):
        """
            Retorna el id del usuario logeado
        """
        return uid

    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(crm_lead, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        # Actualiza la actividad de los partners
        lead = self.browse(cr, uid, res, context=context)
        if lead.partner_id:
            if lead.partner_id.is_company == True:
                partner_obj = self.pool.get('res.partner')
                partner_obj._reset_date_notify(cr, uid, lead.partner_id.id, context=context)
            elif lead.partner_id.parent_id:
                partner_obj = self.pool.get('res.partner')
                partner_obj._reset_date_notify(cr, uid, lead.partner_id.parent_id.id, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de modificar
        super(crm_lead, self).write(cr, uid, ids, vals, context=context)
        
        # Actualiza la actividad de los partners
        partner_obj = self.pool.get('res.partner')
        for lead in self.browse(cr, uid, ids, context=context):
            # Actualiza la actividad de los partners
            if lead.partner_id.is_company == True:
                partner_obj._reset_date_notify(cr, uid, lead.partner_id.id, context=context)
            elif lead.partner_id.parent_id:
                partner_obj._reset_date_notify(cr, uid, lead.partner_id.parent_id, context=context)
        return True

    _columns = {
        'notify_sale' : fields.boolean(string='Enviar recordatorio a vendedor'),
        'notify_sale_date' : fields.date(string='Avisar Dia'),
        'notify_sale_user_id': fields.many2one('res.users', 'Recordar a'),
        'notify_sale_message': fields.text('Mensaje'),
    }
    
    _defaults = {
        'notify_sale': False,
        'notify_sale_date': _get_date_notify_default,
        'notify_sale_user_id': _get_user_notify_default,
    }

crm_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
