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
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)
import openerp.addons.decimal_precision as dp

from openerp.tools.translate import _

#
# crm.meeting is defined in module base_calendar
#

class crm_meeting(osv.Model):
    """ Model for CRM meetings """
    _inherit = 'crm.meeting'
    
    def upload_file(self, cr, uid, ids, context=None):
        """
            Abre wizard para cargar la minuta de la reunion
        """
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si ya hay un archivo adjunto
        check_files = False
        #if meeting.file:
        #    check_files = True
        
        # Agrega al context el proyecto y el template por default
        context.update({
            'default_project_id': meeting.project_id.id,
            'default_phase_id': meeting.phase_id.id,
            'default_meeting_id': meeting.id,
            'default_check_files': check_files
        })
        
        # Carga arhcivo adjunto para subir minuta
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'project_rz_g2', 'wizard_upload_file_meeting_form_view')
        return {
            'name':_("Adjuntar Minuta"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'upload.file.meeting.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            #'res_id' : statement_id, # id of the object to which to redirected
        }
    
    def _evaluate_meting(self, cr, uid, id, type='done', context=None):
        """
            Ventana para calificar al emprendedor en reuniones de seguimiento
        """
        if context is None:
            context = {}
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, id, context=context)
        
        # Agrega al context el proyecto y el template por default
        context.update({
            'default_project_id': meeting.project_id.id,
            'default_phase_id': meeting.phase_id.id,
            'default_meeting_id': meeting.id,
            'type': type # Indicador de evento
        })
        
        # Aplica evaluacion sobre porcentaje de avance entregables
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'project_rz_g2', 'meeting_evaluation_wizard_form_view')
        return {
            'name':_("Evaluar Proyecto"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'meeting.evaluation.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            #'res_id' : statement_id, # id of the object to which to redirected
        }
    
    def action_draft(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Pendiente
        """
        return self.write(cr, uid, ids, {'state_meeting': 'draft'}, context=context)
    
    def meeting_reschedule(self, cr, uid, ids, context=None):
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
    
    def action_reschedule(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Reagendada
        """
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si es una reunion de evaluacion o de Reto zapopan
        if meeting.type == 'seg':
            # Aplica evaluacion sobre porcentaje de avance entregables
            return self._evaluate_meting(cr, uid, ids[0], type='reschedule', context=context)
        
        # Finaliza la reunion
        return self.meeting_reschedule(cr, uid, ids, context=context)
    
    def meeting_done(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado cerrada
        """
        return self.write(cr, uid, ids, {'state_meeting': 'done'}, context=context)
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a realizada
        """
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si es una reunion de evaluacion o de Reto zapopan
        if meeting.type == 'seg':
            # Aplica evaluacion sobre porcentaje de avance entregables
            return self._evaluate_meting(cr, uid, ids[0], type='done', context=context)
        
        # Finaliza la reunion
        return self.meeting_done(cr, uid, ids, context=context)
    
    def meeting_cancel(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Cancalada
        """
        return self.write(cr, uid, ids, {'state_meeting': 'cancel'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado cancelado
        """
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si es una reunion de evaluacion o de Reto zapopan
        if meeting.type == 'seg':
            # Aplica evaluacion sobre porcentaje de avance entregables
            return self._evaluate_meting(cr, uid, ids[0], type='cancel', context=context)
        
        # Finaliza la reunion
        return self.meeting_cancel(cr, uid, ids, context=context)
    
    def meeting_absence(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Inasistencia
        """
        return self.write(cr, uid, ids, {'state_meeting': 'absence'}, context=context)
    
    def action_absence(self, cr, uid, ids, context=None):
        """
            Pasa la reunion a estado Inasistencia
        """
        # Obtiene el objeto reunion a cerrar
        meeting = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si es una reunion de evaluacion o de Reto zapopan
        if meeting.type == 'seg':
            # Aplica evaluacion sobre porcentaje de avance entregables
            return self._evaluate_meting(cr, uid, ids[0], type='absence', context=context)
        
        # Finaliza la reunion
        return self.meeting_absence(cr, uid, ids, context=context)
    
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
        'phase_id': fields.many2one('project.phase', 'Fase proyecto', ondelete='set null'),
        'type': fields.selection([
            ('eval','Evaluacion'),
            ('seg','Seguimiento'),
            ('ase','Consultoria'),
            ('result','Resultados con reto Zapopan'),], 'Tipo', required=True),
        'project_log_project_ids': fields.one2many('project.log.project', 'meeting_id', string="Bitacora", ondelete="cascade"),
        'check_consultor': fields.boolean('Reunion consultoria contabilizada'),
        'file_name': fields.char('Nombre Archivo', readonly=True),
        'file': fields.binary('Archivo', help='Archivo a actualizar', readonly=True),
        'last_log_eval': fields.related('project_id', 'last_log_eval', type='selection', selection=[
            (10,'A'),(9,'B'),
            (8,'C'),(7,'D'),], string='Compromiso proyecto', store=True),
        'progress_eval': fields.related('project_id', 'progress_eval', type='float', digits_compute=dp.get_precision('Account'), string='Avance', store=True),
        'date_week': fields.function(_get_date_week, type="char", string='Semana', track_visibility='always', store=True),
    }
    
    _defaults = {
        'alarm_id': 12,
        'state_meeting': 'draft',
        'check_consultor': False,
        'file_name': 'minuta reunion.pdf'
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        
        default.update({
            'state_meeting' : 'draft',
            'file': False,
            'notify': False
        })
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
    
    def onchange_project(self, cr, uid, ids, project_id, type, context=None):
        """
            Agrega al retorno el domain sobre las fases del proyecto y asigna la fase activa
        """
        if context is None:
            context={}
        phase_obj = self.pool.get('project.phase')
        
        # Funcion original de onchange
        res = super(crm_meeting, self).onchange_project(cr, uid, ids, project_id, type, context=context)
        if not res.get('value',False):
            res['value'] = {}
        
        res['value']['phase_id'] = False
        
        # Actualiza el dominio del proyecto
        vals = [('validate_time','=',True),('state','=','open')]
        if project_id:
            vals.append(('project_id','=',project_id))
            # Obtiene la fase activa
            phase_ids = phase_obj.search(cr, uid, [('project_id','=',project_id),('state','=','open'),('validate_time','=',True)])
            if phase_ids:
                res['value']['phase_id'] = phase_ids[0]
        # Actualiza el dominio
        res['domain'] = {'phase_id': vals}
        
        return res
    
crm_meeting()

class crm_meeting_report(osv.Model):
    """ Model for CRM meetings """
    _name = 'crm.meeting.report'
    _table = "crm_meeting"
    _order = "project_id,date"
    
    _columns = {
        'date': fields.datetime('Date', states={'done': [('readonly', True)]}, required=True,),
        'date_deadline': fields.datetime('End Date', states={'done': [('readonly', True)]}, required=True,),
        'create_date': fields.datetime('Created', readonly=True),
        'duration': fields.float('Duration', states={'done': [('readonly', True)]}),
        'description': fields.text('Description', states={'done': [('readonly', True)]}),
        'location': fields.char('Location', size=264, help="Location of Event", states={'done': [('readonly', True)]}),
        'user_id': fields.many2one('res.users', 'Responsible', states={'done': [('readonly', True)]}),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'write_date': fields.datetime('Write Date', readonly=True),
        'date_open': fields.datetime('Confirmed', readonly=True),
        'date_closed': fields.datetime('Closed', readonly=True),
        'state': fields.selection(
                    [('draft', 'Unconfirmed'), ('open', 'Confirmed')],
                    string='Status', size=16, readonly=True, track_visibility='onchange'),
        'name': fields.char('Meeting Subject', size=128, required=True, states={'done': [('readonly', True)]}),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete="set null", required=True),
        'partner_id': fields.many2one('res.partner', 'Contacto', required=True),
        'consultor_select': fields.boolean('Consultor Seleccionado'),
        'date_string': fields.char('Fecha texto'),
        'date2': fields.date('Fecha'),
        'notify': fields.boolean('Notificado'),
        'trigger_date': fields.datetime('Trigger Date', readonly="True"),
        'state_meeting': fields.selection([
            ('draft','Pendiente'),
            ('reschedule','Reagendada'),
            ('done','Realizada'),
            ('cancel','Cancelada'),
            ('absence','Inasistencia'),
        ], 'Estado', readonly=True, track_visibility='onchange', help='Indicador del estado de la reunion'),
        'phase_id': fields.many2one('project.phase', 'Fase proyecto', ondelete='set null'),
        'type': fields.selection([
            ('eval','Evaluacion'),
            ('seg','Seguimiento'),
            ('ase','Consultoria'),
            ('result','Resultados con reto Zapopan'),], 'Tipo', required=True),
        'check_consultor': fields.boolean('Reunion consultoria contabilizada'),
        'file_name': fields.char('Nombre Archivo', readonly=True),
        'file': fields.binary('Archivo', help='Archivo a actualizar', readonly=True),
        'last_log_eval': fields.related('project_id', 'last_log_eval', type='selection', selection=[
            (10,'A'),(9,'B'),
            (8,'C'),(7,'D'),], string='Compromiso proyecto', store=True),
        'progress_eval': fields.related('project_id', 'progress_eval', type='float', digits_compute=dp.get_precision('Account'), string='Avance', store=True),
        'date_week': fields.char('Semana')
    }
    
crm_meeting_report()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
