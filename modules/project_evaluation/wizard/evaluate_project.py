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

class project_create_attendee_wizard(osv.osv_memory):
    _name = 'project.evaluation.evaluate.project'
    
    def action_evaluate_project(self, cr, uid, ids, context=None):
        """
            Actualiza la evaluacion
        """
        eval_obj = self.pool.get('project.evaluation.evaluation')
        result_obj = self.pool.get('project.evaluation.project')
        
        # Wizard de evaluacion
        evaluate = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si la categoria lleva evaluacion
        if evaluate.eval_category:
            # Busca preguntas sin calificar
            eval_ids = eval_obj.search(cr, uid, [('project_id','=', evaluate.project_id.id),('category_id','=', evaluate.category_id.id),('value','=',None)], context=context)
            if eval_ids:
                raise osv.except_osv(_('Warning!'), _('No se puede guardar porque hay preguntas sin calificar'))
        else:
            # Valida que todas las preguntas tengan algo escrito
            eval_ids = eval_obj.search(cr, uid, [('project_id','=', evaluate.project_id.id),('category_id','=', evaluate.category_id.id),('notes','=',None)], context=context)
            if eval_ids:
                return {
                    'name': 'Calificar Evaluacion',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'project.evaluation.evaluate.project',
                    'target' : 'new',
                    'context': {'default_project_id': evaluate.project_id.id},
                    'type': 'ir.actions.act_window',
                }
        result_ids = result_obj.search(cr, uid, [('project_id','=', evaluate.project_id.id),('category_id','=', evaluate.category_id.id),('eval','=',False)], context=context)
        if result_ids:
            result_obj.write(cr, uid, result_ids, {'eval': True}, context=context)
        
        # Valida que haya categorias para continuar
        result_ids = result_obj.search(cr, uid, [('project_id','=', evaluate.project_id.id),('eval','=',False)], context=context)
        # Si no encuentra mas evaluaciones regresa al proyecto
        if not result_ids:
            mod_obj = self.pool.get('ir.model.data')
            res = mod_obj.get_object_reference(cr, uid, 'project', 'edit_project')
            res_id = res and res[1] or False
            #~ Redirecciona al formulario de solicitud
            return {
                'name':_("Proyectos"),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [res_id],
                'res_model': 'project.project', # object name
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id' : evaluate.project_id.id, # id of the object to which to redirected
            }
        # Va a la parte de calificar evaluacion
        return {
            'name': 'Calificar Evaluacion',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.evaluation.evaluate.project',
            'target' : 'new',
            'context': {'default_project_id': evaluate.project_id.id},
            'type': 'ir.actions.act_window',
        }
    
    def _get_category_evaluation(self, cr, uid, context=None):
        """
            Obtiene la categoria siguiente para mostrar en el wizard
        """
        if context is None:
            context = {}
        res = False
        #print "********* context category ********* ", context
        active_id = context.get('default_project_id', False)
        #print "********* active_id ********* ", active_id
        result_obj = self.pool.get('project.evaluation.project')
        # Valida si hay una relacion con una oportunidad
        result_ids = result_obj.search(cr, uid, [('project_id','=', active_id),('eval','=',False)], context=context)
        #print "*********** result_ids ************* ", result_ids
        if not result_ids:
            raise osv.except_osv(_('Warning!'), _('No hay evaluaciones por calificar para el proyecto'))
        res = result_obj.browse(cr, uid, result_ids[0], context=context).category_id.id
        #print "*********** result ********** ", res
        return res
    
    def _get_category_evaluation(self, cr, uid, context=None):
        """
            Obtiene la categoria siguiente para mostrar en el wizard
        """
        if context is None:
            context = {}
        res = False
        #print "********* context category ********* ", context
        active_id = context.get('default_project_id', False)
        #print "********* active_id ********* ", active_id
        result_obj = self.pool.get('project.evaluation.project')
        # Valida si hay una relacion con una oportunidad
        result_ids = result_obj.search(cr, uid, [('project_id','=', active_id),('eval','=',False)], context=context)
        #print "*********** result_ids ************* ", result_ids
        if not result_ids:
            raise osv.except_osv(_('Warning!'), _('No hay evaluaciones por calificar para el proyecto'))
        res = result_obj.browse(cr, uid, result_ids[0], context=context).category_id.id
        #print "*********** result ********** ", res
        return res
    
    def onchange_category(self, cr, uid, ids, category_id, context=None):
        """
            Retorna el cuestionario
        """
        if context is None:
            context={}
        
        # Obtiene las evaluaciones de la categoria
        active_id = context.get('default_project_id', False)
        eval_obj = self.pool.get('project.evaluation.evaluation')
        
        # Obtiene el objeto categoria
        category = self.pool.get('project.evaluation.category').browse(cr, uid, category_id, context=context)
        
        # Inicializa variable de retorno
        res = {
            'type': category.type,
            'eval_category': category.eval_category,
            'evaluation_ids': [],
            'question_ids': []
        }
        
        values = eval_obj.search(cr, uid, [('project_id','=',active_id),('category_id','=',category_id)], context=context)
        if category.eval_category == True:
            res['evaluation_ids'] = values
        else:
            res['question_ids'] = values
        
        return {'value':res}
    
    _columns = {
        'project_id': fields.many2one('project.project', 'Proyecto', required=True, readonly=True),
        'category_id': fields.many2one('project.evaluation.category', 'Categoria', store=True, readonly=True),
        'evaluation_ids': fields.many2many('project.evaluation.evaluation', 'wizard_evaluation_rel', 'wizard_id', 'evaluation_id', 'Evaluacion'),
        'question_ids': fields.many2many('project.evaluation.evaluation', 'wizard_evaluation_rel', 'wizard_id', 'evaluation_id', 'Evaluacion'),
        'type': fields.selection(selection=[('project','Proyecto'),('partner','Emprendedor'),], string="Evaluacion", readonly=True),
        'eval_category': fields.boolean('Evaluar Preguntas')
    }
    
    _defaults = {
        'category_id': _get_category_evaluation,
    }
    
