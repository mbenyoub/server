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
#              Ivan Macias (ivanfallen@gmail.com)
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

from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)

#
# crm.meeting is defined in module base_calendar
#
class crm_meeting(osv.Model):
    """ Model for CRM meetings """
    _inherit = 'crm.meeting'
    
    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(crm_meeting, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        # Actualiza la actividad de los partners
        partner_obj = self.pool.get('res.partner')
        meeting = self.browse(cr, uid, res, context=context)
        for partner in meeting.partner_ids:
            if partner.is_company == True:
                #print "************* partner ****************** ", partner
                partner_obj._reset_date_notify(cr, uid, partner.id, context=context)
            elif partner.parent_id:
                #print "************* partner ****************** ", partner
                partner_obj._reset_date_notify(cr, uid, partner.parent_id.id, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de modificar
        super(crm_meeting, self).write(cr, uid, ids, vals, context=context)
        
        partner_obj = self.pool.get('res.partner')
        
        # Actualiza el registro de actividad para ver en el calendario
        for meeting in self.browse(cr, uid, ids, context=context):
            # Actualiza la actividad de los partners
            for partner in meeting.partner_ids:
                if partner.is_company == True:
                    #print "************* partner ****************** ", partner
                    partner_obj._reset_date_notify(cr, uid, partner.id, context=context)
                elif partner.parent_id:
                    #print "************* partner ****************** ", partner
                    partner_obj._reset_date_notify(cr, uid, partner.parent_id.id, context=context)
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
