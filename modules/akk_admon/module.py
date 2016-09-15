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
import openerp.addons.decimal_precision as dp
from openerp import netsvc

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import osv, fields

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

import os
import tempfile
import base64

# ---------------------------------------------------------
# Administrar Bases de datos
# ---------------------------------------------------------

class module(osv.Model):
    _inherit = "ir.module.module"
    
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
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
            if ids:
                return self.name_get(cr, user, ids, context=context)
        return super(module, self).name_search(cr, user, name, args=args, operator=operator, context=context, limit=limit)
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        res = []
        for record in self.read(cr, uid, ids, ['shortdesc','name'], context=context):
            name = "%s  (%s)"%(record['shortdesc'], record['name'])
            res.append((record['id'],name ))
        return res
    
module()

class admon_module(osv.osv):
    _name = "admon.database.module"
    _description = "Module"

    _columns = {
        'module_id': fields.many2one('ir.module.module', 'Modulo', ondelete="cascade"),
        'admon_default': fields.boolean('Default modulo'),
        'shortdesc': fields.related('module_id', 'shortdesc', type='char', string="Nombre Corto", readonly=True),
        'summary': fields.related('module_id', 'summary', type='char', string="Resumen", readonly=True),
        'name': fields.related('module_id', 'name', type='char', string="Nombre", readonly=True),
        'icon_image': fields.related('module_id', 'icon_image', type="binary", string="Icono", readonly=True),
        'database_ids': fields.one2many('admon.database.module.relation', 'module_id', 'Bases de datos'),
        'sequence': fields.integer('Prioridad')
    }

    _defaults = {
        'admon_default': False,
        'sequence': 10
    }
    _order = 'sequence asc'
    
    def update_module(self, db_name, module, rel_id=False):
        """
            Actualiza un modulo sobre la base de datos
        """
        # Crea un nuevo registro
        db = ws()
        context={}
        uid = 1
        mod_obj = self.pool.get('ir.module.module')
        data_obj = self.pool.get('ir.model.data')
        mod_rel_obj = self.pool.get('admon.database.module.relation')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            # Revisa si el modulo existe en la base de datos
            mod_ids = mod_obj.search(cr, uid, [('name','=',module)], context=context)
            if mod_ids:
                # Revisa si el modulo esta instalado
                mod = mod_obj.browse(cr, uid, mod_ids[0], context=context)
                print "************ update modules ********** ",db_name, " - ", module, " - ", mod.state
                if mod.state == 'installed':
                    print "********** update ", db_name, " ************** ", module
                    mod_obj.button_immediate_upgrade(cr, uid, [mod.id], context=context)
                elif mod.state == 'to_install':
                    print "********** to install ", db_name, " ************** ", module
                    mod.obj.button_install_cancel(cr, uid, [mod.id], context=context)
                    mod_obj.button_immediate_install(cr, uid, [mod.id], context=context)
                elif mod.state == 'uninstalled':
                    print "********** install ", db_name, "  ************* ", module
                    mod_obj.button_immediate_install(cr, uid, [mod.id], context=context)
                elif mod.state == 'to_upgrade':
                    print "********** to upgrade ", db_name, " ************** ", module
                    mod.obj.button_upgrade_cancel(cr, uid, [mod.id], context=context)
                    mod_obj.button_immediate_upgrade(cr, uid, [mod.id], context=context)
                else:
                    # Si ocurre un error pone el modulo como cancelado
                    mod.obj.button_upgrade_cancel(cr, uid, [mod.id], context=context)
                    # Pone el campo de 
                    if rel_id:
                        update_date = time.strftime('%Y-%m-%d %H:%M:%S')
                        mod_rel_obj.write(cr, uid, [rel_id], {'state':'noupdated', 'date_update':update_date})
                    print "*********** error de instalacion de modulo ************* "
                    raise osv.except_osv(_('Error!'),_("No se pudo instalar el modulo '%s' en la base de datos '%s', realice el proceso directo de la base de datos")%(module,db_name))
        finally:
            #print "************* finaliza conexion - ", db_name, " *************** "
            cr.close()
            #sql_db.close_db(db_name)
        return True
    
    def action_update_on_databases(self, cr, uid, ids, context=None):
        """
            Actualiza el modulo en las bases de datos donde esta registrado
        """
        update_ids = []
        update_date = time.strftime('%Y-%m-%d %H:%M:%S')
        mod_name = ''
        db_name = ''
        try:
            # Recorre los registros
            for mod in self.browse(cr, uid, ids, context=context):
                mod_name = mod.name
                # Recorre las bases de datos a aplicar
                for rel in mod.database_ids:
                    db_name = rel.database_id.code
                    # Actualiza el registro
                    self.update_module(db_name, mod_name, rel.id)
                    update_ids.append(rel.id)
            # Cambia el estado del modulo a actualizado
            self.pool.get('admon.database.module.relation').write(cr, uid, update_ids, {'state':'updated', 'date_update':update_date}, context=context)
        except Exception:
            print "****** exepcion ***** 2 ", update_ids
            # Cambia el estado del modulo a actualizado
            self.pool.get('admon.database.module.relation').write(cr, uid, update_ids, {'state':'noupdated', 'date_update':update_date}, context=context)
            #raise osv.except_osv(_('Error!'),_("Ocurrio un error al actualizar el modulo %s, intentelo nuevamente. Si el problema persiste pongase en contacto con el administrador")%(mod_name,))
            return self.pool.get('warning').error(cr, uid, title='Error!', message=_("Ocurrio un error al actualizar el modulo %s, intentelo nuevamente. Si el problema persiste pongase en contacto con el administrador")%(mod_name,))
        return True

    def action_add_all_database(self, cr, uid, ids, context=None):
        """
            Actualiza la lista de bases de datos y agrega todas las bases sobre el modulo
        """
        update_ids = []
        update_date = time.strftime('%Y-%m-%d %H:%M:%S')
        rel_obj = self.pool.get('admon.database.module.relation')
        database_obj = self.pool.get('admon.database')
        # Recorre los registros
        for module in self.browse(cr, uid, ids, context=context):
            # Revisa si ya hay modulos agregados y si ya hay relacionados los elimina
            rel_ids = rel_obj.search(cr, uid, [('module_id','=',module.id)])
            if rel_ids:
                rel_obj.unlink(cr, uid, rel_ids, context=context)
            # Crea un registro por cada base de datos
            database_ids = database_obj.search(cr, uid, [('state','=','active')], context=context)
            print "*********** database ids ***************** ", database_ids
            for data in database_ids:
                vals = {
                    'module_id': module.id,
                    'database_id': data,
                    'sequence': module.sequence,
                    'date_update': update_date,
                    'state': 'unupdated'
                }
                #print "******************** vals ******************** ", vals
                # Crea el nuevo registro
                rel_obj.create(cr, uid, vals, context=context)
                
admon_module()

class admon_module_rel(osv.osv):
    _name = "admon.database.module.relation"
    _description = "relation Database/Module"

    _columns = {
        'sequence': fields.integer('Prioridad'),
        'database_id': fields.many2one('admon.database', 'Base de datos'),
        'module_id': fields.many2one('admon.database.module', 'Modulo'),
        'date_update': fields.datetime('Ultima actualizacion'),
        'state': fields.selection([
                        ('unupdated','No actualizado'),
                        ('updated','Actualizado'),
                        ('noupdated','Fallo Actualizacion')], 'Estado', required=True),
    }

    _defaults = {
        'state': 'unupdated',
        'date_update': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        if not vals.get('sequence', False):
            vals['sequence'] = self.pool.get('admon.database.module').browse(cr, uid, vals['module_id'], context=context).sequence
        
        # Funcion original de crear
        res = super(admon_module_rel, self).create(cr, uid, vals, context=context)
        return res
    
    def action_update(self, cr, uid, ids, context=None):
        """
            Actualiza el modulo en la base de datos
        """
        update_date = time.strftime('%Y-%m-%d %H:%M:%S')
        mod_name = ''
        db_name = ''
        mod_obj = self.pool.get('admon.database.module')
        
        try:
            # Recorre los registros
            for rel in self.browse(cr, uid, ids, context=context):
                mod_name = rel.module_id.name
                db_name = rel.database_id.code
                # Actualiza el registro
                mod_obj.update_module(db_name, mod_name, rel.id)
            # Cambia el estado del modulo a actualizado
            self.write(cr, uid, ids, {'state':'updated', 'date_update':update_date}, context=context)
        except Exception:
            print "****** exepcion 3 ***** ", ids, "   ", Exception
            # Cambia el estado del modulo a actualizado
            self.write(cr, uid, ids, {'state':'noupdated', 'date_update':update_date}, context=context)
            #raise osv.except_osv(_('Error!'),_("Ocurrio un error al actualizar el modulo %s, intentelo nuevamente. Si el problema persiste pongase en contacto con el administrador")%(mod_name,))
            return self.pool.get('warning').error(cr, uid, title='Error!', message=_("Ocurrio un error al actualizar el modulo %s, intentelo nuevamente. Si el problema persiste pongase en contacto con el administrador")%(mod_name,))
        return True
    
    _order = 'sequence,state asc'

admon_module_rel()
