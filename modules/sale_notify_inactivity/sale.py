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
#              Ivan Macias (ivanfallen@gmail.com)
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

class sale_order(osv.Model):
    """ Model for Sale Order """
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(sale_order, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        # Actualiza la actividad de los partners
        sale = self.browse(cr, uid, res, context=context)
        if sale.partner_id:
            partner_obj = self.pool.get('res.partner')
            if sale.partner_id.is_company == True:
                partner_obj._reset_date_notify(cr, uid, sale.partner_id.id, context=context)
            elif sale.partner_id.parent_id:
                partner_obj._reset_date_notify(cr, uid, sale.partner_id.parent_id.id, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de modificar
        super(sale_order, self).write(cr, uid, ids, vals, context=context)
        res = []
        #print "****************** ids *********************** ", ids, type(ids), type(res)
        
        # Valida que el registro sea un arreglo
        if type(ids) == type(res):
            res = ids
        else:
            res = [ids]
        
        # Actualiza la actividad de los partners
        partner_obj = self.pool.get('res.partner')
        for sale in self.browse(cr, uid, res, context=context):
            # Actualiza la actividad de los partners
            if sale.partner_id:
                if sale.partner_id.is_company == True:
                    partner_obj._reset_date_notify(cr, uid, sale.partner_id.id, context=context)
                elif sale.partner_id.parent_id:
                    partner_obj._reset_date_notify(cr, uid, sale.partner_id.parent_id.id, context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
