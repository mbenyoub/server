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
import base64

# ---------------------------------------------------------
# Actualizacion de categoria de productos
# ---------------------------------------------------------

class admon_update_data_account_account(osv.osv_memory):
    """
        Actualiza la informacion de las cuentas sobre la base de datos
    """
    _name = "admon.update.data.account.account.wizard"
    
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
        'type': fields.selection([('csv','Archivo CSV'),('db','Plantilla BD')], 'Tipo de importacion', help="Si aplica la actualizacion sobre base de datos actualiza el resultado sobbre el plan de cuentas registrado sin eliminar ninguna cuenta."),
        # Gestiona bases de datos activas sobre el servidor
        'db_list': fields.selection(_get_method_db_selection, "Base de Datos origen"),
        # Actualizacion por archivo csv
        'update_data': fields.binary('Archivo importacion', filters='*.csv', help='Importacion de informacion basica de cuentas sobre la base de datos seleccionada en formato csv'),
        # Base a actualizar
        'database_id': fields.many2one('admon.database', 'Base de Datos destino', select=True, ondelete='cascade', required=True),
    }
    
    _defaults = {
        'type': 'db'
    }
    
    def get_import_data(self, csv_file, line=1):
        """
            Obtiene la informacion del archivo csv
        """
        doc_csv = base64.decodestring(csv_file)
        data = []
        import_data = []
        data = doc_csv.split('\n')
        for reg in data:
            # Registros a agregar en los movimientos
            import_data.append(reg.split(","))
        # ELimina el encabezado en caso de estar en el arreglo
        if import_data[0][0] in ['id','code','codigo','Codigo'] or import_data[0][1] not in ['create','edit','delete']:
            reg =  import_data.pop(0) # first item
            # Indica que la linea empieza a importar a partir del 2
            line = 2
        return import_data, line
    
    def import_account_to_db(self, db_name, import_data, line=1, context=None):
        """
            Revisa el csv cargado y actualiza la informacion de las cuentas
        """
        # Inicializa variables
        account_obj = self.pool.get('account.account')
        acc_type_obj = self.pool.get('account.account.type')
        data_obj = self.pool.get('ir.model.data')
        db_obj = self.pool.get('admon.database')
        if context is None:
            context = {}
        uid = 1
        
        create_list = []
        
        # Crea la conexion a la bd
        cr = db_obj.conect_to_db(db_name)
        
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            # Valida que el registro sea un arreglo
            if type(reg) != list:
                x = import_data.index(reg)
                del import_data[x]
                continue
            
            # Valida que el registro contenga mas de un dato
            if len(reg) <= 1:
                x = import_data.index(reg)
                del import_data[x]
                continue
            
            print "******************* reg *************** ", reg
            
            # Valida que haya una accion definida, de no tenerla continua con el siguiente registro
            if reg[1] == '':
                continue
            
            # Valida que la accion a realizar
            if reg[1] not in ['create','edit','delete']:
                raise osv.except_osv("Error Validacion","Revise que las acciones registradas sobre la importacion de cuentas sea valida (Linea: %s, columna: 1)"%(line,))
            
            # Valida que si es un registro a eliminar o modificar tenga el codigo de la cuenta
            if reg[1] in ['edit','delete']:
                # Valida que tenga un codigo de referencia
                if reg[0] == '':
                    raise osv.except_osv("Error Validacion","Revise que los registros a eliminar o modificar tengan la referencia del codigo (Linea: %s, columna: 0)"%(line,))
                # Valida que el codigo a modificar exista
                account_ids = account_obj.search(cr, uid, [('code','=',reg[0])])
                if not account_ids:
                    raise osv.except_osv("Error Validacion","El codigo de la cuenta '%s' no esta registrado en la base de datos, valide que el codigo de la cuenta sea correcto (Linea: %s, columna: 1)"%(reg[0],line))
            
            # Validaciones al crear cuenta
            if reg[1] in ['create']:
                # Valida que el codigo de la cuenta no este registrado
                account_ids = account_obj.search(cr, uid, [('code','=',reg[2])])
                if account_ids:
                    raise osv.except_osv("Error Validacion","El codigo de la cuenta '%s' ya esta registrado en la base de datos (Linea: %s, columna: 2)"%(reg[2],line))
                # Valida que tenga un nombre para la cuenta
                if reg[3] == '':
                    raise osv.except_osv("Error Validacion","El nombre de la cuenta no puede estar vacio (Linea: %s, columna: 3)"%(line,))
                # Valida el tipo de cuenta sobre las cuentas al crear un registro
                if reg[5] not in ['view','other','receivable','payable','liquidity','consolidation','close']:
                    raise osv.except_osv("Error Validacion","Revise que el tipo interno sea valido (Linea: %s, columna: 5)"%(line,))
                # Valida que exista la cuenta padre
                account_apply = reg[4] in create_list
                print "********* esta en la lista a crear ******** ", reg[4], " - ", create_list, " Valida ", account_apply, '  ', '195' in create_list
                if account_apply == False:
                    account_ids = account_obj.search(cr, uid, [('code','=',reg[4])])
                    if not account_ids:
                        raise osv.except_osv("Error Validacion","El codigo de la cuenta padre '%s' no esta registrado en la base de datos, valide que el codigo de la cuenta sea correcto (Linea: %s, columna: 4)"%(reg[4],line))
                # Valida que exista el tipo interno a registrar
                type_ids = acc_type_obj.search(cr, uid, [('code','=',reg[6])])
                if not type_ids:
                    raise osv.except_osv("Error Validacion","El tipo de cuenta seleccionado no esta registrado en la base de datos, valide que el codigo sea correcto (Linea: %s, columna: 7)"%(reg[4],line))
                
                # Asigna a la lista de cuentas a crear
                create_list.append(reg[2])
                
            # Validacioens a la edicion de cuenta
            if reg[1] in ['edit']:
                # Valida el tipo de cuenta sobre las cuentas
                if reg[5] not in ['','view','other','receivable','payable','liquidity','consolidation','close']:
                    raise osv.except_osv("Error Validacion","Revise que el tipo interno sea valido (Linea: %s, columna: 5)"%(line,))
                # Valida que exista la cuenta padre
                if reg[4]:
                    account_apply = reg[4] in create_list
                    if account_apply == False:
                        account_ids = account_obj.search(cr, uid, [('code','=',reg[4])])
                        if not account_ids:
                            raise osv.except_osv("Error Validacion","El codigo de la cuenta padre '%s' no esta registrado en la base de datos, valide que el codigo de la cuenta sea correcto (Linea: %s, columna: 4)"%(reg[4],line))
                if reg[6]:
                    # Valida que exista el tipo interno a registrar
                    type_ids = acc_type_obj.search(cr, uid, [('code','=',reg[6])])
                    if not type_ids:
                        raise osv.except_osv("Error Validacion","El tipo de cuenta seleccionado no esta registrado en la base de datos, valide que el codigo sea correcto (Linea: %s, columna: 6)"%(reg[4],line))
                # Asigna a la lista de cuentas a modificar
                create_list.append(reg[2])
                
            # Incrementa la linea recorrida
            line += 1
        try:
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenga una accion definida
                if reg[1] == '':
                        continue
                
                print "************** accion *************** ", reg[1]
                
                # Verifica si es la accion de eliminar
                if reg[1] == 'delete':
                    # Elimina el registro
                    account_ids = account_obj.search(cr, uid, [('code','=',reg[0])], context=context)
                    print "********* borra registros ********** ", reg[0], " - ", account_ids
                    if account_ids:
                        account_obj.unlink(cr, uid, account_ids, context=context)
                    continue
                    
                # Crea un diccionario con la informacion que debe llevar el nuevo registro con los datos predefinidos
                data = {
                    'active': True,
                    'reconcile': True,
                }
                # Agrega el codigo de la cuenta
                if reg[2] != '':
                    data['code'] = reg[2]
                # Agrega el nombre de la cuenta
                if reg[3] != '':
                    data['name'] = reg[3]
                # Agrega el id de la cuenta padre
                if reg[4] != '':
                    # Busca el registro
                    account_ids = account_obj.search(cr, uid, [('code','=',reg[4])], context=context)
                    if account_ids:
                        data['parent_id'] = account_ids[0]
                # Agrega 
                if reg[5] != '':
                    data['type'] = reg[5]
                # Agrega el id de la cuenta padre
                if reg[6] != '':
                    # Busca el registro
                    type_ids = acc_type_obj.search(cr, uid, [('code','=',reg[6])], context=context)
                    if type_ids:
                        data['user_type'] = type_ids[0]
                print "************** data ************** ", data
                
                # Agrega el nuevo registro
                if reg[1] == 'edit':
                    account_ids = account_obj.search(cr, uid, [('code','=',reg[0])], context=context)
                    
                    account_obj.write(cr, uid, account_ids, data, context=context)
                else:
                    res_id = account_obj.create(cr, uid, data, context=context)
        finally:
            cr.close()
        return True
    
    def update_info_account_account_type(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de los tipos de cuenta de la base de datos
        """
        # Inicializa variables
        type_obj = self.pool.get('account.account.type')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de la base origen
            type_ids = type_obj.search(cr1, uid, ['|',('active','=',True),('active','=',False)], context=context)
            print "*************** tipos a comprobar *************", len(type_ids)
            for acc_type in type_obj.browse(cr1, uid, type_ids, context=context):
                # Arreglo para actualizacion de datos sobre la categoria
                vals = {
                    'name': acc_type.name,
                    'code': acc_type.code,
                    'report_type': acc_type.report_type,
                    'close_method': acc_type.close_method,
                    'sign': acc_type.sign,
                    'note': acc_type.note,
                    'active': acc_type.active
                }
                
                # Valida si ya existe el registro
                type_ids = type_obj.search(cr2, uid, [('code','=',acc_type.code),'|',('active','=',True),('active','=',False)])
                print "*************** tipo codigo int ********** ", acc_type.code
                print "*************** codigo activo ********** ", acc_type.active
                print "*************** ids ********** ", type_ids
                #print "*************** data ********** ", vals
                # Actualiza el registro
                if type_ids:
                    type_obj.write(cr2, uid, type_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    # Valida que no este inactiva para actualizar el registro
                    if acc_type.active:
                        type_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def update_info_account_account_category(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de los rubros fiscales de la base de datos
        """
        # Inicializa variables
        categ_obj = self.pool.get('account.account.category')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de la base origen
            categ_ids = categ_obj.search(cr1, uid, [], context=context)
            for categ in categ_obj.browse(cr1, uid, categ_ids, context=context):
                # Arreglo para actualizacion de datos sobre la categoria
                vals = {
                    'name': categ.name,
                    'code': categ.code,
                    'exclude_deduction': categ.exclude_deduction,
                    'exclude_cum_income': categ.exclude_cum_income,
                    'active': categ.active,
                    'description': categ.description,
                }
                
                # Valida si ya esta registrado el campo
                categ_ids = categ_obj.search(cr2, uid, [('code','=',categ.code)])
                print "******************* codigo categoria *************** ", categ.code
                print "******************* ids categoria *************** ", categ_ids
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
    
    def update_info_account_account(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion del plan de cuentas
        """
        # Inicializa variables
        account_obj = self.pool.get('account.account')
        type_obj = self.pool.get('account.account.type')
        category_obj = self.pool.get('account.account.category')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Actualiza la lista de tipos de cuenta y rubros fiscales
            self.update_info_account_account_type(db_origin, db_destiny, context=context)
            self.update_info_account_account_category(db_origin, db_destiny, context=context)
            
            # Recorre los registros de las cuentas
            account_ids = account_obj.search(cr1, uid, [], context=context)
            for account in account_obj.browse(cr1, uid, account_ids, context=context):
                # Arreglo para actualizacion de datos sobre la cuenta
                vals = {
                    'name': account.name,
                    'code': account.code,
                    'type': account.type,
                    'active': account.active,
                    'reconcile': account.reconcile,
                    'apply_situacion_actual': account.apply_situacion_actual,
                    'note': account.note
                }
                
                # Busca el padre de la cuenta
                if account.parent_id:
                    parent_ids = account_obj.search(cr2, uid, [('code', '=', account.parent_id.code)])
                    if parent_ids:
                        # Agrega el id del registro
                        vals['parent_id'] = parent_ids[0]
                
                # Busca el tipo de cuenta
                if account.user_type:
                    type_ids = type_obj.search(cr2, uid, [('code', '=', account.user_type.code)])
                    if type_ids:
                        # Agrega el id del registro
                        vals['user_type'] = type_ids[0]
                
                # Busca los rubros fiscales
                if account.category_id:
                    category_list = []
                    for category in account.category_id:
                        # Valida que tenga un rubro fiscal
                        if category.code:
                            # Busca el rubro fiscal y lo agrega a la lista
                            category_ids = category_obj.search(cr2, uid, [('code', '=', category.code)])
                            if category_ids:
                                # Agrega el id del registro
                                category_list.append(category_ids[0])
                    vals['category_id'] = [[6, 0, category_list]]
                
                # Valida si la cuenta ya esta registrada
                account_ids = account_obj.search(cr2, uid, [('code','=',account.code)])
                # Actualiza el registro
                if account_ids:
                    print "********* modifica cuenta ********** ", account.code
                    #print "********* modifica cuenta ********** ", vals
                    account_obj.write(cr2, uid, account_ids, vals, context=context)
                # Crea el nuevo registro
                else:
                    print "********* crea cuenta ********** ", account.code
                    #print "********* crea cuenta ********** ", vals
                    account_obj.create(cr2, uid, vals, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def action_update_data(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion del plan de cuentas
        """
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Obtiene la base de datos destino
            db_dest = data.database_id.code or False
            
            # Valida si se va a actualizar el plan de cuentas por un csv o por una base de datos origen
            if data.type == 'csv':
                # Obtiene la informacion del archivo
                import_data, line = self.get_import_data(data.update_data, 1)
                # Actualiza la informacion del plan de cuentas
                self.import_account_to_db(db_dest, import_data, line, context=context)
            else:
                # Obtiene la base de datos origen
                db_origin = data.db_list
                # Actualiza la informacion del plan de cuentas
                self.update_info_account_account(db_origin, db_dest, context=context)
                
        # Muestra un mensaje indicando la actualizacion del registro
        return self.pool.get('warning').info(cr, uid, title='Proceso Completo!', message=_("Se completo la actualizacion de los registros a la base de datos %s")%(db_dest))
    
admon_update_data_account_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
