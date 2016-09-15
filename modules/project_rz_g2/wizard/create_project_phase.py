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
from openerp import netsvc

class create_project_phase_wizard(osv.osv_memory):
    _name = 'create.project.phase.wizard'
    
    def _get_next_date(self, cr, uid, date, days, context=None):
        """
            Obtiene la fecha siguiente incrementando la cantidad de dias
        """
        if days:
            date_next = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            date_next = date_next + timedelta(days=days)
            return date_next.strftime('%Y-%m-%d %H:%M:%S')
        return date
    
    def action_create_project_phase(self, cr, uid, ids, context=None):
        """
            Crea las fases para el proyecto en seguimiento
        """
        project_obj = self.pool.get('project.project')
        phase_obj = self.pool.get('project.phase')
        task_obj = self.pool.get('project.task')
        wf_service = netsvc.LocalService('workflow')
        
        # Obtiene la fecha actual
        cur_date = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Inicializa valores de fechas
            date_ini = cur_date
            date_end = cur_date
            type_id = 1
            
            # Obtiene la primera Fase por tarea
            if data.project_id.type_ids:
                for tp in data.project_id.type_ids:
                    if tp.state == 'draft':
                        type_id = tp.id or False
            
            # Recorre las fases para insertar sobre el proyecto
            for line in data.line_ids:
                # Valida que la fase se encuentre activa
                if line.phase_id.active == False:
                    continue
                
                # Obtiene la fecha siguiente de la fase
                date_end = self._get_next_date(cr, uid, date_ini, line.days, context)
                
                # Crea el nuevo registro de fase del proyecto
                vals = {
                    'name': line.phase_id.name,
                    'code': line.phase_id.code,
                    'project_id': data.project_id.id or False,
                    'date_start': date_ini,
                    'date_end': date_end,
                    'description': line.phase_id.description,
                    'meeting_time': line.meeting_time,
                    'sequence': line.phase_id.sequence,
                    'validate_time': line.phase_id.validate_time
                }
                phase_id = phase_obj.create(cr, uid, vals, context=context)
                
                # Valida que haya entregables para agregar a la fase
                if not line.phase_id.task_ids:
                    continue
                
                # Recorre los entregables a crear por la fase
                for task in line.phase_id.task_ids:
                    # Obtiene la fecha de fin de la tarea
                    date_end_task = self._get_next_date(cr, uid, date_ini, task.days, context)
                    
                    # Crea el nuevo registro de entregable del proyecto
                    vals = {
                        'name': task.name,
                        'project_id': data.project_id.id or False,
                        'phase_id': phase_id,
                        'date_deadline': date_end,
                        'user_id': data.project_id.user_id.id or False,
                        'planned_hours': task.time,
                        'date_start': date_ini,
                        'date_end': date_end_task,
                        'description': task.description,
                        'sequence': task.sequence,
                        'priority': task.priority,
                        'stage_id': type_id
                    }
                    task_obj.create(cr, uid, vals, context=context)
                    
                # Actualiza la fecha de inicio
                date_ini = self._get_next_date(cr, uid, date_end, 0.1, context)
            
            # Obtiene las fases que van sobre el flujo completo del proyecto
            for phase in data.template_id.phase_ids:
                # Valida que la fase se encuentre activa
                if phase.active == False:
                    continue
                # Valida que la fase no aplique sobre un tiempo especifico del proyecto
                if phase.validate_time == True:
                    continue
                
                # Crea el nuevo registro de fase del proyecto
                vals = {
                    'name': phase.name,
                    'code': phase.code,
                    'project_id': data.project_id.id or False,
                    'date_start': cur_date,
                    'date_end': date_end,
                    'description': phase.description,
                    'meeting_time': 0.0,
                    'sequence': phase.sequence,
                    'state': 'open',
                    'validate_time': phase.validate_time
                }
                phase_id = phase_obj.create(cr, uid, vals, context=context)
                
                # Pasa la fase a estado abierto
                wf_service.trg_validate(uid, 'project.phase', phase_id, 'set_open', cr)
                
                # Valida que haya entregables para agregar a la fase
                if not phase.task_ids:
                    continue
                
                # Recorre los entregables a crear por la fase
                for task in phase.task_ids:
                    # Obtiene la fecha de fin de la tarea
                    date_end_task = self._get_next_date(cr, uid, cur_date, task.days, context)
                    
                    # Crea el nuevo registro de entregable del proyecto
                    vals = {
                        'name': task.name,
                        'project_id': data.project_id.id or False,
                        'phase_id': phase_id,
                        'date_deadline': date_end,
                        'user_id': data.project_id.user_id.id or False,
                        'planned_hours': task.time,
                        'date_start': cur_date,
                        'date_end': date_end_task,
                        'description': task.description,
                        'sequence': task.sequence,
                        'priority': task.priority,
                        'stage_id': type_id
                    }
                    task_obj.create(cr, uid, vals, context=context)
            
            # Actualiza el estado del proyecto
            project_obj.write(cr, uid, [data.project_id.id], {'state': 'progress', 'apply_progress': True}, context=context)
        return True
    
    def onchange_template_id(self, cr, uid, ids, template_id, context=None):
        """
            Retorna las fases de la plantilla
        """
        if context is None:
            context={}
        res = []
        # Obtiene las evaluaciones de la categoria
        if template_id:
            template = self.pool.get('project.template.project').browse(cr, uid, template_id, context=context)
            # Obtiene la informacion de las fases
            for phase in template.phase_ids:
                # Valida que la fase se encuentre activa
                if phase.active == False:
                    continue
                # Valida que la fase requiera que se le especifique un tiempo o va sobre el tiempo que dura el periodo
                if phase.validate_time == False:
                    continue
                
                # Crea el diccionario con los datos de la fase
                vals = {
                    'phase_id': phase.id or False,
                    'days': 0,
                    'meeting_time': phase.meeting_time
                }
                res.append(vals)
            
        return {'value':{'line_ids': res}}
    
    _columns = {
        'project_id': fields.many2one('project.project', 'Proyecto', required=True, readonly=True),
        'template_id': fields.many2one('project.template.project', 'Plantilla proyecto', readonly=True),
        'line_ids': fields.one2many('create.project.phase.line.wizard', 'wizard_id', 'Fases'),
    }
    
create_project_phase_wizard()

class create_project_phase_line_wizard(osv.osv_memory):
    _name = 'create.project.phase.line.wizard'
    
    _columns = {
        'wizard_id': fields.many2one('create.project.phase.wizard', 'Wizard', readonly=True),
        'phase_id': fields.many2one('project.template.phase', 'Fase', required=True, ondelete="cascade"),
        'days': fields.integer('Dias planeados', required=True),
        'meeting_time': fields.float('Horas de consultoria', help="Horas sugeridas para consultoria"),
    }
    
create_project_phase_line_wizard()
