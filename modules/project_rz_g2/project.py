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
# Project
# ---------------------------------------------------------

class project_project(osv.osv):
    """Inherited project.project"""
    _inherit = "project.project"
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Si el proyecto esta en seguimiento agrega al consultor que tenga asignado en ese momento a la lista del historico
        """
        if context is None:
            context = {}
        if not ids:
            return True
        if type(ids) != list:
            ids = [ids]
        
        # Funcion original de modificar
        res = super(project_project, self).write(cr, uid, ids, vals, context=context)
        
        log_con_obj = self.pool.get('project.log.consultor')
        cur_date = time.strftime('%Y-%m-%d')
        
        # Recorre los registros a modificar
        for project in self.browse(cr, uid, ids, context=context):
            # Valida que el proyecto se encuentre en estado de seguimiento
            if project.state != 'progress':
                continue
            # Valida que tenga un consultor
            if not project.consultor_id:
                continue
            
            # Valida que no este ya registrado en la lista y pendiente de calificar
            log_ids = log_con_obj.search(cr, uid, [('consultor_id','=',project.consultor_id.id),('project_id','=',project.id),('state','=','draft')], context=context)
            if log_ids:
                continue
            
            # Agrega el nuevo registro
            vals = {
                'date': cur_date,
                'project_id': project.id,
                'consultor_id': project.consultor_id.id,
                'state': 'draft'
            }
            log_con_obj.create(cr, uid, vals, context=context)
        return res
    
    def _get_members(self, cr, uid, project_id, context=None):
        """
            Obtiene los integrantes del proyecto
        """
        project = self.browse(cr, uid, project_id, context=context)
        users = []
        print "************ partner ************ ", project.partner_id
        print "************ partner ************ ", project.partner_id.user_ids
        # Si tiene un emprendedor obtiene el dato del usuario
        if project.partner_id:
            for user in project.partner_id.user_ids:
                users.append(user.id)
        return users
    
    def set_progress_wizard(self, cr, uid, ids, context=None):
        """
            Genera las fases del proyecto y agrega los entregables por fase
        """
        phase_obj = self.pool.get('project.phase')
        template_obj = self.pool.get('project.template.project')
        
        # Obtiene el objeto del proyecto
        project = self.browse(cr, uid, ids[0], context=context)
        # Valida que no se hayan generado fases para el proyecto
        if project.apply_progress:
            # Valida si tiene fases creadas el proyecto
            phase_ids = phase_obj.search(cr, uid, [('project_id','=',project.id)], context=context)
            # Si hay fases activas deja el proceso incompleto
            if phase_ids:
                # Pasa el proyecto a seguimiento
                return self.set_progress(cr, uid, ids, context=context)
        
        # Obtiene los miembros que aplican sobre el proyecto
        member_ids = self._get_members(cr, uid, project.id, context=context)
        if member_ids:
            members = []
            for member in member_ids:
                members.append([4,member])
            
            self.write(cr, uid, [project.id], {'members': members}, context=context)
        #print "************ members ********** ", members
        # Obtiene las plantillas de fases a crear segun aplique 
        template_ids = template_obj.search(cr, uid, [('company_class','=',project.company_class)])
        # Si no hay una plantilla de fases termina el proceso
        if not template_ids:
            # Pasa el proyecto a seguimiento
            return self.set_progress(cr, uid, ids, context=context)
        
        # Agrega al context el proyecto y el template por default
        context.update({
            'default_project_id': project.id,
            'default_template_id': template_ids[0],
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'project_rz_g2', 'create_project_phase_form_view')
        return {
            'name':_("Crear Fases de Proyecto"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'create.project.phase.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            #'res_id' : statement_id, # id of the object to which to redirected
        }
    
    def _get_last_eval(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el resultado de la ultima evaluacion
        """
        if context is None:
            context = {}
        res = {}
        # Recorre los registros
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = False
            for log in project.log_eval_ids:
                res[project.id] = log.result
                break
        return res
    
    def _get_progress(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el porcentaje de avance del proyecto
        """
        task_obj = self.pool.get('project.task')
        
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = {
                'progress_eval': 0.0,
                'progress': 0.0,
            }
            progress = 0.0
            progress_eval = 0.0
            
            task_ids = task_obj.search(cr, uid, [('project_id','=',project.id)])
            if task_ids:
                for task in task_obj.browse(cr, uid, task_ids, context=context):
                    progress += task.progress
                    progress_eval += task.last_log_eval
                
                res[project.id]['progress'] = progress/len(task_ids)
                res[project.id]['progress_eval'] = progress_eval/len(task_ids)
        return res
    
    def _get_last_phase(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el numero de fases terminadas y la fase actual
        """
        phase_obj = self.pool.get('project.phase')
        
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = {
                'last_phase_id': False,
                'num_phase': 0,
            }
            
            # Obtiene el numero de fases terminadas
            phase_ids = phase_obj.search(cr, uid, [('project_id','=',project.id),('state','=','done')], context=context)
            res[project.id]['num_phase'] = len(phase_ids)
            
            # Obtiene la fase que este activa
            phase_ids = phase_obj.search(cr, uid, [('project_id','=',project.id),('state','=','open'),('validate_time','=',True)], context=context)
            if phase_ids:
                res[project.id]['last_phase_id'] = phase_ids[0]
            
        return res
    
    _columns = {
        'company_class': fields.selection([
            ('IDEA','Idea'),
            ('DESA','En desarrollo'),
            ('EXPAN','En expansion')], 'Tipo de Proyecto'),
        'log_consultor_ids': fields.one2many('project.log.consultor', 'project_id', string="Historico Consultorias"),
        'log_eval_ids': fields.one2many('project.log.evaluation.project', 'project_id', string='Evaluaciones'),
        'apply_progress': fields.boolean('Fases creadas'),
        'last_log_eval': fields.function(_get_last_eval, type="selection", selection=[(10,'A'),(9,'B'),
            (8,'C'),(7,'D')], string='Compromiso proyecto'),
        'progress_eval': fields.function(_get_progress, type="float", digits_compute=dp.get_precision('Account'), string='Progreso Evaluador', track_visibility='always', store=False, multi='progress'),
        'progress': fields.function(_get_progress, type="float", digits_compute=dp.get_precision('Account'), string='Progreso Sistema', track_visibility='always', store=False, multi='progress'),
        'last_phase_id': fields.function(_get_last_phase, type="many2one", relation="project.phase", string='Fase Actual', track_visibility='always', store=False, multi='phase'),
        'num_phase': fields.function(_get_last_phase, type="integer", string='Fases terminadas', track_visibility='always', store=False, multi='phase'),
    }
    
    _defaults = {
        'company_class': 'IDEA',
    }

project_project()

class project_phase(osv.Model):
    """Inherited project.phase"""

    _inherit = "project.phase"
    
    def set_open(self, cr, uid, ids, *args):
        """
            Agrega en la funcionalidad que cuando la fase pase a abierto, borre al consultor del proyecto
            Valida que no haya fases abiertas
        """
        log_obj = self.pool.get('project.log.consultor')
        project_ids = []
        # Recorre las fases
        for phase in self.browse(cr, uid, ids):
            # Busca fases abiertas sobre el proyecto
            phase_ids = self.search(cr, uid, [('project_id','=',phase.project_id.id or False),('validate_time','=',True),('state','=','open')])
            if phase_ids:
                num = len(phase_ids)
                raise osv.except_osv(_('Error!'),_("No puede abrir la fase %s, porque hay %s fases abiertas!")%(phase.name,num))
            # Busca si hay consultores sin calificar
            log_ids = log_obj.search(cr, uid, [('project_id','=',phase.project_id.id or False),('state','=','draft')])
            # Si no hay consultores sin calificar agrega el proyecto para borrar a su consultor asignado
            if not log_ids:
                project_ids.append(phase.project_id.id)
        # Elimina los consultores de los proyectos
        if project_ids:
            self.pool.get('project.project').write(cr, uid, project_ids, {'consultor_id': False})
        return super(project_phase, self).set_open(cr, uid, ids, args)
    
    def set_done(self, cr, uid, ids, *args):
        """
            Valida que no haya entregables pendientes ni consultores sin calificar
        """
        task_obj = self.pool.get('project.task')
        log_obj = self.pool.get('project.log.consultor')
        
        for phase in self.browse(cr, uid, ids):
            # Busca entregables pendientes sobre la fase
            task_ids = task_obj.search(cr, uid, [('phase_id','=',phase.id or False),('state','!=','done')])
            if task_ids:
                num = len(task_ids)
                raise osv.except_osv(_('Error!'),_("No puede cerrar la fase %s, porque hay %s entregables pendientes!")%(phase.name,num))
            
            # Valida que no haya consultores sin calificar
            log_ids = log_obj.search(cr, uid, [('project_id','=',phase.project_id.id or False),('state','=','draft')])
            if log_ids:
                raise osv.except_osv(_('Error!'),_("No se puede cerrar la fase, porque hay consultores sin calificar!"))
            
        return super(project_phase, self).set_done(cr, uid, ids)
    
    def _get_progress(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el porcentaje de avance de la fase
        """
        task_obj = self.pool.get('project.task')
        
        res = {}
        for phase in self.browse(cr, uid, ids, context=context):
            res[phase.id] = {
                'progress_eval': 0.0,
                'progress': 0.0,
            }
            progress = 0.0
            progress_eval = 0.0
            
            task_ids = task_obj.search(cr, uid, [('phase_id','=',phase.id)])
            if task_ids:
                for task in task_obj.browse(cr, uid, task_ids, context=context):
                    progress += task.progress
                    progress_eval += task.last_log_eval
                
                res[phase.id]['progress'] = progress/len(task_ids)
                res[phase.id]['progress_eval'] = progress_eval/len(task_ids)
        return res
    
    _columns = {
        # Ya no aplica este proceso por plantilla
        'template_id': fields.many2one('project.phase.template', 'Plantilla', required=False, invisible=True, states={'draft':[('invisible',False)]}),
        'company_class': fields.related('project_id', 'company_class', type="selection", selection=[
            ('IDEA','Idea'),
            ('DESA','En desarrollo'),
            ('EXPAN','En expansion')], store=True, string="Tipo proyecto", readonly=True),
        'validate_time': fields.boolean('Validar fechas', help="Valid que las fechas de las fases no se traslapen"),
        'file_tasks': fields.one2many('project.phase.file.task', 'phase_id', 'Entregables'),
        'file_meetings': fields.one2many('project.phase.file.meeting', 'phase_id', 'Minuta'),
        'progress_eval': fields.function(_get_progress, digits_compute=dp.get_precision('Account'), string='Progreso Evaluador', track_visibility='always', store=False, multi='progress'),
        'progress': fields.function(_get_progress, digits_compute=dp.get_precision('Account'), string='Progreso Sistema', track_visibility='always', store=False, multi='progress'),
        'code': fields.char('Codigo', size=32, required=True),
        'user_id': fields.related('project_id', 'user_id', type='many2one', relation="res.users", string='Evaluador', store=False),
        'partner_id': fields.related('project_id', 'partner_id', type='many2one', relation="res.partner", string='Emprendedor', store=False),
    }
    
    def _check_time_phase(self, cr, uid, ids, context=None):
        """
            Valida que el tiempo de las fechas no choque con otras fases
        """
        # Recorre los registros
        for phase in self.browse(cr, uid, ids, context=context):
            # Checa si debe validar las fechas de las fases
            if phase.validate_time == False:
                continue
            
            # Busca si hay fases que choquen con el periodo inicial
            phase_ids = self.search(cr, uid, [('id','!=',phase.id),('date_start','<=',phase.date_start),('date_end','>=',phase.date_start),('project_id','=', phase.project_id.id or False),('validate_time','=',True)], context=context)
            if phase_ids:
                return False
            # Busca si hay fases que choquen con el periodo final
            phase_ids = self.search(cr, uid, [('id','!=',phase.id),('date_start','<=',phase.date_end),('date_end','>=',phase.date_end),('project_id','=', phase.project_id.id or False),('validate_time','=',True)], context=context)
            if phase_ids:
                return False
        return True

    _constraints = [
        (_check_time_phase, 'Error!\nEl tiempo planteado para la fase no debe chocar con las demas fases del proyecto.', ['date_start','date_end']),
    ]
    
    _defaults = {
        'company_class': 'IDEA', 
        'validate_time': True
    }

project_phase()

class project_task_type(osv.osv):
    _inherit = 'project.task.type'

    _columns = {
        'ticket_ids': fields.many2many('project.ticket', 'project_task_type_ticket_rel', 'type_id', 'ticket_id', 'Ticket'),
    }

project_task_type()

class task(osv.Model):
    """Inherited project.task"""

    _inherit = 'project.task'
    _order = 'project_id,phase_id,sequence'
    
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
            ticket_ids = self.pool.get('project.ticket').name_search(cr, uid, name=ticket_name, context=context)
            if len(ticket_ids) == 1:
                return int(ticket_ids[0][0])
        return None
    
    def action_upload_file(self, cr, uid, ids, context=None):
        """
            Solicita el documento para el cierre del resultado
        """
        task = self.browse(cr, uid, ids[0], context=context)
        
        # Valida si ya hay un archivo adjunto
        check_files = False
        if task.file:
            check_files = True
        
        # Agrega la informacion que va por default en el wizard
        context.update({
            'default_project_id': task.project_id.id,
            'default_phase_id': task.phase_id.id,
            'default_task_id': task.id,
            'default_check_files': check_files
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'project_rz_g2', 'wizard_upload_file_task_form_view')
        return {
            'name':_("Cargar archivo"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'upload.file.task.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            #'res_id' : statement_id, # id of the object to which to redirected
        }
    
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

    def _get_last_eval(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el resultado de la ultima evaluacion
        """
        if context is None:
            context = {}
        res = {}
        # Recorre los registros
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = False
            for log in task.log_eval_ids:
                res[task.id] = log.result
                break
        return res
    
    # Compute: effective_hours, total_hours, progress
    def _hours_get(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        cr.execute("SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_work WHERE task_id IN %s GROUP BY task_id",(tuple(ids),))
        hours = dict(cr.fetchall())
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = {'effective_hours': hours.get(task.id, 0.0), 'total_hours': (task.remaining_hours or 0.0) + hours.get(task.id, 0.0)}
            res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
            res[task.id]['progress'] = 0.0
            if task.state in ('done','cancelled'):
                res[task.id]['progress'] = 100.0
        return res
    
    def _get_task(self, cr, uid, ids, context=None):
        result = {}
        for work in self.pool.get('project.task.work').browse(cr, uid, ids, context=context):
            if work.task_id: result[work.task_id.id] = True
        return result.keys()
    
    _columns = {
        'ticket_id': fields.many2one('project.ticket', 'Ticket', select="1", domain="[('state','!=','request'), ('state','!=','cancel')]"),
        'stage_id': fields.many2one ('project.task.type', 'Stage',
                        track_visibility='onchange',
                        domain="['&', ('fold', '=', False), '|', ('project_ids', '=', project_id), ('ticket_ids', '=', ticket_id)]"),
        'log_eval_ids': fields.one2many('project.log.evaluation.task', 'task_id', string='Evaluaciones'),
        'last_log_eval': fields.function(_get_last_eval, type="float", string='Porcentaje'),
        'file_upload': fields.boolean('Archivo Cargado', readonly=True),
        'file_name': fields.char('Nombre Archivo', readonly=True),
        'file': fields.binary('Archivo', help='Archivo a actualizar', readonly=True),
        'effective_hours': fields.function(_hours_get, string='Hours Spent', multi='hours', help="Computed using the sum of the task work done.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['work_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.work': (_get_task, ['hours'], 10),
            }),
        'remaining_hours': fields.float('Remaining Hours', digits=(16,2), help="Total remaining time, can be re-estimated periodically by the assignee of the task."),
        'total_hours': fields.function(_hours_get, string='Total', multi='hours', help="Computed as: Time Spent + Remaining Time.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['work_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.work': (_get_task, ['hours'], 10),
            }),
        'progress': fields.function(_hours_get, string='Progress (%)', multi='hours', group_operator="avg", help="If the task has a progress of 99.99% you should close the task if it's finished or reevaluate the time",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['work_ids', 'remaining_hours', 'planned_hours','state'], 10),
                'project.task.work': (_get_task, ['hours'], 10),
            }),
        'delay_hours': fields.function(_hours_get, string='Delay Hours', multi='hours', help="Computed as difference between planned hours by the project manager and the total hours of the task.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['work_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.work': (_get_task, ['hours'], 10),
            }),
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids2,
        'file_name': '',
        'file_upload': False
    }

task()
