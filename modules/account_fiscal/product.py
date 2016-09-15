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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class product_category(osv.osv):
    _inherit = 'product.category'
    
    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _columns = {
        'name': fields.char('Name', size=256, required=True, select=True),
        'code': fields.char('Codigo', size=32, required=True, select=True),
        # Valores sobre activos
        'is_asset': fields.boolean('Es un Activo'),
        'default_asset_category_id': fields.many2one('account.asset.category', 'Categoria de activo', change_default=True),
        # Informacion de producto
        'type_product': fields.selection([('product', 'Almacenable'),('consumible', 'Consumible'),('consu', 'Materia Prima'),('service','Servicio')], 'Tipo de producto', help="Consumable are product where you don't manage stock, a service is a non-material product provided by a company or an individual."),
        'uom_id': fields.many2one('product.uom', 'Unidad de Medida', help="Unidad de medida por defecto utilizada para todas las operaciones de stock."),
        'sale_ok': fields.boolean('Puede ser vendido', help="Especifique si un producto puede ser selecccionado en un pedido de venta."),
        'purchase_ok': fields.boolean('Puede ser comprado', help="Indica si el producto es visible en la lista de productos que aparece al seleccionar un producto en una linea de pedido de compra."),
        'hr_expense_ok': fields.boolean('Puede ser un gasto', help="Especifica si el producto puede ser seleccionado en una linea de gasto de RRHH."),
        'uom_po_id': fields.many2one('product.uom', 'Unidad de medida compras'),
        'cost_method': fields.selection([('standard','Precio Estandar'), ('average','Precio Medio')], 'Metodo de coste',
            help="Precio estandar: EL precio de coste es actualizado manualmente al final de un periodo especifico \n Precio medio: El precio de coste es recalculado con cada envio entrante."),
        'valuation':fields.selection([('manual_periodic', 'Periodico (manual)'),
                                        ('real_time','Tiempo real (automatizado)'),], 'Valoracion de Inventario'),
        'taxes_id': fields.many2many('account.tax', 'product_categ_taxes_rel',
            'categ_id', 'tax_id', 'Impuestos Cliente',
            domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])]),
        'supplier_taxes_id': fields.many2many('account.tax',
            'product_categ_supplier_taxes_rel', 'categ_id', 'tax_id',
            'Impuestos proveedor', domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])]),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Nombre.', store=True),
    }
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        """
        Returns a list of tupples containing id, name, as internally it is called {def name_get}
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param name: name to search
        @param args: other arguments
        @param operator: default operator is 'ilike', it can be changed
        @param context: context arguments, like lang, time zone
        @param limit: Returns first 'n' ids of complete result, default is 80.

        @return: Returns a list of tupples containing id and name
        """
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []

        if name:
            ids = self.search(cr, user, ['|',('code', operator, name),('complete_name','ilike',"%" + name + "%")] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context or {})
        return self.name_get(cr, user, ids, context=context)

    def _check_code_uniq(self, cr, uid, ids, context=None):
        """
            Valida que el codigo de la categoria de producto no se repita
        """
        # Recorre los registros
        for categ in self.browse(cr, uid, ids, context=context):
            # Valida que la categoria sea diferente de NA
            if categ.code == 'NA':
                continue
            
            categ_ids = self.search(cr, uid, [('code','=',categ.code),('id','!=', categ.id)], context=context)
            if categ_ids:
                return False
        return True

    _constraints = [
        (_check_code_uniq, 'Error!\nEl codigo de la categoria de producto debe ser unico!.', ['code']),
    ]
    
    _sql_constraints = []
    
    def _get_uom_id(self, cr, uid, *args):
        cr.execute('select id from product_uom order by id limit 1')
        res = cr.fetchone()
        return res and res[0] or False
    
    _defaults = {
        'sale_ok': 1,
        'purchase_ok': 1,
        'uom_id': _get_uom_id,
        'uom_po_id': _get_uom_id,
        'type' : 'consumible',
        'cost_method': 'standard',
        'code': 'NA'
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza la serie del diario
        """
        # Funcion original de modificar
        super(product_category, self).write(cr, uid, ids, vals, context=context)
        
        # Actualiza los modulos hijos de las categorias seleccionadas
        categ_ids = self.search(cr, uid, [('parent_id','in',ids)], context=context)
        if categ_ids:
            self.write(cr, uid, categ_ids, {}, context=context)
        return True
    
    def copy(self, cr, uid, id, default, context=None):
        """
            Agrega a la copia de la categoria de producto el indicador sobre el codigo para que no marque error
        """
        
        categ = self.browse(cr, uid, id, context=context)
        new_code = "%s (Copy)" % categ.code
        # =like is the original LIKE operator from SQL - Regresa una lista de ids por el filtro aplicado
        others_count = self.search(cr, uid, [('code', '=like', new_code+'%')], count=True, context=context)
        if others_count > 0:
            new_code = "%s(%s)" % (new_code, others_count+1)
        default['code'] = new_code
        # en el copy hace un retorno con toda la informacion en base al id marcado
        return super(product_category, self).copy(cr, uid, id, default, context=context)
    
product_category()

class product_template(osv.osv):
    """ Inherits partner and add extra information product """
    _inherit = 'product.template'
    
    _columns = {
        'name': fields.char('Name', size=256, required=True, select=True),
        'type': fields.selection([('product', 'Almacenable'),('consumible', 'Consumible'),('consu', 'Materia Prima'),('service','Servicio')], 'Tipo de producto', required=True, help="Consumable are product where you don't manage stock, a service is a non-material product provided by a company or an individual."),
    }
    
    _defaults = {
        'type': 'consumible'
    }
    
product_template()

class product_product(osv.osv):
    """ Inherits partner and add extra information product """
    _inherit = 'product.product'
    
    def onchange_categ_id(self, cr, uid, ids, categ_id, context=None):
        """
            Actualiza la informacion del producto en base a la categoria seleccionada
        """
        categ_obj = self.pool.get('product.category')
        if not categ_id:
            return {}
        res = {}
        # Obtiene el objeto categoria
        category = categ_obj.browse(cr, uid, categ_id, context=context)
        
        # Indicadores sobre lo que puede o no hacer sobre el producto
        res['sale_ok'] = category.sale_ok
        res['purchase_ok'] = category.purchase_ok
        res['hr_expense_ok'] = category.hr_expense_ok
        res['is_asset'] = category.is_asset
        
        # Actualiza los datos que recibe en la lista
        if category.type_product:
            res['type'] = category.type_product
        if category.uom_id:
            res['uom_id'] = category.uom_id.id
        if category.default_asset_category_id:
            res['default_asset_category_id'] = category.default_asset_category_id.id
        if category.uom_po_id:
            res['uom_po_id'] = category.uom_po_id.id
        if category.cost_method:
            res['cost_method'] = category.cost_method
        if category.valuation:
            res['valuation'] = category.valuation
        if category.taxes_id:
            tax_ids = []
            for tax in category.taxes_id:
                tax_ids.append(tax.id)
            res['taxes_id'] = tax_ids
        if category.supplier_taxes_id:
            tax_ids = []
            for tax in category.supplier_taxes_id:
                tax_ids.append(tax.id)
            res['supplier_taxes_id'] = tax_ids
        return {'value': res}
    
    _columns = {
        'description': fields.text('Descripcion'), # Quita traduccion de la descripcion
    }
    
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
