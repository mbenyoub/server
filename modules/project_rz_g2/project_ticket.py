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

from datetime import datetime, date

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Tickets
# ---------------------------------------------------------
class project_ticket(osv.Model):
    _name = "project.ticket"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def action_ticket_confirm(self, cr, uid, ids, context=None):
        """
            Cambia la solicitud a ticket
        """
        #print "************* funcion confirm ****************"
        date = fields.date.context_today(self,cr,uid,context=context)
        self.write(cr, uid, ids, {'state':'ticket', 'date_approve': date}, context=context)
        return True

    def action_ticket_special(self, cr, uid, ids, context=None):
        """
            Cambia la solicitud a soporte especializado
        """
        self.write(cr, uid, ids, {'state':'special'}, context=context)
        return True

    def action_ticket_done(self, cr, uid, ids, context=None):
        """
            Pone el ticket como terminado
        """
        #print "************* funcion done ****************"
        self.write(cr, uid, ids, {'state':'done'}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """
            Cancela el ticket
        """
        #print "************* funcion cancel ****************"
        self.write(cr, uid, ids, {'state':'cancel'}, context=context)
        task_obj = self.pool.get('project.task')
        #~ Pone como canceladas todas las tareas relacionadas con la solicitud
        for ticket in self.browse(cr, uid, ids, context=context):
            #print "************** Cancela tareas ******************* ", ticket.tasks
            #~ Recorre las tareas y cambia su estado
            task_ids = []
            for task in ticket.tasks:
                task_ids.append(task.id)
            task_obj.write(cr, uid, task_ids, {'state':'cancel'}, context=context)
        return True

    def action_cancel_to_request(self, cr, uid, ids, context=None):
        """
            Pasa el ticket cancelado a una solicitud
        """
        #print "************* funcion cancel to request ****************"
        self.write(cr, uid, ids, {'state':'request'}, context=context)
        return True

    def _ticket_expired(self, cr, uid, ids, prop, arg, context=None):
        """
            Retorna verdadero si la fecha actual pasa de la fecha de entrega
        """
        res = {}
        date = fields.date.context_today(self,cr,uid,context=context)
        for ticket in self.browse(cr, uid, ids, context=context):

            if not ticket.delivery_date:
                res[ticket.id] = False
                continue

            if ticket.delivery_date <= date:
                res[ticket.id] = True
            else:
                res[ticket.id] = False
        return res

    def attachment_tree_view(self, cr, uid, ids, context):
        """
            Opcion para generar documentos digitalizados
        """
        task_ids = self.pool.get('project.task').search(cr, uid, [('ticket_id', 'in', ids)])
        domain = [
             '|',
             '&', ('res_model', '=', 'planning.project.ticket'), ('res_id', 'in', ids),
             '&', ('res_model', '=', 'project.task'), ('res_id', 'in', task_ids)
        ]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    def _task_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        task_ids = self.pool.get('project.task').search(cr, uid, [('ticket_id', 'in', ids)])
        for task in self.pool.get('project.task').browse(cr, uid, task_ids, context):
            res[task.ticket_id.id] += 1
        return res

    def _get_attached_docs(self, cr, uid, ids, field_name, arg, context):
        res = {}
        attachment = self.pool.get('ir.attachment')
        task = self.pool.get('project.task')
        for id in ids:
            project_attachments = attachment.search(cr, uid, [('res_model', '=', 'planning.project.ticket'), ('res_id', '=', id)], context=context, count=True)
            task_ids = task.search(cr, uid, [('ticket_id', '=', id)], context=context)
            task_attachments = attachment.search(cr, uid, [('res_model', '=', 'project.task'), ('res_id', 'in', task_ids)], context=context, count=True)
            res[id] = (project_attachments or 0) + (task_attachments or 0)
        return res

    _order = 'priority,id'

    _columns = {
        'name': fields.char('Nombre', size=64, required=True, select=True),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete='set null', select="1", track_visibility='onchange'),
        'partner_id': fields.many2one('res.partner', 'Solicitante', required=True),
        'date' : fields.date(string='Fecha', required=True),
        'description' : fields.text(string="Descripcion", help='Informacion detallada sobre lo que se solicita'),
        'state': fields.selection([
                    ('request', 'Solicitud'),
                    ('ticket', 'Ticket'),
                    ('special', 'Soporte Especializado'),
                    ('done', 'Terminado'),
                    ('cancel', 'Cancelado'),], 'Status', readonly=True, help="Indica el estado en el que se encuentra nuestro ticket.", select=True),
        'reference': fields.char('Referencia', size=64, help="Referencia del documento del que proviene la solicitud."),
        'date_approve':fields.date('Fecha aprobada', readonly=1, select=True, help="Fecha de aprobacion de la solicitud"),
        'delivery_date':fields.date('Fecha Entrega', select=True, help="Fecha programada para la entrega del ticket"),
        'note': fields.text('Notas'),
        'user_id': fields.many2one('res.users', 'Responsable'),
        'tasks': fields.one2many('project.task', 'ticket_id', "Tareas"),
        'ticket_expired': fields.function(_ticket_expired, string='Expirado', type="boolean"),
        'type_ids': fields.many2many('project.task.type', 'project_task_type_ticket_rel', 'ticket_id', 'type_id', 'Etapas tareas', states={'request':[('readonly',True)], 'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'color': fields.integer('Color Index'),
        'task_count': fields.function(_task_count, type='integer', string="Open Tasks"),
        'doc_count':fields.function(_get_attached_docs, string="Numero de documentos adjuntos", type='int'),
        'priority': fields.selection([
                    ('1', 'Muy Alto'),
                    ('2', 'Alto'),
                    ('3', 'Normal'),
                    ('4', 'Bajo'),
                    ('5', 'Muy Bajo'),], 'Prioridad'),
        'category': fields.selection([
                    ('modify', 'Modificacion'),
                    ('adjust', 'Ajuste'),
                    ('error_sis', 'Sistema'),
                    ('error_data', 'Usuario'),
                    ('new', 'Requerimiento Nuevo'),
                    ('other', 'Otro'),], 'Categoria')
    }

    def _get_type_common(self, cr, uid, context=None):
        ids = self.pool.get('project.task.type').search(cr, uid, [('case_default','=',1)], context=context)
        return ids

    _defaults = {
        'state' : 'ticket',
        'date' : fields.date.today,
        'date_approve' : fields.date.today,
        'type_ids': _get_type_common
    }

project_ticket()
