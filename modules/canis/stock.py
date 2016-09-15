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
#    recode by
#           Alfonso Villalpando Alderete
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
from openerp import netsvc
import openerp.addons.decimal_precision as dp


class stock_picking(osv.Model):
    _inherit = 'stock.picking'
    
    _columns = {
        'state': fields.selection(
            [('draft', 'Draft'),
            ('auto', 'Waiting Another Operation'),
            ('confirmed', 'Waiting Availability'),
            ('assigned', 'Ready to Receive'),
            ('allow', 'Esperando autorizacion'),
            ('done', 'Received'),
            ('cancel', 'Cancelled'),],
            'Status', readonly=True, select=True,
            help="""* Draft: not confirmed yet and will not be scheduled until confirmed\n
                 * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                 * Waiting Availability: still waiting for the availability of products\n
                 * Ready to Receive: products reserved, simply waiting for confirmation.\n
                 * Received: has been processed, can't be modified or cancelled anymore\n
                 * Cancelled: has been cancelled, can't be confirmed anymore"""),
    }
    
stock_picking()


class stock_move(osv.Model):
    _inherit = 'stock.move'
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):
        """
            Metodo super del onchange_product_id para agregarle valor al campo to_weight_product
        """
        product_obj = self.pool.get('product.product')
        product_srch = product_obj.search(cr, uid, [('id', '=', prod_id)])
        
        res = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id,
                    partner_id)
        print "***EMPEZANDO A OBTENER DATOS DEL PRODUCTO***"
        for product in product_obj.browse(cr, uid, product_srch):
            print "***OBTENIENDO DATOS DEL PRODUCTO*****"
            if product.to_weight_product:
                to_weigth = product.to_weight_product
                print "********TO_WEIGHT****: ", to_weigth
                res['value']['to_weight_product'] = to_weigth
            else:
                res['value']['to_weight_product'] = False
                
        print "****RES*****: ", res
        
        return res
    
    def _get_difference_weight(self, cr, uid, ids, fields_name, args, context=None):
        """
            Método para obtener la diferencia entre la pesada de entrada y la de salida 
        """
        difference = 0.0
        real_weigth = 0.0
        weight_in = 0.0
        weight_out = 0.0
        result = {}
        
        for move in self.browse(cr, uid, ids, context=context):
            # Obteniendo la pesada de entrada y salida
            weight_in = move.weight_in
            weight_out = move.weight_out
            # Obteniendo la diferencia
            real_weigth = weight_in - weight_out
            difference = real_weigth - move.product_qty
            difference = difference * (-1)
            print "****DIFFERENCE****: ", difference
            # Obteniendo el peso real 
            #if move.product_qty > weight_out:   
            #    real_weigth = move.product_qty - difference
            #    print "****REAL_WEIGHT*****: ", real_weigth
            #elif difference > 0.0:
            #    real_weigth = move.product_qty + difference
            #    print "****REAL_WEIGHT*****: ", real_weigth
            #else:
            #    difference = difference * (-1)
            #    real_weigth = move.product_qty + difference
            #    print "****REAL_WEIGHT*****: ", real_weigth
                
            # Ingresando los valores al diccionario que se va a devolver
            result[move.id] = {
                'weight_difference': difference,
                'weight_real_order': real_weigth,
            }
        
        return result
        
    
    
    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Reference',
                select=True,
                states={'done': [('readonly', True)]}),
        'picking_state': fields.related('picking_id', 'state',
                type='selection',
                selection=[
                        ('draft', 'New'),
                        ('cancel', 'Cancelled'),
                        ('waiting', 'Waiting Another Move'),
                        ('confirmed', 'Waiting Availability'),
                        ('assigned', 'Available'),
                        ('done', 'Done')], string='Estado entrada',
                readonly=True, store=True),
        'weight_in': fields.float('Pesada Entrada'),
        'weight_out': fields.float('Pesada Salida'),
        # 'to_weight_product': fields.boolean('Pesar'),
        'to_weight_product': fields.boolean('Pesar'),
        'weight_difference': fields.function(_get_difference_weight, type='float', string='diferencia',
            store=True, method=True, multi='weight',
            digits_compute=dp.get_precision('Product Unit of Measure')),
        'weight_real_order': fields.function(_get_difference_weight, type='float', string='Peso real',
            store=True, method=True, multi='weight',
            digits_compute=dp.get_precision('Product Unit of Measure')),
    }
    
stock_move()


class stock_picking(osv.Model):
    _inherit = 'stock.picking.in'
    
    def button_allow(self, cr, uid, ids, context=None):
        """
            Realiza la autorizacion de la recepcion del producto que sobrepaso la tolerancia del peso
            esperado
        """
        if context is None:
            context = {}
        """Open the partial picking wizard"""
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False,
            'allowed': True,
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.partial.picking',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
    
    _columns = {
        'state': fields.selection(
            [('draft', 'Draft'),
            ('auto', 'Waiting Another Operation'),
            ('confirmed', 'Waiting Availability'),
            ('assigned', 'Ready to Receive'),
            ('allow', 'Esperando autorizacion'),
            ('done', 'Received'),
            ('cancel', 'Cancelled'),],
            'Status', readonly=True, select=True,
            help="""* Draft: not confirmed yet and will not be scheduled until confirmed\n
                 * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                 * Waiting Availability: still waiting for the availability of products\n
                 * Ready to Receive: products reserved, simply waiting for confirmation.\n
                 * Received: has been processed, can't be modified or cancelled anymore\n
                 * Cancelled: has been cancelled, can't be confirmed anymore\n
                 * Autorizar: Esperando a la autorizacion si el entrega excede la tolerancia del \n
                   peso esperado del producto"""),
    }