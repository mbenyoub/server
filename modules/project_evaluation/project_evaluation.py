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
# Evaluation
# ---------------------------------------------------------

class project_evaluation_category(osv.Model):
    _name = "project.evaluation.category"
    
    def onchange_eval_category(self, cr, uid, ids, eval_category, context=None):
        """
            Pone el porcentaje de la evaluacion en cero si no se evalua la categoria
        """
        if context is None:
            context={}
        res = {}
        # Obtiene las evaluaciones de la categoria
        if eval_category:
            res = {'porcentage': 0.0}
            
        return {'value': res}
    
    _order = "type desc,sequence"
    
    _columns = {
        'name': fields.char('Nombre', required=True),
        'description': fields.text('Descripcion'),
        'type': fields.selection([
            ('project','Proyecto'),
            ('partner','Emprendedor'),], 'Categoria'),
        'porcentage': fields.float('Porcentaje Evaluacion', required=True),
        'eval_category': fields.boolean('Evaluar Categoria'),
        'sequence': fields.integer('Orden')
    }
    
    _defaults = {
        'type': 'project',
        'eval_category': True
    }

class project_evaluation_template(osv.Model):
    _name = "project.evaluation.template"
    
    _columns = {
        'name': fields.char('Pregunta', required=True),
        'category_id': fields.many2one('project.evaluation.category', 'Categoria', ondelete="cascade", required=True),
        'priority': fields.integer('Secuencia'),
    }
    
    _order = 'category_id,priority'
    
    _defaults = {
        
    }

project_evaluation_template()

class project_evaluation_evaluation(osv.Model):
    _name = "project.evaluation.evaluation"
    
    def _get_value_num(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el valor en numero
        """
        res = {}
        for evaluation in self.browse(cr, uid, ids, context=context):
            res[evaluation.id] = 0.0
            # Agrega el valor que se haya tecleado
            if evaluation.value:
                res[evaluation.id] = float(evaluation.value)
        return res
    
    def _get_date_string(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el valor de la fecha con texto
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            res[log.id] = 'False'
            
            mes_texto = {
                '01': ' de Enero ',
                '02': ' de Febrero ',
                '03': ' de Marzo ',
                '04': ' de Abril ',
                '05': ' de Mayo ',
                '06': ' de Junio ',
                '07': ' de Julio ',
                '08': ' de Agosto ',
                '09': ' de Septiembre ',
                '10': ' de Octubre ',
                '11': ' de Noviembre ',
                '12': ' de Diciembre ',
            }
            
            if log.date:
                (anio, mes, dia) = log.date.split("-")
                res[log.id] = dia + mes_texto[mes] + anio
        return res
    
    def _get_user(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el usuario activo
        """
        res = {}
        for id in ids:
            res[id] = uid
        return res
    
    def _get_date(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa la fecha actual
        """
        res = {}
        for id in ids:
            res[id] = time.strftime('%Y-%m-%d')
        return res
    
    _columns = {
        'name': fields.char('Pregunta', required=True, readonly=True),
        'category_id': fields.many2one('project.evaluation.category', 'Categoria', ondelete="set null", readonly=True),
        'notes': fields.text('Notas'),
        'value': fields.selection([
            ('1.0','A'),
            ('0.8','B'),
            ('0.6','C'),
            ('0.4','D'),], 'Calificacion', help="""A=El concepto esta claro, existe y esta documentado adecuadamente.
B=El concepto esta claro o existe y esta documentado pero tiene areas de oportunidad.
C=El concepto esta claro pero no existe y no esta documentado (En proceso de desarrollarse).
D= El concepto no es claro, o no existe, o no esta documentado."""),
        'partner_id': fields.many2one('res.partner', 'Emprendedor', ondelete="set null", required=True, readonly=True),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete="set null", readonly=True),
        'type': fields.related('category_id', 'type', type="char", relation="project.evaluation.category", store=True, string="Tipo", readonly=True),
        #'user_id': fields.many2one('res.users', 'Evaluador'),
        #'date': fields.date('Fecha', readonly=False),
        'date_string': fields.function(_get_date_string, method=True, store=True, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
        'value_num': fields.function(_get_value_num, method=True, store=True, string='Valor numero', readonly=True, type='float'),
        'user_id': fields.many2one('res.users','Evaluador'),
        'date': fields.function(_get_date, method=True, store=True, string='Fecha', readonly=True, type='date'),
    }
    
    _defaults = {
        #'date' : fields.date.today,
        #'user_id': _get_user,
    }

project_evaluation_evaluation()

class project_evaluation_project(osv.Model):
    _name = "project.evaluation.project"
    
    def _get_result(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el resultado de la evaluacion por la categoria
        """
        res = {}
        # Recorre los registros
        for result in self.browse(cr, uid, ids, context=context):
            cont = 0.0
            val = 0.0
            # Valida si es una categoria sin evaluacion
            if result.eval_category == False:
                res[result.id] = {
                    'performance': 1.0,
                    'result': 1.0
                }
                continue
            
            if result.project_id and result.category_id:
                # Obtiene el desempeño de la evaluacion
                cr.execute("""select category_id, count(value) as Cantidad, value, (count(value)*value_num) as result
                                from project_evaluation_evaluation 
                                where project_id = %s and category_id=%s
                                group by category_id,value,value_num""", (str(result.project_id.id), str(result.category_id.id)))
                for category_id, cant, value, res_value in cr.fetchall():
                    cont += float(cant)
                    val += float(res_value)
                #print "************ val **************** ", val
                #print "************ cont ************* ", cont
                val = val/cont if cont > 0 else val
            
            #print "*********** val *********** ", val, " *** ", type(val)
            #print "*********** id *********** ", result.id
            res[result.id] = {
                'performance': float(val)*100.0,
                'result': float(val)
            }
        return res
    
    _order="type desc, sequence"
    
    _columns = {
        'category_id': fields.many2one('project.evaluation.category', 'Categoria', ondelete="set null", readonly=True),
        'eval': fields.boolean('Evaluado', readonly=True),
        'porcentage': fields.related('category_id', 'porcentage', type="float", relation="project.evaluation.category", store=True, string="Porcentaje", readonly=True),
        'result': fields.function(_get_result, method=True, string='Resultado', readonly=True, type='float', multi="res_eval"),
        'performance': fields.function(_get_result, method=True, string='Rendimiento', readonly=True, type='float', multi="res_eval"),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete="set null", readonly=True),
        'type': fields.related('category_id', 'type', type="selection", selection=[('project','Proyecto'),('partner','Emprendedor'),], relation="project.evaluation.category", store=True, string="Tipo", readonly=True),
        'eval_category': fields.related('category_id', 'eval_category', type="boolean", relation="project.evaluation.category", store=True, string="Evaluar preguntas", readonly=True),
        'sequence': fields.related('category_id', 'sequence', type='integer', store=True, string="Orden", readonly=True)
    }
    
    _defaults = {
        'eval': False,
        'porcentage': 0.0,
        'result': 0.0,
        'performance': 0.0,
    }

project_evaluation_project()
