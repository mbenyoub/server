# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Israel Cabrera <icabrera@saas.com.mx>"
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
class stock_picking(osv.Model):
    _inherit = 'stock.picking'
    _table = "stock_picking"
    _columns = {
        'catalogo_bitacora_ids': fields.one2many('catalogo.bitacora', 'picking_id', 'Bitacora')
            }
stock_picking()
class stock_picking_in(osv.Model):
    _inherit = 'stock.picking.in'
   
    _columns = {
        'move_lines': fields.one2many('stock.move',
                                      'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        # 'campo' :  fields.char('campo', size=254),
        'catalogo_bitacora_ids': fields.one2many('catalogo.bitacora', 'picking_id', 'Bitacora')
       
        
    }
stock_picking_in()


class stock_move(osv.Model):
    _inherit = 'stock.move'
    
    def inspeccion(self, cr, uid, ids, context=None):
        
        product_id = self.browse(cr, uid, ids[0], context)['product_id']
        analisis_id = self.browse(cr, uid, ids[0], context)['catalogo_producto_m2o_id']
        picking_id = self.browse(cr, uid, ids[0], context)['picking_id']
        
        catalogo_product_obj = self.pool.get('catalogo.bitacora')
        catalogo_product_src = catalogo_product_obj.search(cr, uid, [('picking_id', '=', picking_id.id),
            ('product_id', '=', product_id.id or False)])
        
        var = {
            'product_id': product_id.id or False,
            'analisis_id': analisis_id.id or False,
            'picking_id': picking_id.id or False,
        }
        
        if not catalogo_product_src:
            catalogo_product_obj.create(cr, uid, var, context)
        else:
            catalogo_product_get = catalogo_product_obj.browse(cr, uid, catalogo_product_src[0], context)['id']
            catalogo_product_obj.write(cr, uid, catalogo_product_get, var, context)
                 
        return True
    
           
    _columns = {
        'catalogo_m2o_id' : fields.many2one('catalogo.producto','Tipo de analisis', required=True),
        'si_inspeccion' : fields.boolean('Aplicar analisis'),
        'catalogo_producto_m2o_id' : fields.many2one('catalogo.producto','Control de Calidad', required=True),
                }
stock_move()


class catalogo_bitacora(osv.Model):
    
    _name = 'catalogo.bitacora'
    _rec_name = 'product_id'
    _columns = {
        'product_id': fields.many2one('product.product', 'Producto'),
        'analisis_id': fields.many2one('catalogo.producto', 'Analisis'),
        'picking_id': fields.many2one('stock.picking.in', 'Picking ID'),
        'producto_analisis_id' : fields.many2one('producto.analisis', 'Producto analizar'),
    }
catalogo_bitacora()