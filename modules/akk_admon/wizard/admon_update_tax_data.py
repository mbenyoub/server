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
# Actualizacion de Impuestos
# ---------------------------------------------------------

class admon_update_tax_data(osv.osv_memory):
    """
        Actualiza la informaicon de las categorias de productos a travez de otra base de datos
    """
    _name = "admon.update.tax.data.wizard"

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
    
    def update_info_tax_category(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de las categorias de impuestos de la base de datos
        """
        # Inicializa variables
        tax_categ_obj = self.pool.get('account.tax.category')
        user_obj = self.pool.get('res.users')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Obtiene la compañia del usuario
            company_id = user_obj.browse(cr2, uid, uid, context=context).company_id.id
            
            # Recorre los registros de las categorias de la base origen
            tax_ids = tax_categ_obj.search(cr1, uid, [], context=context)
            for tax in tax_categ_obj.browse(cr1, uid, tax_ids, context=context):
                # Arreglo para actualizacion de datos sobre los impuestos
                vals = {
                    'name': tax.name,
                    'company_id': company_id,
                    'active': tax.active,
                    'code': tax.code,
                    'sign': tax.sign
                }
                
                print "************** actualiza categoria de impuesto *********** ", tax.code
                #print "************** actualiza categoria de impuesto *********** ", vals
                
                # Valida si ya registrado en la base de destino
                tax_ids = tax_categ_obj.search(cr2, uid, [('code','=',tax.code)])
                # Actualiza el registro
                if tax_ids:
                    tax_categ_obj.write(cr2, uid, tax_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    tax_categ_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def update_info_tax_code(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de los codigos de impuestos de la base de datos
        """
        # Inicializa variables
        tax_code_obj = self.pool.get('account.tax.code')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de los codigos de impuesto de la base origen
            code_ids = tax_code_obj.search(cr1, uid, [], context=context)
            for code in tax_code_obj.browse(cr1, uid, code_ids, context=context):
                # Arreglo para actualizacion de datos sobre los impuestos
                vals = {
                    'name': code.name,
                    'code': code.code,
                    'notprintable': code.notprintable,
                    'sequence': code.sequence,
                    'visible': code.visible,
                    'sign': code.sign,
                    'percent': code.percent,
                    'apply_balance': code.apply_balance,
                    'info': code.info,
                }
                
                # Busca el codigo padre
                if code.parent_id:
                    code_ids = tax_code_obj.search(cr2, uid, [('code', '=', code.parent_id.code)])
                    if code_ids:
                        # Agrega el id del registro
                        vals['parent_id'] = code_ids[0]
                
                print "************** actualiza codigo de impuesto *********** ", code.code
                #print "************** actualiza codigo de impuesto *********** ", vals
                
                # Valida si ya registrado en la base de destino
                code_ids = tax_code_obj.search(cr2, uid, [('code','=',code.code)])
                # Actualiza el registro
                if code_ids:
                    tax_code_obj.write(cr2, uid, code_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    tax_code_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def update_info_tax(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de los impuestos de la base de datos
        """
        # Inicializa variables
        tax_obj = self.pool.get('account.tax')
        tax_code_obj = self.pool.get('account.tax.code')
        tax_categ_obj = self.pool.get('account.tax.category')
        account_obj = self.pool.get('account.account')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de las categorias de la base origen
            tax_ids = tax_obj.search(cr1, uid, [], context=context)
            for tax in tax_obj.browse(cr1, uid, tax_ids, context=context):
                # Arreglo para actualizacion de datos sobre los impuestos
                vals = {
                    'name': tax.name,
                    'description': tax.description,
                    'type_tax_use': tax.type_tax_use,
                    'active': tax.active,
                    'type': tax.type,
                    'amount': tax.amount,
                    'sequence': tax.sequence,
                    'price_include': tax.price_include,
                    'child_depend': tax.child_depend,
                    'python_compute': tax.python_compute,
                    'python_compute_inv': tax.python_compute_inv,
                    'applicable_type': tax.applicable_type,
                    'python_applicable': tax.python_applicable,
                    'domain': tax.domain,
                    'tax_sign': tax.tax_sign,
                    'ref_tax_sign': tax.ref_tax_sign,
                    'chil_depend': tax.child_depend,
                }
                
                # Busca la categoria de impuesto
                if tax.tax_category_id:
                    categ_ids = tax_categ_obj.search(cr2, uid, [('code', '=', tax.tax_category_id.code)])
                    if categ_ids:
                        # Agrega el id del registro
                        vals['tax_category_id'] = categ_ids[0]
                
                # Busca la cuenta de impuestos por trasladar
                if tax.account_collected_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', tax.account_collected_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_collected_id'] = account_ids[0]
                
                # Busca la cuenta de impuestos de nota de venta
                if tax.account_collected_note_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', tax.account_collected_note_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_collected_note_id'] = account_ids[0]
                
                # Busca la cuenta de impuestos trasladados
                if tax.account_collected_id_apply:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', tax.account_collected_id_apply.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_collected_id_apply'] = account_ids[0]
                
                # Busca la cuenta de impuestos de nota de credito por trasladar
                if tax.account_paid_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', tax.account_paid_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_paid_id'] = account_ids[0]
                
                # Busca la cuenta de impuestos de nota de credito trasladados
                if tax.account_paid_id_apply:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', tax.account_paid_id_apply.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_paid_id_apply'] = account_ids[0]
                
                # Busca el codigo de impuesto
                if tax.tax_code_id:
                    code_ids = tax_code_obj.search(cr2, uid, [('code', '=', tax.tax_code_id.code)])
                    if code_ids:
                        # Agrega el id del registro
                        vals['tax_code_id'] = code_ids[0]
                
                # Busca el codigo de impuesto de nota de credito
                if tax.ref_tax_code_id:
                    code_ids = tax_code_obj.search(cr2, uid, [('code', '=', tax.ref_tax_code_id.code)])
                    if code_ids:
                        # Agrega el id del registro
                        vals['ref_tax_code_id'] = code_ids[0]
                
                # Busca los impuestos hijos relacionados
                if tax.child_ids:
                    child_list = []
                    for child in tax.child_ids:
                        # Valida que tenga un codigo de impuesto
                        if child.description:
                            # Busca el impuesto y lo agrega a la lista
                            tax_ids = tax_obj.search(cr2, uid, [('description', '=', child.description)])
                            if tax_ids:
                                # Agrega el id del registro
                                child_list.append(tax_ids[0])
                    vals['child_ids'] = [[6, 0, child_list]]
                
                print "************** actualiza impuesto *********** ", tax.description
                #print "************** actualiza impuesto *********** ", vals
                
                # Valida si ya registrado en la base de destino
                tax_ids = tax_obj.search(cr2, uid, [('description','=',tax.description)])
                # Actualiza el registro
                if tax_ids:
                    tax_obj.write(cr2, uid, tax_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    tax_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def action_update_data(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de impuestos
        """
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Obtiene la base de datos origen
            db_origin = data.db_list
            # Obtiene la base de datos destino
            db_dest = data.database_id.code or False
            
            # Actualiza la informacion de la base
            self.update_info_tax_category(db_origin, db_dest, context=context)
            self.update_info_tax_code(db_origin, db_dest, context=context)
            self.update_info_tax(db_origin, db_dest, context=context)
        # Muestra un mensaje indicando la actualizacion del registro
        return self.pool.get('warning').info(cr, uid, title='Proceso Completo!', message=_("Se completo la actualizacion de los registros de la base origen %s a la base destino %s")%(db_origin,db_dest))
    
admon_update_tax_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
