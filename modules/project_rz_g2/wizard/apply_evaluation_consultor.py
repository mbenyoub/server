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

class consultor_evaluation_wizard(osv.osv_memory):
    _name = 'consultor.evaluation.wizard'
    
    def action_evaluation_apply(self, cr, uid, ids, context=None):
        """
            Actualiza la calificacion sobre el proyecto para cada consultor asignado
        """
        log_obj = self.pool.get('project.log.consultor')
        meeting_obj = self.pool.get('crm.meeting')
        # Obtiene la fecha actual
        date = time.strftime('%Y-%m-%d')
        # objeto wizard
        data = self.browse(cr, uid, ids[0], context=context)
        
        # Valida que no haya reuniones de consultoria pendientes
        meeting_ids = meeting_obj.search(cr, uid, [('project_id','=',data.project_id.id or False),('type','=','ase'),('check_consultor','=',False),('state_meeting','in',['draft'])], context=context)
        if meeting_ids:
            raise osv.except_osv(_('Error!'),_("No se puede aplicar la evaluacion porque hay reuniones de consultoria pendientes de confirmar!"))
        # Valida que haya consultores para confirmar
        if not data.line_ids:
            raise osv.except_osv(_('Error!'),_("No hay consultores pendientes para evaluar!"))
        
        # Recorre los registros de las lineas de consultoria 
        for line in data.line_ids:
            # Valida que haya un registro de bitacora de consultor relacionado
            if not line.log_id:
                continue
            # Actualiza el log para el consultor
            vals = {
                'date_done': date,
                'phase_id': data.phase_id.id or False,
                'user_id': uid,
                'meetings': line.meetings,
                'time': line.time,
                'state': 'done',
                'result': line.result
            }
            log_obj.write(cr, uid, [line.log_id.id], vals, context=context)
        
        # Pone las reuniones de asesoria como aplicadas
        meeting_ids = meeting_obj.search(cr, uid, [('project_id','=',data.project_id.id or False),('type','=','ase'),('check_consultor','=',False),('state_meeting','in',['done'])], context=context)
        meeting_obj.write(cr, uid, meeting_ids, {'check_consultor': True}, context=context)
        return True
    
    def onchange_project_id(self, cr, uid, ids, project_id, type, context=None):
        """
            Agrega al retorno el domain sobre las fases del proyecto y asigna la fase activa
        """
        if context is None:
            context={}
        log_obj = self.pool.get('project.log.consultor')
        phase_obj = self.pool.get('project.phase')
        meeting_obj = self.pool.get('crm.meeting')
        phase_id = False
        line_ids = []
        domain= []
        
        # Si trae el campo de proyecto obtiene la fase
        if project_id:
            domain = [('project_id','=',project_id),('state','=','open'),('validate_time','=',True)]
            # Obtiene la fase activa
            phase_ids = phase_obj.search(cr, uid, [('project_id','=',project_id),('state','=','open'),('validate_time','=',True)])
            if phase_ids:
                phase_id = phase_ids[0]
            
            log_ids = log_obj.search(cr, uid, [('project_id','=',project_id),('state','=','draft')], context=context)
            #print "************ log ids ********* ", log_ids
            
            # Obtiene la informacion de las fases
            for log in log_obj.browse(cr, uid, log_ids, context=context):
                meetings = 0
                time = 0
                # Obtiene el total de horas invertidas por el consultor
                meeting_ids = meeting_obj.search(cr, uid, [('project_id','=',project_id),('partner_id','=',log.consultor_id.id or False),('type','=','ase'),('check_consultor','=',False),('state_meeting','not in',['reschedule','cancel','absence'])], context=context)
                meetings = len(meeting_ids)
                if meetings > 0:
                    # Obtiene el tiempo invertido por el consultor
                    for meeting in meeting_obj.browse(cr, uid, meeting_ids, context=context):
                        # Valida que la reunion no
                        if meeting.state_meeting == 'draft':
                            raise osv.except_osv(_('Error!'),_("El consultor %s tiene una reunion pendiente en la fecha %s!")%(meeting.partner_id.name,meeting.date))
                        time += meeting.duration
                
                # Crea el diccionario con los datos de la fase
                vals = {
                    'consultor_id': log.consultor_id.id or False,
                    'meetings': meetings,
                    'time': time,
                    'log_id': log.id
                }
                line_ids.append(vals)
        
        return {'value':{'phase_id': phase_id, 'line_ids': line_ids}, 'domain': {'phase_id': domain}}
    
    def _get_project_default(self, cr, uid, ids, context=None):
        """
            Obtiene el proyecto por default si es un emprendedor
        """
        res = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.partner_id.type_contact == 'emp':
            project_ids = self.pool.get('project.project').search(cr, uid, [('partner_id','=',user.partner_id.id)], context=context)
            if project_ids:
                res = project_ids[0]
        return res
    
    _columns = {
        'project_id': fields.many2one('project.project', 'Proyecto', required=True),
        'phase_id': fields.many2one('project.phase', 'Fase', required=True),
        'line_ids': fields.one2many('consultor.evaluation.line.wizard', 'wizard_id', 'Entregables'),
    }
    
    _defaults = {
        'project_id': _get_project_default
    }
    
consultor_evaluation_wizard()

class consultor_evaluation_line_wizard(osv.osv_memory):
    _name = 'consultor.evaluation.line.wizard'
    
    _columns = {
        'wizard_id': fields.many2one('consultor.evaluation.wizard', 'Wizard', readonly=True),
        'meetings': fields.integer('Total Reuniones', readonly=True),
        'consultor_id': fields.many2one('res.partner', 'Consultor', required=True, readonly=True),
        'log_id': fields.many2one('project.log.consultor', 'Registro Evaluado', required=True, readonly=True),
        'date_done' : fields.date(string='Fecha', readonly=True),
        'time' : fields.float(string='Horas Invertidas', readonly=True),
        #'result': fields.float('Calificacion',digits=(2,1)),
        'result': fields.selection([(1,'1'),(2,'2'),
            (3,'3'),(4,'4'),(5,'5')], string="Rating", required=True),
        'note': fields.text('Notas'),
    }
    
    _defaults = {
        'date_done': fields.date.context_today,
        'meetings': 0,
        'time': 0.0
    }
    
consultor_evaluation_line_wizard()
