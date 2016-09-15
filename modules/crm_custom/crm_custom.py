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
        'date' : fields.date('Fecha', required=True, readonly=True, select=True),
        'user_id' : fields.many2one('res.users', 'Responsable', readonly=True),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
    }
    
crm_custom_calendar_activity()

# ---------------------------------------------------------
# CRM - Notificacion de llamadas y reuniones
# ---------------------------------------------------------

class crm_custom_notify(osv.Model):
    _name = "crm.custom.notify"
    _inherits = {'mail.message': 'mail_message_id'}
    
    def _get_default_from(self, cr, uid, context=None):
        """
            Obtiene el remitente por default para el envio de correos y notificaciones
        """
        this = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if this.alias_domain:
            return '%s@%s' % (this.alias_name, this.alias_domain)
        elif this.email:
            return this.email
        raise osv.except_osv(_('Invalid Action!'), _("Unable to send email, please configure the sender's email address or alias."))
    
    def cron_notify_event(self, cr, uid, context=None):
        """
            Envia un correo electronico a los partners que tienen llamadas planificadas
        """
        #print "************************************************************* "
        #print "*********************** Envio mail ************************** "
        
        phone_obj = self.pool.get('crm.phonecall')
        meeting_obj = self.pool.get('crm.meeting')
        
        if context is None:
            context = {}
        # Envia notificaciones sobre las llamdas
        current_datetime = time.strftime('%Y-%m-%d %H:%M:%S')
        phone_ids = phone_obj.search(cr, uid, [('state', '!=', 'done'),('alarm_id','!=',False),('notify','=',False),('trigger_date','<=',current_datetime)], context=context)
        #print "******************* fecha actual ******************* ", current_datetime
        #print "******************* llamadas por validar *********** ", phone_ids
        if phone_ids:
            self.send_mail_phonecall(cr, uid, phone_ids, context=context)
        
        # Envia notificaciones sobre las reuniones
        meeting_ids = meeting_obj.search(cr, uid, [('alarm_id','!=',False),('notify','=',False),('trigger_date','<=',current_datetime)], context=context)
        #print "******************* fecha actual ******************* ", current_datetime
        #print "******************* Reuniones por validar *********** ", meeting_ids
        if meeting_ids:
            self.send_mail_meeting(cr, uid, meeting_ids, context=context)
        
        return True
    
    def send_mail_phonecall(self, cr, uid, phone_ids, context=None):
        """
            Envia un correo con relacion a las llamadas que tienen el recordatorio disponible
        """
        phone_obj = self.pool.get('crm.phonecall')
        notify_ids = []
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        current_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        # Recorre las llamadas y valida si la fecha de notificacion aplica
        for phone in phone_obj.browse(cr, uid, phone_ids, context=context):
            event_date = datetime.strptime(phone.trigger_date, '%Y-%m-%d %H:%M:%S')
            #print "************* type **************** ", type(event_date), "  - ", type(current_date)
            if not phone.user_id:
                continue
            #print "*********** validate dates ************ ", current_date, " >= ", event_date
            # Valida las fechas del documento
            if current_date >= event_date:
                notify_ids.append(phone.id)
                #~ tz = pytz.timezone(phone.user_id.tz) if phone.user_id.tz else pytz.utc
                #~ start = pytz.utc.localize(event_date).astimezone(tz)     # convert start in user's timezone
                #~ start = start.replace(hour=0, minute=0, second=0)   # change start's time to 00:00:00
                #~ start = start.astimezone(pytz.utc)                  # convert start back to utc
                #~ start_date = start.strftime("%Y-%m-%d %H:%M:%S")
                #~ phone_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(phone.date, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context)
                
                # Da formato a la fecha
                delta = timedelta(hours=6)
                phone_date = event_date - delta
                #print "*************** phonecall date ************** ", phone_date
                
                # Envia la notificacion sobre la llamada
                values = {
                    'subject': 'Recordatorio de Llamada %s - %s'%(phone_date,phone.name),
                    'event': phone.name,
                    'date': phone_date,
                    'response': phone.user_id.name,
                    'description': phone.description
                }
                partner_ids = []
                partner_ids.append(phone.user_id.partner_id.id)
                # Envia el mensaje
                self.send_mail(cr, uid, partner_ids, values, context=context) 
        # Actualiza los registros notificados
        phone_obj.write(cr, uid, notify_ids, {'notify': True,}, context=context)
        return True
    
    def notify_message(self, cr, uid, res_id, model, subject, body, partner_ids=[], context=None):
        """
            Agrega una nota sobre mensajeria
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        email_from = user.email
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'body': body,
            'email_from': email_from,
            'notified_partner_ids': [[6,False,partner_ids]],
            'type': 'notification',
            #'attachment_ids': [(6, 0, attachments)],
            'res_id': res_id,
            'model': model,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'author_id': uid
        }
        mail_message_id = self.pool.get('mail.message').create(cr, uid, values_message, context=context)
        
        return True
    
    def send_mail_meeting(self, cr, uid, meeting_ids, context=None):
        """
            Envia un correo con relacion a las Reuniones que tienen el recordatorio disponible
        """
        meeting_obj = self.pool.get('crm.meeting')
        notify_ids = []
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        current_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        # Recorre las llamadas y valida si la fecha de notificacion aplica
        for meeting in meeting_obj.browse(cr, uid, meeting_ids, context=context):
            event_date = datetime.strptime(meeting.trigger_date, '%Y-%m-%d %H:%M:%S')
            #print "************* type **************** ", type(event_date), "  - ", type(current_date)
            if not meeting.user_id:
                continue
            #print "*********** validate dates ************ ", current_date, " >= ", event_date
            # Valida las fechas del documento
            if current_date >= event_date:
                notify_ids.append(meeting.id)
                
                #meeting_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(meeting.date, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context)
                
                # Da formato a la fecha
                delta = timedelta(hours=6)
                meeting_date = event_date - delta
                #print "*************** meeting date ************** ", meeting_date
                
                # Envia la notificacion sobre la llamada
                values = {
                    'subject': 'Recordatorio de Reunion %s - %s'%(meeting_date,meeting.name),
                    'event': meeting.name,
                    'date': meeting_date,
                    'response': meeting.user_id.name,
                    'description': meeting.description
                }
                partner_ids = []
                partner_ids.append(meeting.user_id.partner_id.id)
                # Agrega a los asistentes
                if meeting.partner_ids:
                    for partner in meeting.partner_ids:
                        partner_ids.append(partner.id)
                # Envia el mensaje
                self.send_mail(cr, uid, partner_ids, values, context=context) 
        # Actualiza los registros notificados
        meeting_obj.write(cr, uid, notify_ids, {'notify': True,}, context=context)
        return True
    
    def send_mail(self, cr, uid, part_ids, values, context=None):
        """
            Envia un correo a los partners recibidos en los parametros
        """
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = uid
        parent_id = company.partner_id.id
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = values['subject']
        # Valida que no vengan repetidos los contactos
        partner_ids = []
        for p_id in part_ids:
            if not (p_id in partner_ids):
                partner_ids.append(p_id)
        
        # Obtiene el contenido del mensaje y agrega la informacion de la compañia
        body_html = u"""
            <br><br>
            Evento: %s <br>
            Fecha: %s <br>
            Responsable: %s <br>
            Descripcion:  <br>
            <div>
               %s
            </div>
            <br>
            <br>
            <div style="width: 375px; margin: 0px; padding: 0px; background-color: #8E0000; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px; background-repeat: repeat no-repeat;">
                <h3 style="margin: 0px; padding: 2px 14px; font-size: 12px; color: #DDD;">
                    <strong style="text-transform:uppercase;">%s</strong></h3>
            </div>
            <div style="width: 347px; margin: 0px; padding: 5px 14px; line-height: 16px; background-color: #F2F2F2;">
                <span style="color: #222; margin-bottom: 5px; display: block; ">
                    %s <br/>
                    %s %s<br/>
                    %s %s %s<br/>
                </span>
                <div style="margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: 0px; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px; ">
                    Teléfono:&nbsp; %s
                </div>
                <div>
                    Pagina web :&nbsp; %s
                </div>
                <p></p>
            """%(values['event'],values['date'],values['response'],values['description'],company.name,company.street,company.street2,company.zip,company.city,company.state_id.name,company.country_id.name,company.phone,company.website)
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'body': body_html,
            'email_from': email_from,
            'partner_ids': [[6, False, partner_ids]],
            'model': 'crm.custom.notify',
            'res_id': 0,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
        
        
        # Recorre los partners para enviar los mensajes
        for partner in self.pool.get('res.partner').browse(cr, uid, partner_ids, context=context):
            # Configuracion del correo para el partner
            email_to = "%s <%s>" %(partner.name, partner.email)
            body_mail = body_html
            #print "***************** email to **************** ", email_to
            #print "***************** email from **************** ", email_from
            
            # Registra documento en mail.mail
            mail_mail_id = mail_mail_obj.create(cr, uid, {
                'mail_message_id': mail_message_id,
                'mail_server_id': mail_server_ids and mail_server_ids[0],
                'state': 'outgoing',
                'email_from': email_from,
                'email_to': email_to,
                'email_cc': '',
                'reply_to': reply_to,
                'body_html': body_mail}, context=context)
            if mail_mail_id:
                # Envia el correo al partner
                mail_mail_obj.send(cr, uid, [mail_mail_id], context=context)
                #print "*********************** mensaje enviado (Evento) ****************** "
            
        self.notify_message(cr, uid, 0, 'crm.custom.notify', subject, body_html, partner_ids=partner_ids, context=context)
        return True

crm_custom_notify()
