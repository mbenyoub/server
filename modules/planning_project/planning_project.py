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
# Bitacora
# ---------------------------------------------------------

_TASK_STATE = [('draft', 'New'),('open', 'In Progress'),('pending', 'Pending'), ('done', 'Done'), ('cancelled', 'Cancelled')]

class task_log(osv.Model):
    _name = "planning.project.task.log"

    def action_finish_task(self, cr, uid, ids, context=None):
        """
        
            Pone la tarea del ticket como finalizada
        """
        #print "************* Finaliza la tarea ****************"

        task_obj = self.pool.get('project.task')
        project_obj = self.pool.get('project.project')
        ticket_obj = self.pool.get('planning.project.ticket')
        
        #~ Recorre la bitacora
        for log in self.browse(cr, uid, ids, context=context):
            #~ Valida que haya una tarea seleccionada
            if not log.task_id.id:
                raise osv.except_osv(_('Error!'),_('No hay una tarea seleccionada para la actividad registrada'))

            #~ Obtiene la tarea
            task = task_obj.browse(cr, uid, log.task_id.id, context=context)
            #print "********************* task *********************** ", task
            #print "******************** task info ******************* ", task_obj.read(cr, uid, log.task_id.id, context=context)
            #print "******************** stage ********************** ", task.stage_id.name
            #~ Identifica la etapa final
            if task.ticket_id.id:
                ticket = ticket_obj.browse(cr, uid, task.ticket_id.id, context=context)
                #print "************************ ticket.type_ids ********************** ", ticket.type_ids
                stages = ticket.type_ids

            elif task.project_id.id:
                project = project_obj.browse(cr, uid, task.project_id.id, context=context)
                #print "************************ project.type_ids ********************** ", project.type_ids
                stages = project.type_ids
            else:
                raise osv.except_osv(_('Error!'),_('No se puede finalizar la tarea porque no hay un ticket o un proyecto asignado'))

            stage_id = 0
            #~ Recorre las etapas y busca una con estado final
            for stage in stages:
                #print "*********************** stage state ************************ ", stage.state
                if stage.state == 'done':
                    stage_id = stage.id
                    break

            #print "***************** stage id ********************** ", stage_id
            #~ Cambia el estado de la tarea
            if not stage_id:
                raise osv.except_osv(_('Error!'),_('No hay una etapa final para esta tarea'))
            task_obj.write(cr, uid, log.task_id.id, {'stage_id': stage_id, 'state': 'done'}, context=context)
            
        return True

    def _is_task_finish(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si la tarea se encuentra en una etapa final
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            res[log.id] = 'False'
            if log.task_id:
                if log.task_id.state == 'done':
                    res[log.id] = 'True'
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
                #print "****************** fecha ****************** ", log.date
                #print "******************* dia ******************* ", dia
                #print "******************* mes ******************* ", mes
                #print "******************* anio ******************* ", anio
                res[log.id] = dia + mes_texto[mes] + anio
                
        return res

    def _get_user(self, cr, uid, ids, context=None):
        """
            Regresa el usuario activo
        """
        #print "************** uid ************** ", uid, "  context  ", context, "   ids ", ids
        return uid

    _columns = {
        'user_id': fields.many2one('res.users', 'Created By', readonly=True),
        'task_id' : fields.many2one('project.task', string='Tarea', required=True, domain=[('state','not in',('done','cancelled'))], help="Tarea donde proviene la actividad para registrar en la bitacora."),
        'date' : fields.date(string='Fecha', required=True),
        'time' : fields.integer(string='Duracion', required=True),
        'description' : fields.text(string="Descripcion", help='Información adicional sobre el movimiento'),
        'task_finish': fields.function(_is_task_finish, method=True, string='Tarea terminada', readonly=True, type='char', size=5, help="Indica si la tarea fue finalizada."),
        'state': fields.related('task_id', 'state', type="selection", store=True,
                selection=_TASK_STATE, string="Status", readonly=True,
                help='The status is set to \'Draft\', when a case is created.\
                      If the case is in progress the status is set to \'Open\'.\
                      When the case is over, the status is set to \'Done\'.\
                      If the case needs to be reviewed then the status is \
                      set to \'Pending\'.'),
        'project_id': fields.related('task_id', 'project_id', type="many2one", relation="project.project", store=True, string="Proyecto", readonly=True),
        'ticket_id': fields.related('task_id', 'ticket_id', type="many2one", relation="planning.project.ticket", store=True, string="Ticket", readonly=True),
        'date_string': fields.function(_get_date_string, method=True, store=True, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
    }

    _defaults = {
        'date' : fields.date.today,
        'user_id': _get_user,
    }

    _order = 'id desc'

task_log()

# ---------------------------------------------------------
# Tickets
# ---------------------------------------------------------
class ticket(osv.Model):
    _name = "planning.project.ticket"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def action_ticket_confirm(self, cr, uid, ids, context=None):
        """
            Cambia la solicitud a ticket
        """
        #print "************* funcion confirm ****************"
        date = fields.date.context_today(self,cr,uid,context=context)
        self.write(cr, uid, ids, {'state':'ticket', 'date_approve': date}, context=context)
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

    def _issue_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        issue_ids = self.pool.get('project.issue').search(cr, uid, [('ticket_id', 'in', ids)])
        for issue in self.pool.get('project.issue').browse(cr, uid, issue_ids, context):
            if issue.state not in ('done', 'cancelled'):
                res[issue.ticket_id.id] += 1
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

    def _sum_log(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la suma de las actividades del ticket
        """
        #print "****************** suma de actividades proyecto ************************** "
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            #~ Obtiene la suma de tiempo invertido en las actividades del ticket
            sql = 'select t.id as ticket_id, (CASE WHEN sum(p.time) > 0 THEN sum(p.time) ELSE 0 END) AS suma from planning_project_ticket t LEFT JOIN planning_project_task_log p on (t.id=p.ticket_id) where t.id=' + str(ticket.id) + ' group by t.id'
            #print "**************************** sql ejecutado en la consulta tareas ticket ************************* ", sql
            cr.execute(sql)
            #~ Recorre el cursor para obtener el tiempo utilizado
            for row in cr.dictfetchall():
                #print "************** row ticket ******************* ", row
                time = float(row['suma'])
            #print "******************* tiempo ticket ", ticket.name, " ****************** ", time
            hours = (time / 60)
            #print "******************** tiempo en horas **************************** ", hours 
            #~ Asigna el tiempo en horas a la tarea
            res[ticket.id] = hours
            if hours != 0.0:
                self.write(cr, uid, ticket.id, {'task_log_time': hours}, context=context)
            if not hours:
                res[ticket.id] = 0.0
        return res
        
    _order = 'sequence'

    _columns = {
        'name': fields.char('Nombre', size=64, required=True, select=True),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete='set null', select="1", track_visibility='onchange'),
        'partner_id': fields.many2one('res.partner', 'Solicitante', required=True),
        'date' : fields.date(string='Fecha', required=True),
        'description' : fields.text(string="Descripcion", help='Información detallada sobre lo que se solicita'),
        'state': fields.selection([
                    ('request', 'Solicitud'),
                    ('ticket', 'Ticket'),
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
        'issue_count': fields.function(_issue_count, type='integer', string="Unclosed Issues"),
        'doc_count':fields.function(_get_attached_docs, string="Numero de documentos adjuntos", type='int'),
        'priority': fields.selection([
                    ('1', 'Muy Alto'),
                    ('2', 'Alto'),
                    ('3', 'Normal'),
                    ('4', 'Bajo'),
                    ('5', 'Muy Bajo'),], 'Prioridad'),
        'task_log_time_function': fields.function(_sum_log, type='float', string="Horas funcion", method=True, readonly=True),
        'task_log_time': fields.float(string='Horas trabajadas', readonly=True, help="Total de tiempo invertido en tareas del ticket"),
    }

    def _get_type_common(self, cr, uid, context=None):
        ids = self.pool.get('project.task.type').search(cr, uid, [('case_default','=',1)], context=context)
        #print "********************* ids *********************** ", ids
        return ids

    _defaults = {
        'state' : 'request',
        'date' : fields.date.today,
        'type_ids': _get_type_common,
        'task_log_time': 0.0
    }

    _order = 'id desc'

ticket()
