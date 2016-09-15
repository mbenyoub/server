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

import time
from datetime import datetime, timedelta, date
from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)

#
# crm.meeting is defined in module base_calendar
#
class crm_meeting(osv.Model):
    """ Model for CRM meetings """
    _inherit = 'crm.meeting'
    
    def action_draft(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Pendiente
        """
        return self.write(cr, uid, ids, {'state_meeting': 'draft'}, context=context)
    
    def action_reschedule(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Reagendada
        """
        # Reagenda la reunion
        self.write(cr, uid, ids, {'state_meeting': 'reschedule'}, context=context)
        
        # Duplica la reunion
        res = self.copy(cr, uid, ids[0], context=context)
        print "*********** res ************* ", res
        
        # Aplica evaluacion sobre porcentaje de avance entregables
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base_calendar', 'view_crm_meeting_form')
        return {
            'name':_("Reunion"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'crm.meeting',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : res, # id of the object to which to redirected
        }
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Realizada
        """
        return self.write(cr, uid, ids, {'state_meeting': 'done'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Cancalada
        """
        return self.write(cr, uid, ids, {'state_meeting': 'cancel'}, context=context)
    
    def action_absence(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Inasistencia
        """
        return self.write(cr, uid, ids, {'state_meeting': 'absence'}, context=context)
    
    def _get_date(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la fecha en formato año-mes-dia
        """
        if context is None:
            context = {}
        res = {}
        # Recorre los registros
        for meeting in self.browse(cr, uid, ids, context=context):
            res[meeting.id] = meeting.date
        return res
    
    def _get_date_week(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la fecha en formato año-mes-dia
        """
        if context is None:
            context = {}
        res = {}
        
        # Recorre los registros
        for meeting in self.browse(cr, uid, ids, context=context):
            date = time.strftime('%Y-%m-%d')
            
            if meeting.date2:
                date = meeting.date2
            week = datetime.strptime(date, '%Y-%m-%d').strftime('%W')
            res[meeting.id] = week
        return res
    
    _columns = {
        'notify': fields.boolean('Notificado'),
        'trigger_date': fields.datetime('Trigger Date', readonly="True"),
        'calendar_activity_id': fields.many2one('crm.custom.calendar.activity', 'Actividad calendario', ondelete='cascade'),
        'state_meeting': fields.selection([
            ('draft','Pendiente'),
            ('reschedule','Reagendada'),
            ('done','Realizada'),
            ('cancel','Cancelada'),
            ('absence','Inasistencia'),
        ], 'Estado', readonly=True, track_visibility='onchange', help='Indicador del estado de la reunion'),
        'date2': fields.function(_get_date, type="date", string='Fecha', track_visibility='always', store=True),
        'date_week': fields.function(_get_date_week, type="char", string='Semana', track_visibility='always', store=True),
    }
    
    _defaults = {
        'alarm_id': 12,
        'state_meeting': 'draft'
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'state_meeting' : 'draft',
            'file': False,
            'notify': False,
        })
        # Funcion original duplicar
        res = super(crm_meeting, self).copy(cr, uid, id, default, context)
        
         # Crea el registro de actividad para ver en el calendario
        meeting = self.browse(cr, uid, res, context=context)
        reference = 'crm.meeting,' + str(meeting.id)
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_id = activity_obj.create(cr, uid, {
            'name': meeting.name,
            'date': meeting.date,
            'user_id': meeting.user_id.id,
            'category': 'Reunion',
            'reference': reference
            }, context=context)
        # Actualiza el registro de reunion para agregar el id de la actividad
        self.write(cr, uid, [meeting.id], {'calendar_activity_id': activity_id, 'name': "%s (Copia)"%(meeting.name,)}, context=context)
        
        return res
    
    def create(self, cr, uid, vals, context=None):
        """
            Registra una actividad ligada a la reunion para visualizar en el calendario
        """
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
        res = super(crm_meeting, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        #~ Revisa que la reunion no tenga una actividad
        meeting = self.browse(cr, uid, res, context=context)
        #print "************** meeting ************** ", meeting
        if meeting.calendar_activity_id:
            #print "******* actividad creada (create)******** "
            return res
        
        #~ Valida que el objeto crm.meeting se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.meeting'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Reunion', 'object': 'crm.meeting', })
        
        # Crea el registro de actividad para ver en el calendario
        meeting = self.browse(cr, uid, res, context=context)
        reference = 'crm.meeting,' + str(meeting.id)
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_id = activity_obj.create(cr, uid, {
            'name': meeting.name,
            'date': meeting.date,
            'user_id': meeting.user_id.id,
            'category': 'Reunion',
            'reference': reference
            }, context=context)
        #print "**************** activity ************** ", activity_id
        # Actualiza el registro de reunion para agregar el id de la actividad
        self.write(cr, uid, [meeting.id], {'calendar_activity_id': activity_id,}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza una actividad ligada a la reunion para visualizar en el calendario
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
        super(crm_meeting, self).write(cr, uid, ids, vals, context=context)
        
        #print "************** vals ***************** ", vals
        if vals.get('calendar_activity_id'):
            #print "************ no crear ************* "
            return True
        
        #~ Valida que el objeto crm.meeting se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.meeting'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Reunion', 'object': 'crm.meeting', })
        
        # Actualiza el registro de actividad para ver en el calendario
        for meeting in self.browse(cr, uid, ids, context=context):
            activity_obj = self.pool.get('crm.custom.calendar.activity')
            # Si no existe el registro lo crea
            if not meeting.calendar_activity_id:
                reference = 'crm.meeting,' + str(meeting.id)
                activity_id = activity_obj.create(cr, uid, {
                    'name': meeting.name,
                    'date': meeting.date,
                    'user_id': meeting.user_id.id,
                    'category': 'Reunion',
                    'reference': reference
                    }, context=context)
                #print "**************** activity ************** ", activity_id
                # Actualiza el registro de reunion para agregar el id de la actividad
                self.write(cr, uid, [meeting.id], {'calendar_activity_id': activity_id,}, context=context)
            else:
                # Si existe actualiza la informacion
                activity_id = activity_obj.write(cr, uid, [meeting.calendar_activity_id.id], {
                    'name': meeting.name,
                    'date': meeting.date,
                    'user_id': meeting.user_id.id
                    }, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Elimina el registro del calendario de actividades
        """
        #print "**************** funcion unlink ************************** "
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_delete = []
        #~ Elimina el registro relacionado con el
        for meeting in self.browse(cr, uid, ids, context=context):
            if meeting.calendar_activity_id:
                activity_delete.append(meeting.calendar_activity_id.id)
                #print "***************** Eliminado documento relacionado ", meeting.calendar_activity_id.id
        # Elimina los registros y sus dependencias
        res = super(crm_meeting, self).unlink(cr, uid, ids, context=context)
        activity_obj.unlink(cr, uid, activity_delete, context=context)
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
