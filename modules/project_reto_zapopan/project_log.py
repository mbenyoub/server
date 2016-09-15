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
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Bitacora
# ---------------------------------------------------------

class project_log_meeting(osv.Model):
    _name = "project.log.meeting"

    def action_validate_consulting(self, cr, uid, ids, context=None):
        """
            Valida que se llevo a cabo la consultoria
        """
        self.write(cr, uid, ids, {'confirm_time':'valid'})
        return True
    
    def action_decline_consulting(self, cr, uid, ids, context=None):
        """
            Marca como invalida la consultoria
        """
        self.write(cr, uid, ids, {'confirm_time':'invalid'})
        return True
    
    def action_make_meeting(self, cr, uid, ids, context=None):
        """
            Genera una nueva reunion
        """
        meeting = self.browse(cr, uid, ids[0], context=context).meeting_id
        res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid, 'base_calendar', 'action_crm_meeting', context)
        res['context'] = {
            'default_partner_id': meeting.partner_id and meeting.partner_id.id or False,
            'default_user_id': meeting.user_id and meeting.user_id.id or False,
            'default_state': 'open',
            'default_name': meeting.name,
            'default_project_id': meeting.project_id and meeting.project_id.id or False,
            'default_type': meeting.type
        }
        return res
    
    def onchange_project(self, cr, uid, ids, project_id, meeting_id, context=None):
        """
            Limpia la reunion si no es del proyecto
        """
        if context is None:
            context={}
        if not project_id:
            return {'value':{'meeting_id': meeting_id}, 'domain':{'meeting_id': []}}
        meeting_ids = self.pool.get('crm.meeting').search(cr, uid, [('project_id','=',project_id),('id','=',meeting_id)], context=context)
        if not meeting_ids:
            return {'value':{'meeting_id': False}, 'domain':{'meeting_id': [('project_id','=',project_id)]}}
        return {'value':{'meeting_id': meeting_id}, 'domain':{'meeting_id': []}}
    
    def onchange_meeting(self, cr, uid, ids, meeting_id, context=None):
        """
            Retorna el proyecto asignado de la reunion
        """
        if context is None:
            context={}
        project_id = self.pool.get('crm.meeting').browse(cr, uid, meeting_id, context=context).project_id.id
        return {'value':{'project_id': project_id}, 'domain':{'meeting_id': [('project_id','=',project_id)]}}

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
    
    def _get_type_contact(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el tipo de contacto que registro el campo en la bitacora
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            res[log.id] = False
            
            if log.user_id.partner_id.type_contact:
                res[log.id] = log.user_id.partner_id.type_contact
        return res

    def _get_user(self, cr, uid, ids, context=None):
        """
            Regresa el usuario activo
        """
        return uid
    
    def _is_manager_default(self, cr, uid, ids, context=None):
        """
            Indica si el usuario es el administrador del proyecto
        """
        res = False
        if self.pool.get('res.users').has_group(cr, uid, 'project.group_project_manager'):
            res = True
        return res
    
    def _is_manager_function(self, cr, uid, ids, field_name, arg, context=None):
        """
            Indica si el usuario es el administrador del proyecto
        """
        res = {}
        for this_id in ids:
            res[this_id] = False
            if self.pool.get('res.users').has_group(cr, uid, 'project.group_project_manager'):
                res[this_id] = True
        return res
    
    def _get_emprendedor_ids(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa los emprendedores del proyecto
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            members = []
            for member in log.meeting_id.project_id.members:
                members.append([member.id])
            res[log.id] = members
        return res

    _columns = {
        'user_id': fields.many2one('res.users', 'Creado por', select="1"),
        'meeting_id' : fields.many2one('crm.meeting', string='Reunion', help="Reunion a la que hace referencia la actividad"),
        'date' : fields.date(string='Fecha', required=True),
        'date_string': fields.function(_get_date_string, method=True, store=True, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
        'time' : fields.float(string='Duracion', required=True),
        'description' : fields.text(string="Descripcion", help='Informacion adicional sobre el movimiento'),
        'project_id': fields.related('meeting_id', 'project_id', type="many2one", relation="project.project", store=True, string="Proyecto"),
        'type': fields.selection([
            ('draft','Pendiente'),
            ('done','Realizada'),
            ('consulting','Consultoria'),
            ('absent','Inasistencia'),
            ('modify','Modificada'),
            ('cancel','Cancelada')], 'Tipo'),
        'type_contact': fields.function(_get_type_contact, method=True, store=True, type="selection", string='Tipo Contacto', selection=[
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor')], readonly=True),
        'confirm_time': fields.selection([
            ('no','Sin confirmar'),
            ('valid','Confirmado'),
            ('invalid','No Valido'),], 'Confirmacion', readonly=True, help="Confirmacion del Emprendedor sobre el evento registrado"),
        'is_manager':fields.function(_is_manager_function, type='boolean', string="Manager"),
        'emprendedor_ids': fields.related('project_id', 'members', type="many2many", relation='res.users', table='project_user_rel', string='Project Members'),
        'type_meeting': fields.related('meeting_id', 'type', type="char", store=True, string="Tipo Reunion", readonly=True),
    }

    _defaults = {
        'date' : fields.date.today,
        'user_id': _get_user,
        'type': 'draft',
        'project_id': lambda self, cr, uid, context: context.get('default_project_id', False),
        'is_manager': _is_manager_default,
        'confirm_time': 'no'
    }

    _order = 'type_contact, id desc'

project_log_meeting()

class project_log_project(osv.Model):
    _name = "project.log.project"

    def onchange_project(self, cr, uid, ids, project_id, phase_id, context=None):
        """
            Limpia la fase si no es del proyecto
        """
        if context is None:
            context={}
        if not project_id:
            return {'value':{'phase_id': phase_id}, 'domain':{'phase_id': []}}
        phase_ids = self.pool.get('project.phase').search(cr, uid, [('project_id','=',project_id),('id','=',phase_id)], context=context)
        if not phase_ids:
            return {'value':{'phase_id': False}, 'domain':{'phase_id': [('project_id','=',project_id)]}}
        return {'value':{'phase_id': phase_id}, 'domain':{'phase_id': []}}
    
    def onchange_phase(self, cr, uid, ids, phase_id, context=None):
        """
            Retorna el proyecto asignado de la fase
        """
        if context is None:
            context={}
        project_id = self.pool.get('project.phase').browse(cr, uid, phase_id, context=context).project_id.id
        return {'value':{'project_id': project_id}, 'domain':{'phase_id': [('project_id','=',project_id)]}}

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
    
    def _get_type_contact(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el tipo de contacto que registro el campo en la bitacora
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            res[log.id] = False
            
            if log.user_id.partner_id.type_contact:
                res[log.id] = log.user_id.partner_id.type_contact
        return res

    def _get_user(self, cr, uid, ids, context=None):
        """
            Regresa el usuario activo
        """
        return uid

    _columns = {
        'user_id': fields.many2one('res.users', 'Created By', readonly=True),
        'project_id' : fields.many2one('project.project', string='Proyecto', required=True, help="Referencia la actividad del proyecto"),
        'date' : fields.date(string='Fecha', required=True),
        'date_string': fields.function(_get_date_string, method=True, store=True, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
        'time' : fields.float(string='Duracion', required=True),
        'description' : fields.text(string="Descripcion", help='Informacion adicional sobre el movimiento'),
        'type_contact': fields.function(_get_type_contact, method=True, store=True, type="selection", string='Tipo Contacto', selection=[
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor')], readonly=True),
        'phase_id': fields.many2one('project.phase', 'Fase Proyecto')
    }

    _defaults = {
        'date' : fields.date.today,
        'user_id': _get_user,
    }

    _order = 'id desc'

project_log_project()
