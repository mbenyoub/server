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
# Sector
# ---------------------------------------------------------

class project_sector(osv.osv):
    _description="Sector"
    _name = 'project.sector'
    _columns = {
        'name' : fields.char('Nombre del Sector', size=64, required=True),
        'code' : fields.char('Codigo del Sector', size = 3, help='El codigo solo puede tener 3 caracteres', required=True),
    }
    _order = 'name'

project_sector()

# ---------------------------------------------------------
# Project
# ---------------------------------------------------------

class project(osv.Model):
    """Inherited project.project"""

    _inherit = "project.project"
    
    def create_meeting_evaluation(self, cr, uid, ids, context=None):
        """
            Crea una nueva reunion de evaluacion
        """
        project = self.browse(cr, uid, ids[0], context=context)
        # Crea la nueva reunion
        res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid, 'base_calendar', 'action_crm_meeting', context)
        context = {
            'default_partner_id': project.partner_id and project.partner_id.id or False,
            'default_user_id': project.user_id and project.user_id.id or False,
            'default_name': 'Evaluacion de proyecto ' + project.name,
            'default_project_id': project.id,
            'default_type': 'eval'
        }
        meeting_id = self.pool.get('crm.meeting').create(cr, uid, {
                                            'name': 'Evaluacion de proyecto ' + project.name,
                                            'project_id': project.id,
                                            'user_id': project.user_id.id,
                                            'partner_id': project.partner_id.id,
                                            'type': 'eval',
                                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                            'date_deadline': time.strftime('%Y-%m-%d %H:%M:%S'),
                                            'create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                            'duration': 1.0}, context=context)
        
        #print "************* meeting_id ***************** ", meeting_id
        
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'base_calendar', 'view_crm_meeting_form')
        res_id = res and res[1] or False
        
        #~ Redirecciona al formulario de solicitud
        return {
            'name': "Reunion",
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'crm.meeting', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'context': context,
            'res_id' : meeting_id, # id of the object to which to redirected
        }
    
    def set_progress(self, cr, uid, ids, context=None):
        """
            Cambia el proyecto a la etapa de seguimiento
        """
        # Recorre las ventas recibidas en el parametro
        for project in self.browse(cr, uid, ids, context=context):
            # Valida que no falte ninguna evaluacion
            evaluation_ids = self.pool.get('project.evaluation.project').search(cr, uid, [('project_id', '=', project.id),('eval','=',False)], context=context)
            if evaluation_ids:
                raise osv.except_osv(_('Warning!'), _('No se puede pasar el proyecto a Seguimiento hasta que se hayan realizado todas sus evaluaciones!'))
                
        self.write(cr, uid, ids, {'state': 'progress'}, context=context)
        return True
    
    def update_eval(self, cr, uid, ids, context=None):
        """
            Agrega a todos los proyectos las evaluaciones
        """
        project_ids = self.search(cr, uid, [('state', '=', 'open')], context=context)
        if project_ids:
            self.set_open(cr, uid, project_ids, context=context)
        return True
    
    def _is_manager_default(self, cr, uid, ids, context=None):
        """
            Indica si el usuario es el administrador del proyecto
        """
        res = False
        if self.pool.get('res.users').has_group(cr, uid, 'project.group_project_manager'):
            res = True
        #print "********** is manager ************* ", res
        return res
    
    def _is_manager_function(self, cr, uid, ids, field_name, arg, context=None):
        """
            Indica si el usuario es el administrador del proyecto
        """
        res = {}
        for this_id in ids:
            res[this_id] = False
            if self.pool.get('res.users').has_group(cr, uid, 'base.group_project_reto_zapopan_eval'):
                res[this_id] = True
        return res
    
    _columns = {
        'company_class': fields.selection([
            ('OPERA','Ya opera'),
            ('IDEA','Es una idea'),], 'Clasificacion'),
        'company_old': fields.char('Antiguedad'),
        'sector_id': fields.many2one('project.sector', 'Sector', ondelete="set null"),
        'question1': fields.text('Pregunta1'),
        'question2': fields.text('Pregunta2'),
        'question3': fields.text('Pregunta3'),
        'question4': fields.text('Pregunta4'),
        'question5': fields.text('Pregunta5'),
        'question6': fields.text('Pregunta6'),
        'question7': fields.text('Pregunta7'),
        'question8': fields.text('Pregunta8'),
        'question9': fields.text('Pregunta9'),
        'question10': fields.text('Pregunta10'),
        'question11': fields.text('Pregunta11'),
        'description': fields.text('Descripcion'),
        'state': fields.selection([
            ('template', 'Plantilla'),
            ('draft','Nuevo'),
            ('open','Evaluacion'),
            ('progress','Seguimiento'),
            ('cancelled', 'Cancelado'),
            ('pending','Pendiente'),
            ('close','Calificado')], 'Estado', required=True),
        'code': fields.char('Codigo', size=10),
        'project_log_meeting_ids': fields.one2many('project.log.meeting', 'project_id', string="Bitacora de Reuniones", ondelete="cascade"),
        'project_log_project_ids': fields.one2many('project.log.project', 'project_id', string="Bitacora", ondelete="cascade"),
        'consultor_id': fields.many2one('res.partner', 'Consultor'),
        'eval_extra1': fields.text('Evaluacion extra1'),
        'eval_extra2': fields.text('Evaluacion extra2'),
        'eval_extra3': fields.text('Evaluacion extra3'),
        'is_manager':fields.function(_is_manager_function, type='boolean', string="Manager"),
    }
    
    _defaults = {
        'is_manager': _is_manager_default,
        'company_class': 'IDEA',
        'privacy_visibility': 'portal',
        'state': 'draft',
        'use_phases': True,
    }

project()

class project_task(osv.Model):
    """Inherited project.task"""

    _inherit = "project.task"
    
    def _get_tag(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la primera etiqueta de la tarea
        """
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = False
            for tag in task.categ_ids:
                res[task.id] = tag.id
                break
        return res
    
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
        'categ_id':fields.function(_get_tag, type='many2one', relation="project.category", string="Etiqueta", store=True),
    }
    
    _defaults = {
        'project_id': _get_project_default,
    }
    