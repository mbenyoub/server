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
# Project phase - Template
# ---------------------------------------------------------

class project_phase_template_result(osv.Model):
    """Inherited project.phase.template.result"""

    _name = "project.phase.template.result"
    
    _columns = {
        'name': fields.text("Name", required=True),
        'template_id': fields.many2one('project.phase.template', 'Template'),
     }

project_phase_template_result()

class project_phase_template(osv.Model):
    """Inherited project.phase.template"""

    _name = "project.phase.template"
    
    _columns = {
        'name': fields.char("Name", size=64, required=True),
        'sequence': fields.integer('Etapa', select=True, help="Secuencia de las fases."),
        'date_start': fields.datetime('Fecha Inicio', select=True, help="Fecha de inicio de la Fase."),
        'date_end': fields.datetime('Fecha Final', help="Fecha final de la Fase"),
        'meeting_time': fields.float('Horas sugeridas', help="Horas sugeridas para consultoria"),
        'expected_results': fields.one2many('project.phase.template.result', 'template_id', 'Resultados esperados')
     }
    
    _order = "name, date_start, sequence"

project_phase_template()

# ---------------------------------------------------------
# Project phase
# ---------------------------------------------------------

class project_phase_result(osv.Model):
    """Inherited project.phase.result"""

    _name = "project.phase.result"
    
    _columns = {
        'name': fields.text("Name", required=True),
        'phase_id': fields.many2one('project.phase', 'Fase'),
     }

project_phase_result()

class project_phase(osv.Model):
    """Inherited project.phase"""

    _inherit = "project.phase"
    
    def onchange_project_id(self, cr, uid, ids, project_id, context=None):
        """
            Actualiza los recursos disponibles en base al proyecto
        """
        if context is None:
            context={}
        project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
        values = []
        # obtiene la nueva lista de rusuarios
        for user in project.members:
            # Genera las evaluaciones para el perfil
            values.append([0, False, {'user_id': user.id}])
        return {'value':{'user_ids': values}}
    
    def onchange_template(self, cr, uid, ids, template_id, context=None):
        """
            Actualiza la informacion de la fase por medio del template
        """
        if context is None:
            context={}
        template = self.pool.get('project.phase.template').browse(cr, uid, template_id, context=context)
        result_values = []
        values = {
            'name': template.name,
            'date_start': template.date_start,
            'date_end': template.date_end,
            'sequence': template.sequence,
            'meeting_time': template.meeting_time
        }
        # Si existen resultados de la fase cargados anteriormente los elimina
        if len(ids):
            result_obj = self.pool.get('project.phase.result')
            p_result_ids = result_obj.search(cr, uid, [('phase_id','=',ids[0])], context=context)
            if p_result_ids:
                result_obj.unlink(cr, uid, p_result_ids)
        # obtiene la nueva lista de resultados esperados
        for result_template in template.expected_results:
            # Genera las evaluaciones para el perfil
            result_values.append([0, False, {'name': result_template.name}])
        values['expected_results'] = result_values
        return {'value':values}
    
    def _get_duration(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa la duracion en relacion al rango de fechas de las fases
        """
        res = {}
        for phase in self.browse(cr, uid, ids, context=context):
            res[phase.id] = 0.0
            if phase.date_start and phase.date_end:
                date_start = datetime.strptime(phase.date_start[:10], '%Y-%m-%d')
                date_end = datetime.strptime(phase.date_end[:10], '%Y-%m-%d')
                duration = date_end - date_start
            res[phase.id] = duration.days
        return res
    
    _columns = {
        'sequence': fields.integer('Etapa', select=True, help="Secuencia de las fases."),
        'date_start': fields.datetime('Fecha Inicio', required=True, select=True, help="Fecha de inicio de la Fase."),
        'date_end': fields.datetime('Fecha Final', required=True, help="Fecha final de la Fase"),
        'meeting_time': fields.float('Horas de consultoria', help="Horas sugeridas para consultoria"),
        'expected_results': fields.one2many('project.phase.result', 'phase_id', 'Resultados esperados'),
        'duration': fields.function(_get_duration, method=True, store=True, type="float", string='Duracion', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Duration Unit of Measure', readonly=True, required=True, help="Unit of Measure (Unit of Measure) is the unit of measurement for Duration", states={'done':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        'template_id': fields.many2one('project.phase.template', 'Plantilla', required=True, invisible=True, states={'draft':[('invisible',False)]}),
        'project_log_project_ids': fields.one2many('project.log.project', 'phase_id', string="Bitacora", ondelete="cascade"),
     }
    
    def _get_product_uom(self, cr, uid, ids, context=None):
        """
            Regresa por default dias
        """
        uom_id = self.pool.get('product.uom').search(cr, uid, ['|',('name','like','Dia%'),('name','like','Day%')])[0]
        return uom_id
    
    _defaults = {
        'product_uom': _get_product_uom
    }

project_phase()
