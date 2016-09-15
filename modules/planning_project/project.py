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
    Herencia sobre modulo de proyecto y tareas
"""

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

class project_task_type(osv.osv):
    _inherit = 'project.task.type'

    _columns = {
        'ticket_ids': fields.many2many('planning.project.ticket', 'project_task_type_ticket_rel', 'type_id', 'ticket_id', 'Ticket'),
    }

project_task_type()

class project(osv.Model):
    """Inherited crossovered.budget"""

    _inherit = "project.project"

    def _task_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        task_ids = self.pool.get('project.task').search(cr, uid, [('project_id', 'in', ids), ('ticket_id', '=', False)])
        #print "***************** task ids **************************** ", task_ids
        for task in self.pool.get('project.task').browse(cr, uid, task_ids, context):
            res[task.project_id.id] += 1
        return res

    def _issue_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        issue_ids = self.pool.get('project.issue').search(cr, uid, [('project_id', 'in', ids), ('ticket_id', '=', False)])
        for issue in self.pool.get('project.issue').browse(cr, uid, issue_ids, context):
            if issue.state not in ('done', 'cancelled'):
                res[issue.project_id.id] += 1
        return res

    def _ticket_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        ticket_ids = self.pool.get('planning.project.ticket').search(cr, uid, [('project_id', 'in', ids)])
        for ticket in self.pool.get('planning.project.ticket').browse(cr, uid, ticket_ids, context):
            if ticket.state not in ('done', 'cancel', 'request'):
                res[ticket.project_id.id] += 1
                #print "**************** cuenta ", ticket.project_id.id, " - ", ticket.state, " ********** ", res[ticket.project_id.id]
        #print "**************** resultado ********** ", res
        return res

    def _sum_log(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la suma de las actividades del proyecto
        """
        #print "****************** suma de actividades proyecto ************************** "
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            #~ Obtiene la suma de tiempo invertido en las actividades del proyecto
            sql = 'select t.id as project_id, (CASE WHEN sum(p.time) > 0 THEN sum(p.time) ELSE 0 END) AS suma from project_project t LEFT JOIN planning_project_task_log p on (t.id=p.project_id and p.ticket_id is null) where t.id=' + str(project.id) + ' group by t.id'
            #print "**************************** sql ejecutado en la consulta tareas project ************************* ", sql
            cr.execute(sql)
            #~ Recorre el cursor para obtener el tiempo utilizado
            for row in cr.dictfetchall():
                #print "************** row project ******************* ", row
                time_project = float(row['suma'])
            #~ Obtiene la suma de tiempo invertido en las actividades del ticket
            sql = 'select t.id as project_id, (CASE WHEN sum(p.time) > 0 THEN sum(p.time) ELSE 0 END) AS suma from project_project t LEFT JOIN planning_project_task_log p on (t.id=p.project_id and p.ticket_id is not null) where t.id=' + str(project.id) + ' group by t.id'
            #print "**************************** sql ejecutado en la consulta tareas ticket ************************* ", sql
            cr.execute(sql)
            #~ Recorre el cursor para obtener el tiempo utilizado
            for row in cr.dictfetchall():
                #print "************** row ticket ******************* ", row
                time_ticket = float(row['suma'])
            time = time_project + time_ticket
            #print "******************* tiempo ticket ", project.name, " ****************** ", time
            hours_ticket = (time_ticket / 60)
            hours_project = (time_project / 60)
            hours = (time / 60)
            #print "******************** tiempo en horas **************************** ", hours 
            #~ Asigna el tiempo en horas a la tarea
            res[project.id] = hours
            if hours != 0.0:
                self.write(cr, uid, project.id, {'task_log_time_total': hours,'task_log_time_ticket': hours_ticket,'task_log_time_project': hours_project}, context=context)
            if not hours:
                res[project.id] = 0.0
        #print "************* resultado ************* ", res
        return res
    
    _columns = {
        'description': fields.text('Descripcion'),
        'ticket_id': fields.one2many('planning.project.ticket', 'tasks', 'Tareas'),
        'task_count': fields.function(_task_count, type='integer', string="Open Tasks"),
        'issue_count': fields.function(_issue_count, type='integer', string="Unclosed Issues"),
        'ticket_count': fields.function(_ticket_count, type='integer', string="Unclosed Tickets"),
        'task_log_time_function': fields.function(_sum_log, type='float', string="Horas funcion", method=True, readonly=True),
        'task_log_time_ticket': fields.float(string='Horas trabajadas tickets', readonly=True, help="Total de tiempo invertido en tareas relacionadas a tickets"),
        'task_log_time_project': fields.float(string='Horas trabajadas proyecto', readonly=True, help="Total de tiempo invertido en las tareas relacionadas al proyecto"),
        'task_log_time_total': fields.float(string='Hrs trabajadas', readonly=True, help="Total de tiempo invertido en el proyecto"),
    }

    _default = {
        'task_log_time_ticket': 0.0,
        'task_log_time_project': 0.0,
        'task_log_time_total': 0.0,
    }

project()

class task(osv.Model):
    """Inherited project.task"""

    _inherit = 'project.task'
    _order = 'id desc'

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
        """
            Valida si es un ticket
        """
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = 'False'
            if task.ticket_id:
                res[task.id] = 'True'
        return res

    # Override view according to the company definition
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
            Se reemplaza la funcion en las tareas porque estaba quitando el widget de float_time
        """
        users_obj = self.pool.get('res.users')
        if context is None: context = {}
        # read uom as admin to avoid access rights issues, e.g. for portal/share users,
        # this should be safe (no context passed to avoid side-effects)
        obj_tm = users_obj.browse(cr, SUPERUSER_ID, uid, context=context).company_id.project_time_mode_id
        tm = obj_tm and obj_tm.name or 'Hours'

        res = super(task, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu=submenu)

        if tm in ['Hours','Hour']:
            return res

        eview = etree.fromstring(res['arch'])

        def _check_rec(eview):
            #print "************ atributo ************ ", eview.attrib.get('widget','')
            if eview.attrib.get('widget','') == 'f_time':
                #print "********** set float **************"
                # Se deja igual float_time
                eview.set('widget','float_time')
            for child in eview:
                _check_rec(child)
            return True

        _check_rec(eview)

        res['arch'] = etree.tostring(eview)

        for f in res['fields']:
            if 'Hours' in res['fields'][f]['string']:
                res['fields'][f]['string'] = res['fields'][f]['string'].replace('Hours',tm)
        return res

    def _sum_task_log(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la suma de las actividades del ticket
        """
        #print "****************** suma de actividades ************************** "
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            #~ Obtiene la suma de tiempo invertido en las actividades
            sql = 'select t.id as task_id, (CASE WHEN sum(p.time) > 0 THEN sum(p.time) ELSE 0 END) AS suma from project_task t LEFT JOIN planning_project_task_log p on (t.id=p.task_id) where t.id =' + str(task.id) + ' group by t.id'
            #print "**************************** sql ejecutado en la consulta ************************* ", sql
            cr.execute(sql)
            #~ Recorre el cursor para obtener el tiempo utilizado
            for row in cr.dictfetchall():
                #print "************** row ******************* ", row
                time = float(row['suma'])
            #print "******************* tiempo ticket ", task.name, " ****************** ", time
            hours = (time / 60)
            #print "******************** tiempo en horas **************************** ", hours 
            #~ Asigna el tiempo en horas a la tarea
            res[task.id] = hours
            if hours != 0.0:
                self.write(cr, uid, task.id, {'task_log_time': hours}, context=context)
            if not hours:
                res[task.id] = 0.0
        #print "************* resultado ************* ", res
        return res

    _columns = {
        'log_id': fields.one2many('planning.project.task.log', 'task_id', 'Bitacora'),
        'ticket_id': fields.many2one('planning.project.ticket', 'Ticket', select="1", domain="[('state','!=','request'), ('state','!=','cancel')]"),
        'stage_id': fields.many2one ('project.task.type', 'Stage',
                        track_visibility='onchange',
                        domain="['&', ('fold', '=', False), '|', ('project_ids', '=', project_id), ('ticket_ids', '=', ticket_id)]"),
        'is_ticket': fields.function(_is_ticket, type='char', string="Es Ticket", store=True, readonly=True, size=5),
        'task_log_time_function': fields.function(_sum_task_log, type="float", string="Horas funcion", method=True, readonly=True),
        'task_log_time': fields.float(string='Hrs trabajadas', readonly=True, help="Tiempo invertido sobre la tarea"),
    }

    _defaults = {
        'task_log_time': 0.0,
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids2,
    }

task()
