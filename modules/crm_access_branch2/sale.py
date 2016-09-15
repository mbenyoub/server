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

class sale_order_line(osv.Model):
    _inherit = "sale.order"
    
    def onchange_partner_id(self, cr, uid, ids, field, context=None):
        """
            Actualiza la sucursal y pone la sucursal del cliente en el partner
        """
        # Obtiene el valor de la sucursal del padre
        partner = self.pool.get('res.partner').browse(cr, uid, field, context=context)
        return {'value':{'branch_id': partner.branch_id.id}}
    
    _columns = {
        # 'branch_id': fields.many2one('crm.access.branch', 'Sucursal'),
        'branch_id': fields.related('partner_id', 'branch_id', type="many2one", relation="crm.access.branch", store=True, string="Sucursal", readonly=True),
    }
    
    def _get_branch_default_id(self, cr, uid, context=None):
        """
            Obtiene la sucursal del usuario y la pone por default para el cliente
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.branch_id.id or None

    
    _defaults = {
        'branch_id': _get_branch_default_id
    }
    
sale_order_line()
    