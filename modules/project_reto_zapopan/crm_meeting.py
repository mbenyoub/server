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

from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _

#
# crm.meeting is defined in module base_calendar
#
class crm_meeting(osv.Model):
    """ Model for CRM meetings """
    _inherit = 'crm.meeting'
    
    def onchange_project(self, cr, uid, ids, project_id, type, context=None):
        """
            Retorna el consultor asignado al proyecto si es una reunion de asesoria
        """
        if context is None:
            context={}
        # Obtiene la informacion del proyecto
        project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
        #print "*************** project *************** ", project
        if not project or not project_id:
            return {}
        if type == 'ase':
            #print "************ project consultor ****************** ", project.consultor_id
            # Si hay un consultor asignado lo inserta
            if project.consultor_id:
                res = {'partner_id': project.consultor_id.id or False, 'consultor_select':True, 'project_id': project_id, 'type': type}
            else:
                # El emprendedor debe seleccionar un consultor
                res = {'partner_id': False, 'consultor_select':False, 'project_id': project_id, 'type': type}
            # Actualiza al emprendedor del proyecto
            if project.partner_id.user_ids:
                    res['user_id'] = project.partner_id.user_ids[0].id
            return {'value':res}
        elif type == 'eval' or type == 'seg':
            # Retorna al emprendedor del proyecto
            return {'value':{'partner_id': project.partner_id.id or False, 'project_id': project_id, 'type': type}}
        return {}
    
    def _get_consultor_default(self, cr, uid, ids, context=None):
        """
            Obtiene el consultor desde el proyecto si es que lo tiene
        """
        res = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.partner_id.type_contact == 'emp':
            project_ids = self.pool.get('project.project').search(cr, uid, [('partner_id','=',user.partner_id.id)], context=context)
            if project_ids:
                project = self.pool.get('project.project').browse(cr, uid, project_ids[0], context=context)
                if project.consultor_id:
                    res = project.consultor_id.id
        return res
    
    def _get_project_default(self, cr, uid, ids, context=None):
        """
            Obtiene el proyecto por default si es un emprendedor
        """
        #print "**************** uid ************ ", uid, " - ", ids
        res = False
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.partner_id.type_contact == 'emp':
            project_ids = self.pool.get('project.project').search(cr, uid, [('partner_id','=',user.partner_id.id)], context=context)
            if project_ids:
                res = project_ids[0]
        return res
    
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
            Indica si el usuario es el administrador del proyecto
        """
        res = {}
        for this_id in ids:
            res[this_id] = False
            if self.pool.get('res.users').has_group(cr, uid, 'base.group_project_reto_zapopan_eval'):
                res[this_id] = True
        return res
    
    def _is_consultor_function(self, cr, uid, ids, field_name, arg, context=None):
        """
            Indica si el usuario es un consultor del proyecto, no tiene permisos para modificar
        """
        res = {}
        for this_id in ids:
            res[this_id] = False
            if self.pool.get('res.users').has_group(cr, uid, 'base.group_project_reto_zapopan_con'):
                res[this_id] = True
        return res
    
    def _get_users(self, cr, uid, ids, field_names=None, arg=None, context=None):
        """
            Lista de usuarios invitados
        """
        res = {}
        if not ids: return res
        
        for meeting in self.browse(cr, uid, ids, context=context):
            user_list = []
            user_list.append(str(meeting.user_id.id))
            if meeting.partner_id.user_ids:
                user_list.append(str(meeting.partner_id.user_ids[0].id))
            for attendee in meeting.attendee_ids:
                if attendee.partner_id.user_ids:
                    user_list.append(str(attendee.partner_id.user_ids[0].id))
            #print "********* usuarios disponibles ********** ", ','.join(user_list)
            res[meeting.id] = ',' + ','.join(user_list) + ','
        return res
    
    def _get_date_string(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el valor de la fecha con texto
        """
        res = {}
        for meeting in self.browse(cr, uid, ids, context=context):
            res[meeting.id] = 'False'
            
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
            
            if meeting.date:
                (anio, mes, dia) = meeting.date.split("-")
                dia = dia[:2]
                res[meeting.id] = dia + mes_texto[mes] + anio
        return res
    
    def _get_date(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la fecha en formato año-mes-dia
        """
        if context is None:
            context = {}
        res = {}
        # Recorre los registros
        for meeting in self.browse(cr, uid, ids, context=context):
            res[meeting.id] = meeting.date
        return res
    
    _columns = {
        'calendar_activity_id': fields.many2one('crm.custom.calendar.activity', 'Actividad calendario', ondelete='cascade'),
        'project_id': fields.many2one('project.project', 'Proyecto', ondelete="set null", required=True),
        'mode': fields.selection([
            ('virtual','Virtual'),
            ('present','Presencial'),], 'Modalidad', required=True),
        'partner_id': fields.many2one('res.partner', 'Contacto', required=True),
        'type': fields.selection([
            ('eval','Evaluacion'),
            ('seg','Seguimiento'),
            ('ase','Asesoria'),
            ('result','Resultados con reto Zapopan'),], 'Tipo', required=True),
        'project_log_meeting_ids': fields.one2many('project.log.meeting', 'meeting_id', string="Bitacora de Reuniones", ondelete="cascade"),
        'is_manager':fields.function(_is_manager_function, type='boolean', string="Manager"),
        'is_consultor':fields.function(_is_consultor_function, type='boolean', string="Consultor"),
        'consultor_select': fields.boolean('Consultor Seleccionado'),
        'user_ids': fields.function(_get_users, type="text", string="Usuarios", store=True),
        'date_string': fields.function(_get_date_string, method=True, store=True, string='Fecha Texto', readonly=True, type='char', size=40, help="Fecha."),
        'date2': fields.function(_get_date, type="date", string='Fecha', track_visibility='always', store=True),
    }
    
    _defaults = {
        'is_manager': _is_manager_default,
        'project_id': _get_project_default,
        'partner_id': _get_consultor_default,
        'mode': 'present',
        'type': 'ase',
        'consultor_select': False
    }
    
    _order = "project_id,date"
    
    def onchange_type(self, cr, uid, ids, type, context=None):
        """
            Retorna el cuestionario
        """
        if context is None:
            context={}
        #print "************* type *************** ", type
        if type == 'ase':
            return {'domain':{'partner_id': [('type_contact','=','con'),('user_ids','!=', False)]}}
        elif type == 'eval' or type == 'seg':
            return {'domain':{'partner_id': [('type_contact','=','emp'),('user_ids','!=', False)]}}
        return {'domain':{'partner_id': []}}
    
    def create(self, cr, uid, vals, context=None):
        """
            Registra una actividad ligada a la reunion para visualizar en el calendario
        """
        add_log = False
        # Agrega a la bitacora un registro para que actualice el evaluador y otro para que lo haga el consultor
        if vals.get('project_log_meeting_ids', []) == []:
            add_log = True
            logs = []
            # Revisa si hay mas consultores en los invitados
            if vals.get('attendee_ids',False):
                for attendee in vals.get('attendee_ids',[]):
                    partner = self.pool.get('res.partner').browse(cr, uid, attendee[2]['partner_id'], context=None)
                    if partner.type_contact == 'con':
                        if vals.get('type','ase') == 'ase':
                            raise osv.except_osv(_('Warning!'), _('No puede agregar mas de un consultor como invitado a la reunion de Asesoria!. (Consultor: ' + partner.name + ')'))
                        else:
                            if len(partner.user_ids):
                                logs.append([0, False, {'date': vals.get('date',context.get('default_date')), 'user_id': partner.user_ids[0].id, 'time': vals.get('duration',context.get('default_duration')), 'type': 'consulting', 'project_id': vals.get('project_id',context.get('default_project_id'))}])
                                vals['consultor_select'] = True
            vals['project_log_meeting_ids'] = logs
        
        # Pone que el consultor fue seleccionado sobre la reunion para que el emprendedor no pueda cambiarlo
        if vals.get('type','ase') == 'ase':
            vals['consultor_select'] = True
            #print "*********** partner_id ********** ", vals.get('partner_id')
            #print "*********** default partner_id ********** ", vals.get('default_partner_id')
        
        # Funcion original de crear
        res = super(crm_meeting, self).create(cr, uid, vals, context=context)
        
        #Obtiene el objeto reunion creado
        meeting = self.browse(cr, uid, res, context=context)
        
        #log = self.pool.get('project.log.meeting')
        
        ## Agrega a la bitacora un registro para que actualice el evaluador y otro para que lo haga el consultor
        #if meeting.project_log_meeting_ids == [] or add_log:
        #    # Agrega el log para el evaluador
        #    if meeting.type != 'ase':
        #        log.create(cr, uid, {'date': meeting.date, 'user_id': meeting.user_id.id, 'meeting_id': meeting.id, 'time': meeting.duration, 'type': 'draft', 'project_id': meeting.project_id.id}, context=context)
        #    # Agrega el log para el consultor en la reunion de asesoria
        #    else:
        #        user_ids = meeting.partner_id.user_ids
        #        if user_ids:
        #            log.create(cr, uid, {'date': meeting.date, 'user_id':user_ids[0].id, 'meeting_id': meeting.id, 'time': meeting.duration, 'type': 'consulting', 'project_id': meeting.project_id.id}, context=context)
        # Al ser reunion de asesoria le asigna al emprendedor el consultor que selecciono para que trabaje con el
        if meeting.type == 'ase' and meeting.consultor_select:
            self.pool.get('project.project').write(cr, uid, [meeting.project_id.id], {'consultor_id': meeting.partner_id.id})
        
        #~ Revisa que la reunion no tenga una actividad
        if meeting.calendar_activity_id:
            return res
        
        #~ Valida que el objeto crm.meeting se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.meeting'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Reunion', 'object': 'crm.meeting', })
        
        # Crea el registro de actividad para ver en el calendario
        meeting = self.browse(cr, uid, res, context=context)
        reference = 'crm.meeting,' + str(meeting.id)
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_id = activity_obj.create(cr, uid, {
            'name': meeting.name,
            'date': meeting.date,
            'user_id': meeting.user_id.id,
            'category': 'Reunion',
            'reference': reference
            }, context=context)
        # Actualiza el registro de reunion para agregar el id de la actividad
        self.write(cr, uid, [meeting.id], {'calendar_activity_id': activity_id,}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza una actividad ligada a la reunion para visualizar en el calendario
        """
        # Valida que el emprendedor no cambie la fecha de las reuniones de seguimiento y evaluacion
        if vals.get('date',False) or vals.get('duration',False):
            for meeting in self.browse(cr, uid, ids, context):
                # Valida que si no es reunion de asesoria, que no se cambie la fecha
                if meeting.type != 'ase' and not self.pool.get('res.users').has_group(cr, uid, 'base.group_project_reto_zapopan_eval'):
                    raise osv.except_osv(_('Warning!'), _('No puedes cambiar la informacion de la reunion, para realizar algun cambio sobre esta reunion contacta al administrador!'))
        
        # Funcion original de modificar
        super(crm_meeting, self).write(cr, uid, ids, vals, context=context)
        
        # Si se cambia el consultor, valida que el consultor este en los invitados y si no lo crea
        if len(ids) == 1:
            res = False
            partner_ids = []
            meeting = self.browse(cr, uid, ids[0], context=context)
            if meeting.partner_id:
                # Agrupa los registros de los invitados
                for partner in meeting.partner_ids:
                    if partner.id == meeting.partner_id.id:
                        res = True
                        break
                    partner_ids.append(partner.id)
                
                if not res:
                    #~ Si no esta en las referencias agrega el registro
                    partner_ids.append(meeting.partner_id.id)
                    vals = {'partner_ids': [[6, False, partner_ids]]}
                    super(crm_meeting, self).write(cr, uid, ids, vals, context=context)
                    
        if vals.get('calendar_activity_id'):
            return True
        
        #~ Valida que el objeto crm.meeting se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.meeting'),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Reunion', 'object': 'crm.meeting', })
        
        # Actualiza el registro de actividad para ver en el calendario
        for meeting in self.browse(cr, uid, ids, context=context):
            activity_obj = self.pool.get('crm.custom.calendar.activity')
            # Si no existe el registro lo crea
            if not meeting.calendar_activity_id:
                reference = 'crm.meeting,' + str(meeting.id)
                activity_id = activity_obj.create(cr, uid, {
                    'name': meeting.name,
                    'date': meeting.date,
                    'user_id': meeting.user_id.id,
                    'category': 'Reunion',
                    'reference': reference
                    }, context=context)
                # Actualiza el registro de reunion para agregar el id de la actividad
                self.write(cr, uid, [meeting.id], {'calendar_activity_id': activity_id,}, context=context)
            else:
                # Si existe actualiza la informacion
                activity_id = activity_obj.write(cr, uid, [meeting.calendar_activity_id.id], {
                    'name': meeting.name,
                    'date': meeting.date,
                    'user_id': meeting.user_id.id
                    }, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Elimina el registro del calendario de actividades
        """
        #print "**************** funcion unlink ************************** "
        activity_obj = self.pool.get('crm.custom.calendar.activity')
        activity_delete = []
        #~ Elimina el registro relacionado con el
        for meeting in self.browse(cr, uid, ids, context=context):
            if meeting.calendar_activity_id:
                activity_delete.append(meeting.calendar_activity_id.id)
                #print "***************** Eliminado documento relacionado ", meeting.calendar_activity_id.id
        # Elimina los registros y sus dependencias
        res = super(crm_meeting, self).unlink(cr, uid, ids, context=context)
        activity_obj.unlink(cr, uid, activity_delete, context=context)
        return res

class calendar_attendee(osv.osv):
    """
    Calendar Attendee Information
    """
    _inherit = 'calendar.attendee'
    
    def do_accept(self, cr, uid, ids, context=None, *args):
        """
        Update state of invitation as Accepted and if the invited user is other
        then event user it will make a copy of this event for invited user.
        @param cr: the current row, from the database cursor
        @param uid: the current user's ID for security checks
        @param ids: list of calendar attendee's IDs
        @param context: a standard dictionary for contextual values
        @return: True
        """
        if context is None:
            context = {}
        
        # Cambia el estado de la invitacion a aceptado
        self.write(cr, uid, ids, {'state': 'accepted'}, context)
        return True

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
