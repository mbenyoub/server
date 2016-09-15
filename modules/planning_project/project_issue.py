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
    Herencia sobre modulo de Incidencias
"""

import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Project Issue
# ---------------------------------------------------------

class project_issue(osv.Model):
    """Inherited project.issue"""

    _inherit = "project.issue"

    def action_create_ticket(self, cr, uid, ids, context=None):
        """
            Crea una nueva solicitud en base a la informacion registrada en la incidencia
        """
        #print "******************** Crear solicitud de ticket ************************** "
        ticket_obj = self.pool.get('planning.project.ticket')
        ticket_id = 0
        
        #~ Recorre las incidencias
        for issue in self.browse(cr, uid, ids, context=context):
            #~ Valida que haya un contacto seleccionado
            if not issue.partner_id.id:
                raise osv.except_osv(_('Warning!'),_('Se necesita seleccionar un contacto para generar una solicitud.'))
            #~ Genera un diccionario con la informacion de la nueva solicitud
            vals = {
                'name': issue.name,
                'user_id': issue.user_id.id,
                'project_id': issue.project_id.id,
                'priority': issue.priority,
                'partner_id': issue.partner_id.id,
                'description': issue.description,
                'reference': 'Incidencia ' + str(issue.id),
                'state': 'request',
            }
            #print "*************** crear solicitud ******************** ", vals
            #~ Crea la nueva solicitud
            ticket_id = ticket_obj.create(cr, uid, vals, context=context)

            #print "************ modificar llamada ********************* ", ticket_id
            #~ Agrega el id del ticket creado a la incidencia
            self.write(cr, uid, issue.id, {'new_ticket_id':ticket_id,}, context=context)
            
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
        
        return True

    def create(self, cr, uid, vals, context=None):
        #print "************* create issue ivan ***************** "
        if context is None:
            context = {}
        if not vals.get('stage_id'):
            ctx = context.copy()
            if vals.get('ticket_id'):
                ctx['default_ticket_id'] = vals['ticket_id']
                #print "*************** vals ticket ************ ", vals['ticket_id']
                vals['stage_id'] = self._get_default_stage_ticket_id(cr, uid, context=ctx)
            elif vals.get('project_id'):
                ctx['default_project_id'] = vals['project_id']
                #print "*************** vals project ************ ", vals['project_id']
            vals['stage_id'] = self._get_default_stage_id(cr, uid, context=ctx)
        return super(project_issue, self).create(cr, uid, vals, context=context)

    def _get_default_stage_id(self, cr, uid, context=None):
        """ Gives default stage_id """

        #print "****************** context default stage *************************** ", context
        if context.get('default_ticket_id'):
            ticket_id = self._get_default_ticket_id(cr, uid, context=context)
            return self.stage_find(cr, uid, [], ticket_id, [('state', '=', 'draft')], context=context)
        else:
            project_id = self._get_default_project_id(cr, uid, context=context)
            return self.stage_find(cr, uid, [], project_id, [('state', '=', 'draft')], context=context)

    def _get_default_ticket_id(self, cr, uid, context=None):
        """ Gives default project by checking if present in the context """
        return self._resolve_ticket_id_from_context(cr, uid, context=context)

    def _resolve_ticket_id_from_context(self, cr, uid, context=None):
        """ Returns ID of project based on the value of 'default_ticket_id'
            context key, or None if it cannot be resolved to a single
            project.
        """
        if context is None:
            context = {}
        if type(context.get('default_ticket_id')) in (int, long):
            return context.get('default_ticket_id')
        if isinstance(context.get('default_ticket_id'), basestring):
            ticket_name = context['default_ticket_id']
            ticket_ids = self.pool.get('planning.project.ticket').name_search(cr, uid, name=ticket_name, context=context)
            if len(ticket_ids) == 1:
                return int(ticket_ids[0][0])
        return None

    def stage_find(self, cr, uid, cases, section_id, domain=[], order='sequence', context=None):
        """ Override of the base.stage method
            Parameter of the stage search taken from the issue:
            - type: stage type must be the same or 'both'
            - section_id: if set, stages must belong to this section or
              be a default case
        """

        #print "****************** stage find ******************* ", cases
        if isinstance(cases, (int, long)):
            cases = self.browse(cr, uid, cases, context=context)
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        for task in cases:
            #print "************* task ticket ***************** ", task.ticket_id
            #print "************* task project ***************** ", task.project_id
            if task.project_id:
                section_ids.append(task.project_id.id)
        # OR all section_ids and OR with case_default
        search_domain = []
        #print "*************** setction ids ********************** ", section_ids
        if section_ids:
            search_domain += [('|')] * (len(section_ids)-1)
            for section_id in section_ids:
                if context.get('default_ticket_id'):
                    search_domain.append(('ticket_ids', '=', section_id))
                else:
                    search_domain.append(('project_ids', '=', section_id))
        search_domain += list(domain)
        #print "*********************** search domain ********************** ", search_domain
        # perform search, return the first found
        stage_ids = self.pool.get('project.task.type').search(cr, uid, search_domain, order=order, context=context)
        if stage_ids:
            #print "******************* stage ids ********************* ", stage_ids
            return stage_ids[0]
        return False

    def _read_group_stage_ids2(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        #print "************************* tareas project issue ivan ********************* ", context
        #print "************************* context project issue ********************* ", context
        access_rights_uid = access_rights_uid or uid
        stage_obj = self.pool.get('project.task.type')
        order = stage_obj._order
        # lame hack to allow reverting search, should just work in the trivial case
        if read_group_order == 'stage_id desc':
            order = "%s desc" % order
        # retrieve section_id from the context and write the domain
        # - ('id', 'in', 'ids'): add columns that should be present
        # - OR ('case_default', '=', True), ('fold', '=', False): add default columns that are not folded
        # - OR ('project_ids', 'in', project_id), ('fold', '=', False) if project_id: add project columns that are not folded
        search_domain = []
        ticket_id = self._resolve_ticket_id_from_context(cr, uid, context=context)
        if ticket_id:
            #print "******************* ticket id ******************* ", ticket_id
            search_domain += ['|', ('ticket_ids', '=', ticket_id)]
        project_id = self._resolve_project_id_from_context(cr, uid, context=context)
        if project_id:
            #print "******************** project id ******************** ", project_id
            search_domain += ['|', ('project_ids', '=', project_id)]
        search_domain += [('id', 'in', ids)]
        #print "************************* search domain ******************** ", search_domain
        # perform search
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x,y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False

        #print "*********************** result ************************ ", result
        #print "*********************** fold ************************** ", fold
        return result, fold

    def _is_ticket(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = 'False'
            if task.ticket_id:
                res[task.id] = 'True'
        return res

    _columns = {
        'ticket_id': fields.many2one('planning.project.ticket', 'Ticket', select="1", domain="[('state','!=','request'), ('state','!=','cancel')]"),
        'stage_id': fields.many2one ('project.task.type', 'Stage',
                        track_visibility='onchange',
                        domain="['&', ('fold', '=', False), '|', ('project_ids', '=', project_id), ('ticket_ids', '=', ticket_id)]"),
        'is_ticket': fields.function(_is_ticket, type='char', string="Es Ticket", store=True, readonly=True, size=5),
        'new_ticket_id': fields.many2one('planning.project.ticket', 'Nuevo Ticket', select="1", readonly=True, ondelete="set null"),
    }

    _defaults = {
        'stage_id': lambda s, cr, uid, c: s._get_default_stage_id(cr, uid, c),
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids2
    }
