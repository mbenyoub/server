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

class sale_notify_inactivity_log(osv.Model):
    """
        Bitacora para registro de notificaciones a vendedor
    """
    _name = "sale.notify.inactivity.log"
    
    _columns = {
        'date': fields.date(string='Fecha', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'user_id': fields.many2one('res.users', 'Usuario', readonly=True),
        'section_id': fields.many2one('crm.case.section', 'Equipo de ventas', readonly=True),
    }

sale_notify_inactivity_log()

class sale_notify_inactivity_mail(osv.Model):
    _name = "sale.notify.inactivity.mail"
    _inherits = {'mail.message': 'mail_message_id'}
    
    def cron_sale_notify_inactivity(self, cr, uid, context=None):
        """
            Envia un correo de notificacion al vendedor cuando no se ha comunicado con el cliente
        """
        #print "************************************************************* "
        #print "*********************** Notificacion mail ************************** "
        
        if context is None:
            context = {}
        
        partner_ids = []
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene a los partners que se les tiene que enviar la notificacion
        cr.execute("""
         select id
         from res_partner
         where
            notify=True and
            user_id>0 and
            notify_activity<='%s'"""%(date,))
        
        partner_ids = [x[0] for x in cr.fetchall()]
        #print "************************** partner_ids ************************ ", partner_ids
        
        # Envia correo electronico a los partner
        if len(partner_ids):
            self.send_mail_sale(cr, uid, partner_ids, context=context)
        return True
    
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
    
    def send_mail_sale(self, cr, uid, partner_ids, context=None):
        """
            Envia un correo a los vendedores de los partner recibidos para notificar inactividad
        """
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = company.user_mail
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = "Notificacion de inactividad de Cliente"
        # Obtiene el contenido del mensaje
        body_html = "No se ha tenido contacto con el cliente. Se recomienda contactar con el cliente a la brevedad." 
        
        # Recorre los partners para enviar los mensajes
        for partner in partner_obj.browse(cr, uid, partner_ids, context=context):
            # Registra en la bitacora la notificacion del contacto
            vals_log = {'date': time.strftime('%Y-%m-%d'), 'partner_id': partner.id, 'user_id': partner.user_id.id, 'section_id': partner.section_id.id}
            #print "******************* registro log **************** ", vals_log
            self.pool.get('sale.notify.inactivity.log').create(cr, uid, vals_log, context=context)
            
            user_id = False
            
            #print "******************** scale **************** ", partner.notify_scale
            # Obtiene el mensaje a enviar
            if partner.notify_scale == 1:
                body_mail = """
                            <div>No se ha tenido contacto con el cliente <span style="font-weight: bold;">"%s"</span> desde el dia <span style="font-weight: bold;">%s</span>.</div>
                            <br>
                            <div>Se recomienda contactar con el cliente a la brevedad.</div>
                            """ %(partner.name, partner.activity)
                # Configuracion del correo a enviar
                email_to = "%s <%s>" %(partner.user_id.name, partner.user_id.email)
                user_id = partner.user_id.id
            else:
                body_mail = """
                            <div>El vendedor <span style="font-weight: bold;">"%s"</span> no ha tenido contacto con el cliente <span style="font-weight: bold;">"%s"</span> desde el dia <span style="font-weight: bold;">%s</span>.</div>
                            <br>
                            <div>Se recomienda contactar con el responsable del equipo de ventas <span style="font-weight: bold;">%s</span> para darle seguimiento al cliente.</div>
                            """ %(partner.user_id.name, partner.name, partner.activity, partner.section_id.name)
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(partner.notify_scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo
                        break
                #print "**************** section ************** ", section
                # Configuracion del correo a enviar
                email_to = "%s <%s>" %(section.user_id.name, section.user_id.email)
                user_id = section.user_id.id
            #print "***************** email to **************** ", email_to
            #print "***************** email from **************** ", email_from
            
            part_ids = []
            if user_id:
                part_ids.append(user_id)
            
            # Registra el evento en mail.message
            values_message = {
                'subject': subject,
                'body': body_html,
                'email_from': email_from,
                'partner_ids': [[6, False, part_ids]],
                'model': 'sale.notify.inactivity.mail',
                'res_id': 0,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
            
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
                # Envia el correo al vendedor
                mail_mail_obj.send(cr, uid, [mail_mail_id], context=context)
                #print "*********************** mensaje enviado ****************** "
            # Aplica el escalado del registro
            partner_obj._next_notify_scale(cr, uid, partner.id, context=context)
            
            # Notificacion sobre el vendedor en el sistema
            self.notify_message(cr, uid, 0, 'sale.notify.inactivity.mail', subject, body_html, partner_ids=part_ids, context=context)
        return True
    
    def cron_sale_notify_lead(self, cr, uid, context=None):
        """
            Envia un recordatorio a un usuario sobre un pedido de venta
        """
        #print "************************************************************* "
        #print "*********************** Recordatorio mail ************************** "
        
        if context is None:
            context = {}
        
        lead_ids = []
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene a los usuarios que se les tiene que enviar la notificacion
        cr.execute("""
         select id
         from crm_lead
         where
            notify_sale=True and
            notify_sale_user_id>0 and
            notify_sale_date='%s'"""%(date,))
        
        lead_ids = [x[0] for x in cr.fetchall()]
        #print "************************** lead_ids ************************ ", lead_ids
        
        # Envia correo electronico a los usuarios solicitados
        if len(lead_ids):
            self.send_mail_lead(cr, uid, lead_ids, context=context)
        return True
    
    def send_mail_lead(self, cr, uid, lead_ids, context=None):
        """
            Envia un correo a los usuarios en las iniciativas donde se solicito un recordatorio
        """
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        lead_obj = self.pool.get('crm.lead')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = company.user_mail
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = "Recordatorio de Iniciativa/Oportunidad"
        # Obtiene el contenido del mensaje
        body_html = "Revisar oportunidad." 
        
        partner_ids = []
        if lead.notify_sale_user_id:
            partner_ids.append(lead.notify_sale_user_id.partner_id.id)
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'body': body_html,
            'email_from': email_from,
            'partner_ids': [[6,False,partner_ids]],
            'model': 'sale.notify.inactivity.mail',
            'res_id': 0,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
        
        # Recorre las oportunidades para enviar los mensajes
        for lead in lead_obj.browse(cr, uid, lead_ids, context=context):
            # Revisa si es una iniciativa u oportunidad
            lead_type = 'Oportunidad' if lead.type == 'opportunity' else 'Iniciativa'
            # Obtiene el mensaje a enviar
            body_mail = """
                        <h3>%s "%s":</h3>
                        <div>%s</div>
                        """ %(lead_type, lead.name, lead.notify_sale_message)
            # Configuracion del correo a enviar
            email_to = "%s <%s>" %(lead.notify_sale_user_id.name, lead.notify_sale_user_id.email)
        
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
                # Envia el correo al vendedor
                mail_mail_obj.send(cr, uid, [mail_mail_id], context=context)
                #print "*********************** mensaje enviado ****************** "

        return True


class sale_notify_inactivity_sale_mail(osv.Model):
    _name = "sale.notify.inactivity.sale.mail"
    _inherits = {'mail.message': 'mail_message_id'}
    
    def cron_sale_notify_inactivity(self, cr, uid, context=None):
        """
            Envia un correo de notificacion al vendedor cuando no se ha comunicado con el cliente
        """
        #print "************************************************************* "
        #print "*********************** Notificacion mail ************************** "
        
        if context is None:
            context = {}
        
        partner_ids = []
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene a los partners que se les tiene que enviar la notificacion
        cr.execute("""
         select id
         from res_partner
         where
            notify_sale=True and
            user_id>0 and
            notify_activity_sale<='%s'"""%(date,))
        
        partner_ids = [x[0] for x in cr.fetchall()]
        #print "************************** partner_ids ************************ ", partner_ids
        
        # Envia correo electronico a los partner
        if len(partner_ids):
            self.send_mail_sale(cr, uid, partner_ids, context=context)
        return True
    
    def notify_message(self, cr, uid, res_id, model, subject, body, partner_ids=[], context=None):
        """
            Agrega una nota sobre el sistema 
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
    
    def send_mail_sale(self, cr, uid, partner_ids, context=None):
        """
            Envia un correo a los vendedores de los partner recibidos para notificar inactividad
        """
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = company.user_mail
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = "Notificacion de inactividad de Cliente (Ventas)"
        # Obtiene el contenido del mensaje
        body_html = "No se ha tenido contacto con el cliente para concretar las ventas pendientes. Se recomienda contactar con el cliente a la brevedad." 
        
        # Recorre los partners para enviar los mensajes
        for partner in partner_obj.browse(cr, uid, partner_ids, context=context):
            # Registra en la bitacora la notificacion del contacto
            vals_log = {'date': time.strftime('%Y-%m-%d'), 'partner_id': partner.id, 'user_id': partner.user_id.id, 'section_id': partner.section_id.id}
            #print "******************* registro log **************** ", vals_log
            self.pool.get('sale.notify.inactivity.log').create(cr, uid, vals_log, context=context)
            user_id = False
            
            #print "******************** scale **************** ", partner.notify_scale
            # Obtiene el mensaje a enviar
            if partner.notify_scale == 1:
                body_mail = """
                            <div>No se ha tenido contacto con el cliente <span style="font-weight: bold;">"%s"</span> desde el dia <span style="font-weight: bold;">%s</span> para concretar ventas pendientes.</div>
                            <br>
                            <div>Se recomienda contactar con el cliente a la brevedad.</div>
                            """ %(partner.name, partner.activity)
                # Configuracion del correo a enviar
                email_to = "%s <%s>" %(partner.user_id.name, partner.user_id.email)
                user_id = partner.user_id.id
            else:
                body_mail = """
                            <div>El vendedor <span style="font-weight: bold;">"%s"</span> no ha tenido contacto con el cliente <span style="font-weight: bold;">"%s"</span> desde el dia <span style="font-weight: bold;">%s</span>.</div>
                            <br>
                            <div>Se recomienda contactar con el responsable del equipo de ventas <span style="font-weight: bold;">%s</span> para darle seguimiento al cliente.</div>
                            """ %(partner.user_id.name, partner.name, partner.activity, partner.section_id.name)
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(partner.notify_scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo
                        break
                #print "**************** section ************** ", section
                # Configuracion del correo a enviar
                email_to = "%s <%s>" %(section.user_id.name, section.user_id.email)
                user_id = section.user_id.id
            #print "***************** email to **************** ", email_to
            #print "***************** email from **************** ", email_from
            
            part_ids = []
            if user_id:
                part_ids.append(user_id)
            
            # Registra el evento en mail.message
            values_message = {
                'subject': subject,
                'body': body_html,
                'email_from': email_from,
                'partner_ids': [[6, False, part_ids]],
                'model': 'sale.notify.inactivity.sale.mail',
                'res_id': 0,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
            
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
                # Envia el correo al vendedor
                mail_mail_obj.send(cr, uid, [mail_mail_id], context=context)
                #print "*********************** mensaje enviado ****************** "
            # Aplica el escalado del registro
            partner_obj._next_notify_scale_sale(cr, uid, partner.id, context=context)
            
            # Notificacion sobre el vendedor en el sistema
            self.notify_message(cr, uid, 0, 'sale.notify.inactivity.sale.mail', subject, body_html, partner_ids=part_ids, context=context)
        return True
    