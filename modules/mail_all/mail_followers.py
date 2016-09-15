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

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import osv, fields

# ---------------------------------------------------------
# Mensajes de correo
# ---------------------------------------------------------

class mail_notification(osv.Model):
    _inherit = "mail.notification"
    
    def get_partners_to_notify(self, cr, uid, message, partners_to_notify=None, context=None):
        """ Return the list of partners to notify, based on their preferences.

            :param browse_record message: mail.message to notify
            :param list partners_to_notify: optional list of partner ids restricting
                the notifications to process
        """
        print "************************ get partner notify *****************+ "
        notify_pids = []
        for notification in message.notification_ids:
            if notification.read:
                continue
            partner = notification.partner_id
            # If partners_to_notify specified: restrict to them
            if partners_to_notify is not None and partner.id not in partners_to_notify:
                continue
            # Do not send to partners without email address defined
            if not partner.email:
                continue
            # Do not send to partners having same email address than the author (can cause loops or bounce effect due to messy database)
            #if message.author_id and message.author_id.email == partner.email:
            #    continue
            # Partner does not want to receive any emails or is opt-out
            if partner.notification_email_send == 'none':
                continue
            # Partner wants to receive only emails and comments
            #if partner.notification_email_send == 'comment' and message.type not in ('email', 'comment'):
            #    continue
            # Partner wants to receive only emails
            #if partner.notification_email_send == 'email' and message.type != 'email':
            #    continue
            notify_pids.append(partner.id)
        print "******************* notify_pids ************** ", notify_pids
        return notify_pids
    
mail_notification()

