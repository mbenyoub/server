# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from datetime import datetime

from _common import rounding

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

#----------------------------------------------------------
# Price lists
#----------------------------------------------------------

class product_pricelist(osv.osv):
    _inherit = "product.pricelist"

    _columns = {
        'discount_ids': fields.one2many('product.pricelist.discount', 'pricelist_id', 'Descuentos'),
        
        # ------MODIFICACION 07-04-2015-------
        # AGREGACION DE
        
        'limit_min_sale': fields.float('Precio minimo')
        
        # ----------------------------
    }

product_pricelist()

#class product_pricelist_item(osv.osv):
#    _inherit = "product.pricelist.item"
#
#    _columns = {
#        'compute_ids': fields.one2many('product.pricelist.item.compute', 'item_id', 'Calculos extra'),
#    }
#
#product_pricelist_item()
#
#class product_pricelist_item_compute(osv.osv_memory):
#    _name = 'product.pricelist.item.compute'
#    
#    _columns = {
#        'item_id': fields.many2one('product.pricelist.item', 'Codigo', select=True, ondelete='cascade'),
#        'factor': fields.selection([
#                        ('sum','Suma'),
#                        ('res','Resta'),
#                        ('mul','Multiplicacion'),
#                        ('div','Division')], 'Factor'),
#        'type': fields.selection([
#                        ('val','Valor Fijo'),
#                        ('anio','Precio publico'),
#                        ('per','Precio coste')], 'Tipo'),
#        'value': fields.float('Valor', digits=(16,4))
#    }
#    
#    _defaults = {
#        'type': 'val',
#        'factor': 'sum',
#        'value': 0.0
#    }
#    
#product_pricelist_item_compute()

#----------------------------------------------------------
# Price lists - Descuentos
#----------------------------------------------------------

class product_pricelist_discount_type(osv.osv):
    _name = "product.pricelist.discount.type"
    _description = "Pricelist Type"
    _columns = {
        'name': fields.char('Descuento',size=64, required=True, translate=True),
        'key': fields.char('Codigo', size=64, required=True, help="Codigo para identificar el descuento."),
        'note': fields.text('Nota'),
        'to_paid': fields.boolean('Aplica sobre el pago', help='Si aplica sobre el pago la condicion, es contra factura y se ve reflejada hasta el pago'),
        'to_mix': fields.boolean('Aplica sobre mezclas', help='Si aplica sobre mezcla, el calculo se vera reflejado sobre las mezclas de diferentes categorias de productos'),
        'to_quantity': fields.boolean('Aplica sobre cantidad', help='Si aplica sobre volumen, el calculo se vera reflejado sobre el pedido'),
    }
    
product_pricelist_discount_type()

class product_pricelist_discount(osv.osv):
    _name = "product.pricelist.discount"
    _description = "Pricelist Discount"
    
    def get_number_days(self, cr, uid, date_ini, date_end, context=None):
        """
            Obtiene la diferencia de dias entre fechas
        """
        # Cambia las fechas a formato datetime
        date_ini = datetime.strptime(date_ini, '%Y-%m-%d')
        date_end = datetime.strptime(date_end, '%Y-%m-%d')
        # Obtiene la diferencia de las fechas
        date_dif = date_end - date_ini
        return date_dif.days
    
    def _pricelist_type_get(self, cr, uid, context=None):
        """
            Obtiene los tipos de descuentos que estan disponibles para las listas de precios
        """
        pricelist_type_obj = self.pool.get('product.pricelist.discount.type')
        pricelist_type_ids = pricelist_type_obj.search(cr, uid, [], order='name')
        pricelist_types = pricelist_type_obj.read(cr, uid, pricelist_type_ids, ['key','name'], context=context)
        res = []
        for type in pricelist_types:
            res.append((type['key'],type['name']))
        return res
    
    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', 'Tarifa', required=True, select=True, ondelete='cascade', domain=[('type','=','sale')]),
        #'type': fields.selection(_pricelist_type_get, 'Tipo descuento', required=True),
        'type_id': fields.many2one('product.pricelist.discount.type', 'Tipo descuento', select=True, ondelete='restrict', required=True),
        'name': fields.char('Nombre', size=64, required=True, translate=True),
        'active': fields.boolean('Activo', help='Al duplicar'),
        'item_ids': fields.one2many('product.pricelist.discount.item', 'discount_id', 'Reglas Descuento'),
        'company_id': fields.related('pricelist_id','company_id',type='many2one', readonly=True, relation='res.company', string='Compañia', store=True),
        'to_paid': fields.related('type_id','to_paid', type='boolean', readonly=True, string='Aplica sobre pago'),
        'to_mix': fields.related('type_id','to_paid', type='boolean', readonly=True, string='Aplica sobre mezcla'),
    }
    _defaults = {
        'active': lambda *a: 1,
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Al duplicar un registro lo deja como inactivo
        """
        if not default: default= {}
        default['active'] = False
        return super(product_pricelist_discount, self).copy(cr, uid, id, default, context)
    
    def onchange_type_id(self, cr, uid, ids, type_id, context=None):
        """
            Revisa si el descuento se aplica al momento del pago
        """
        if not type_id:
            return {}
        discount_type = self.pool.get('product.pricelist.discount.type').read(cr, uid, type_id, ['to_paid','to_mix'])
        if discount_type.get('to_paid', None) is not None:
            return {'value': {'to_paid': discount_type['to_paid'], 'to_mix': discount_type['to_mix']}}
        return {}
    
product_pricelist_discount()

class product_pricelist_discount_item(osv.osv):
    _name = "product.pricelist.discount.item"
    _description = "Pricelist item"
    _order = "sequence"
    
    def validate_exception_categ(self, cr, uid, id, invoice_id, context=None):
        """
            Valida que no existan productos con categorias de productos en la lista de excepciones
        """
        categ_obj = self.pool.get('product.category')
        item = self.browse(cr, uid, id, context=context)
        
        categ_ids = []
        for categ in item.exception_categ_ids:
            categ_ids.append(categ.id)
        if len(categ_ids) > 0:
            # Obtiene categorias a excluir y categorias hijas directaente relacionadas
            categ_ids = categ_obj.search(cr, uid, ['|',('id','in',categ_ids),('parent_id','in',categ_ids)], context=context)
            categ_list_ids = []
            for categ in categ_ids:
                categ_list_ids.append(str(categ))
            categ_list_ids = ",".join(categ_list_ids)
            # Valida que la factura no tenga productos sobre las categorias excluidas
            cr.execute("""
                        select count(l.id) as cantidad 
                        from 
                                account_invoice_line as l 
                                INNER JOIN product_product as p on p.id=l.product_id 
                                INNER JOIN product_template as t on p.product_tmpl_id=t.id and t.categ_id in (%s)
                        where l.invoice_id = %s
                        having count(l.id) > 0"""%(categ_list_ids,invoice_id))
            if cr.fetchone():
                return True
        return False
    
    def _get_attr_type(self, cr, uid, ids, fields, arg, context=None):
        """
            Obtiene el valor sobre el codigo en donde se revisa si se aplica mezcla o no
        """
        result = {}
        # Recorre los registros
        for item in self.browse(cr, uid, ids, context=context):
            result[item.id] = {
                'to_mix': False,
                'to_paid': False,
                'to_quantity': False
            }
            # Valida si hay un descuento asignado a la regla
            if item.discount_id:
                result[item.id]['to_mix'] = item.discount_id.type_id.to_mix
                result[item.id]['to_paid'] = item.discount_id.type_id.to_paid
                result[item.id]['to_quantity'] = item.discount_id.type_id.to_quantity
        return result
    
    _columns = {
        'name': fields.char('Nombre de la Regla', size=64, help="Nombre explicito para la regla del descuento."),
        'discount_id': fields.many2one('product.pricelist.discount', 'Relacion Descuento', select=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Producto', ondelete='cascade', help="Especifique si la regla aplica sobre un producto especifico, dejar en blanco para el caso contrario."),
        'categ_id': fields.many2one('product.category', 'Product Category', ondelete='cascade', help="Especifique una categoria de producto si  esta regla solo aplica a los productos pertenecientes a esta categoria o a sus categorias hijas. Dejar en blanco en caso contrario."),
        'min_quantity': fields.integer('Peso min.', required=True, help="Especifique la cantidad minima que debe ser vendida para aplicar esta regla."),
        'sequence': fields.integer('Secuencia', required=True, help="Indica el orden en que los elementos de los descuentos sobre la tarifa seran comprobados. En la evaluacion se da maxima prioridad a la secuencia mas baja y se detiene en el momento en el que encuentra un elemento coincidente."),
        'discount': fields.float('Descuento', digits=(2,2)),
        'company_id': fields.related('discount_id','company_id',type='many2one', readonly=True, relation='res.company', string='Company', store=True),
        'mix_ids': fields.one2many('product.pricelist.discount.mix', 'item_id', 'Reglas Descuento'),
        'exception_categ_ids': fields.many2many('product.category', 'product_pricelist_discount_category_rel', 'discount_item_id', 'categ_id', 'Categorias de productos excluidos sobre la regla'),
        'to_mix': fields.function(_get_attr_type, type="boolean", string="Aplica sobre mezcla", multi="to_type"),
        'to_paid': fields.function(_get_attr_type, type="boolean", string="Aplica sobre pago", multi="to_type"),
        'to_quantity': fields.function(_get_attr_type, type="boolean", string="Aplica sobre pago", multi="to_type"),
    }
    _defaults = {
        'min_quantity': lambda *a: 0,
        'sequence': lambda *a: 5,
        'discount': lambda *a: 0,
    }
    
    def _check_mix(self, cr, uid, ids, context=None):
        """
            Valida que el total sobre las mezclas no rebase el 100 porciento
        """
        for item in self.browse(cr, uid, ids, context=context):
            # Recorre las mezclas si contiene registros
            if item.mix_ids:
                proportion = 0
                for mix in item.mix_ids:
                    proportion += mix.max_proportion
                    # Valida que no rebase el 100 porciento disponible
                    if proportion > 100:
                        return False
        return True
    
    def _check_discount(self, cr, uid, ids, context=None):
        """
            Valida que el descuento no rebase el 100 porciento
        """
        for item in self.browse(cr, uid, ids, context=context):
            # Valida que el descuento no sea mayor al 100 porciento 
            if item.discount > 100:
                return False
        return True

    _constraints = [
        #(_check_mix, 'Error! El total de los maximos en la mezcla no debe rebasar el 100 porciento!', ['mix_ids']),
        #(_check_discount, 'Error! El descuento no puede ser mayor al 100 porciento disponible!', ['discount']),
    ]
    
    def onchange_discount_id(self, cr, uid, ids, discount_id, context=None):
        """
            Revisa si el descuento se aplica al momento del pago
        """
        res = {}
        if not discount_id:
            return res
        # Obtiene del tipo de descuento si aplica la mezcla o no
        discount = self.pool.get('product.pricelist.discount').browse(cr, uid, discount_id, context=context)
        if discount:
            res['to_mix'] = discount.type_id.to_mix
        return {'value': res}
    
    def product_id_change(self, cr, uid, ids, product_id, name, context=None):
        """
            Cambia el nombre de la regla en base al codigo del producto
        """
        # Si no se recibe un producto en los parametros y la regla ya tiene un nombre asignado omite el proceso
        if not product_id or name:
            return {}
        prod = self.pool.get('product.product').read(cr, uid, [product_id], ['code','name'])
        if prod[0]['code']:
            return {'value': {'name': prod[0]['code']}}
        return {}
    
product_pricelist_discount_item()

class product_pricelist_discount_mix(osv.osv):
    _name = "product.pricelist.discount.mix"
    _description = "Pricelist mix"
    _order = "min_proportion desc"
    
    _columns = {
        'item_id': fields.many2one('product.pricelist.discount.item', 'Regla descuento', ondelete='cascade', required=True),
        'categ_id': fields.many2one('product.category', 'Product Category', ondelete='cascade', required=True, help="Especifique una categoria de producto para validar la proporcion sobre la mezcla."),
        'min_proportion': fields.float('Valor min.', digits=(2,2),  required=True, help="Especifique la cantidad minima que debe ser vendida para aplicar esta mezcla en proporcion a la venta."),
        'max_proportion': fields.float('Valor max.', digits=(2,2), required=True, help="Especifique la cantidad maxima que puede ser vendida para aplicar esta regla en proporcion a la venta."),
    }
    _defaults = {
        'min_proportion': lambda *a: 0.0,
        'max_proportion': lambda *a: 0.0,
    }
    
    def _check_categ(self, cr, uid, ids, context=None):
        """
            Valida que no se dupliquen las categorias sobre la regla
        """
        # Recorre los registros
        for mix in self.browse(cr, uid, ids, context=context):
            # Revisa si no hay una categoria igual a la que se esta registrando
            mix_ids = self.search(cr, uid, [('item_id','=',mix.item_id.id),('categ_id','=',mix.categ_id.id),('id','!=',mix.id)], context=context)
            if mix_ids:
                return False
        return True
    
    def _check_margin(self, cr, uid, ids, context=None):
        """
            Valida que la proporcion minima no sea mayor que la maxima
        """
        for mix in self.browse(cr, uid, ids, context=context):
            if (mix.min_proportion > mix.max_proportion):
                return False
        return True
    
    def _check_proportion(self, cr, uid, ids, context=None):
        """
            Valida que la proporcion minima y maxima no rebasen el 100 porciento disponible
        """
        for mix in self.browse(cr, uid, ids, context=context):
            if mix.min_proportion >= 101:
                return False
            if mix.max_proportion >= 101:
                return False
        return True
    
    _constraints = [
        (_check_categ, 'Error! Tu no puedes agregar mezclas con categorias repetidas sobre la regla!', ['categ_id']),
        (_check_margin, 'Error! La proporcion minima debe ser mayor a la proporcion maxima.', ['min_proportion', 'max_proportion']),
        #(_check_proportion, 'Error! La proporcion no debe sobrepasar el 100 porciento disponible.', ['min_proportion', 'max_proportion'])
    ]
    
product_pricelist_discount_mix()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

