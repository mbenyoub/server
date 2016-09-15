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

import time
from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.Model):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner'
    
    def action_update_eval_consulting(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de los consultores para que tenga
        """
        evaluation_obj = self.pool.get('res.partner.evaluation.evaluation')
        template_obj = self.pool.get('res.partner.evaluation.template')
        if context is None:
            context={}
        eval_ids = []
        partners = []
        
        partner_ids = self.search(cr, uid, [('type_contact','=','con')], context=context)
        if len(partner_ids):
            for partner in self.browse(cr, uid, partner_ids, context=context):
                if not partner.evaluation_ids:
                    partners.append(partner.id)
            
            if partners:
                # Genera las evaluaciones para el perfil
                template_ids = template_obj.search(cr, uid, [('active','=',True)])
                # Obtiene la plantilla de los cuestionarios y genera las preguntas
                for template in template_obj.browse(cr, uid, template_ids, context=context):
                    eval_ids.append([0, False, {'notes': False, 'sector_ids': [[6, False, []]], 'category_id': template.category_id.id, 'name': template.name, 'experience': 0}])
                self.write(cr, uid, partners, {'evaluation_ids': eval_ids}, context=context)
    
    def onchange_type_contact(self, cr, uid, ids, type_contact, evaluation_ids, context=None):
        """
            Agrega o elimina las areas a evaluar por el consultor
        """
        evaluation_obj = self.pool.get('res.partner.evaluation.evaluation')
        template_obj = self.pool.get('res.partner.evaluation.template')
        if context is None:
            context={}
        eval_ids = []
        
        # Si recibe un id, elimina la informacion anterior
        if len(ids):
            s_eval_ids = evaluation_obj.search(cr, uid, [('partner_id','=',ids[0])])
            if s_eval_ids:
                evaluation_obj.unlink(cr, uid, s_eval_ids)
        
        # Valida que el contacto no tenga evaluaciones ya agregadas para el proyecto
        if type_contact=='con':
            if not evaluation_ids:
                # Genera las evaluaciones para el perfil
                template_ids = template_obj.search(cr, uid, [('active','=',True)])
                # Obtiene la plantilla de los cuestionarios y genera las preguntas
                for template in template_obj.browse(cr, uid, template_ids, context=context):
                    eval_ids.append([0, False, {'notes': False, 'sector_ids': [[6, False, []]], 'category_id': template.category_id.id, 'name': template.name, 'experience': 0}])
            else:
                eval_ids = []
        return {'value':{'evaluation_ids': eval_ids}}
    
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
            Indica si el usuario es el administrador del proyecto, si no lo es y es su contacto le doy permisos de escritura
        """
        partner_id = self.pool.get('res.users').browse(cr, uid, uid, None).partner_id.id
        res = {}
        for this_id in ids:
            res[this_id] = False
            if self.pool.get('res.users').has_group(cr, uid, 'base.group_project_reto_zapopan_eval'):
                res[this_id] = True
            elif partner_id == this_id:
                res[this_id] = True
        return res
    
    _columns = {
        'sex': fields.selection([
            ('hombre','Hombre'),
            ('mujer','Mujer'),
            ('indistinto','Indistinto')], 'Sexo'),
        'type_contact': fields.selection([
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor'),], 'Tipo'),
        'evaluation_ids': fields.one2many('res.partner.evaluation.evaluation', 'partner_id', string='Consultoria', ondelete="cascade", help=" Las siguientes areas son temas de intervencion posible en Reto Zapopan, los cuales estan relacionados al diagnostico inicial de los proyectos y empresas integrantes de la Generacion 2013. Seleccione aquellas areas en las que tiene oferta de intervencion, indicando años de experiencia de acuerdo al sector o contexto según sea el caso. Por favor considere que debe poseer informacion comprobable como evidencia de la oferta propuesta."),
        'evaluation_notes1': fields.text('Nota1'),
        'evaluation_notes2': fields.text('Nota2'),
        'rfc': fields.char('RFC'),
        'consultor_matter': fields.text('Materia'),
        'speciality': fields.char('Especializacion'),
        'consulting_hr_cost': fields.char('Costo por hora', help="Costo por hora consultoria, servicio mas iva"),
        'is_manager':fields.function(_is_manager_function, type='boolean', string="Manager"),
    }
    
    _defaults = {
        'sex': 'hombre',
        'type_contact': 'emp',
        'evaluation_ids': [],
        'is_manager': _is_manager_default,
    }
    
res_partner()

class res_partner_read(osv.osv):
    _name = "res.partner.read"
    _inherit = "res.partner"
    _table = "res_partner"
    _description = "Lectura de Contacto"

res_partner_read()

class res_partner_edit(osv.osv):
    _name = "res.partner.edit"
    _inherit = "res.partner"
    _table = "res_partner"
    _description = "Edicion de Contacto"
    _order = "id"

res_partner_edit()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
