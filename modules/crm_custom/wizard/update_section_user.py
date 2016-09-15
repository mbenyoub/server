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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _

class update_section_user_wizard(osv.osv_memory):
    """ Actualiza los usuarios de un equipo de ventas especifico """
    _name = 'update.section.user.wizard'
    _description = 'Actualiza'
    
    def action_update_section(self, cr, uid, ids, context=None):
        """
            Valida que la conciliacion con los registros seleccionados sea correcta
        """
        user_obj = self.pool.get('res.users')
        user_ids = []
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            section_id = data.section_id.id
            # Obtiene un arreglo con la lista de usuario a actualizar
            for line in data.user_ids:
                user_ids.append(line.user_id.id)
            
            # Actualiza el equipo de ventas sobre los usuarios
            user_obj.write(cr, uid, user_ids, {'default_section_id': section_id}, context=context)
            
        return True
    
    def onchange_section_id(self, cr, uid, ids, section_id, context=None):
        """
            Actualiza la informacion de los movimientos pendientes de relacionar
        """
        section_obj = self.pool.get('crm.case.section')
        lines = []
        user_ids = []
        if section_id:
            # Obtiene los usuarios que se mostraran sobre el equipo de ventas
            section = section_obj.browse(cr, uid, section_id, context=context)
            if section.user_id:
                user_ids.append(section.user_id.id or False)
            for member in section.member_ids:
                try:
                    user_ids.index(member.id)
                except:
                    user_ids.append(member.id or False)
            
            if user_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for user_id in user_ids:
                    val = {
                        'user_id': user_id,
                    }
                    lines.append(val)
        # Actualiza los valores de retorno
        return {'value': {'user_ids': lines}}
    
    _columns = {
        'section_id': fields.many2one('crm.case.section','Equipo de ventas', select="1", readonly=True, required=True),
        'user_ids':fields.one2many('update.section.user.line.wizard', 'wizard_id', 'Usuarios a asignar a equipo por default'),
        #'user_ids':fields.many2many('res.users', 'update_section_user_rel', 'wizard_id', 'user_id', 'Usuarios a asignar a equipo por default'),
    }

update_section_user_wizard()

class update_section_user_line_wizard(osv.TransientModel):
    _name = 'update.section.user.line.wizard'
    _columns = {
        'wizard_id':fields.many2one('update.section.user.wizard', ' '),
        'user_id': fields.many2one('res.users', 'Usuario', required=True),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
