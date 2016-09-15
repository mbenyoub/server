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

class res_partner(osv.osv):
    """ Inherits partner and add extra information kober """
    _inherit = 'res.partner'
    
    def onchange_parent_id(self, cr, uid, ids, field, context=None):
        """
            Actualiza la sucursal y pone la sucursal del padre en el partner
        """
        # Obtiene el valor de la sucursal del padre
        partner = self.browse(cr, uid, field, context=context)
        return {'value':{'branch_id': partner.branch_id}}
    
    _columns = {
        'branch_id': fields.many2one('crm.access.branch', 'Sucursal', required=True),
    }
    
    def _get_branch_default_id(self, cr, uid, context=None):
        """
            Obtiene la sucursal del usuario y la pone por default para el cliente
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.branch_id.id or None
    
    def _get_default_user(self, cr, uid, context=None):
        """
            Retorna el id del usuario activo
        """
        return uid
    
    _defaults = {
        'branch_id': _get_branch_default_id,
        'user_id': _get_default_user
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
