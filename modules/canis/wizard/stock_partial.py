# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
# -----MODIFICACION 21/04/2015-----
#   Modificacion del metodo o funcion 'do_partial', se agrego 'cr.commit()' para mostrar el mensaje de
#   error y cambiar de estado a 'esperando autorizacion' cuando se excede del limite de peso esperado

from openerp.osv import osv, fields
from openerp.tools.float_utils import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc


class stock_partial_picking_line(osv.TransientModel):
    _inherit = 'stock.partial.picking.line'    
    
    _columns = {
        # 'weight_real_order': fields.related('move_id', 'weight_real_order', type='float',
        #     string='Peso real', store=True),
        # 'weight_real_order': fields.float('Peso real'),
        'to_weight_product': fields.boolean('Pesar'),
        'weight_in': fields.float('Pesada entrada'),
        'weight_out': fields.float('Pesada salida'),
    }
    
    
stock_partial_picking_line()


class stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'
    
    # -------MODIFICACION 15/04/2015------------
    def _raise(self, exc, attrib=None):
        self.__compile_function([], True, _MeProxyError(self, attrib, exc))
        raise exc
    # -----------------------------------------
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        allow = context and context.get('allowed', False) or False
        picking_ids = context and context.get('active_ids', [])
        
        if 'allowed' in fields:
            res.update({'allowed': allow})
            
        # print "****RES*****: ", res 
        return res
    
    # ----------MODIFICACION 15/04/2015-----------
    def _partial_move_for(self, cr, uid, move):
        print "****QUANTITY MOVE****: ", move.weight_real_order
        print "****STATE MOVE****: ", move.state
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' : move.weight_real_order if move.state == 'assigned' or move.state == 'confirmed' else 0,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
            'to_weight_product': move.to_weight_product,
            'weight_in': move.weight_in,
            'weight_out': move.weight_out,
        }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move
    #-------------------------------------
    
    def _do_partial(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        
        for wizard_line in partial.move_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id
        #Quantiny must be Positive
            if wizard_line.quantity < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))
    
            #Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)
    
            if line_uom.factor and line_uom.factor <> 0:
                if float_compare(qty_in_line_uom, wizard_line.quantity, precision_rounding=line_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only rounding of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
            if move_id:
                #Check rounding Quantity.ex.
                #picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
                #partial delivery: 253g
                #=> result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
                initial_uom = wizard_line.move_id.product_uom
                #Compute the quantity for respective wizard_line in the initial uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
                without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
                if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only rounding of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
            else:
                seq_obj_name =  'stock.picking.' + picking_type
                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uom': wizard_line.product_uom.id,
                                                    'prodlot_id': wizard_line.prodlot_id.id,
                                                    'location_id' : wizard_line.location_id.id,
                                                    'location_dest_id' : wizard_line.location_dest_id.id,
                                                    'picking_id': partial.picking_id.id
                                                    },context=context)
                stock_move.action_confirm(cr, uid, [move_id], context)
            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.quantity,
                'product_uom': wizard_line.product_uom.id,
                'prodlot_id': wizard_line.prodlot_id.id,
            }
            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
                                                                  product_currency=wizard_line.currency.id)
        # print "****PARTIAL_DATA********: ", partial_data
        stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
    
    def do_partial(self, cr, uid, ids, context=None):
        """
            Boton para realizar la recepcion de mercancia
        """
        tolerance_quantity = 0.0
        tolerance_product = 0.0
        difference = 0.0
        picking_in_obj = self.pool.get('stock.picking.in')
        move_obj = self.pool.get('stock.move')
        partial = self.browse(cr, uid, ids[0], context=context)
        
        for wizard_line in partial.move_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id
            
            allow = partial.allowed
            
            if allow is True:
                print "****REALIZANDO LA RECEPCION****"
                return self._do_partial(cr, uid, ids, context=context)
            
            picking_in_srch = picking_in_obj.search(cr, uid,
                [('id', '=', wizard_line.move_id.picking_id.id or False)], context=context)
            
            # ------MODIFICACION 15/04/2015---------------
            
            # Obteniendo la cantidad de producto de la orden de entrada
            move_srch = move_obj.search(cr, uid, [('picking_id', '=', picking_in_srch),
                ('product_id', '=', wizard_line.product_id.id or False)], context=context)            
            quantity = move_obj.browse(cr, uid, move_srch[0], context=context)['product_qty']
            tolerance_product = quantity * (wizard_line.product_id.tolerance_percent / 100)
            
            
            # -----------------------------------------------
            
            # Validando si el producto fue pesado o no para seguir con el procedimiento de la entrega
            if wizard_line.to_weight_product is True:
                
                # Validando que el producto fue pesado
                if wizard_line.weight_in > 0.0 and wizard_line.weight_out > 0.0:
        
                    # Obteniendo la diferencia entre el peso real y la cantidad del producto en la
                    # orden de entrada
                    difference = wizard_line.quantity - quantity
                    
                    # Validando si el valor absoluto de la diferencia es mayor al porcentaje de tolerancia del
                    # producto para recibirlo
                    if tolerance_product >= abs(difference):
                        # print "******CANTIDAD DENTRO DE LA TOLERANCIA DEL PRODUCTO**********"
                        super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
                    else:
                        self.pool.get('stock.picking.in').write(cr, uid, picking_in_srch,
                            {'state': 'allow'}, context=context)
                        cr.commit()
                        raise osv.except_osv(_('Error!'), _('Se excede el limite de tolerancia'))
                        # return {'warning': warning}
                else:
                    raise osv.except_osv(_('Error'), _('Producto no pesado'))
            else:
                # print "*****PRODUCTO NO PESABLE*****"
                return super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
                
    _columns = {
        'allowed': fields.boolean('Permitido'),
        }
        
stock_partial_picking()