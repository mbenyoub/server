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

from lxml import etree

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Template Project
# ---------------------------------------------------------

class project_tempate_project(osv.Model):

    _name = "project.template.project"
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'company_class': fields.selection([
            ('IDEA','Idea'),
            ('DESA','En desarrollo'),
            ('EXPAN','En expansion')], 'Tipo de Proyecto', required=True),
        'date': fields.date('Fecha creacion'),
        'description': fields.text('Descripcion'),
        'active': fields.boolean('Activo', help='Esta opcion indica si el registro se encuentra en uso'),
        'phase_ids': fields.one2many('project.template.phase', 'project_id', string="Fases"),
    }
    
    _order = "id desc"
    
    _defaults = {
        'date': fields.date.context_today,
        'company_class': 'IDEA',
        'active': True
    }

project_tempate_project()

class project_tempate_phase(osv.Model):

    _name = "project.template.phase"
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'code': fields.char('Codigo', size=32, required=True),
        'sequence': fields.integer('orden'),
        'description': fields.text('Descripcion'),
        'active': fields.boolean('Activo', help='Esta opcion indica si el registro se encuentra en uso'),
        'project_id': fields.many2one('project.template.project', 'Proyecto'),
        'task_ids': fields.one2many('project.template.task', 'phase_id', string="Fases"),
        'meeting_time': fields.float('Horas de consultoria', help="Horas sugeridas para consultoria"),
        'company_class': fields.related('project_id', 'company_class', type="selection", selection=[
            ('IDEA','Idea'),
            ('DESA','En desarrollo'),
            ('EXPAN','En expansion')], store=False, string="Tipo Proyecto"),
        'validate_time': fields.boolean('Validar Fechas')
    }
    
    _order = "project_id, sequence"
    
    _defaults = {
        'active': True,
        'meeting_time': 4,
        'sequence': 0,
        'validate_time': True
    }

project_tempate_phase()

class project_tempate_task(osv.Model):

    _name = "project.template.task"
    
    def update_task(self, cr, uid, ids, context=None):
        """
            Actualiza los entregables
        """
        temp_task_obj = self.pool.get('project.template.task')
        task_obj = self.pool.get('project.task')
        
        temp_ids = temp_task_obj.search(cr, uid, [], context=context)
        if temp_ids:
            for temp in temp_task_obj.browse(cr, uid, temp_ids, context=context):
                var = {
                    'name': temp.name,
                    'description': temp.description
                }
                task_ids = task_obj.search(cr, uid, [('project_id.company_class','=',temp.phase_id.project_id.company_class),('phase_id.code','=',temp.phase_id.code),('sequence','=',temp.sequence)], context=context)
                if task_ids:
                    task_obj.write(cr, uid, task_ids, var, context=context)
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'sequence': fields.integer('orden'),
        'description': fields.text('Descripcion'),
        'phase_id': fields.many2one('project.template.phase', 'Fase Proyecto'),
        'time': fields.float('Horas planificadas', help="Horas sugeridas para consultoria"),
        'days': fields.integer('Dias planificacion'),
        'priority': fields.selection([('4','Muy Baja'), ('3','Baja'), ('2','Medio'), ('1','Importante'), ('0','Muy importante')], 'Prioridad', select=True),
        'company_class': fields.related('phase_id', 'company_class', type="selection", selection=[
            ('IDEA','Idea'),
            ('DESA','En desarrollo'),
            ('EXPAN','En expansion')], store=False, string="Tipo Proyecto"),
        'project_id': fields.related('phase_id', 'project_id', type="many2one", relation='project.template.project', store=True, string="Proyecto"),
    }
    
    _order = "sequence"
    
    _defaults = {
        'time': 4,
        'days': 5,
        'sequence': 0,
        'priority': '2'
    }

project_tempate_task()
