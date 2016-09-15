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
# ----MODIFICACION 16/04/2015----
# Agregacion de metodo para obtener el lote de produccion por default en el modelo 'mrp.monitoring.product'
# Cambio de nombre de campo de 'lot_number' por 'lot_id' asi como del tipo de campo de float a many2one en
# en 'mrp.monitoring.product'

from openerp.osv import osv, fields

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    
    _columns = {
        'monitoring_product_ids': fields.one2many('mrp.monitoring.product', 'production_id', 'Productos monitoreados'),
    }
    
mrp_production()

class mrp_monitoring_product(osv.osv):
    _name = 'mrp.monitoring.product'
    _description = 'Administracion de calidad'
    
    def _get_lot_number(self, cr, uid , context=None):
        """
            Obtiene la orden de produccion
        """
        lot_id = False
       
        production_obj = self.pool.get('mrp.production')
        # Obteniendo el id activo
        user_id = context and context.get('uid', False) or False
        print "*****USER_ID****: ", user_id
        # Obteniendo la orden de produccion actual
        if user_id:
            production_srch = production_obj.search(cr, uid, [('user_id', '=', user_id)],
                context = context)
            production = production_obj.browse(cr, uid, production_srch[0], context=context)
            lot_id = production.mrp_lot_id.id or False
        
        return lot_id
        
    
    
    _columns = {
        'name': fields.char('Nombre de analisis'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'product_qty': fields.float('Cantidad de producto (kg)'),
        'product_humidity': fields.float('Humedad'),
        'product_size': fields.float('Tamaño-dimensiones'),
        'dosage_percent': fields.float('Porcentaje de dosificacion'),
        'lot_id': fields.many2one('mrp.lot','Número de lote'),
        'production_id': fields.many2one('mrp.production', 'Orden de produccion'),
        'move_id': fields.many2one('stock.move', 'movimiento')
    }
    
    _defaults = {
        'lot_id': _get_lot_number,
        'production_id': lambda self, cr, uid, context : (context['production_id']) if (context and ('production_id' in context)) else (None)
    }
