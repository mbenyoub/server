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
        'move_lines': fields.one2many('stock.move','picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        # 'campo' :  fields.char('campo', size=254),
        'catalogo_bitacora_ids': fields.one2many('catalogo.bitacora', 'picking_id', 'Bitacora')
       
        
    }
stock_picking_in()


class stock_move(osv.Model):
    _inherit = 'stock.move'
    def catalogo_bitacora_new_view(self,cr,uid,ids,context=None):
        
        analisis_type = self.browse(cr, uid, ids[0], context)['analisis_type']
        picking_id = self.browse(cr, uid, ids[0], context)['picking_id']
        
        context.update({
                #'default_target_id': len(ids) and ids[0] or False,
                'default_name': analisis_type.name,
                'default_mov':  picking_id.id,
                'default_used1': analisis_type.used1,
                'default_used2': analisis_type.used2,
                'default_used3': analisis_type.used3,
                'default_used4': analisis_type.used4,
                'default_used5': analisis_type.used5,
                'default_used6': analisis_type.used6,
                'default_used7': analisis_type.used7,
                'default_used8': analisis_type.used8,
                'default_used9': analisis_type.used9,
                'default_used11': analisis_type.used11,
                'default_used12': analisis_type.used12,
                'default_used13': analisis_type.used13,
                'default_used14': analisis_type.used14,
                'default_used15': analisis_type.used15,
                'default_used16': analisis_type.used16,
                'default_used17': analisis_type.used17,
                'default_used18': analisis_type.used18,
                'default_used19': analisis_type.used19,
                'default_used20': analisis_type.used20,
                'default_used21': analisis_type.used21,
                'default_used22': analisis_type.used22,
                'default_used23': analisis_type.used23,
                'default_used24': analisis_type.used24,
            })
        return{
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'nueva.tabla',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
    
    def inspeccion(self, cr, uid, ids, context=None):
        
        product_id = self.browse(cr, uid, ids[0], context={'product_id'})
        analisis_id = self.browse(cr, uid, ids[0], context={'catalogo_producto_m2o_id'})
        picking_id = self.browse(cr, uid, ids[0], context={'picking_id'})
        
        catalogo_product_obj = self.pool.get('analisis_type')
        
        catalogo_product_src = catalogo_product_obj.search(cr, uid, [('picking_id', '=', picking_id.id),('product_id', '=', product_id.id or False)])
        
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
        'analisis' : fields.boolean('Aplicar analisis'),
        'analisis_type' : fields.many2one('catalogo.producto','Control de Calidad'),
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