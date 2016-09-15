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
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
import pdb
import time

import openerp
from openerp import netsvc, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product

_logger = logging.getLogger(__name__)

class pos_config(osv.osv):
    _inherit = 'pos.config'
    
    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Cliente default'),
        'lot_stock_id': fields.many2one('stock.location', 'Almacen Origen'),
        'lot_output_id': fields.many2one('stock.location', 'Almacen Destino'),
    }
    
pos_config()

class pos_order(osv.osv):
    _inherit = "pos.order"
    _description = "Point of Sale"
    
    def create_picking(self, cr, uid, ids, context=None):
        """
            Crea la salida del almacen de origen y almacen destino
        """
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):
            if not order.state=='draft':
                continue
            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            picking_id = picking_obj.create(cr, uid, {
                'origin': order.name,
                'partner_id': addr.get('delivery',False),
                'type': 'out',
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'note': order.note or "",
                'invoice_state': 'none',
                'auto_picking': True,
            }, context=context)
            self.write(cr, uid, [order.id], {'picking_id': picking_id}, context=context)
            # Almacen de origen y destino por default, definido por la tienda
            location_id = order.shop_id.warehouse_id.lot_stock_id.id
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            
            # Valida si en la configuracion de la terminal tiene configurado un almacen de origen y destino
            if order.session_id.config_id.lot_stock_id:
                location_id = order.session_id.config_id.lot_stock_id.id
            if order.session_id.config_id.lot_output_id:
                output_id = order.session_id.config_id.lot_output_id.id

            for line in order.lines:
                if line.product_id and line.product_id.type == 'service':
                    continue
                if line.qty < 0:
                    location_id, output_id = output_id, location_id

                move_obj.create(cr, uid, {
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uos': line.product_id.uom_id.id,
                    'picking_id': picking_id,
                    'product_id': line.product_id.id,
                    'product_uos_qty': abs(line.qty),
                    'product_qty': abs(line.qty),
                    'tracking_id': False,
                    'state': 'draft',
                    'location_id': location_id,
                    'location_dest_id': output_id,
                }, context=context)
                if line.qty < 0:
                    location_id, output_id = output_id, location_id

            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            picking_obj.force_assign(cr, uid, [picking_id], context)
        return True
    
    def _default_partner(self, cr, uid, context=None):
        so = self.pool.get('pos.session')
        partner_id = False
        session_ids = so.search(cr, uid, [('state','=', 'opened'), ('user_id','=',uid)], context=context)
        if session_ids:
            # Obtiene el partner relacionado a la sesion
            session = so.browse(cr, uid, session_ids[0], context=context)
            partner_id = session.config_id.partner_id.id or False
        return partner_id

    _defaults = {
        'partner_id': _default_partner,
    }

pos_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
