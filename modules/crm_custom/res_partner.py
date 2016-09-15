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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Partner
# ---------------------------------------------------------

class res_partner(osv.Model):
    _inherit = 'res.partner'
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Ejecuta funcion de duplicar
        """
        if default is None:
            default = {}
        default.update({
            'child_ids': []
        })
        res = super(res_partner, self).copy(cr, uid, id, default, context=context)
        return res
    
    def onchange_user_id(self, cr, uid, ids, user_id, context=None):
        """
            Agrega el Equipo de ventas del vendedor asignado
        """
        res = {'section_id': False}
        # Valida que exista el usuario
        if user_id:
            user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
            res['section_id'] = user.default_section_id.id or False
            
        return {'value': res}
    
    def _get_user_default(self, cr, uid, context=None):
        """
            Retorna el id del usuario por default
        """
        return uid
    
    def _get_pricelist_partner(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la lista de precio del cliente
        """
        result = {}
        for partner in self.browse(cr, uid, ids, context=context):
            result[partner.id] = partner.property_product_pricelist.id or False
        return result
    
    _columns = {
        'pricelist_id': fields.function(_get_pricelist_partner, type='many2one', store=True, relation='product.pricelist', string='Lista de precio'),
    }
    
    _defaults = {
        'user_id': _get_user_default
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
