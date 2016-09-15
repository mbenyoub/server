# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Salda?a (riss_600@hotmail.com)
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

from openerp.osv import osv, fields
from tools.translate import _
import time
from lxml import etree
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp

class prepare_delivery_stock_route_wizard(osv.osv_memory):
    _name = 'prepare.delivery.stock.route'
    
    def action_apply_all(self, cr, uid, ids, context=None):
        """
            Ejecuta la entrega de todos los movimientos del pedido
        """
        print"****EJECUTANDO LA ENTREGA DE TODOS LOS MOVIMIENTOS DEL PEDIDO*****"
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        rline_obj = self.pool.get('delivery.route.line')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        # Obtiene la informacion del wizard
        data = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : date
        }
        picking_type = data.picking_id.type
        # Recorre las lineas a entregar
        for wizard_line in data.line_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id

            # Valida que haya un movimiento relacionado
            if not move_id:
                continue
            # Valida que la cantidad de la linea del pedido no sea negativo
            if wizard_line.product_qty < 0:
                raise osv.except_osv(_('Warning!'), _('No puede hacer entregas de productos sobre cantidades negativas.'))

            # Calcula la cantidad del producto en base a la unidad de medida base
            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.product_qty, line_uom.id)

            # Valida el factor de la linea
            if line_uom.factor and line_uom.factor != 0:
                if float_compare(qty_in_line_uom, wizard_line.product_qty, precision_rounding=line_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('La unidad de redondeo medida no permite que usted envíe "%s %s", solo redondeo de "%s %s" es aceptado por la unidad de medida.') % (wizard_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
            # Valida que el movimiento no este entregado
            if wizard_line.move_id.state != 'done':
                initial_uom = wizard_line.move_id.product_uom
                #Compute the quantity for respective wizard_line in the initial uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.product_qty, initial_uom.id)
                without_rounding_qty = (wizard_line.product_qty / line_uom.factor) * initial_uom.factor
                if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('La unidad de redondeo medida no permite que usted envíe "%s %s", solo redondeo de "%s %s" es aceptado por la unidad de medida.') % (wizard_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
                # Agrega la informacion del producto a entregar
                partial_data['move%s' % (move_id)] = {
                    'product_id': wizard_line.product_id.id or False,
                    'product_qty': wizard_line.product_qty,
                    'product_uom': wizard_line.product_uom.id or False,
                    'prodlot_id': wizard_line.move_id.prodlot_id.id or False,
                }
        # Aplica la salida de almacen sobre los productos a entregar
        picking_obj.do_partial(cr, uid, [data.picking_id.id], partial_data, context=context)
        # Indica que la linea fue entregada
        rline_obj.write(cr, uid, [data.route_line_id.id], {'delivered': True}, context=context)
        # Pone la linea de la ruta como entregado
        rline_obj.action_done(cr, uid, [data.route_line_id.id], context=context)
        return {'type': 'ir.actions.act_window_close'}

    def onchange_picking_id(self, cr, uid, ids, picking_id, context=None):
        """
            Retorna los movimientos a entregar
        """
        move_obj = self.pool.get('stock.move')
        if context is None:
            context={}
        #res = {}
        lines = []
        # Obtiene los movimientos de los productos a cargar en la camioneta
        move_ids = move_obj.search(cr, uid, [('picking_id','=',picking_id)], context=context)
        
        # Genera la lista de movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Informacion de movimiento
            vals = {
                'name': move.name,
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'product_uom': move.product_uom.id or False,
                'location_id': move.location_id.id or False,
                'location_dest_id': move.location_dest_id.id or False,
                'state': move.state,
                'picking_id': picking_id,
                'route_line_id': move.route_line_id.id or False,
                'move_id': move.id
            }
            lines.append(vals)
        
        return {'value': {'line_ids': lines}}
    
    _columns = {
        'route_id': fields.many2one('delivery.route', 'Ruta', readonly=True),
        'route_line_id': fields.many2one('delivery.route.line', 'Linea Ruta', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Movimiento Almacen', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'line_ids': fields.one2many('prepare.delivery.stock.route.line', 'wizard_id', 'Entrega'),
    }
    
prepare_delivery_stock_route_wizard()

class prepare_delivery_stock_route_line_wizard(osv.osv_memory):
    """
        Movimientos de stock
    """
    _name = "prepare.delivery.stock.route.line"
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Aplica la entrega del producto al cliente
        """
        picking_id = False
        res_id = False
        rline_obj = self.pool.get('delivery.route.line')
        move_obj = self.pool.get('stock.move')
        # Recorre las lineas a confirmar para obtener el movimiento
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id:
                # Valida que haya cantidad disponible para hacer la entrega
                if line.product_qty > line.virtual_available:
                    raise osv.except_osv(_('Error'), _("No hay producto disponible para surtir este pedido sobre la ruta la Ruta. (Producto: %s)"%(line.name,)))
                # Pone el producto como cargado en la camioneta
                move_obj.action_done(cr, uid, [line.move_id.id], context=context)
            picking_id = line.picking_id.id or False
            res_id = line.wizard_id.id or False
            route_line_id = line.route_line_id.id or False
        # Revisa si hay movimientos pendientes
        move_ids = move_obj.search(cr, uid, [('picking_id','=',picking_id),('state','not in',['cancel','done'])])
        print "*****MOVE_IDS****: ", move_ids
        if move_ids:
            print "****ENTRANDO A ENTREGAR PRODUCTO*****"
            # Va a la parte de Entregar producto
            return {
                'name': 'Entregar producto',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'prepare.delivery.stock.route',
                'target' : 'new',
                'context': {},
                'type': 'ir.actions.act_window',
                'res_id': res_id
            }
        # Indica que la linea fue entregada
        rline_obj.write(cr, uid, [line.route_line_id.id], {'delivered': True}, context=context)
        for move in rline_obj.browse(cr, uid, [route_line_id], context=context):
            print "*****ENTREGADO WIZARD*****: ", move.delivered
        
        # Pone la linea de la ruta como entregado
        rline_obj.action_done(cr, uid, [route_line_id], context=context)
        return {'type': 'ir.actions.act_window_close'}
    
    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Retorna el producto disponible sobre la tienda
        """
        product_obj = self.pool.get('product.product')
        res = {}
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({ 'states': ('waiting','assigned','done'), 'what': ('in', 'out') })
        #Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context):
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                # Obtiene el id de la ubicacion origen
                if line.location_id:
                    ctx['location'] = line.location_id.id
                # Asigna la stock virtual del producto a la linea del pedido de venta.
                stock = product_obj.get_product_available(cr, uid, [line.product_id.id], context=ctx)
                res[line.id] = stock.get(line.product_id.id, 0.0)
        return res
    
    _columns = {
        'name': fields.char('Descripcion', size=128),
        'wizard_id': fields.many2one('prepare.delivery.stock.route', 'Wizard', ondelete="cascade"),
        'move_id': fields.many2one('stock.move', 'Movimiento Stock', ondelete="cascade", required=True),
        'picking_id': fields.many2one('stock.picking', 'Almacen'),
        'route_line_id': fields.many2one('delivery.route.line', 'Ruta'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'product_qty': fields.float('Cantidad'),
        'product_uom': fields.many2one('product.uom', 'Unidad de medida', ondelete="cascade"),
        'location_id': fields.many2one('stock.location', 'Ubicacion origen', ondelete="set null"),
        'location_dest_id': fields.many2one('stock.location', 'Ubicacion destino', ondelete="set null"),
        'state': fields.related('move_id', 'state', type="selection", selection=[
            ('draft','Por cargar'),
            ('cancel','Cancelado'),
            ('waiting','Esperando otro movimiento'),
            ('confirmed','Esperando disponibilidad'),
            ('assigned','Reservado'),
            ('done','Realizado'),
            ], string='Estado', select=True),
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
    }
    
prepare_delivery_stock_route_line_wizard()