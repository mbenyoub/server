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

from datetime import datetime, date
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Historico sobre consultores
# ---------------------------------------------------------

class project_log_consultor(osv.Model):
    _name = "project.log.consultor"

    def action_cancel(self, cr, uid, ids, context=None):
        """
            Cancela al consultor seleccionado
        """
        project_obj = self.pool.get('project.project')
        project_ids = []
        # Recorre los registros del log
        for log in self.browse(cr, uid, ids, context=context):
            consultor_id = log.project_id.consultor_id.id or False
            # Valida que el consultor a cancelar sobre el proyecto no sea el mismo cancelado
            if consultor_id == log.consultor_id.id:
                project_ids.append(log.project_id.id)
        # Quita al consultor de los proyectos
        if project_ids:
            project_obj.write(cr, uid, project_ids, {'consultor_id': False}, context=context)
        # Pone como cancelados los registros de log
        self.write(cr, uid, ids, {'state':'cancel','user_id': uid}, context=context)
        return True
        
    _columns = {
        'meetings': fields.integer('Reuniones'),
        'phase_id' : fields.many2one('project.phase', 'Fase'),
        'consultor_id': fields.many2one('res.partner', 'Consultor', required=True),
        'user_id': fields.many2one('res.users', 'Aplicado por'),
        'date' : fields.date(string='Fecha'),
        'date_done' : fields.date(string='Fecha Evaluacion'),
        'time' : fields.float(string='Horas Invertidas'),
        'project_id': fields.many2one('project.project', string="Proyecto", required=True),
        #'result': fields.float('Calificacion',digits=(3,1)),
        'state': fields.selection([('draft','Pendiente'),('done','Realizada'),
            ('cancel','Cancelada')], string="Estado"),
        'result': fields.selection([(1,'5'),(2,'2'),
            (3,'3'),(4,'4'),(5,'5')], string="Rating"),
        'note': fields.text('Notas'),
    }
    
    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
        'meetings': 0,
        'time': 0.0
    }

project_log_consultor()

# ---------------------------------------------------------
# Historico sobre calificacion avance tarea y proyecto
# ---------------------------------------------------------

class project_log_evaluation_task(osv.Model):
    _name = "project.log.evaluation.task"

    _order = "id desc"

    _columns = {
        'date' : fields.date(string='Fecha'),
        'phase_id' : fields.many2one('project.phase', 'Fase'),
        'user_id': fields.many2one('res.users', 'Evaluador', required=True),
        'project_id': fields.many2one('project.project', string="Proyecto"),
        'task_id': fields.many2one('project.task', string="Tarea", required=True),
        'meeting_id': fields.many2one('crm.meeting', string="Reunion"),
        'result' : fields.float(string='Porcentaje Avance', digits=(3,1), required=True),
        'note': fields.text('Comentarios')
    }
    
    _defaults = {
        'date': fields.date.context_today,
        'result': 0
    }

project_log_evaluation_task()

class project_log_evaluation_project(osv.Model):
    _name = "project.log.evaluation.project"

    _order = "id desc"

    _columns = {
        'date' : fields.date(string='Fecha'),
        'phase_id' : fields.many2one('project.phase', 'Fase'),
        'user_id': fields.many2one('res.users', 'Evaluador', required=True),
        'project_id': fields.many2one('project.project', string="Proyecto", required=True),
        'meeting_id': fields.many2one('crm.meeting', string="Reunion"),
        'result': fields.selection([(10,'A'),(9,'B'),
            (8,'C'),(7,'D')], string="Compromiso", required=True),
    }
    
    _defaults = {
        'date': fields.date.context_today,
        'result': 10
    }

project_log_evaluation_project()


class project_log_project(osv.Model):
    _inherit = "project.log.project"

    _columns = {
        'meeting_id' : fields.many2one('crm.meeting', string='Reunion', help="Reunion a la que hace referencia la actividad"),
    }

project_log_project()


# ---------------------------------------------------------
# Adjuntos cargados sobre la fase
# ---------------------------------------------------------

class project_phase_file_task(osv.Model):
    """ Entregables - Adjunto """
    _name = "project.phase.file.task"

    _columns = {
        'file_name': fields.char('Nombre Archivo'),
        'phase_id' : fields.many2one('project.phase', 'Fase', readonly=True),
        'task_id' : fields.many2one('project.task', 'Entregable', readonly=True),
        'date' : fields.date(string='Fecha', readonly=True),
        'file' : fields.binary('Archivo', help='Archivo a actualizar', readonly=True),
    }
    
    _defaults = {
        'date': fields.date.context_today,
        'file_name': 'entregable_fase.pdf'
    }

project_phase_file_task()

class project_phase_file_meeting(osv.Model):
    """ Minuta reunion - Adjunto """
    _name = "project.phase.file.meeting"

    _columns = {
        'file_name': fields.char('Nombre Archivo'),
        'phase_id' : fields.many2one('project.phase', 'Fase', readonly=True),
        'meeting_id' : fields.many2one('crm.meeting', 'Reunion', readonly=True),
        'date' : fields.date(string='Fecha', readonly=True),
        'file' : fields.binary('Archivo', help='Archivo a actualizar', readonly=True),
        'type': fields.related('meeting_id', 'type', type="selection", selection=[
            ('eval','Evaluacion'),
            ('seg','Seguimiento'),
            ('ase','Consultoria'),
            ('result','Resultados Reto Zapopan')], store=True, string="Tipo", readonly=True),
    }
    
    _defaults = {
        'date': fields.date.context_today,
        'file_name': 'minuta_reunion.pdf'
    }

project_phase_file_meeting()
