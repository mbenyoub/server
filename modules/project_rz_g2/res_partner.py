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
    
    def action_open_meeting(self, cr, uid, ids, context=None):
        """
            Redirecciona al calendario para crear reuniones de seguimiento para el consultor
        """
        project_obj = self.pool.get('project.project')
        
        # Obtiene el id del contacto
        partner_id = self.browse(cr, uid, ids[0], context=context).id
        
        # Valida que el usuario no sea consultor
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.type_contact == 'con':
            raise osv.except_osv(_('Aviso!'),_("El emprendedor debe crear la reunion de seguimiento!"))
        elif user.type_contact == 'emp':
            # Obtiene el proyecto sin consultor asignado del emprendedor
            project_ids = project_obj.search(cr, uid, [('partner_id','=',user.partner_id.id),('consultor_id','=',False)], context=context)
            # Valida que se haya encontrado un proyecto sin consultor
            if not project_ids:
                raise osv.except_osv(_('Aviso!'),_("Ya hay un consultor asignado. Si desea cambiar de consultor, contacte con su evaluador!"))
            context['default_project_id'] = project_ids[0]
        
        context['default_type'] = 'ase'
        context['default_partner_id'] = partner_id
        
        # Obtiene la vista formulario de contactos
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'base_calendar', 'view_crm_meeting_calendar')
        res_id = res and res[1] or False
        #~ Redirecciona al formulario de solicitud
        return {
            'name':_("Reunion de Asesoria"),
            'view_type': 'form',
            'view_mode': 'calendar',
            'view_id': res_id,
            'res_model': 'crm.meeting', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'context': context,
            #'res_id' : partner_id, # id of the object to which to redirected
        }
    
    _columns = {
        'type_contact': fields.selection([
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor'),
            ('otr','Otro')], 'Tipo'),
    }
    
    _defaults = {
        'type_contact': 'otr',
    }
    
res_partner()

class res_partner_read(osv.Model):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner.read'
    
    def action_open_meeting(self, cr, uid, ids, context=None):
        """
            Redirecciona al calendario para crear reuniones de seguimiento para el consultor
        """
        project_obj = self.pool.get('project.project')
        
        # Obtiene el id del contacto
        partner_id = self.browse(cr, uid, ids[0], context=context).id
        
        # Valida que el usuario no sea consultor
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.type_contact == 'con':
            raise osv.except_osv(_('Aviso!'),_("El emprendedor debe crear la reunion de seguimiento!"))
        elif user.type_contact == 'emp':
            # Obtiene el proyecto sin consultor asignado del emprendedor
            project_ids = project_obj.search(cr, uid, [('partner_id','=',user.partner_id.id),('consultor_id','=',False)], context=context)
            # Valida que se haya encontrado un proyecto sin consultor
            if not project_ids:
                raise osv.except_osv(_('Aviso!'),_("Ya hay un consultor asignado. Si desea cambiar de consultor, contacte con su evaluador!"))
            context['default_project_id'] = project_ids[0]
        
        context['default_type'] = 'ase'
        context['default_partner_id'] = partner_id
        
        # Obtiene la vista formulario de contactos
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'base_calendar', 'view_crm_meeting_calendar')
        res_id = res and res[1] or False
        #~ Redirecciona al formulario de solicitud
        return {
            'name':_("Reunion de Asesoria"),
            'view_type': 'form',
            'view_mode': 'calendar',
            'view_id': res_id,
            'res_model': 'crm.meeting', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'context': context,
            #'res_id' : partner_id, # id of the object to which to redirected
        }
    
    _columns = {
        'type_contact': fields.selection([
            ('emp','Emprendedor'),
            ('eval','Evaluador'),
            ('con','Consultor'),
            ('otr','Otro')], 'Tipo'),
    }
    
    _defaults = {
        'type_contact': 'otr',
    }
    
res_partner_read()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
