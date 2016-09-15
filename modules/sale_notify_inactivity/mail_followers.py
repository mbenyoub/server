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

class mail_notification(osv.Model):
    """ Model for Sale Order """
    _inherit = 'mail.notification'

    def _notify(self, cr, uid, msg_id, partners_to_notify=None, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(mail_notification, self)._notify(cr, uid, msg_id, partners_to_notify=partners_to_notify, context=context)
        
        #print "*************** partners_to_notify ************* ", partners_to_notify
        
        # Actualiza la actividad de los partners
        if partners_to_notify:
            partner_obj = self.pool.get('res.partner')
            for partner in partner_obj.browse(cr, uid, partners_to_notify, context=context):
                if partner.is_company == True:
                    partner_obj._reset_date_notify(cr, uid, partner.id, context=context)
                elif partner.parent_id:
                    partner_obj._reset_date_notify(cr, uid, partner.parent_id.id, context=context)
        return res

mail_notification()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
