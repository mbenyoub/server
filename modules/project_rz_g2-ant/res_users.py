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

class res_users(osv.osv):
    """ Inherits partner and add extra information kober """
    _inherit = 'res.users'
    
    def action_update_evaluation_consulting(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de los consultores para que tenga
        """
        evaluation_obj = self.pool.get('res.partner.evaluation.evaluation')
        template_obj = self.pool.get('res.partner.evaluation.template')
        category_obj = self.pool.get('res.partner.evaluation.category')
        partner_obj = self.pool.get('res.partner')
        if context is None:
            context={}
        eval_ids = []
        partners = []
        
        # Recorre a los usuarios consultores que se tienen que actualizar
        user_ids = self.search(cr, uid, [('type_contact','=','con'),('id','in',ids)], context=context)
        for user in self.browse(cr, uid, user_ids, context=context):
            filters = []
            
            # Valida que el usuario sea un consultor y que tenga que filtrar las categorias
            if user.type_contact != 'con' or user.filter_category == False:
                continue
            
            # Obtiene las categorias que aplican sobre el contacto
            if user.category_ids:
                for categ in user.category_ids:
                    filters.append(categ.id)
            else:
                # Obtiene todas las fases
                filters = category_obj.search(cr, uid, [], context=context)
            
            # Valida si el consultor tiene asignadas categorias que no le correspondan
            evaluation_ids = evaluation_obj.search(cr, uid, [('category_id','not in',filters),('partner_id','=',user.partner_id.id or False)], context=context)
            if evaluation_ids:
                # Elimina las fases encontradas
                evaluation_obj.unlink(cr, uid, evaluation_ids, context=context)
            
            # Obtiene los templates que aplican sobre las fases
            template_ids = template_obj.search(cr, uid, [('category_id','in',filters),('active','=',True)], context=context)
            # Recorre los registros de las subespecialidades
            for template in template_obj.browse(cr, uid, template_ids, context=context):
                # Valida que el contacto no tenga la subespecialidad agregada
                evaluation_ids = evaluation_obj.search(cr, uid, [('template_id','=',template.id),('partner_id','=',user.partner_id.id or False)], context=context)
                if evaluation_ids:
                    continue
                # Agrega al nuevo registro de evaluacion para el consultor
                evaluation_obj.create(cr, uid,{
                    'phase_id': template.phase_id.id or False,
                    'category_id': template.category_id.id or False,
                    'template_id': template.id or False,
                    'name': template.name,
                    'experience': 0,
                    'sequence': template.priority,
                    'partner_id': user.partner_id.id or False,
                    'notes': False,
                    'sector_ids': [[6, False, []]]}, context=context)
                
        return True
    
    def action_view_partner(self, cr, uid, ids, context=None):
        """
            Muestra el contacto del usuario
        """
        # Obtiene el objeto del proyecto
        user = self.browse(cr, uid, ids[0], context=context)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base', 'view_partner_form')
        return {
            'name':_("Contactos"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            'res_id' : user.partner_id.id or False, # id of the object to which to redirected
        }
    
    def create(self, cr, uid, vals, context=None):
        """
            Si el usuario es un consultor agrega la informacion del consultor en caso de que cambie el tipo de contacto
        """
        if context is None:
            context = {}
        # Funcion original de crear usuario
        res = super(res_users, self).create(cr, uid, vals, context=context)
        
        partner_obj = self.pool.get('res.partner')
        
        # Actualiza el tipo de contacto
        if vals.get('type_contact',False):
            #user = self.browse(cr, uid, res, context=context)
            self.write(cr, uid, [res], {'type_contact': vals.get('type_contact','otr')}, context=context)
        
        # Agrega las preguntas a los consultores que no las tengan
        #self.action_update_evaluation_consulting(cr, uid, [res], context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Si el usuario es un consultor agrega la informacion del consultor en caso de que cambie el tipo de contacto
        """
        if context is None:
            context = {}
        if not ids:
            return True
        if type(ids) != list:
            ids = [ids]
        # Funcion original de modificar
        res = super(res_users, self).write(cr, uid, ids, vals, context=context)
        
        # Agrega las preguntas a los consultores que no las tengan
        self.action_update_evaluation_consulting(cr, uid, ids, context=context)
        return res
    
    _columns = {
        'type_contact': fields.related('partner_id', 'type_contact', type='selection', selection=[
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor'),
            ('otr','Otro'),], string='Tipo', store=True),
        'category_ids': fields.many2many('res.partner.evaluation.category', 'res_users_evaluation_category_rel', 'user_id', 'category_id', string='Filtrar Especialidades', help="Aplicar un filtro sobre las Especialidades en las que entra el consultor"),
        'phase_ids': fields.boolean('Filtrar especialidades'),
        'filter_category': fields.boolean('Filtrar especialidades')
    }
    
    _defaults = {
        'type_contact': 'emp',
        'filter_category': True
    }
    
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
