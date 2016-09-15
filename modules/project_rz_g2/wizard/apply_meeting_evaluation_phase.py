# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Salda?a (riss_600@hotmail.com)
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

from openerp.osv import osv, fields
from tools.translate import _

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

class meeting_evaluation_wizard(osv.osv_memory):
    _name = 'meeting.evaluation.wizard'
    
    def action_meeting_apply(self, cr, uid, ids, context=None):
        """
            Actualiza la calificacion sobre el proyecto y el porcentaje sobre entregables
        """
        if context is None:
            context = {}
        eval_project_obj = self.pool.get('project.log.evaluation.project')
        eval_task_obj = self.pool.get('project.log.evaluation.task')
        meeting_obj = self.pool.get('crm.meeting')
        
        # Obtiene la fecha actual
        date = time.strftime('%Y-%m-%d')
        
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Crea el log para el proyecto
            vals = {
                'date': date,
                'phase_id': data.phase_id.id or False,
                'user_id': uid,
                'project_id': data.project_id.id or False,
                'meeting_id': data.meeting_id.id or False,
                'result': data.result
            }
            eval_project_id = eval_project_obj.create(cr, uid, vals, context=context)
            
            # Recorre las evaluaciones sobre entregables
            for line in data.line_ids:
                # Valida que el resultado no revase el 100 porciento
                if line.result > 100:
                    raise osv.except_osv(_('Error!'),_("El porcentaje de avance de las tareas no puede ser superior al 100 porciento!"))
                
                # Crea el log para los entregables con el porcentaje de avance
                vals = {
                    'date': date,
                    'phase_id': data.phase_id.id or False,
                    'user_id': uid,
                    'project_id': data.project_id.id or False,
                    'task_id': line.task_id.id or False,
                    'meeting_id': data.meeting_id.id or False,
                    'result': line.result,
                    'note': line.note
                }
                eval_task_id = eval_task_obj.create(cr, uid, vals, context=context)
            
            # Valida el tipo de accion que se debe ejecutar sobre la reunion
            action_type = context.get('type', 'done')
            if action_type == 'reschedule':
                # Pone la reunion como reagendada
                res = meeting_obj.meeting_reschedule(cr, uid, [data.meeting_id.id or False], context=context)
            elif action_type == 'cancel':
                # Pone la reunion como cancelada
                res = meeting_obj.meeting_cancel(cr, uid, [data.meeting_id.id or False], context=context)
            elif action_type == 'absence':
                # Pone la reunion como inasistencia
                res = meeting_obj.meeting_absence(cr, uid, [data.meeting_id.id or False], context=context)
            else:
                # Pone la reunion como realizada
                res = meeting_obj.meeting_done(cr, uid, [data.meeting_id.id or False], context=context)
        return res
    
    def onchange_phase_id(self, cr, uid, ids, phase_id, context=None):
        """
            Retorna la lista de entregables
        """
        if context is None:
            context={}
        res = []
        # Obtiene las evaluaciones de la categoria
        if phase_id:
            phase = self.pool.get('project.phase').browse(cr, uid, phase_id, context=context)
            # Obtiene la informacion de las fases
            for task in phase.task_ids:
                # Valida que la fase no este concluida
                if task.state in ['done','cancelled']:
                    continue
                
                # Crea el diccionario con los datos de la fase
                vals = {
                    'task_id': task.id or False,
                }
                res.append(vals)
            
        return {'value':{'line_ids': res}}
    
    _columns = {
        'project_id': fields.many2one('project.project', 'Proyecto', required=True, readonly=True),
        'phase_id': fields.many2one('project.phase', 'Fase', required=True, readonly=True),
        'meeting_id': fields.many2one('crm.meeting', 'Reunion', readonly=True),
        'result': fields.selection([(10,'A'),(9,'B'),
            (8,'C')], string="Compromiso", required=True),
        'line_ids': fields.one2many('meeting.evaluation.line.wizard', 'wizard_id', 'Entregables'),
    }
    
meeting_evaluation_wizard()

class meeting_evaluation_line_wizard(osv.osv_memory):
    _name = 'meeting.evaluation.line.wizard'
    
    _columns = {
        'wizard_id': fields.many2one('meeting.evaluation.wizard', 'Wizard', readonly=True),
        'task_id': fields.many2one('project.task', 'Entregable', required=True, ondelete="cascade"),
        'note': fields.text('Notas'),
        'result': fields.float('Porcentaje', digits=(3,1)),
    }
    
    defaults = {
        'result': 0.0
    }
    
meeting_evaluation_line_wizard()
