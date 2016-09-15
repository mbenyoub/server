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
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Project
# ---------------------------------------------------------

class project(osv.Model):
    """Inherited crossovered.budget"""

    _inherit = "project.project"
    
    def set_done(self, cr, uid, ids, context=None):
        """
            Valida que para pasar a calificado no haya fases abiertas
        """
        phase_obj = self.pool.get('project.phase')
        # Valida que no haya fases por terminar
        phase_ids = phase_obj.search(cr, uid, [('project_id', 'in', ids),('state','=','open')], context=context)
        if phase_ids:
            raise osv.except_osv(_('Warning!'), _('No se puede calificar el proyecto porque tiene fases en proceso'))
        
        # Continua con el flujo original
        return super(project, self).set_done(cr, uid, ids, context=context)
    
    def set_open(self, cr, uid, ids, context=None):
        """
            Genera las evaluaciones del proyecto y cambia su estado a open
        """
        category_obj = self.pool.get('project.evaluation.category')
        template_obj = self.pool.get('project.evaluation.template')
        evaluation_obj = self.pool.get('project.evaluation.evaluation')
        result_obj = self.pool.get('project.evaluation.project')

        # Recorre los proyectos
        for project in self.browse(cr, uid, ids, context=context):
            vals = {'state': 'open'}
            evaluation_ids = []
            # Valida que el proyecto no tenga evaluaciones ya agregadas para el partner
            if not project.evaluation_partner_ids:
                #print "********* partner evaluation ************* "
                res_evaluation_partner_ids = []
                # Busca si hay cuestionarios para agregar al proyecto
                category_ids = category_obj.search(cr, uid, [('type', '=', 'partner')], context=context)
                if category_ids:
                    # Genera los cuestionarios y las evaluaciones
                    template_ids = template_obj.search(cr, uid, [('category_id', 'in', category_ids)])
                    # Obtiene la plantilla de los cuestionarios y genera las preguntas
                    for template in template_obj.browse(cr, uid, template_ids, context=context):
                        eval_id = evaluation_obj.create(cr, uid, {'name': template.name, 'category_id': template.category_id.id, 'partner_id': project.partner_id.id, 'project_id': project.id}, context=context)
                        evaluation_ids.append((4, eval_id))
                    # Agrega el valor del resultado por categoria
                    for category_id in category_ids:
                        eval_id = result_obj.create(cr, uid, {'category_id': category_id, 'project_id': project.id}, context=context)
                        res_evaluation_partner_ids.append((4, eval_id))
                    vals['evaluation_partner_ids'] = res_evaluation_partner_ids
                    #print "***************** evaluation partners ******* ", res_evaluation_partner_ids
            #print "***************** if evaluation project ****** ", project.evaluation_project_ids
            # Valida que el proyecto no tenga evaluaciones ya agregadas para el proyecto
            if not project.evaluation_project_ids:
                #print "********* project evaluation ************* "
                res_evaluation_project_ids = []
                # Busca si hay cuestionarios para agregar al proyecto
                category_ids = category_obj.search(cr, uid, [('type', '=', 'project')], context=context)
                if category_ids:
                    # Genera los cuestionarios y las evaluaciones
                    template_ids = template_obj.search(cr, uid, [('category_id', 'in', category_ids)])
                    # Obtiene la plantilla de los cuestionarios y genera las preguntas
                    for template in template_obj.browse(cr, uid, template_ids, context=context):
                        eval_id = evaluation_obj.create(cr, uid, {'name': template.name, 'category_id': template.category_id.id, 'partner_id': project.partner_id.id, 'project_id': project.id}, context=context)
                        evaluation_ids.append((4, eval_id))
                    # Agrega el valor del resultado por categoria
                    for category_id in category_ids:
                        eval_id = result_obj.create(cr, uid, {'category_id': category_id, 'project_id': project.id}, context=context)
                        res_evaluation_project_ids.append((4, eval_id))
                    vals['evaluation_project_ids'] = res_evaluation_project_ids
                    #print "*********** evaluation project *********** ", res_evaluation_project_ids
            if evaluation_ids:
                vals['evaluation_ids'] = evaluation_ids
            #print "******************* vals ****************** ", vals
            # Actualiza el registro
            self.write(cr, uid, [project.id], vals, context=context)
        return True
    
    def _have_meeting_evaluation(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si hay reuniones de evaluacion para el proyecto
        """
        res = {}
        meeting_obj = self.pool.get('crm.meeting')
        # Recorre las ventas recibidas en el parametro
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = 'False'
            # Valida si hay una relacion con una oportunidad
            meeting_ids = meeting_obj.search(cr, uid, [('project_id', '=', project.id),('type','=','eval')], context=context)
            if meeting_ids:
                res[project.id] = 'True'
        return res
    
    def _pending_evaluation(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si hay evaluaciones pendientes
        """
        res = {}
        result_obj = self.pool.get('project.evaluation.project')
        # Recorre las ventas recibidas en el parametro
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = 'False'
            # Valida si hay una relacion con una oportunidad
            result_ids = result_obj.search(cr, uid, [('project_id', '=', project.id),('eval','=',False)], context=context)
            if result_ids:
                res[project.id] = 'True'
        return res
    
    def _get_result(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el resultado de la evaluacion del proyecto
        """
        res = {}
        # Recorre los registros
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = {}
            val_partner = 0.0
            val_project = 0.0
            #print "*********** partner *********** ", project.evaluation_partner_ids
            #print "*********** project *********** ", project.evaluation_project_ids
            # Obtiene el total por emprendedor
            for eval_partner in project.evaluation_partner_ids:
                val_partner += ((eval_partner.porcentage/100.0)*eval_partner.result)
            # Obtiene el total por proyecto
            for eval_project in project.evaluation_project_ids:
                val_project += ((eval_project.porcentage/100.0)*eval_project.result)
            
            #print "********* val_partner ************ ", val_partner
            #print "********* val_project ************ ", val_project
            res[project.id] = {
                'res_partner_result': val_partner,
                'res_partner_performance': val_partner*100.0,
                'res_project_result': val_project,
                'res_project_performance': val_project*100.0,
                'res_result': (val_partner+val_project)/2,
                'res_performance': ((val_partner+val_project)*100.0)/2,
            }
        return res
    
    _columns = {
        'evaluation_project_ids': fields.one2many('project.evaluation.project', 'project_id', string="Evaluaciones proyecto", domain=[('type','=','project')], ondelete="cascade"),
        'evaluation_partner_ids': fields.one2many('project.evaluation.project', 'project_id', string="Evaluaciones partner", domain=[('type','=','partner')], ondelete="cascade"),
        'have_meeting_evaluation': fields.function(_have_meeting_evaluation, method=True, string='Tiene Reunion evaluacion', readonly=True, type='char'),
        'pending_evaluation': fields.function(_pending_evaluation, method=True, string='Tiene evaluaciones pendientes', readonly=True, type='char'),
        'evaluation_ids': fields.one2many('project.evaluation.evaluation', 'project_id', string='Evaluaciones', ondelete="cascade"),
        'res_partner_result': fields.function(_get_result, method=True, string='Evaluacion Emprendedor', readonly=True, type='float', multi="res_eval"),
        'res_partner_performance': fields.function(_get_result, method=True, string='Evaluacion Emprendedor', readonly=True, type='float', multi="res_eval"),
        'res_project_result': fields.function(_get_result, method=True, string='Evaluacion Proyecto', readonly=True, type='float', multi="res_eval"),
        'res_project_performance': fields.function(_get_result, method=True, string='Evaluacion proyecto', readonly=True, type='float', multi="res_eval"),
        'res_result': fields.function(_get_result, method=True, string='Resultado Total', readonly=True, type='float', multi="res_eval"),
        'res_performance': fields.function(_get_result, method=True, string='Resultado Total', readonly=True, type='float', multi="res_eval"),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True)
    }

    _defaults = {
        'state': 'draft',
        'have_meeting_evaluation': 'False',
        'pending_evaluation': 'True',
    }

project()
