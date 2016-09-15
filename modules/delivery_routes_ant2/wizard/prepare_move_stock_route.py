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

class prepare_move_stock_route_wizard(osv.osv_memory):
    _name = 'prepare.move.stock.route'
    
    def onchange_route_id(self, cr, uid, ids, route_id, context=None):
        """
            Retorna los movimientos a entregar
        """
        move_obj = self.pool.get('stock.move')
        if context is None:
            context={}
        #res = {}
        lines = []
        # Obtiene los movimientos de los productos a cargar en la camioneta
        move_ids = move_obj.search(cr, uid, [('route_id','=',route_id)], context=context)
        #print "****************** valores ruta ***************** ", move_ids
        #res['move_ids'] = move_ids
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
                'route_id': route_id,
                'move_id': move.id
            }
            lines.append(vals)
        
        return {'value': {'line_ids': lines}}
    
    _columns = {
        'route_id': fields.many2one('delivery.route', 'Ruta', readonly=True),
        #'move_ids': fields.many2many('stock.move', 'wizard_evaluation_rel', 'wizard_id', 'route_id', 'Embarque'),
        'line_ids': fields.one2many('prepare.move.stock.route.line', 'wizard_id', 'Embarque'),
    }
    
prepare_move_stock_route_wizard()

class prepare_move_stock_route_line_wizard(osv.osv_memory):
    """
        Movimientos de stock
    """
    _name = "prepare.move.stock.route.line"
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Prepara la carga al vehiculo
        """
        print"PREPARANDO LA CARGA AL VEHICULO****"
        route_id = False
        res_id = False
        #print "**************** prepara la carga ****************** ", ids
        move_obj = self.pool.get('stock.move')
        # Recorre las lineas a confirmar para obtener el movimiento
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id:
                # Valida que haya cantidad disponible para hacer la entrega
                if line.product_qty > line.virtual_available:
                    raise osv.except_osv(_('Error'), _("No hay producto disponible para surtir este pedido sobre la ruta la Ruta. (Producto: %s)"%(line.name,)))
                print "****PONIENDO EL PRODUCTO COMO CARGADO EN LA CAMIONETA"
                # Pone el producto como cargado en la camioneta
                move_obj.action_done(cr, uid, [line.move_id.id], context=context)
            route_id = line.route_id.id or False
            res_id = line.wizard_id.id or False
            #print "************* linea *************** ", line
        # Revisa si hay movimientos pendientes
        move_ids = move_obj.search(cr, uid, [('route_id','=',route_id),('state','not in',['cancel','done'])])
        if move_ids:
            # Va a la parte de Preparar embarque
            return {
                'name': 'Preparar Embarque',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'prepare.move.stock.route',
                'target' : 'new',
                'context': {'default_route_id': route_id},
                'type': 'ir.actions.act_window',
                'res_id': res_id
            }
        return self.pool.get('delivery.route').update_stock(cr, uid, [route_id], context=context)
    
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
        'wizard_id': fields.many2one('prepare.move.stock.route', 'Wizard', ondelete="cascade"),
        'move_id': fields.many2one('stock.move', 'Movimiento Stock', ondelete="cascade", required=True),
        'route_id': fields.many2one('delivery.route', 'Ruta'),
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
    
prepare_move_stock_route_line_wizard()