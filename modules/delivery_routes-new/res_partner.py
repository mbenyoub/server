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
import base64
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class res_partner(osv.Model):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner'
    
    def _default_delivery_schedule(self, cr, uid, context=None):
        """
            Función para colocar el horario de entrega por default
        """
        prop = self.pool.get('ir.property').get(cr, uid, 'delivery_schedule_property', 'delivery.schedule', context=context)
        
        print "**********PROP***********: ", prop
        
        return prop and prop.id or False
        
    
    _columns = {
        'property_delivery_zone': fields.property(
            'delivery.zone',
            type='many2one',
            relation='delivery.zone',
            string ='Zona',
            view_load=True,
            help="Zona donde se encuentra el cliente"),
        'property_delivery_term': fields.property(
            'delivery.term',
            type='many2one',
            relation='delivery.term',
            string ='Plazo de entrega',
            view_load=True,
            help="Se utilizara este plazo de entrega predeterminado para los pedidos de venta y salidas de almacen"),
        'schedule_id': fields.property('schedule.client',
            type='many2one',
            relation='delivery.schedule',
            string='Horario de entrega',
            view_load=True,
            help="Se utilizará este horario para la entrega de producto"),
        'deliver_zone':   fields.char('Delivery Zone', size= 64),
        'carrier_bol': fields.boolean('Transportista'),
        'concept_id': fields.many2one('product.product', 'Concepto'),
    }
    
    _defaults = {
        'schedule_id': _default_delivery_schedule
    }
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
