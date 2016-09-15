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

from datetime import datetime, timedelta, date
from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)

#
# crm.phonecall is defined in module base_calendar
#
class crm_phonecall(osv.Model):
    """ Model for CRM phonecall """
    _inherit = 'crm.phonecall'
    _columns = {
        'notify': fields.boolean('Notificado'),
        'alarm_id': fields.many2one('res.alarm', 'Recordatorio', ondelete='cascade'),
        'trigger_date': fields.datetime('Trigger Date', readonly="True"),
        'calendar_activity_id': fields.many2one('crm.custom.calendar.activity', 'Actividad calendario', ondelete='cascade'),
    }
    
    def cron_notify_event_button(self, cr, uid, ids, context=None):
        self.pool.get('crm.custom.notify').cron_notify_event(cr, uid, context=context)
        return True
    
    def create(self, cr, uid, vals, context=None):
        """
            Registra una actividad ligada a la llamada para visualizar en el calendario
        """
        #print "********* create call ********** "
        
        # Proceso para calcular la fecha sobre notificacion a llamadas
        if context is None:
            context = {}
        event_date = vals.get('date', False)
        alarm_id = vals.get('alarm_id', False)
        if event_date and alarm_id:
            alarm = self.pool.get('res.alarm').browse(cr, uid, alarm_id, context=context)
            # Actualiza la fecha de notificacion del evento
            dtstart = datetime.strptime(vals['date'], "%Y-%m-%d %H:%M:%S")
            if alarm.trigger_interval == 'days':
                delta = timedelta(days=alarm.trigger_duration)
            if alarm.trigger_interval == 'hours':
                delta = timedelta(hours=alarm.trigger_duration)
            if alarm.trigger_interval == 'minutes':
                delta = timedelta(minutes=alarm.trigger_duration)
            trigger_date = dtstart + (alarm.trigger_occurs == 'after' and delta or -delta)
            vals['trigger_date'] = trigger_date
            vals['notify'] = False
        
        # Funcion original de crear
        res = super(crm_phonecall, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        #~ Revisa que la llamada no tenga una actividad
        phonecall = self.browse(cr, uid, res, context=context)
        if phonecall.calendar_activity_id:
            #print "******* actividad creada (create)******** "
            return res
        
        #~ Valida que el objeto crm.phonecall se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.phonecall'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Llamadas', 'object': 'crm.phonecall', })
        
        #print "*************** reg request.link *************** "
        
        # Crea el registro de actividad para ver en el calendario
        #print "*************** phonecall ****************** ", phonecall
        reference = 'crm.phonecall,' + str(phonecall.id)
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_id = activity_obj.create(cr, uid, {
            'name': phonecall.name,
            'date': phonecall.date,
            'user_id': phonecall.user_id.id,
            'category': 'Llamada',
            'reference': reference
            }, context=context)
        #print "**************** activity ************** ", activity_id
        # Actualiza el registro de reunion para agregar el id de la actividad
        self.write(cr, uid, [phonecall.id], {'calendar_activity_id': activity_id,}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza una actividad ligada a la llamada para visualizar en el calendario
        """
        
        # Proceso para actualizar la fecha sobre notificacion a llamadas
        if context is None:
            context = {}
        event_date = vals.get('date', False)
        alarm_id = vals.get('alarm_id', False)
        if event_date or alarm_id:
            # Obtiene el primer registro
            phone = self.browse(cr, uid, ids[0], context=context)
            # Revisa si recibio el parametro de alarma sino pone el anterior
            if alarm_id:
                alarm = self.pool.get('res.alarm').browse(cr, uid, alarm_id, context=context)
            else:
                alarm = phone.alarm_id
            # Revisa si cambio la fecha sino pone la anterior
            if not event_date:
                event_date = phone.date
            # Actualiza la fecha de notificacion del evento
            dtstart = datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S")
            if alarm.trigger_interval == 'days':
                delta = timedelta(days=alarm.trigger_duration)
            if alarm.trigger_interval == 'hours':
                delta = timedelta(hours=alarm.trigger_duration)
            if alarm.trigger_interval == 'minutes':
                delta = timedelta(minutes=alarm.trigger_duration)
            trigger_date = dtstart + (alarm.trigger_occurs == 'after' and delta or -delta)
            vals['trigger_date'] = trigger_date
            vals['notify'] = False
        
        # Funcion original de modificar
        super(crm_phonecall, self).write(cr, uid, ids, vals, context=context)
        
        if vals.get('calendar_activity_id'):
            return True
        
        #~ Valida que el objeto crm.phonecall se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.phonecall'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Llamadas', 'object': 'crm.phonecall', })
        
        # Actualiza el registro de actividad para ver en el calendario
        for phonecall in self.browse(cr, uid, ids, context=context):
            activity_obj = self.pool.get('crm.custom.calendar.activity')
            # Si no existe el registro lo crea
            if not phonecall.calendar_activity_id:
                reference = 'crm.phonecall,' + str(phonecall.id)
                activity_id = activity_obj.create(cr, uid, {
                    'name': phonecall.name,
                    'date': phonecall.date,
                    'user_id': phonecall.user_id.id,
                    'category': 'Llamada',
                    'reference': reference
                    }, context=context)
                #print "**************** activity ************** ", activity_id
                # Actualiza el registro de reunion para agregar el id de la actividad
                self.write(cr, uid, [phonecall.id], {'calendar_activity_id': activity_id,}, context=context)
            else:
                # Si existe actualiza la informacion
                activity_id = activity_obj.write(cr, uid, [phonecall.calendar_activity_id.id], {
                    'name': phonecall.name,
                    'date': phonecall.date,
                    'user_id': phonecall.user_id.id
                    }, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        """
            Elimina el registro del calendario de actividades
        """
        #print "**************** funcion unlink ************************** "
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_delete = []
        #~ Obtiene los ids de las actividades a eliminar
        for phonecall in self.browse(cr, uid, ids, context=context):
            if phonecall.calendar_activity_id:
                activity_delete.append(phonecall.calendar_activity_id.id)
                #print "***************** Eliminado documento ", phonecall.calendar_activity_id.id
        # Elimina los registros y sus dependencias
        res = super(crm_phonecall, self).unlink(cr, uid, ids, context=context)
        activity_obj.unlink(cr, uid, activity_delete, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
