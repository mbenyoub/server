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
from openerp.osv import fields, osv
from openerp import pooler

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

# ---------------------------------------------------------
# Actualizacion de categoria de productos
# ---------------------------------------------------------

class admon_update_data_product_category(osv.osv_memory):
    """
        Actualiza la informaicon de las categorias de productos a travez de otra base de datos
    """
    _name = "admon.update.data.product.category.wizard"

    def _get_method_db_selection(self, cr, uid, context=None):
        # From module of PAC inherit this function and add new methods
        db_list = []
        result = []
        db = ws()
        res = []
        # Obtiene la lista de 
        db_list = db.exp_list()
        for db in db_list:
            res.append((db,' %s '%(db,)))
        result.extend(
            res
        )
        return result

    _columns = {
        'name': fields.char('Nombre', size=32),
        # Gestiona bases de datos activas sobre el servidor
        'db_list': fields.selection(_get_method_db_selection, "Base de Datos origen", required=True),
        # Configuracion timbrado
        'database_id': fields.many2one('admon.database', 'Base de Datos destino', select=True, ondelete='cascade', required=True),
    }
    
    def update_info_product_category(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de la compañia de la base de datos
        """
        # Inicializa variables
        categ_obj = self.pool.get('product.category')
        uom_obj = self.pool.get('product.uom')
        asset_obj = self.pool.get('account.asset.category')
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        tax_obj = self.pool.get('account.tax')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de las categorias de la base origen
            categ_ids = categ_obj.search(cr1, uid, [], context=context)
            for categ in categ_obj.browse(cr1, uid, categ_ids, context=context):
                # Arreglo para actualizacion de datos sobre la categoria
                vals = {
                    'name': categ.name,
                    'sale_ok': categ.sale_ok,
                    'purchase_ok': categ.purchase_ok,
                    'hr_expense_ok': categ.hr_expense_ok,
                    'is_asset': categ.is_asset,
                    'code': categ.code,
                    'type': categ.type,
                    'type_product': categ.type_product,
                    'cost_method': categ.cost_method,
                    'property_stock_journal': categ.property_stock_journal,
                    'valuation': categ.valuation
                }
                
                # Busca el padre de la categoria del producto
                if categ.parent_id:
                    parent_ids = categ_obj.search(cr2, uid, [('code', '=', categ.parent_id.code)])
                    if parent_ids:
                        # Agrega el id del registro
                        vals['parent_id'] = parent_ids[0]
                
                # Busca la unidad de medida para ventas
                if categ.uom_id:
                    uom_ids = uom_obj.search(cr2, uid, [('name', '=', categ.uom_id.name)])
                    if uom_ids:
                        # Agrega el id del registro
                        vals['uom_id'] = uom_ids[0]
                
                # Busca la unidad de medida para compras
                if categ.uom_po_id:
                    uom_ids = uom_obj.search(cr2, uid, [('name', '=', categ.uom_po_id.name)])
                    if uom_ids:
                        # Agrega el id del registro
                        vals['uom_po_id'] = uom_ids[0]
                
                # Busca la categoria de activo
                if categ.default_asset_category_id:
                    asset_ids = asset_obj.search(cr2, uid, [('code', '=', categ.default_asset_category_id.code)])
                    if asset_ids:
                        # Agrega el id del registro
                        vals['default_asset_category_id'] = asset_ids[0]
                
                # Busca la cuenta de ingresos
                if categ.property_account_income_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_account_income_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_account_income_categ'] = account_ids[0]
                
                # Busca la cuenta de nota de venta para productos
                if categ.property_account_income_note_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_account_income_note_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_account_income_note_categ'] = account_ids[0]
                
                # Busca la cuenta de costo de venta
                if categ.property_account_expense_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_account_expense_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_account_expense_categ'] = account_ids[0]
                
                # Busca la cuenta de NDC ingresos
                if categ.property_account_income_refund_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_account_income_refund_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_account_income_refund_categ'] = account_ids[0]
                
                # Busca la cuenta de NDC gastos
                if categ.property_account_expense_refund_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_account_expense_refund_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_account_expense_refund_categ'] = account_ids[0]
                
                # Busca la cuenta por pagar transitoria
                if categ.property_stock_account_input_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_stock_account_input_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_stock_account_input_categ'] = account_ids[0]
                
                # Busca la cuenta por cobrar transitoria
                if categ.property_stock_account_output_categ:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_stock_account_output_categ.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_stock_account_output_categ'] = account_ids[0]
                
                # Busca la cuenta de valoracion de existencias
                if categ.property_stock_valuation_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_stock_valuation_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_stock_valuation_account_id'] = account_ids[0]
                
                # Busca el diario de existencias
                if categ.property_stock_valuation_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', categ.property_stock_valuation_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['property_stock_valuation_account_id'] = account_ids[0]
                
                # Busca los impuestos de venta
                if categ.taxes_id:
                    tax_list = []
                    for tax in categ.taxes_id:
                        # Valida que tenga un codigo de impuesto
                        if tax.description:
                            # Busca el impuesto y lo agrega a la lista
                            tax_ids = tax_obj.search(cr2, uid, [('description', '=', tax.description)])
                            if tax_ids:
                                # Agrega el id del registro
                                tax_list.append(tax_ids[0])
                    vals['taxes_id'] = [[6, 0, tax_list]]
                
                # Busca los impuestos de compra
                if categ.supplier_taxes_id:
                    tax_list = []
                    for tax in categ.supplier_taxes_id:
                        # Valida que tenga un codigo de impuesto
                        if tax.description:
                            # Busca el impuesto y lo agrega a la lista
                            tax_ids = tax_obj.search(cr2, uid, [('description', '=', tax.description)])
                            if tax_ids:
                                # Agrega el id del registro
                                tax_list.append(tax_ids[0])
                    vals['supplier_taxes_id'] = [[6, 0, tax_list]]
                
                # Valida si la categoria del producto se encuentra ya registrada en la base de destino
                categ_ids = categ_obj.search(cr2, uid, [('code','=',categ.code)])
                # Actualiza el registro
                if categ_ids:
                    categ_obj.write(cr2, uid, categ_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    categ_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def action_update_data(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de categorias de productos
        """
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Obtiene la base de datos origen
            db_origin = data.db_list
            # Obtiene la base de datos destino
            db_dest = data.database_id.code or False
            
            # Actualiza la informacion de la compañia
            self.update_info_product_category(db_origin, db_dest, context=context)
        # Muestra un mensaje indicando la actualizacion del registro
        return self.pool.get('warning').info(cr, uid, title='Proceso Completo!', message=_("Se completo la actualizacion de los registros de la base origen %s a la base destino %s")%(db_origin,db_dest))
    
admon_update_data_product_category()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
