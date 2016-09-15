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

class res_partner(osv.Model):
    """ Inherits partner to notify client"""
    _inherit = 'res.partner'

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
            Obtiene la fecha de notificacion por default
        """
        date = time.strftime('%Y-%m-%d')
        date_notify = self._get_date_notify(cr, uid, date, 30, context=context)
        return date_notify
    
    def _get_date_next(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la fecha de la ultima actividad mas 31 dias
        """
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.activity:
                date = partner.activity
            else:
                date = time.strftime('%Y-%m-%d')
            datet = datetime.strptime(date, '%Y-%m-%d')
            datet = datet + timedelta(days=31)
            date_ant = datet.strftime('%Y-%m-%d')
            # Agrega la fecha anterior
            res[partner.id] = date_ant
        return res
    
    def _next_notify_scale(self, cr, uid, partner_id, context=None):
        """
            Prepara el escalado para la siguiente notificacion
        """
        partner = self.browse(cr, uid, partner_id, context=context)
        
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa y la escala
        if partner.notify:
            # Actualiza la escala
            next_scale = partner.notify_scale + 1
            if next_scale == 1:
                # Toma los dias de notificacion para el vendedor y actualiza la fecha de notificacion
                days = partner.section_id.notify_trade
                #print "************* notificacion igual a 1 dias ************* ", days
            else:
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(next_scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo y regresa una escala
                        next_scale -= 1
                        break
                # Obtiene los dias que aplican sobre el equipo de trabajo al responsable
                days = section.notify_boss
                #print "*********** notificacion igual a ", partner.notify_scale, " ******** ", days
            # Actualiza la fecha de notificacion para el vendedor
            date_notify = self._get_date_notify(cr, uid, partner.notify_activity, days, context=context)
            self.write(cr, uid, [partner.id], {'notify_scale': next_scale, 'notify_activity': date_notify}, context=context)
    
    def _reset_date_notify(self, cr, uid, partner_id, context=None):
        """
            Actualiza la fecha en la que se debe notificar con el escalado 1
        """
        partner = self.browse(cr, uid, partner_id, context=context)
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa
        if partner.notify:
            # Obtiene los dias para la notificacion del vendedor
            days = partner.section_id.notify_trade
            date = time.strftime('%Y-%m-%d')
            # Obtiene la fecha a notificar
            date_notify = self._get_date_notify(cr, uid, date, days, context=context)
            # Actualiza el registro
            self.write(cr, uid, [partner.id], {'notify_activity': date_notify, 'notify_scale': 1, 'activity': date}, context=context)
            #print "******************* date notify **************** ", date_notify
    
    def _update_date_notify(self, cr, uid, partner_id, context=None):
        """
            Actualiza la fecha en la que se debe notificar al vendedor
        """
        partner = self.browse(cr, uid, partner_id, context=None)
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa
        if partner.notify:
            scale = partner.notify_scale
            if scale == 1:
                # Toma los dias de notificacion para el vendedor y actualiza la fecha de notificacion
                days = partner.section_id.notify_trade
                #print "************* notificacion igual a 1 dias ************* ", days
            else:
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo
                        break
                # Obtiene los dias que aplican sobre el equipo de trabajo al responsable
                days = section.notify_boss
                #print "*********** notificacion igual a ", partner.notify_scale, " ******** ", days
            # Valida que tenga la fecha de actividad
            date = time.strftime('%Y-%m-%d') if not partner.activity else partner.activity
            #print "****************** fecha actividad *************** ", date, "  dias ", days
            # Obtiene la fecha a notificar
            date_notify = self._get_date_notify(cr, uid, date, days, context=context)
            # Actualiza el registro
            self.write(cr, uid, [partner.id], {'notify_activity': date_notify}, context=context)
            #print "******************* date notify **************** ", date_notify
    
    def _next_notify_scale_sale(self, cr, uid, partner_id, context=None):
        """
            Prepara el escalado para la siguiente notificacion para ventas
        """
        partner = self.browse(cr, uid, partner_id, context=context)
        
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa y la escala
        if partner.notify_sale:
            # Actualiza la escala
            next_scale = partner.notify_scale_sale + 1
            if next_scale == 1:
                # Toma los dias de notificacion para el vendedor y actualiza la fecha de notificacion
                days = partner.section_id.notify_trade
                #print "************* notificacion igual a 1 dias ************* ", days
            else:
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(next_scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo y regresa una escala
                        next_scale -= 1
                        break
                # Obtiene los dias que aplican sobre el equipo de trabajo al responsable
                days = section.notify_boss
                #print "*********** notificacion ventas igual a ", partner.notify_scale_sale, " ******** ", days
            # Actualiza la fecha de notificacion para el vendedor
            date_notify = self._get_date_notify(cr, uid, partner.notify_activity_sale, days, context=context)
            self.write(cr, uid, [partner.id], {'notify_scale_sale': next_scale, 'notify_activity_sale': date_notify}, context=context)
    
    def _reset_date_notify_sale(self, cr, uid, partner_id, context=None):
        """
            Actualiza la fecha en la que se debe notificar con el escalado 1 en ventas
        """
        partner = self.browse(cr, uid, partner_id, context=context)
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa
        if partner.notify_sale:
            # Obtiene los dias para la notificacion del vendedor
            days = partner.section_id.notify_trade
            date = time.strftime('%Y-%m-%d')
            # Obtiene la fecha a notificar
            date_notify = self._get_date_notify(cr, uid, date, days, context=context)
            # Actualiza el registro
            self.write(cr, uid, [partner.id], {'notify_activity_sale': date_notify, 'notify_scale_sale': 1, 'activity_sale': date}, context=context)
            #print "******************* date notify venta **************** ", date_notify
    
    def _update_date_notify_sale(self, cr, uid, partner_id, context=None):
        """
            Actualiza la fecha en la que se debe notificar al vendedor cuando no hay ventas
        """
        partner = self.browse(cr, uid, partner_id, context=None)
        # Actualiza la fecha de notificacion si el partner tiene la opcion de notify activa
        if partner.notify_sale:
            scale = partner.notify_scale_sale
            if scale == 1:
                # Toma los dias de notificacion para el vendedor y actualiza la fecha de notificacion
                days = partner.section_id.notify_trade
                #print "************* notificacion venta igual a 1 dias ************* ", days
            else:
                # Equipo de ventas principal asignado al cliente
                section = partner.section_id
                # Toma el responsable del equipo de ventas segun el escalado
                for i in range(scale - 2):
                    # Toma los dias de notificacion para el responsable del equipo de trabajo y actualiza la fecha de notificacion
                    if section.parent_id:
                        # Escala sobre el equipo de trabajo segun tenga configurado el escalado el cliente
                        section = section.parent_id
                    else:
                        # Si ya no hay a donde escalar detiene el flujo
                        break
                # Obtiene los dias que aplican sobre el equipo de trabajo al responsable
                days = section.notify_boss
                #print "*********** notificacion venta igual a ", partner.notify_scale_sale, " ******** ", days
            # Valida que tenga la fecha de actividad
            date = time.strftime('%Y-%m-%d') if not partner.activity_sale else partner.activity_sale
            #print "****************** fecha actividad venta *************** ", date, "  dias ", days
            # Obtiene la fecha a notificar
            date_notify = self._get_date_notify(cr, uid, date, days, context=context)
            # Actualiza el registro
            self.write(cr, uid, [partner.id], {'notify_activity_sale': date_notify}, context=context)
            #print "******************* date notify venta **************** ", date_notify
    
    def button_scale_sale(self, cr, uid, ids, context=None):
        """
            Escala sobre el vendedor y el equipo de ventas
        """
        # Recorre los partnersd
        for partner in self.browse(cr, uid, ids, context=None):
            # Escalado sobre vendedores y a equipo de ventas
            section = partner.section_id
            # Valida que el cliente tenga un vendedor
            if not section:
                raise osv.except_osv('Error escalado!', 'Verifique que el cliente tenga un vendedor asignado.')
            # Valida que el cliente tenga un equipo de ventas
            if not section:
                raise osv.except_osv('Error escalado!', 'Verifique que el cliente tenga un equipo de ventas asignado.')
            # Valida que el equipo de ventas tenga otro equipo de ventas para aplicar el escalado
            if not section.parent_id:
                raise osv.except_osv('Error escalado!', 'No se pudo realizar el escalado, porque no hay otro equipo de ventas asignado en el arbol.')
            # Escala al vendedor y el equipo de ventas
            self.write(cr, uid, [partner.id], {'user_id': section.user_id.id, 'section_id': section.parent_id.id}, context=context)
        
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'base', 'view_partner_form')
        res_id = res and res[1] or False
        
        #~ Redirecciona al formulario de solicitud
        return {
            'name': "Clientes",
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'res.partner', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id' : ids[0], # id of the object to which to redirected
        }
    
    def create(self, cr, uid, vals, context=None):
        """
            Agrega el nuevo cliente a la base de datos de intelisis
        """
        # Funcion original de crear
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        # Revisa si debe notificar al vendedor y calcula la fecha siguiente para la notificacion si no hay actividad
        if vals.get("notify"):
            # Si la escala es igual a 1 se prepara para notificar al vendedor
            if vals.get("notify_scale") == 1:
                # Actualiza los dias a escalar el registro
                self._update_date_notify(cr, uid, res, context=context)
        # Revisa si debe notificar al vendedor por ventas
        if vals.get("notify_sale"):
            # Si la escala es igual a 1 se prepara para notificar al vendedor
            if vals.get("notify_scale_sale") == 1:
                # Actualiza los dias a escalar el registro
                self._update_date_notify_sale(cr, uid, res, context=context)
        return res
        
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza en el cliente la proxima fecha de notificacion
        """
        # Fecha actual
        date = time.strftime('%Y-%m-%d')
        date_time = datetime.strptime(date, '%Y-%m-%d')
        
        #print "***************** ids ************ ", ids, "  ", type(ids)
        
        # Valida que los ids vengan en una lista, de no ser asi crea una lista
        if type(ids) != list:
            ids = [ids]
        
        # Recorre los clientes para ver si hay que actualizar la notificacion
        for partner in self.browse(cr, uid, ids, context=context):
            # Revisa si debe notificar al vendedor y calcula la fecha siguiente para la notificacion si no hay actividad
            if vals.get('notify') and ((not partner.notify_activity) or (date_time > datetime.strptime(partner.notify_activity, '%Y-%m-%d'))):
                # Obtiene los dias para la notificacion del vendedor
                days = partner.section_id.notify_trade
                 # Obtiene la fecha a notificar
                date_notify = self._get_date_notify(cr, uid, date, days, context=context)
                # Actualiza los valores a modificar
                vals['activity'] = date
                vals['notify_scale'] = 1
                vals['notify_activity'] = date_notify
            if vals.get('notify_sale') and ((not partner.notify_activity_sale) or (date_time > datetime.strptime(partner.notify_activity_sale, '%Y-%m-%d'))):
                # Obtiene los dias para la notificacion del vendedor
                days = partner.section_id.notify_trade
                 # Obtiene la fecha a notificar
                date_notify = self._get_date_notify(cr, uid, date, days, context=context)
                # Actualiza los valores a modificar
                vals['activity_sale'] = date
                vals['notify_scale_sale'] = 1
                vals['notify_activity_sale'] = date_notify
        # Funcion original de modificar
        res = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        #print "**************** write notify ****************** ", res
        return res
        
    _columns = {
        # Notificacion inactividad
        'notify' : fields.boolean(string='Enviar notificacion por inactividad', help="Notifica al vendedor cuando el vendedor no ha tenido contacto con el cliente sobre un periodo de tiempo especificado sobre el equipo de ventas"),
        'activity' : fields.date(string='Ultima actividad', readonly=True),
        'notify_activity' : fields.date('Fecha Aviso notificacion', readonly=True),
        'notify_scale' : fields.integer('Escala notificacion'),
        'activity_ref': fields.function(_get_date_next, type="date", string='Fecha + 30 dias', store=True),
        # Notificacion ventas
        'notify_sale' : fields.boolean(string='Enviar notificacion de ventas', help="Notifica al vendedor cuando el cliente no a concretado una venta sobre un periodo de tiempo especificado sobre el equipo de ventas"),
        'activity_sale' : fields.date(string='Ultima actividad sobre ventas', readonly=True),
        'notify_activity_sale' : fields.date('Fecha Aviso notificacion ventas', readonly=True),
        'notify_scale_sale' : fields.integer('Escala notificacion ventas'),
    }
    
    _defaults = {
        'notify': False,
        'activity': lambda *a: time.strftime('%Y-%m-%d'),
        'notify_activity': _get_date_notify_default,
        'notify_scale': 1,
        'notify_sale': False,
        'activity_sale': lambda *a: time.strftime('%Y-%m-%d'),
        'notify_activity_sale': _get_date_notify_default,
        'notify_scale_sale': 1
    }

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
