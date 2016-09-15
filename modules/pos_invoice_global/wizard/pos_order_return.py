# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas(joropeza@akkadian.com.mx)
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
from openerp import netsvc
import time

from openerp.osv import osv,fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class pos_order_return_memory(osv.osv_memory):
    
    #def onchange_validar(self, cr, uid, ids, quantity) :
    #      return{
    #        'value' :{ 'quantity':34},
    #         } 
      
      
    _name = 'pos.order.return.memory'
    _rec_name = "product_id"
    _columns = {
        'product_id': fields.many2one('product.product', 'Producto'),
        'quantity': fields.float('Cantidad'),
        'move_id' : fields.many2one('stock.move', "Movimientos almacen"),
        'wizard_id': fields.many2one('pos.order.return', 'wizard')
    }
pos_order_return_memory()


class pos_order_return(osv.osv_memory):
    _name = 'pos.order.return'
    
    _columns = {
        'pos_order_moves': fields.one2many('pos.order.return.memory', 'wizard_id', 'Productos a devolver'),
        'pos_order_state': fields.selection([
            ('draft', 'Nuevo'),
            ('picking', 'Entregado'),
            ('to_paid', 'Pendiente de pago'),
            ('paid', 'Pagado'),
            ('return', 'En devolicion'),
            ('done', 'Contabilizado'),
            ('global', 'Aplicando factura global'),
            ('cancel', 'Cancelado'),
            ('invoiced', 'Facturado')])
    }
    
    
    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        res = super(pos_order_return, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        pos_obj = self.pool.get('pos.order')
        
        pos = pos_obj.browse(cr, uid, record_id, context=context)
        if pos:
            return_history = self.get_return_history(cr, uid, record_id, context)       
            for line in pos.lines:
                qty = line.qty - return_history.get(line.id, 0)
                if line.qty > 0:
                    result1.append({'product_id': line.product_id.id, 'quantity': line.qty, 'move_id':line.id})
            #print "*****RESULT1*****: ", result1
            if 'pos_order_moves' in fields:
                res.update({'pos_order_moves': result1})
        return res
    
    def get_return_history(self, cr, uid, pick_id, context=None):
        """ 
         Get  return_history.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param pick_id: Picking id
         @param context: A standard dictionary
         @return: A dictionary which of values.
        """
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, pick_id, context=context)
        return_history = {}
        for m  in pick.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    # only take into account 'product return' moves, ignoring any other
                    # kind of upstream moves, such as internal procurements, etc.
                    # a valid return move will be the exact opposite of ours:
                    #     (src location, dest location) <=> (dest location, src location))
                    if rec.location_dest_id.id == m.location_id.id \
                        and rec.location_id.id == m.location_dest_id.id:
                        return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history
    
    def _create_picking_out(self, cr, uid, clone_id, context=None):
        """
            Metodo para generar la salida de almacen del pedido de ventas de la devolucion
        """
        lines = []
        
        picking_obj = self.pool.get('stock.picking.out')
        move_obj = self.pool.get('stock.move')
        order_obj = self.pool.get('pos.order')
        
        order_srch = order_obj.search(cr, uid, [('id', '=', clone_id)], context=context)
        
        order = order_obj.browse(cr, uid, order_srch[0], context=context)
        partner_id = order['partner_id']
        date_order = order['date_order']
        order_name = order['name']
        user_id = order['user_id']
            
        # Generando la orden de salida de almacen        
        vals_order = {
            'partner_id': partner_id.id or False,
            'date': date_order,
            'origin': order_name,
            'company_id': user_id.company_id.id or False,
            'delivery_term_id': partner_id.property_delivery_term.id or False,
            'invoice_state': 'none',
            'move_type': 'direct',
            'return': 'none',
            'type': 'out',
        }
        print "****VALS_ORDER****: ", vals_order
        picking_id = picking_obj.create(cr, uid, vals_order, context=context)
        
        for line_order in order['lines']:
            product = line_order.product_id
            quantity = line_order.qty
            
            # Se guardan en el diccionario los productos para el movimiento de almacen
            vals = {
                'product_id': product.id or False,
                'product_qty': quantity,
                'product_uom': product.uom_id.id or False,
                'location_id': order.session_id.config_id.shop_id.warehouse_id.lot_stock_id.id or False,
                'location_dest_id': partner_id.property_stock_customer.id or False,
                'company_id': user_id.company_id.id or False,
                'date': date_order,
                'date_expected': date_order,
                'name': picking_obj.browse(cr, uid, picking_id, context=context)['name'],
                'weight_uom_id': product.uom_id.id or False,
                'picking_id': picking_id,
            }
            print "****VALS***: ", vals
            lines.append(vals)        
        
        
        # Actualizando las lineas de la orden de almacen
        picking_obj.write(cr, uid, picking_id, {'move_lines': [(0, 0, x) for x in lines]}, context=context)
        
        return picking_id
        
    
    def _create_new_order(self, cr, uid, ids, order, context=None):
        """
            Método para crear un clon del pedido de venta con el producto que no fue devuelto
        """
        subtotal_return = 0.0
        clone_list = []
        products = []
        
        record_id = context and context.get('active_id', False) or False
        returned = self.browse(cr, uid, record_id, context=context)
        
        pos_obj = self.pool.get('pos.order')
        line_obj = self.pool.get('pos.order.line')
        returned_product_obj = self.pool.get('returned.product')
        #print "*****ORDER.ID*****: ", order['name']
        ############################################################################
        pos_srch = pos_obj.search(cr, uid, [('name', '=', order['name'])], context=context)
        ############################################################################
        
        # Obtienendo el diario
        session = self.pool.get('pos.session').browse(cr, uid, order.session_id.id or False, context=context)
        cash_journal = session.cash_journal_id
        if not cash_journal:
            cash_journal_ids = filter(lambda st: st.journal_id.type=='cash', session.statement_ids)
            if not len(cash_journal_ids):
                raise osv.except_osv( _('error!'),
                    _("No cash statement found for this session. Unable to record returned cash."))
            cash_journal = cash_journal_ids[0].journal_id
        
        for move in pos_obj.browse(cr, uid, pos_srch, context=context):
            clone_id = pos_obj.copy(cr, uid, move.id, {
                'name': order.name + 'DEVUELTO',
                'order_origin_id': move.id or False,
                }, context=context)
            print "****CLONE_ID*****: ", clone_id
            clone_list.append(clone_id)
            
        for clone in pos_obj.browse(cr, uid, clone_list, context=context):
            for move in self.browse(cr, uid, ids ,context=context):
                for line in move.pos_order_moves:
                    product_id = line.product_id.id or False
                    qty = line.quantity
                    
                    returned_product_id = False
                    if clone.lines:
                        for clone_line in clone.lines:
                            line_id = clone_line.id or False
                            product_order = clone_line.product_id.id or False
                            quantity_order = clone_line.qty
                            # Se guardan en el diccionario el producto a devolver y la cantidad devuelta
                            vals = {
                                'product_id': product_order,
                                'price_unit': clone_line.price_unit,
                                'discount': clone_line.discount,
                                'order_id': clone.id or False
                            }
                            returned_product_srch = returned_product_obj.search(cr, uid, [('order_id', '=', clone.id),
                                ('product_id', '=', product_order)], context=context)
                            # Se valida que el producto a devolver sea el mismo al del pedido de venta
                            if product_order == product_id:
                                # Se valida que la cantidad a devolver sea la misma al del producto
                                if quantity_order == qty:
                                    # Se valida si el producto devuelto ya existe en la linea de las devoluciones
                                    if not returned_product_id:
                                        vals['quantity'] = quantity_order
                                        #quantity = quantity_order
                                        returned_product_id = returned_product_obj.create(cr, uid, vals, context)
                                        subtotal_product = returned_product_obj.browse(cr, uid, returned_product_id,
                                            context=context)['price_subtotal_incl']
                                        subtotal_return += subtotal_product
                                    else:
                                        returned_product_obj.write(cr, uid, returned_product_srch, {'quantity', qty},
                                            context=context)
                                        subtotal_product = returned_product_obj.browse(cr, uid, returned_product_srch[0],
                                            context=context)['price_subtotal_incl']
                                        subtotal_return += subtotal_product
                                        # Se elimina la linea del producto en caso de ser iguales las cantidades (devolucion/pedido)
                                    line_obj.unlink(cr, uid, line_id, context=context)
                                else:
                                    # Se resta la cantidad a devolver a la cantidad del producto en caso de no ser iguales
                                    quantity_product = quantity_order - qty
                                    if not returned_product_id:
                                        vals['quantity'] = quantity_product
                                        returned_product_id = returned_product_obj.create(cr, uid, vals, context)
                                        subtotal_product = returned_product_obj.browse(cr, uid, returned_product_id,
                                            context=context)['price_subtotal_incl']
                                        subtotal_return += subtotal_product
                                    else:
                                        returned_product_obj.write(cr, uid, returned_product_srch,
                                            {'quantity': quantity_product}, context=context)
                                        subtotal_product = returned_product_obj.browse(cr, uid, returned_produc_srch,
                                            context=context)['price_subtotal_incl']
                                        subtotal_return += subtotal_product
                                    line_obj.write(cr, uid, line_id, {'qty': quantity_product}, context=context)
                                    
                                
                
                # Generando el pago a devolver
                pos_obj.add_payment(cr, uid, clone.id, {
                        'amount': -subtotal_return,
                        #'amount': -order.amount_product_return,
                        'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'payment_name': _('return'),
                        'journal': cash_journal.id,
                    }, context=context)
                
        self._create_picking_out(cr, uid, clone_id, context=context)
                
        ret = {
            #'domain': "[('id', 'in', ["+new_order+"])]",
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id':clone_list[0],
            'view_id': False,
            'context':context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        
        return ret
        
    
    def _create_returns_stock(self, cr, uid, ids, order, context=None):
        """
            Metodo para realizar la orden de devolucion en el almacen
        """
        if context is None:
            context = {} 
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('pos.order.return.memory')
        #act_obj = self.pool.get('ir.actions.act_window')
        #model_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")
        pick_srch = pick_obj.search(cr, uid, [('origin', '=', order.name)], context=context)
        #print "****PICK_SRCH****: ", pick_srch
        # Se hace una referencia al albaran actual
        #referencia a la salida de almacen
        pick = pick_obj.browse(cr, uid, pick_srch[0], context=context)
        
        data = self.read(cr, uid, ids[0], context=context)
        # Obteniendo la fecha actual
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        set_invoice_state_to_none = True
        returned_lines = 0
        
#        Create new picking for returned products
        # Creado un nueva orden de entrada para regresar los productos
        if pick.type =='out':
            new_type = 'in'
        elif pick.type =='in':
            new_type = 'out'
        else:
            new_type = 'internal'
        
        seq_obj_name = 'stock.picking.' + new_type
        #seq_obj_name = 'stock.picking.' + 'out'
        new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
        new_picking = pick_obj.copy(cr, uid, pick.id, {
                                        'name': _('%s-%s-return') % (new_pick_name, pick.name),
                                        'move_lines': [], 
                                        'state':'draft', 
                                        'type': new_type,
                                        'return': 'customer',
                                        'date':date_cur, 
                                        #'invoice_state': data['invoice_state'],
        })
        
        val_id = data['pos_order_moves']
        #print "*****VAL_ID*****: ", val_id
        # Recorriendo la linea de los productos a eliminar
        for v in val_id:
            data_get = data_obj.browse(cr, uid, v, context=context)
            mov_id = data_get.move_id.id
            #print "****MOV_ID****: ", mov_id
            if not mov_id:
                raise osv.except_osv(_('Warning !'), _(" Tienes que colocar los productos manualmente para el procedimiento"))
            # Se obtiene la cantidad a devolver
            new_qty = data_get.quantity
            # Se genera el movimiento de almacen
            move = move_obj.browse(cr, uid, mov_id, context=context)
            # Obteniendo el almacen del cliente
            new_location = move.location_dest_id.id
            returned_qty = move.product_qty
            for rec in move.move_history_ids2:
                returned_qty -= rec.product_qty

            if returned_qty != new_qty:
                set_invoice_state_to_none = False
            if new_qty:
                returned_lines += 1
                # Genera un nuevo movimiento de almacen
                new_move=move_obj.copy(cr, uid, move.id, {
                                            'product_qty': new_qty,
                                            'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                                            'picking_id': new_picking, 
                                            'state': 'draft',
                                            'location_id': new_location, 
                                            'location_dest_id': order.session_id.config_id.shop_id.warehouse_id.lot_stock_id.id or False,
                                            'date': date_cur,
                })
                move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]}, context=context)
        if not returned_lines:
            raise osv.except_osv(_('Warning!'), _("Por favor, colocar una cantidad distinta de cero"))

        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        # Update view id in context, lp:702939
        model_list = {
                'out': 'stock.picking.out',
                'in': 'stock.picking.in',
                'internal': 'stock.picking',
        }
        #print "***NEW_TYPE****: ", 
        return {
            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            'name': _('Returned Picking'),
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model': model_list.get(new_type, 'stock.picking'),
            'type':'ir.actions.act_window',
            'context':context,
        }
    

    def create_returns(self, cr, uid, ids, context=None):
        """
            Boton para hacer las devoluciones
        """
        returned_product_list = []
        order_obj = self.pool.get('pos.order')
        line_obj = self.pool.get('pos.order.line')
        
        record_id = context and context.get('active_id', False) or False
        # Se obtiene el pedido de venta activo o donde se va a realizar la devolucion
        order = order_obj.browse(cr, uid, record_id, context=context)                              
            
        order_obj.write(cr, uid, order.id, {'state': 'cancel'}, context=context)
        # Se realiza la devolucion en el almacen correspondiente
        self._create_returns_stock(cr, uid, ids, order, context=context)
        self._create_new_order(cr, uid, ids, order, context=context)
        
        return {'type': 'ir.actions.act_window_close'}
                    
        
    