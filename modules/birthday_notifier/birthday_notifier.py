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

class birthday_notifier(osv.Model):
    _name = "birthday.notifier.mail"
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
    
    def notify_message(self, cr, uid, res_id, model, subject, body, partner_ids=[], context=None):
        """
            Agrega una nota sobre el sistema avisando los cumpleaños
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
    
    def cron_birthday_notifier(self, cr, uid, context=None):
        """
            Envia un correo electronico a los partners que cumplen años
        """
        #print "************************************************************* "
        #print "*********************** Envio mail ************************** "
        
        if context is None:
            context = {}
        
        partner_ids = []
        
        # Obtiene los partners que cumplen años y que son clientes de openerp
        cr.execute("""
            select id
            from res_partner
            where
                is_company=False and
                email!='' and
                to_char(date_birth, 'DD-MM')=to_char(current_timestamp, 'DD-MM')""")
        
        partner_ids = [x[0] for x in cr.fetchall()]
        #print "************************** partner_ids ************************ ", partner_ids
        
        # Envia correo electronico a los partner
        if len(partner_ids):
            self.send_mail(cr, uid, partner_ids, context=context)
        return True
    
    def send_mail(self, cr, uid, partner_ids, context=None):
        """
            Envia un correo a los partners recibidos en los parametros con una felicitacion de cumpleaños
        """
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = company.user_mail
        parent_id = user_id.partner_id.id
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = company.birthday_subject
        subject = subject.replace(u'${COMPANY}', str(company.name))
        # Obtiene el contenido del mensaje y agrega la informacion de la compañia
        body_html = company.birthday_body
        body_html = body_html.replace(u'${COMPANY}', str(company.name))
        body_html = body_html.replace(u'${COMPANY_STREET}', str(company.street))
        body_html = body_html.replace(u'${COMPANY_STREET2}', str(company.street2))
        body_html = body_html.replace(u'${COMPANY_ZIP}', str(company.zip))
        body_html = body_html.replace(u'${COMPANY_CITY}', str(company.city))
        body_html = body_html.replace(u'${COMPANY_STATE}', str(company.state_id.name))
        body_html = body_html.replace(u'${COMPANY_COUNTRY}', str(company.country_id.name))
        body_html = body_html.replace(u'${COMPANY_PHONE}', str(company.phone))
        body_html = body_html.replace(u'${COMPANY_WEBSITE}', str(company.website))
        
        #print "*************************** website ********************* ", str(company.website)
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'body': body_html,
            'email_from': email_from,
            'partner_ids': [[6, 0, partner_ids]],
            'model': 'birthday.notifier.mail',
            'res_id': 0,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
        
        # Recorre los partners para enviar los mensajes
        for partner in self.pool.get('res.partner').browse(cr, uid, partner_ids, context=context):
            # Configuracion del correo para el partner
            email_to = "%s <%s>" %(partner.name, partner.email)
            body_mail = body_html.replace(u'${PARTNER}', str(partner.name))
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
                #print "*********************** mensaje enviado ****************** "
            
            print "************* Cumpleaños de ************* ", partner.name
            
            name = u'%s '%(partner.name)
            
            # Si tiene un vendedor notifica al vendedor
            if partner.user_id:
                if partner.parent_id:
                    body_sale = u"""
                                <div>Hoy <span style="font-weight: bold;">%s</span> es cumpleaños del cliente <span style="font-weight: bold;">"%s"</span> de la empresa <span style="font-weight: bold;">"%s"</span>.</div>
                                <br>
                                <div>Puedes contactar con el cliente para darle una felicitacion.</div>
                                """ %(partner.date_birth, partner.name, partner.parent_id.name)
                else:
                    body_sale = u"""
                                <div>Hoy <span style="font-weight: bold;">%s</span> es cumpleaños del cliente <span style="font-weight: bold;">"%s"</span>.</div>
                                <br>
                                <div>Puedes contactar con el cliente para darle una felicitacion.</div>
                                """ %(partner.date_birth, name)
                
                subject = u'Hoy es cumpleaños del cliente ' + name
                part_ids = []
                if partner.user_id:
                    part_ids.append(partner.user_id.partner_id.id)
                
                # Registra el evento en mail.message
                values_message = {
                    'subject': subject,
                    'body': body_sale,
                    'email_from': email_from,
                    'partner_ids': [[6,False,part_ids]],
                    'model': 'birthday.notifier.mail',
                    'res_id': 0,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                mail_message_sale_id = mail_message_obj.create(cr, uid, values_message, context=context)
                
                # Registra documento en mail.mail
                mail_sale_id = mail_mail_obj.create(cr, uid, {
                    'mail_message_id': mail_message_sale_id,
                    'mail_server_id': mail_server_ids and mail_server_ids[0],
                    'state': 'outgoing',
                    'email_from': email_from,
                    'email_to': "%s <%s>" %(partner.user_id.name, partner.user_id.email),
                    'email_cc': '',
                    'reply_to': reply_to,
                    'body_html': body_sale}, context=context)
                if mail_sale_id:
                    # Envia el correo al partner
                    mail_mail_obj.send(cr, uid, [mail_sale_id], context=context)
                
                # Notificacion sobre el vendedor en el sistema
                self.notify_message(cr, uid, 0, 'birthday.notifier.mail', subject, body_sale, partner_ids=part_ids, context=context)
        return True
    
