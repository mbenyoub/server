# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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

"""
    Herencia sobre modulo de crm
"""

import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# PhoneCall
# ---------------------------------------------------------

class crm_phonecall(osv.osv):
    _inherit = 'crm.phonecall'

    def action_create_ticket(self, cr, uid, ids, context=None):
        """
            Genera una solicitud de ticket sobre una llamada realizada
        """
        ticket_obj = self.pool.get('planning.project.ticket')
        ticket_id = 0
        
        #~ Recorre las llamadas
        for call in self.browse(cr, uid, ids, context=context):
            #~ Valida que haya un contacto seleccionado
            if not call.partner_id.id:
                raise osv.except_osv(_('Warning!'),_('Se necesita seleccionar un contacto para generar una solicitud.'))
            
            request = {
                'name': call.name,
                'date': call.date,
                'partner_id': call.partner_id.id,
                'priority': call.priority,
                'user_id': call.user_id.id,
                'description': call.description,
                'project_id': call.project_id.id,
                'reference': 'Llamada ' + str(call.id),
                'state': 'request',
            }
            
            #print "*************** crear solicitud ******************** ", request
            
            #~ Crea una nueva solicitud con la informacion de la llamada
            ticket_id = ticket_obj.create(cr, uid, request, context=context)
            
            #print "************ modificar llamada ********************* ", ticket_id
            #~ Agrega el id del ticket creado a la llamada
            self.write(cr, uid, call.id, {'ticket_id':ticket_id,}, context=context)
            
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'planning_project', 'act_planning_project_request_ticket_form_view')
        res_id = res and res[1] or False
        
        #~ Redirecciona al formulario de solicitud
        return {
            'name':_("Ticket"),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'planning.project.ticket', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id' : ticket_id, # id of the object to which to redirected
        }

    _columns = {
        'project_id': fields.many2one('project.project', 'Proyecto', select="1"),
        'ticket_id': fields.many2one('planning.project.ticket', 'Ticket', select="1", readonly=True),
        'is_project': fields.boolean('Llamada de proyecto', readonly=True, select=True),
    }

    def _get_default_type_call(self, cr, uid, context=None):
        """
            Retorna verdadero si es una llamada de proyecto
        """
        #print "******************** context ********************* ", context
        # Valida por medio del parametro default si proviene de un proyecto o no
        if context and context.get('default_is_project', False):
            #print "************** is project default *************** ", context.get('default_is_project')
            return context.get('default_is_project')
        #print " **************** default project false ******************** "
        return False

    _defaults = {
        'is_project': _get_default_type_call
    }

crm_phonecall()
