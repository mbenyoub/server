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
from openerp.osv import fields, osv, orm
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

import math
import re

# ---------------------------------------------------------
# Actualizacion de registros
# ---------------------------------------------------------

class admon_database_user(osv.Model):
    _name = "admon.database.user"
    
    _columns = {
        'id': fields.integer('ID'),
        'name': fields.char('Nombre', required=True),
        'login': fields.char('Usuario', size=64, required=True, help="Utilizado para conectarse al sistema"),
        'password': fields.char('Password', size=64, invisible=True),
        'user_email': fields.char('Email', size=128),
        'database_id': fields.many2one('admon.database', 'Base de Datos', select=True, ondelete='cascade', required=True),
        'state': fields.selection([
                        ('draft','Borrador'),
                        ('active','Activo'),
                        ('inactive','Inactivo'),
                        ('delete','Eliminado'),
                        ('cancel','Cancelado')], 'Estado', required=True),
        'info': fields.text('Comentarios'),
        'profile_id': fields.many2one('admon.database.user.profile', 'Perfil de Usuario', ondelete='set null', required=True),
        'date_end': fields.date('Fecha vencimiento'),
        'db_user_id': fields.integer('Id Usuario BD'),
        'superuser': fields.boolean('Superuser')
    }
    
    def _get_date_end(self, cr, uid, date, days, context=None):
        """
            Obtiene la fecha de notificacion
        """
        if days:
            date = datetime.strptime(date, '%Y-%m-%d')
            date = date + timedelta(days=days)
            return date.strftime('%Y-%m-%d')
        return date
    
    def _get_date_end_default(self, cr, uid, ids, context=None):
        """
            Obtiene la fecha de vencimiento por default 15 dias
        """
        date = time.strftime('%Y-%m-%d')
        date = self._get_date_end(cr, uid, date, 15, context=context)
        return date
    
    _defaults = {
        'password': '',
        'state': 'draft',
        'date_end': _get_date_end_default,
        'superuser': False
    }
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Elimina el registro del calendario de actividades
        """
        if context is None:
            context = {}
        
        # Valida que solo se puedan eliminar los registros que esten en estado borrador o cancelado
        for user in self.browse(cr, uid, ids, context=context):
            if user.state == 'draft' or user.state == '':
                continue
            else:
                raise osv.except_osv(_('Error!'),_("No se puede eliminar el usuario, solo se pueden eliminar usuarios en estado borrador o cancelado"))
        
        # Elimina los registros
        res = super(admon_database_user, self).unlink(cr, uid, ids, context=context)
        return res
    
    def update_user(self, db_name, user_id, vals, profile):
        """
            Crea un nuevo usuario sobre la base de datos
        """
        # Crea un nuevo registro
        db = ws()
        context = {}
        uid = 1
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.group')
        data_obj = self.pool.get('ir.model.data')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        # Valida que haya recibido el id del usuario de la base de datos
        if user_id == False:
            raise osv.except_osv(_('Error!'),_("No se registro el id del usuario en la base de datos"))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            group_ids = []
            # Recorre los grupos del perfil y lo asigna al objeto
            if profile:
                for group in profile:
                    (model,xml_id) = group.split(".")
                    try:
                        group_id = data_obj.get_object(cr, uid, model, xml_id).id
                        group_ids.append(group_id)
                    except Exception:
                        continue
                vals['groups_id'] = [(6, 0, group_ids)]
            
            user_obj.write(cr, uid, [user_id], vals, context=context)
        finally:
            cr.close()
        return user_id
    
    def action_update_user(self, cr, uid, ids, context=None):
        """
            Crear un usuario sobre la base de datos
        """
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            # Genera un diccionario con la informacion del usuario
            vals = {
                'name': user.name,
                'login': user.login,
                'email': user.user_email,
            }
            db_name = user.database_id.code
            # Obtiene la informacion del profile
            profile = []
            for group in user.profile_id.groups_id:
                profile.append(group.reference)
            # Actualiza la informacion del usuario sobre la base de datos
            user_id = self.update_user(db_name, user.db_user_id, vals, profile)
        return True
    
    def create_user(self, db_name, user, profile):
        """
            Crea un nuevo usuario sobre la base de datos
        """
        # Crea un nuevo registro
        db = ws()
        context = {}
        uid = 1
        user_id = False
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.group')
        data_obj = self.pool.get('ir.model.data')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            group_ids = []
            # Recorre los grupos del perfil y lo asigna al objeto
            if profile:
                for group in profile:
                    (model,xml_id) = group.split(".")
                    try:
                        group_id = data_obj.get_object(cr, uid, model, xml_id).id
                        group_ids.append(group_id)
                    except Exception:
                        continue
                user['groups_id'] = [(6, 0, group_ids)]
            # Crea el nuevo usuario
            user_id = user_obj.create(cr, uid, user, context=context)
            #try:
            #    cr.execute("update res_users set password='123' where id=4")
            #except Exception, e:
            #    _logger.error('Modify DB: %s failed:\n%s', db_name, e)
            #    raise Exception("No se pudo modificar el usuario en la base %s: %s" % (db_name, e))
        finally:
            cr.close()
        return user_id
    
    def action_create_user(self, cr, uid, ids, context=None):
        """
            Crear un usuario sobre la base de datos
        """
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            # Genera un diccionario con la informacion del usuario
            vals = {
                'name': user.name,
                'login': user.login,
                'password': user.login,
                'email': user.user_email,
                'notification_email_send': 'comment'
            }
            db_name = user.database_id.code
            # Valida si hay suficiente espacio para agregar nuevos registros sobre la base de datos
            if user.database_id.active_users >= user.database_id.max_user:
                raise osv.except_osv(_('Error!'),_("Se ha exedido el limite de usuarios disponible para la base '%s'")%(db_name,))
            
            #print "************** db name **************** ", db_name
            # Obtiene la informacion del profile
            profile = []
            for group in user.profile_id.groups_id:
                profile.append(group.reference)
            #print "***************** create user *********** ", vals, " ** ", profile
            # Crea el nuevo usuario sobre la base de datos
            user_id = self.create_user(db_name, vals, profile)
            # Cambia el estado del usuario a activo
            self.write(cr, uid, [user.id], {'state':'active', 'db_user_id': user_id}, context=context)
        return True
    
    def reset_pass_user(self, db_name, user_id, password):
        """
            Actualiza el password del usuario en la base de datos
        """
        db = ws()
        context = {}
        uid = 1
        user_obj = self.pool.get('res.users')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        # Valida que haya recibido el id del usuario de la base de datos
        if user_id == False:
            raise osv.except_osv(_('Error!'),_("No se registro el id del usuario en la base de datos"))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            # Inactiva al usuario
            user_obj.write(cr, uid, [user_id], {'password': password}, context=context)
        finally:
            cr.close()
        return True
    
    def action_reset_pass(self, cr, uid, ids, context=None):
        """
            Pone la contraseña igual al usuario
        """
        if context is None:
            context = {}
        
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            db_name = user.database_id.code
            # Resetea el password del usuario sobre la base de datos
            self.reset_pass_user(db_name, user.db_user_id, user.password)
        return True
    
    def active_user(self, db_name, user_id):
        """
            Pone como activo al usuario en la base de datos
        """
        # Crea un nuevo registro
        db = ws()
        context = {}
        uid = 1
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.group')
        data_obj = self.pool.get('ir.model.data')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        # Valida que haya recibido el id del usuario de la base de datos
        if user_id == False:
            raise osv.except_osv(_('Error!'),_("No se registro el id del usuario en la base de datos"))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            # Inactiva al usuario
            user_obj.write(cr, uid, [user_id], {'active': True}, context=context)
        finally:
            cr.close()
        return True
    
    def action_active_user(self, cr, uid, ids, context=None):
        """
            Pone al usuario como activo
        """
        if context is None:
            context = {}
        date = time.strftime('%Y-%m-%d')
        
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            db_name = user.database_id.code
            # Valida si hay suficiente espacio para agregar nuevos registros sobre la base de datos
            if user.database_id.active_users >= user.database_id.max_user:
                raise osv.except_osv(_('Error!'),_("Se ha exedido el limite de usuarios disponible para la base '%s'")%(db_name,))
            
            # Inactiva el usuario sobre la base de datos
            self.active_user(db_name, user.db_user_id)
        
        # Obtiene la fecha por default a 30 dias si no recibe el valor
        if context.get('date_end', False):
            date = context.get('date_end')
        else:
            date = _get_date_end(self, cr, uid, date, 30, context=None)
        
        # Cambia el estado del usuario a activo
        self.write(cr, uid, ids, {'state':'active', 'date_end': date}, context=context)
        return True
    
    def inactive_user(self, db_name, user_id):
        """
            Pone como inactivo al usuario en la base de datos
        """
        # Crea un nuevo registro
        db = ws()
        context = {}
        uid = 1
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.group')
        data_obj = self.pool.get('ir.model.data')
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        # Valida que haya recibido el id del usuario de la base de datos
        if user_id == False:
            raise osv.except_osv(_('Error!'),_("No se registro el id del usuario en la base de datos"))
        
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        try:
            # Inactiva al usuario
            user_obj.write(cr, uid, [user_id], {'active': False}, context=context)
        finally:
            cr.close()
        return True
    
    def action_delete_user(self, cr, uid, ids, context=None):
        """
            Elimina al usuario de la base de datos
        """
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            # Elimina al registro si se encuentra en estado borrador
            if user.state == 'draft':
                self.unlink(cr, uid, [user.id], context=context)
                continue
            
            db_name = user.database_id.code
            # Inactiva el usuario sobre la base de datos
            self.inactive_user(db_name, user.db_user_id)
        
        # Cambia el estado del usuario a eliminado
        self.write(cr, uid, ids, {'state':'delete'}, context=context)
        return True
    
    def action_inactive_user(self, cr, uid, ids, context=None):
        """
            Pone al usuario como inactivo
        """
        # Recorre los registros
        for user in self.browse(cr, uid, ids, context=context):
            db_name = user.database_id.code
            # Inactiva el usuario sobre la base de datos
            self.inactive_user(db_name, user.db_user_id)
        
        #print "************ write ids ********** ", ids
        # Cambia el estado del usuario a activo
        self.write(cr, uid, ids, {'state':'inactive'}, context=context)
        return True
    
    def cron_inactive_user(self, cr, uid, context=None):
        """
            Inactiva los usuarios donde la fecha de vencimiento ya paso
        """
        if context is None:
            context = {}
        user_ids = []
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene a los partners que se les tiene que enviar la notificacion
        cr.execute("""
         select id
         from admon_database_user
         where
            state='active' and superuser = False and
            date_end<'%s'"""%(date,))
        user_ids = [x[0] for x in cr.fetchall()]
        
        # Pone como inactivos a los usuarios recibidos
        if user_ids:
            self.action_inactive_user(cr, uid, user_ids, context=context)
        return True
    
    def action_active_user_wizard(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard para solicitar la nueva fecha de vencimiento del usuario
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'akk_admon', 'view_admon_active_user_wizard')
        
        return {
            'name':_("Activar usaurio"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'admon.active.user.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_user_id': ids[0],
            }
        }
    
admon_database_user()

class admon_database_user_profile(osv.Model):
    _name = "admon.database.user.profile"
    
    _columns = {
        'name': fields.char('Nombre', required=True),
        'info': fields.text('Comentarios'),
        'groups_id': fields.many2many('admon.database.user.profile.groups', 'admon_database_groups_users_rel', 'uid', 'gid', 'Grupos'),
    }
    
admon_database_user_profile()

class admon_database_user_profile_groups(osv.Model):
    _name = "admon.database.user.profile.groups"
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'reference': fields.char('Referencia', required=True, help="referencia sobre el id externo de la base de datos"),
    }
    
admon_database_user_profile_groups()

# ---------------------------------------------------------
# Importacion de impuestos
# ---------------------------------------------------------

class admon_database_import(osv.Model):
    _name = "admon.database.import"
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'code': fields.char('Codigo', size=64, required=True, help="Valor del codigo sobre el que hara referencia para identificar el impuesto o codigo fiscal a aplicar"),
        'type_tax': fields.selection([('tax','Impuesto'),
                                    ('code','Codigo Fiscal'),], 'Tipo', required=True),
        'type_code': fields.selection([('month','Mensual'),
                                    ('year','Anual'),], 'Tipo codigo Fiscal'),
    }
    
    _defaults = {
        'type_tax': 'tax',
        'type_code': 'month'
    }
    
admon_database_import()

# ---------------------------------------------------------
# Informacion sobre base de datos
# ---------------------------------------------------------

class admon_database_info(osv.osv):
    _name = "admon.database.info"
    
    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            #print "*************** image ************* ", obj.image
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    def _has_image(self, cr, uid, ids, name, args, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.image != False
        return result
    
    def _get_date_string(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el valor de la fecha con texto
        """
        res = {}
        for info in self.browse(cr, uid, ids, context=context):
            res[info.id] = ' '
            mes_texto = {
                '01': 'Enero',
                '02': 'Febrero',
                '03': 'Marzo',
                '04': 'Abril',
                '05': 'Mayo',
                '06': 'Junio',
                '07': 'Julio',
                '08': 'Agosto',
                '09': 'Septiembre',
                '10': 'Octubre',
                '11': 'Noviembre',
                '12': 'Diciembre',
            }
            if info.date:
                (anio, mes, dia) = info.date.split("-")
                res[info.id] = ' %s de %s de %s '%(dia, mes_texto[mes],anio)
        return res
    
    def get_config_template(self, cr, uid):
        """
            Obtiene de la configuracion los archivos que estan por default
        """
        res = {}
        # Obtiene la configuracion activa
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            conf = self.pool.get('admon.config.settings').browse(cr, uid, data)
            res = {
                'import_partner': conf.import_partner,
                'import_product': conf.import_product,
                'import_asset': conf.import_asset,
                'import_bank': conf.import_bank,
                'import_balance': conf.import_balance,
                'import_payment': conf.import_payment,
                'import_rate': conf.import_rate,
                'import_utility': conf.import_utility,
                'import_tax': conf.import_tax
            }
        return res
    
    def _get_template(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene de la configuracion los archivos que estan por default
        """
        res = {}
        # Obtiene la configuracion activa
        conf = self.get_config_template(cr, uid)
        #print "**************** configuracion ******************* ", conf
        # Recorre los registros
        for id in ids:
            res[id] = {
                'template_partner': conf['import_partner'],
                'template_product': conf['import_product'],
                'template_asset': conf['import_asset'],
                'template_bank': conf['import_bank'],
                'template_balance': conf['import_balance'],
                'template_payment': conf['import_payment'],
                'template_rate': conf['import_rate'],
                'template_utility': conf['import_utility'],
                'template_tax': conf['import_tax']
            }
        return res
    
    _columns = {
        'database_id': fields.many2one('admon.database', 'Base de Datos', select=True, ondelete='cascade'),
        'name': fields.char('Nombre Empresa', size=264),
        'response': fields.char('Nombre Representante legal', size=264),
        'email': fields.char('Correo', size=128),
        'phone': fields.char('Telefono', size=64),
        'mobile': fields.char('Celular', size=64),
        'vat': fields.char('RFC', size=32, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements."),
        'website': fields.char('Website', size=64, help="Website of Partner or Company"),
        'street': fields.char('Direccion', size=128),
        'street2': fields.char('Colonia', size=128),
        'zip': fields.char('CP', change_default=True, size=24),
        'city': fields.char('ciudad', size=128),
        'state_id': fields.many2one("res.country.state", 'Estado'),
        'country_id': fields.many2one('res.country', 'Pais'),
        'l10n_mx_street3': fields.char('Numero Externo', size=128,
            help='External number of the partner address'),
        'l10n_mx_street4': fields.char('Numero Interno', size=128,
            help='Internal number of the partner address'),
        'l10n_mx_city2': fields.char('Localidad', size=128,
            help='Locality configurated for this partner'),
        # image: all image fields are base64 encoded and PIL-supported
        'image': fields.binary("Logo Empresa",
            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'admon.database.info': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of this contact. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'admon.database.info': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),
        'regimen_fiscal_id': fields.many2one('regimen.fiscal', 'Regimen fiscal', store=True, ondelete="set null", select=True),
        # Informacion certificado
        'certificate_file': fields.binary('Certificate File',
            filters='*.cer,*.certificate,*.cert',
            help='This file .cer is proportionate by the SAT'),
        'certificate_key_file': fields.binary('Certificate Key File',
            filters='*.key', help='This file .key is \
            proportionate by the SAT'),
        'certificate_password': fields.char('Certificate Password', size=64,
            invisible=False, help='This password is \
            proportionate by the SAT'),
        'certificate_file_pem': fields.binary('Certificate File PEM',
            filters='*.pem,*.cer,*.certificate,*.cert', help='This file is \
            generated with the file.cer'),
        'certificate_key_file_pem': fields.binary('Certificate Key File PEM',
            filters='*.pem,*.key', help='This file is generated with the \
            file.key'),
        'date_start': fields.date('Date Start', help='Date \
            start the certificate before the SAT'),
        'date_end': fields.date('Date End', help='Date end of \
            validity of the certificate'),
        'serial_number': fields.char('Serial Number', size=64,
            help='Number of serie of the certificate'),
        
        # Informacion para solucion factible
        'sf_email': fields.char('Correo/Usuario', size=128, help='Usuario solucion factible'),
        'sf_password': fields.char('Password', size=64,
            invisible=False, help='Contraseña con la que se registro el usuario de Solucion Factible'),
        'sf_manifesto': fields.binary('Manifiesto',
            filters='*.png,*.jpg,*.pdf',
            help='Documento firmado y escaneado con la informacion de la compañia para timbrado (Formato PNG, JPG o PDF)'),
        'date': fields.date('Fecha'),
        'date_string': fields.function(_get_date_string, method=True, store=False, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
        'sf_manifesto': fields.binary('Manifiesto',
            filters='*.png,*.jpg,*.pdf',
            help='Documento firmado y escaneado con la informacion de la compañia para timbrado (Formato PNG, JPG o PDF)'),
        # Importacion de datos
        'import_partner': fields.binary('Importacion Cliente/Proveedor', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_partner_ok': fields.boolean('Importado'),
        'import_product': fields.binary('Importacion Productos', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_product_ok': fields.boolean('Importado'),
        'import_asset': fields.binary('Importacion Activos', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_asset_ok': fields.boolean('Importado'),
        'import_bank': fields.binary('Importacion de Cuentas bancarias', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_balance': fields.binary('Importacion de saldos iniciales', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_payment': fields.binary('Importacion de cobros y pagos pendientes', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_balance_ok': fields.boolean('Importado'),
        'import_rate': fields.binary('Importacion de saldos fiscales', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_rate_ok': fields.boolean('Importado'),
        'import_utility': fields.binary('Importacion de perdidas fiscales', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_utility_ok': fields.boolean('Importado'),
        'import_tax': fields.binary('Importacion de impuestos a favor', filters='*.csv', help='Importacion de carga inicial de datos proporcionados en formato csv'),
        'import_tax_ok': fields.boolean('Importado'),
        
        # Plantillas para importacion de datos
        'template_partner': fields.function(_get_template, type='binary', string='Plantilla Contacto', store=False, multi='template_binary', readonly=True),
        'template_product': fields.function(_get_template, type='binary', string='Plantilla Producto', store=False, multi='template_binary', readonly=True),
        'template_asset': fields.function(_get_template, type='binary', string='Plantilla Activo', store=False, multi='template_binary', readonly=True),
        'template_bank': fields.function(_get_template, type='binary', string='Plantilla cuentas bancarias', store=False, multi='template_binary', readonly=True),
        'template_balance': fields.function(_get_template, type='binary', string='Plantilla saldos iniciales', store=False, multi='template_binary', readonly=True),
        'template_payment': fields.function(_get_template, type='binary', string='Plantilla pendientes de cobro y pago', store=False, multi='template_binary', readonly=True),
        'template_rate': fields.function(_get_template, type='binary', string='Plantilla saldos fiscales', store=False, multi='template_binary', readonly=True),
        'template_utility': fields.function(_get_template, type='binary', string='Plantilla perdidas fiscales', store=False, multi='template_binary', readonly=True),
        'template_tax': fields.function(_get_template, type='binary', string='Plantilla impuestos a favor', store=False, multi='template_binary', readonly=True),
    }
    
    _defaults = {
        'image': False,
        'date': fields.datetime.now
    }
    
    def _get_period(self, cr, uid, context=None):
        """
            Obtiene el periodo actual
        """
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    
    def conect_to_db(self, db_name):
        """
            Conecta a la base de datos especificada
        """
        db = ws()
        # Valida que exista la base de datos
        db_exist = db.exp_db_exist(db_name)
        if db_exist == False:
            raise osv.except_osv(_('Error!'),_("la base de datos que intenta modificar no existe '%s'")%(db_name,))
        # Crea un cursor que apunte a la base de datos a modificar
        db = sql_db.db_connect(db_name)
        cr = db.cursor()
        cr.autocommit(True) # avoid transaction block
        return cr
    
    def get_import_data(self, csv_file, line=1):
        """
            Obtiene la informacion del archivo para saldos iniciales
        """
        doc_csv = base64.decodestring(csv_file)
        data = []
        import_data = []
        data = doc_csv.split('\n')
        for reg in data:
            # Registros a agregar en los movimientos
            import_data.append(reg.split(","))
        # ELimina el encabezado en caso de estar en el arreglo
        if import_data[0][0] in ['id','code','fiscalyear']:
            reg =  import_data.pop(0) # first item
            #print "************ reg ************** ", reg
            # Indica que la linea empieza a importar a partir del 2
            line = 2
        return import_data, line
    
    def create_account_bank(self, cr, uid, info, context=None):
        """
            Crea la cuenta bancaria para el cliente
        """
        # Inicializa variables
        data_obj = self.pool.get('ir.model.data')
        journal_obj = self.pool.get('account.journal')
        account_obj = self.pool.get('account.account')
        bank_obj = self.pool.get('res.partner.bank')
        user_obj = self.pool.get('res.users')
        num = 1
        
        # Obtiene la cuenta padre de Bancos
        cr.execute(
            """ select id, code, name, parent_id
                from account_account
                where type = 'liquidity' and code like '1113%'
                order by code desc limit 1
            """)
        dat = cr.dictfetchall()
        #print "************* dat ************ ", dat
        code = dat and dat[0]['code'] or False
        parent_id = dat and dat[0]['parent_id'] or False
        #print "******* parent_id ********** ", parent_id
        #print "******* code ********** ", code
        
        # Genera el nuevo codigo a partir del ultimo codigo registrado
        new_code = str(int(code) + 1)
        #print "******** new code ************** ", new_code
        
        # Obtiene el id de la compañia
        company = user_obj.browse(cr, uid, uid, context=context).company_id
        company_id = company.id
        
        # Valida que la cuenta no exista y si existe pone el siguiente
        for n in xrange(num, 100):
            acc_ids = account_obj.search(cr, uid, [('code','=', new_code),('company_id','=',company_id)])
            if not acc_ids:
                break
            new_code = str(int(new_code) + 1)
        
        # Crea la cuenta bancaria
        tmp = data_obj.get_object_reference(cr, uid, 'account', 'data_account_type_bank')
        bank_type = tmp and tmp[1] or False
        account_id = account_obj.create(cr, uid, {
                'name': info['name'],
                'currency_id': False,
                'code': new_code,
                'type': 'liquidity',
                'user_type': bank_type,
                'parent_id': parent_id or False,
                'company_id': company_id,
        })
        
        # Obtiene el numero siguiente para el codigo del diario
        cr.execute(
            """ select count(type) + 1 as num
                from account_journal
                where type in ('bank','cash')
            """)
        dat = cr.dictfetchall()
        current_num = dat and dat[0]['num'] or 1
        # Verifica que no se este usando el numero sobre el diario y si se esta usando lo cambia por el siguiente
        for num in xrange(current_num, 100):
            # journal_code has a maximal size of 5, hence we can enforce the boundary num < 100
            journal_code = 'BNK' + str(num)
            ids = journal_obj.search(cr, uid, [('code', '=', journal_code), ('company_id', '=', company_id)], context=context)
            if not ids:
                break
        
        # Crea el diario sobre el banco
        journal_id = journal_obj.create(cr, uid, {
                'name': info['name'],
                'code': journal_code,
                'type': 'bank',
                'company_id': company_id,
                'analytic_journal_id': False,
                'currency': False,
                'default_credit_account_id': account_id,
                'default_debit_account_id': account_id,
        })
        
        # Agrega la cuenta bancaria a la compañia
        bank_id = bank_obj.create(cr, uid, {
            'state': 'bank',
            'acc_number': info['number'],
            'bank_name': info['name'],
            'clabe': info['clabe'],
            'partner_id': company.partner_id.id or False,
            'journal_id': journal_id,
            'footer': True,
            'company_id': company_id
        })
        #print "***** bank_id *********** ", bank_id
        return account_id
    
    def onchange_import_balance(self, cr, uid, ids, import_bank, import_balance, import_payment, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_bank or not import_balance or not import_payment:
            return {'value':{'import_balance_ok': False}}
        return {}
    
    def import_balance_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        mline_obj = self.pool.get('account.move.line')
        journal_obj = self.pool.get('account.journal')
        bank_obj = self.pool.get('res.partner.bank')
        partner_obj = self.pool.get('res.partner')
        seq_obj = self.pool.get('ir.sequence')
        move_tax_obj = self.pool.get('account.move.tax')
        tax_obj = self.pool.get('account.tax')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line_ban = 1
        line_bal = 1
        line_pay = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo para cuentas bancarias
        import_ban, line_ban = self.get_import_data(info.import_bank, 1)
        # Obtiene la informacion del archivo para saldos iniciales
        import_bal, line_bal = self.get_import_data(info.import_balance, 1)
        # Obtiene la informacion del archivo para cobros y pagos
        import_pay, line_pay = self.get_import_data(info.import_payment, 1)
        
        # Variables para la validacion de registros
        cxp = {
            'bal': {'debit': 0.0,'credit': 0.0,},
            'pay': {'debit': 0.0,'credit': 0.0,}
        }
        cxc = {
            'bal': {'debit': 0.0,'credit': 0.0,},
            'pay': {'debit': 0.0,'credit': 0.0,}
        }
        ant_cxp = {
            'bal': {'debit': 0.0,'credit': 0.0,},
            'pay': {'debit': 0.0,'credit': 0.0,}
        }
        ant_cxc = {
            'bal': {'debit': 0.0,'credit': 0.0,},
            'pay': {'debit': 0.0,'credit': 0.0,}
        }
        credit = 0.0
        debit = 0.0
        
        file_name = "Cuentas bancarias"
        line = line_ban
        # Recorre los archivos importados y valida que la informacion recabada sobre bancos sea correcta
        for reg in import_ban:
            #print "**************** registro a validar - Bancos *************** ", reg
            # Valida que el registro sea un arreglo
            if type(reg) != list:
                x = import_ban.index(reg)
                del import_ban[x]
                continue
            
            # Valida que el registro contenga mas de un dato
            if len(reg) <= 1:
                x = import_ban.index(reg)
                del import_ban[x]
                continue
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un id (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
            
            # Valida que el id no este registrado
            try:
                register_model, register_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
            except (orm.except_orm, ValueError):
                register_id = False
            if register_id:
                raise osv.except_osv("Error Validacion","El id externo ya esta registrado en la base de datos, revise que no se haya importado el registro anteriormente (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
            
            # Valida que tenga un nombre
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Nombre (Linea: %s, columna: 1, archivo: %s)"%(line,file_name))
            
            # Valida que el nombre del banco no se este usando por algun diario
            journal_ids = journal_obj.search(cr, uid, [('name','=',reg[1])])
            if journal_ids:
                raise osv.except_osv("Error Validacion","El Nombre nombre del banco ya se encuentra registrado en la base de datos, valide que no exista un diario con el mismo nombre (Linea: %s, columna: 1, archivo: %s)"%(line,file_name))
            
            # Valida que tenga un saldo
            if reg[2] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor original (Linea: %s, columna: 2, archivo: %s)"%(line,file_name))
            try:
               # Valida que sea un valor flotante
               float(reg[2])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor original valido (Linea: %s, columna: 2, archivo: %s)"%(line,file_name))
            
            # Valida que tenga un numero de cuenta
            if reg[3] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor contable (Linea: %s, columna: 3, archivo: %s)"%(line,file_name))
            
            # Actualiza el total sobre el debe y el haber
            debit += float(reg[2])
            
            # Incrementa la linea recorrida
            line += 1
        
        # Valida que exista la cuenta de cuentas por cobrar sobre la bd
        account_cxc_ids = account_obj.search(cr, uid, [('code','=','1122001000')])
        if not account_cxc_ids:
            raise osv.except_osv("Error Validacion","La cuenta por cobrar cliente no se encuentra registrada (codigo: 1122001000)")
        # Valida que exista la cuenta por pagar a proveedor sobre la bd
        account_cxp_ids = account_obj.search(cr, uid, [('code','=','2122001000')])
        if not account_cxp_ids:
            raise osv.except_osv("Error Validacion","La cuenta por pagar proveedor no se encuentra registrada (codigo: 2122001000)")
        # Valida que exista la cuenta de anticipos a cliente
        account_ant_cxc_ids = account_obj.search(cr, uid, [('code','=','2131001000')])
        if not account_ant_cxc_ids:
            raise osv.except_osv("Error Validacion","La cuenta anticipos a cliente no se encuentra registrada (codigo: 2131001000)")
        # Valida que exista la cuenta de anticipos a cliente
        account_ant_cxp_ids = account_obj.search(cr, uid, [('code','=','1129008000')])
        if not account_ant_cxp_ids:
            raise osv.except_osv("Error Validacion","La cuenta anticipos a proveedor no se encuentra registrada (codigo: 1129008000)")
        
        file_name = "Saldo inicial"
        line = line_bal
        # Recorre los archivos importados y valida que la informacion recabada sobre saldos sea correcta
        for reg in import_bal:
            #print "**************** registro a validar - balance *************** ", reg
            # Valida que el registro sea un arreglo
            if type(reg) != list:
                x = import_bal.index(reg)
                del import_bal[x]
                continue
            
            # Valida que el registro contenga mas de un dato
            if len(reg) <= 1:
                x = import_bal.index(reg)
                del import_bal[x]
                continue
            
            # Valida que si hay un valor sobre el debe o el haber de la cuenta, la cuenta exista sobre el plan contable
            if reg[2] not in ['','0'] or reg[3] not in ['','0']:
                # Valida que exista la cuenta sobre el plan contable
                account_ids = account_obj.search(cr, uid, [('code','=',reg[0])])
                if not account_ids:
                    raise osv.except_osv("Error Validacion","Revise que no se hayan modificado los codigos de las cuentas del plan contable (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
                
                # Valida que el registro con valor sea numero
                if reg[2] != '':
                    try:
                        # Valida que sea un valor flotante
                        float(reg[2])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el debe sean numeros (Linea: %s, columna: 2, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    debit += float(reg[2])
                # Valida que el registro con valor sea numero
                if reg[3] != '':
                    try:
                        # Valida que sea un valor flotante
                        float(reg[3])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el haber sean numeros (Linea: %s, columna: 3, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    credit += float(reg[3])
            
            # Valida que si es la cuenta por cobrar de cliente sume el debe y el haber
            if reg[0] == '1122001000':
                if reg[2] != '':
                    cxc['bal']['debit'] = float(reg[2])
                if reg[3] != '':
                    cxc['bal']['credit'] = float(reg[3])
            
            # Valida que si es la cuenta por pagar a proveedor sume el debe y el haber
            if reg[0] == '2122001000':
                if reg[2] != '':
                    cxp['bal']['debit'] = float(reg[2])
                if reg[3] != '':
                    cxp['bal']['credit'] = float(reg[3])
            
            # Valida que si es la cuenta de anticipos de cliente sume el debe y el haber
            if reg[0] == '2131001000':
                if reg[2] != '':
                    ant_cxc['bal']['debit'] = float(reg[2])
                if reg[3] != '':
                    ant_cxc['bal']['credit'] = float(reg[3])
            
            # Valida que si es la cuenta de antipos a proveedor sume el debe y el haber
            if reg[0] == '1129008000':
                if reg[2] != '':
                    ant_cxp['bal']['debit'] = float(reg[2])
                if reg[3] != '':
                    ant_cxp['bal']['credit'] = float(reg[3])
            
            # Incrementa la linea recorrida
            line += 1
        
        file_name = "Cobros y pagos"
        line = line_pay
        # Recorre los archivos importados y valida que la informacion recabada sobre los cobros y pagos sea correcta
        for reg in import_pay:
            #print "**************** registro a validar - Cobros y pagos *************** ", reg
            # Valida que el registro sea un arreglo
            if type(reg) != list:
                x = import_pay.index(reg)
                del import_pay[x]
                continue
            
            # Valida que el registro contenga mas de un dato
            if len(reg) <= 1:
                x = import_pay.index(reg)
                del import_pay[x]
                continue
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un id (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
            
            # Valida que el id del contacto este registrado
            try:
                register_model, register_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
            except (orm.except_orm, ValueError):
                register_id = False
            if not register_id:
                raise osv.except_osv("Error Validacion","El id externo del contacto no esta registrado en la base de datos, revise que se haya realizado la importacion de contactos previamente sobre la bd (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
            
            # Obtiene el identificador sobre el cliente para indicar si es un cliente o un proveedor
            partner = partner_obj.browse(cr, uid, register_id)
            customer = partner.customer
            supplier = partner.supplier
            #print "*********** Cliente ", customer, ", Proveedor ", supplier, "  ***** "
            
            # Valida que exista el nombre de la factura
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un numero de factura (Linea: %s, columna: 1, archivo: %s)"%(line,file_name))
            
            # Valida la fecha de compra
            if reg[2] != '':
                # Valida que la fecha sea correcta
                try:
                    date = datetime.strptime(reg[2] , '%Y-%m-%d')
                except Exception:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha valida (Linea: %s, columna: 2)"%(line,))
            
            # Valida que si hay un valor sobre los montos a cobrar o a pagar
            if reg[3] not in ['','0'] or reg[4] not in ['','0']:
                # Valida que el registro con valor sea numero
                if reg[3] not in ['','0']:
                    # Valida que sea un cliente
                    if customer == False:
                        raise osv.except_osv("Error Validacion","El contacto registrado no es un cliente, no se pueden aplicar pendientes de cobro (Linea: %s, columna: , archivo: %s)"%(line,file_name))
                    try:
                        # Valida que sea un valor flotante
                        float(reg[3])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el debe sean numeros (Linea: %s, columna: 4, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    cxc['pay']['debit'] += float(reg[3])
                # Valida que el registro con valor sea numero
                if reg[4] not in ['','0']:
                    # Valida que sea un proveedor
                    if supplier == False:
                        raise osv.except_osv("Error Validacion","El contacto registrado no es un proveedor, no se pueden aplicar pendientes de pago (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
                    try:
                        # Valida que sea un valor flotante
                        float(reg[4])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el haber sean numeros (Linea: %s, columna: 5, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    cxp['pay']['credit'] += float(reg[4])
            
            # Valida que si hay un valor sobre los anticipos a cobros o a pagos
            if reg[5] not in ['','0'] or reg[6] not in ['','0']:
                # Valida que el registro con valor sea numero
                if reg[5] not in ['','0']:
                    # Valida que sea un cliente
                    if customer == False:
                        raise osv.except_osv("Error Validacion","El contacto registrado no es un cliente, no se pueden aplicar anticipos de cobro (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
                    try:
                        # Valida que sea un valor flotante
                        float(reg[5])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el debe sean numeros (Linea: %s, columna: 5, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    ant_cxc['pay']['credit'] += float(reg[5])
                # Valida que el registro con valor sea numero
                if reg[6] not in ['','0']:
                    # Valida que sea un proveedor
                    if supplier == False:
                        raise osv.except_osv("Error Validacion","El contacto registrado no es un proveedor, no se pueden aplicar anticipos de pago (Linea: %s, columna: 0, archivo: %s)"%(line,file_name))
                    try:
                        # Valida que sea un valor flotante
                        float(reg[6])
                    except:
                        raise osv.except_osv("Error Validacion","Revise que los registros que contengan valor en el haber sean numeros (Linea: %s, columna: 6, archivo: %s)"%(line,file_name))
                    # Actualiza el total sobre el debe y el haber
                    ant_cxp['pay']['debit'] += float(reg[6])
            
            # Incrementa la linea recorrida
            line += 1
        
        # Valida que el total sobre el debe y el haber en el saldo coincidan para poder cuadrar la poliza
        if debit != credit:
            raise osv.except_osv("Error Validacion","El total sobre cargos y abonos registrados no coincide para generar la poliza de saldos iniciales")
        
        #print "********** credit ********* ", credit
        #print "********** debit ********* ", debit
        
        # Valida que el total de cxc sea igual
        if cxc['pay']['debit'] != cxc['bal']['debit']:
            raise osv.except_osv("Error Validacion","El total sobre cargos registrados en las CXC y los Saldos iniciales no coincide (%s != %s)"%(cxc['pay']['debit'],cxc['bal']['debit']))
        if cxc['pay']['credit'] != cxc['bal']['credit']:
            raise osv.except_osv("Error Validacion","El total sobre abonos registrados en las CXC y los Saldos iniciales no coincide (%s != %s)"%(cxc['pay']['credit'],cxc['bal']['credit']))
        
        # Valida que el total de cxp sea igual
        if cxp['pay']['debit'] != cxp['bal']['debit']:
            raise osv.except_osv("Error Validacion","El total sobre cargos registrados en las CXP y los Saldos iniciales no coincide (%s != %s)"%(cxp['pay']['debit'],cxp['bal']['debit']))
        if cxp['pay']['credit'] != cxp['bal']['credit']:
            raise osv.except_osv("Error Validacion","El total sobre abonos registrados en las CXP y los Saldos iniciales no coincide (%s != %s)"%(cxp['pay']['credit'],cxp['bal']['credit']))
        
        # Valida que el total de anticipos a clientes sea igual
        if ant_cxc['pay']['debit'] != ant_cxc['bal']['debit']:
            raise osv.except_osv("Error Validacion","El total sobre cargos registrados en anticipos a cliente y los Saldos iniciales no coincide (%s != %s)"%(ant_cxc['pay']['debit'],ant_cxc['bal']['debit']))
        if ant_cxc['pay']['credit'] != ant_cxc['bal']['credit']:
            raise osv.except_osv("Error Validacion","El total sobre abonos registrados en anticipos a cliente y los Saldos iniciales no coincide (%s != %s)"%(ant_cxc['pay']['credit'],ant_cxc['bal']['credit']))
        
        # Valida que el total de anticipos a proveedor sea igual
        if ant_cxp['pay']['debit'] != ant_cxp['bal']['debit']:
            raise osv.except_osv("Error Validacion","El total sobre cargos registrados en anticipos a proveedor y los Saldos iniciales no coincide (%s != %s)"%(ant_cxp['pay']['debit'],ant_cxp['bal']['debit']))
        if ant_cxp['pay']['credit'] != ant_cxp['bal']['credit']:
            raise osv.except_osv("Error Validacion","El total sobre abonos registrados en anticipos a proveedor y los Saldos iniciales no coincide (%s != %s)"%(ant_cxp['pay']['credit'],ant_cxp['bal']['credit']))
        
        # Obtiene el diario donde se cargaran los saldos iniciales
        journal_ids = journal_obj.search(cr, uid, [('type','=','situation')])
        if not journal_ids:
            raise osv.except_osv("Error Validacion","No se pueden cargar los saldos iniciales porque no existe un diario de apertura sobre la base de datos")
        journal_id = journal_ids[0]
        journal = journal_obj.browse(cr, uid, journal_id)
        
        # Obtiene el periodo actual
        period_id = self._get_period(cr, uid, context=context)
        
        # Obtiene la fecha actual
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene el numero de la secuencia del movimiento
        mov_number = '/'
        if journal.sequence_id:
            mov_number = seq_obj.next_by_id(cr, uid, journal.sequence_id.id, context=context)
        
        # Genera la nueva poliza sobre la que se cargaran los registros
        move_id = move_obj.create(cr, uid, {
            'name': mov_number,
            'journal_id': journal_id or False,
            'date': date,
            'period_id': period_id,
            'narration': 'Importacion saldos iniciales (ADMON)'
        }, context=context)
        mov_lines = []
        
        try:
            # Registra los movimientos sobre las cuentas bancarias
            for reg in import_ban:
                # Informacion requerida para generar las cuentas de banco
                info_bank = {
                    'id': reg[0],
                    'name': reg[1],
                    'number': reg[3],
                    'clabe': reg[4]
                }
                # Crea la cuenta bancaria
                account_ban = self.create_account_bank(cr, uid, info_bank, context=context)
                #print "*********** account_ban ************** ", account_ban
                
                # Crea un movimiento sobre el apunte contable
                if reg[2] not in ['','0']:
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': 'BANK/INI/',
                        'account_id': account_ban,
                        'move_id': move_id,
                        'partner_id': False,
                        'credit': 0.0,
                        'debit': float(reg[2]),
                        'date': date,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
            
            # Registra los movimientos sobre los saldos iniciales
            for reg in import_bal:
                # Omite la creacion del movimiento en las cuentas por cobrar, cuentas por pagar y anticipos
                if reg[0] in ['1122001000','2122001000','2131001000','1129008000']:
                    continue
                
                account_id = False
                # Obtiene el id de la cuenta
                account_ids = account_obj.search(cr, uid, [('code','=',reg[0])])
                if account_ids:
                    account_id = account_ids[0]
                
                # Crea un movimiento sobre el apunte contable cargando al debe
                if reg[2] not in ['','0']:
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': 'BALANCE/INI/',
                        'account_id': account_id,
                        'move_id': move_id,
                        'partner_id': False,
                        'credit': 0.0,
                        'debit': float(reg[2]),
                        'date': date,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
                # Crea un movimiento sobre el apunte contable cargando al haber
                if reg[3] not in ['','0']:
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': 'BALANCE/INI/',
                        'account_id': account_id,
                        'move_id': move_id,
                        'partner_id': False,
                        'credit': float(reg[3]),
                        'debit': 0.0,
                        'date': date,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
            
            account_cxc = False
            account_cxp = False
            account_ant_cxc = False
            account_ant_cxp = False
            # Obtiene las cuentas donde se van a registrar los cobros y pagos de los contactos
            account_cxc_ids = account_obj.search(cr, uid, [('code','=','1122001000')])
            if account_cxc_ids:
                account_cxc = account_cxc_ids[0]
            account_cxp_ids = account_obj.search(cr, uid, [('code','=','2122001000')])
            if account_cxp_ids:
                account_cxp = account_cxp_ids[0]
            account_ant_cxc_ids = account_obj.search(cr, uid, [('code','=','2131001000')])
            if account_ant_cxc_ids:
                account_ant_cxc = account_ant_cxc_ids[0]
            account_ant_cxp_ids = account_obj.search(cr, uid, [('code','=','1129008000')])
            if account_ant_cxp_ids:
                account_ant_cxp = account_ant_cxp_ids[0]
                
            #print "************ account_cxc ******** ", account_cxc
            #print "************ account_cxp ******** ", account_cxp
            #print "************ account_ant_cxc ******** ", account_ant_cxc
            #print "************ account_ant_cxp ******** ", account_ant_cxp
            
            tax_sale = False
            tax_purchase = False
            # Obtiene los impuestos del IVA al 16% sobre compras y ventas
            tax_sale_ids = tax_obj.search(cr, uid, [('type_tax_use','=','sale'),('name','like','IVA%'),('amount','=',0.16),('active','=',True)])
            if tax_sale_ids:
                tax_sale = tax_obj.browse(cr, uid, tax_sale_ids[0])
            tax_purchase_ids = tax_obj.search(cr, uid, [('type_tax_use','=','purchase'),('name','like','IVA%'),('amount','=',0.16),('active','=',True)])
            if tax_purchase_ids:
                tax_purchase = tax_obj.browse(cr, uid, tax_purchase_ids[0])
            
            # Registra los movimientos sobre los cobros y pagos pendientes
            for reg in import_pay:
                # Obtiene el id del contacto sobre la base
                try:
                    register_model, partner_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
                except (orm.except_orm, ValueError):
                    partner_id = False
                
                # Fecha de factura
                date_pay = date
                if reg[2] != '':
                    date_pay = reg[2]
                
                # Crea un movimiento sobre el apunte contable
                if reg[3] not in ['','0']:
                    amount = float(reg[3])
                    # Genera las lineas de movimiento sobre el ingreso
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': reg[1] or 'PAYMENT/INI/',
                        'account_id': account_cxc,
                        'move_id': move_id,
                        'partner_id': partner_id,
                        'credit': 0.0,
                        'debit': amount,
                        'date': date_pay,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
                    
                    # Obtiene la base y el iva del monto a cobrar
                    iva = (amount * 16)/116
                    base = amount - iva
                    # Agrega la informacion del iva a trasladar sobre el monto
                    if tax_sale:
                        # Actualiza el valor de la cuenta a aplicar para los impuestos
                        account_id = tax_sale.account_collected_id_apply.id or False
                        # Crea el nuevo movimiento
                        mt_id = move_tax_obj.create(cr, uid, {
                                                    'move_line_id':new_id,
                                                    'name': tax_sale.name,
                                                    'tax_id': tax_sale.id or False,
                                                    'invoice_total': amount,
                                                    'base': base,
                                                    'base_tax': amount,
                                                    'tax_code_id': tax_sale.tax_code_id.id or False,
                                                    'amount': 0.0,
                                                    'percent': 16,
                                                    'account_id': account_id or False}, context=context)
                    
                if reg[4] not in ['','0']:
                    amount = float(reg[4])
                    # Genera las lineas de movimiento sobre el ingreso
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': reg[1] or 'PAYMENT/INI/',
                        'account_id': account_cxp,
                        'move_id': move_id,
                        'partner_id': partner_id,
                        'credit': amount,
                        'debit': 0.0,
                        'date': date_pay,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
                    
                    # Obtiene la base y el iva del monto a cobrar
                    iva = (amount * 16)/116
                    base = amount - iva
                    # Agrega la informacion del iva a trasladar sobre el monto
                    if tax_purchase:
                        # Actualiza el valor de la cuenta a aplicar para los impuestos
                        account_id = tax_purchase.account_collected_id_apply.id or False
                        # Crea el nuevo movimiento
                        mt_id = move_tax_obj.create(cr, uid, {
                                                    'move_line_id':new_id,
                                                    'name': tax_purchase.name,
                                                    'tax_id': tax_purchase.id or False,
                                                    'invoice_total': amount,
                                                    'base': base,
                                                    'base_tax': amount,
                                                    'tax_code_id': tax_purchase.tax_code_id.id or False,
                                                    'amount': 0.0,
                                                    'percent': 16,
                                                    'account_id': account_id or False}, context=context)
                    
                # Crea un movimiento sobre el apunte contable
                if reg[5] not in ['','0']:
                    # Genera las lineas de movimiento sobre el ingreso
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': reg[1] or 'ADVANCE/INI/',
                        'account_id': account_ant_cxc,
                        'move_id': move_id,
                        'partner_id': partner_id,
                        'credit': 0.0,
                        'debit': float(reg[5]),
                        'date': date_pay,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
                if reg[6] not in ['','0']:
                    # Genera las lineas de movimiento sobre el ingreso
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'name': reg[1] or 'ADVANCE/INI/',
                        'account_id': account_ant_cxp,
                        'move_id': move_id,
                        'partner_id': partner_id,
                        'credit': float(reg[6]),
                        'debit': 0.0,
                        'date': date_pay,
                        'ref': mov_number
                    }
                    new_id = mline_obj.create(cr, uid, move_line, context=context)
                    mov_lines.append(new_id)
        finally:
            cr.close()
        return True
    
    def action_import_balance_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_balance_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_balance_ok':True}, context=context)
        return True
    
    def onchange_import_tax(self, cr, uid, ids, import_tax, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_tax:
            return {'value':{'import_tax_ok': False}}
        return {}
    
    def import_tax_to_db(self, cr_admon, uid_admon, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        code_obj = self.pool.get('account.fiscal.code')
        tax_obj = self.pool.get('account.tax.code')
        balance_obj = self.pool.get('account.fiscal.balance')
        import_obj = self.pool.get('admon.database.import')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line = 1
        cur_date = time.strftime('%Y-%m-%d')
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_tax, line)
        #print "********** import data *********** ", import_data
        
        n = 0
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            #print "**************** registro a validar *************** ", reg
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
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Impuesto (Linea: %s, columna: 0)"%(line,))
            
            # Valida que el codigo se encuentre registrado sobre los impuestos a seleccionar
            import_ids = import_obj.search(cr_admon, uid_admon, [('name','=',reg[0])])
            if not import_ids:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Impuesto valido (Linea: %s, columna: 0)"%(line,))
            import_tax = import_obj.browse(cr_admon, uid_admon, import_ids[0])
            if import_tax.type_tax == 'tax':
                # Valida que exista en la base de datos el impuesto
                tax_ids = tax_obj.search(cr, uid, [('code','=',import_tax.code)])
                if not tax_ids:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Impuesto valido, validar que se se encuentre registrado sobre la base de datos a cargar (Linea: %s, columna: 0)"%(line,))
                # Reemplaza el valor por el id obtenido
                import_data[n][0] = tax_ids[0]
            else:
                # Valida que exista en la base de datos el impuesto
                code_ids = code_obj.search(cr, uid, [('code','=', import_tax.code)])
                if not code_ids:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Impuesto valido, validar que se se encuentre registrado sobre la base de datos a cargar (Linea: %s, columna: 0)"%(line,))
                # Reemplaza el valor por el id obtenido
                import_data[n][0] = code_ids[0]
            # Agrega la informacion extra sobre el nuevo registro
            import_data[n].insert(3,import_tax.type_tax)
            import_data[n].insert(4,import_tax.type_code)
                
            # Valida que tenga si tiene un valor sea numerico
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un saldo (Linea: %s, columna: 1)"%(line,))
            try:
                # Valida que sea un valor flotante
                float(reg[1])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un saldo valido (Linea: %s, columna: 1)"%(line,))
            
            # Valida la fecha de compra
            if reg[2] != '':
                # Valida que la fecha sea correcta
                try:
                    date = datetime.strptime(reg[2] , '%Y-%m-%d')
                except Exception:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha valida (Linea: %s, columna: 2)"%(line,))
            
            # Incrementa la linea recorrida
            line += 1
            n += 1
        try:
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                
                if reg[0] != '' and reg[3]:
                    date = cur_date
                    # Obtiene la fecha registrar o sino pone la fecha actual
                    if reg[2] != '':
                        date = reg[2]
                    
                    # Crea la plantilla para cargar los datos
                    vals = {
                        'amount': float(reg[1]),
                        'date': date,
                        'type': reg[3],
                        'type_code': reg[4]
                    }
                    if reg[3] == 'tax':
                        vals['tax_code_id'] = reg[0] or False
                    else:
                        vals['code_id'] = reg[0] or False
                    #print "*********** nuevo registro vals *********** ", vals
                    # Crea el nuevo registro
                    balance_id = balance_obj.create(cr, uid, vals, context=context)
        finally:
            cr.close()
        return True
    
    def action_import_tax_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_tax_to_db(cr, uid, info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_tax_ok':True}, context=context)
        return True
    
    def onchange_import_utility(self, cr, uid, ids, import_utility, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_utility:
            return {'value':{'import_utility_ok': False}}
        return {}
    
    def import_utility_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        utility_obj = self.pool.get('account.fiscal.utility')
        line_obj = self.pool.get('account.fiscal.utility.line')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_utility, line)
        #print "********** import data *********** ", import_data
        
        # Variables para apoyo de la validacion de registros
        last_year = 0
        loss = {}
        cur_year = time.strftime('%Y')
        
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            #print "**************** registro a validar *************** ", reg
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
            
            # Valida que contenga un ejercicio seleccionado
            if reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Ejercicio (Linea: %s, columna: 0)"%(line,))
            # Valida que el ejercicio sea valido
            try:
                # Valida que sea un valor entero y que no haya un ejercicio mayo antes de el
                if last_year > int(reg[0]):
                    raise osv.except_osv("Error Validacion","Revise que el listado de ejercicios se encuentre ordenado en forma ascendente (Linea: %s, columna: 0)"%(line,))
                last_year = int(reg[0])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un ejercicio valido (Linea: %s, columna: 0)"%(line,))
            # Valida que el año a agregar no sea el año en curso
            if cur_year == reg[0]:
                raise osv.except_osv('Error Validacion', u'No puede agregar perdidas fiscales sobre el año en curso.. (Linea: %s, columna: 0)'%(line,))
            
            # Valida que contenga un valor de la perdida o en la amortizacion de la perdida
            if reg[1] == '' and reg[2] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros apliquen una perdida o una amortizacion (Linea: %s, columna: 1,2)"%(line,))
            
            value1 = 0.0
            value2 = 0.0
            
            # Valida que si hay una perdida, que sea numerico
            if reg[1] != '':
                try:
                    # Valida que sea un valor flotante
                    value1 = float(reg[1])
                except:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor de la perdida valido (Linea: %s, columna: 1)"%(line,))
                
            # Valida que si hay una perdida amortizada, que sea numerico
            if reg[2] != '':
                try:
                    # Valida que sea un valor flotante
                    value2 = float(reg[2])
                except:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor de la perdida amortizada valido (Linea: %s, columna: 2)"%(line,))
            
            # Valida que contenga un ejercicio de aplicacion
            if reg[3] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Ejercicio de aplicacion (Linea: %s, columna: 3)"%(line,))
            # Valida que el año a agregar no sea el año en curso
            if cur_year == reg[0]:
                raise osv.except_osv('Error Validacion', "No puede amortizar perdidas fiscales sobre el año en curso. (Linea: %s, columna: 3)"%(line,))
            # Valida que el ejercicio sea valido
            try:
                # Valida que sea un valor entero y que no haya un ejercicio mayor antes de el
                if last_year  > int(reg[3]):
                    raise osv.except_osv("Error Validacion","Solo puede aplicar sobre ejercicio declarados, valide que el ejercicio de aplicacion no sea menor que ej ejercicio (Linea: %s, columna: 3)"%(line,))
                # Valida que si el ejercicio es igual al año de aplicacion
                if last_year == int(reg[3]):
                    if value1 < 0 or value2 > 0:
                        raise osv.except_osv("Error Validacion","Si los ejercicios son iguales solo puede aplicarse una perdida (Linea: %s, columna: 1)"%(line,))
                    # Registra sobre las perdidas a validar
                    loss[reg[0]] = 0
                # Valida que si el ejercicio es mayor al año de aplicacion
                if last_year < int(reg[3]):
                    if value2 < 0 or value1 > 0:
                        raise osv.except_osv("Error Validacion","Si el año de aplicacion es mayor al del ejercicio, debe aplicar una amortizacion (Linea: %s, columna: 2)"%(line,))
                    # Valida que el ejercicio sobre el que amortiza sea una perdida
                    if not loss.get(reg[0],False) == False:
                        raise osv.except_osv("Error Validacion","Debe aplicar primero una perdida sobre el ejercicio %s para poder aplicar la amortizacion (Linea: %s, columna: 2)"%(last_year,line,))
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un ejercicio de aplicacion valido (Linea: %s, columna: 3)"%(line,))
            
            # Incrementa la linea recorrida
            line += 1
        try:
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                
                # Valida si es una perdida el registro
                if loss.get(reg[0], False) == 0:
                    # Registra la perdida fiscal
                    util_id = utility_obj.create(cr, uid, {
                        'fiscalyear': int(reg[0]),
                        'utility': float(reg[1]) * -1
                    })
                    #print "******** perdida ", reg[0], " ********** ", util_id 
                    loss[reg[0]] = util_id
                else:
                    #print "************* amortizacion ************** ", reg[0]
                    # Registra la utilidad sobre los registros
                    util_id = loss.get(reg[0],False)
                    #print "*********** utilidad ************ ", util_id
                    
                    # Obtiene la informacion de la utilidad
                    util = utility_obj.browse(cr, uid, util_id, context=context)
                    fiscalyear = util.last_fiscalyear
                    if len(util.line_ids) > 0:
                        fiscalyear += 1
                    #print "************* fiscalyear *********** ", fiscalyear
                    #print "************* fiscalyear amortizado *********** ", int(reg[3])
                    # Registra ejercicios en cero si no es el año que se va a amortizar
                    while fiscalyear < int(reg[3]):
                        amount = 0.0
                        # Agrega el nuevo registro
                        values = {
                            'utility_id': util.id,
                            'remnant_before': util.remnant,
                            'inpc_id1': util.last_inpc_id.id,
                            'inpc_id2': util.next_inpc_id.id,
                            'remnant_amortized': amount,
                            'fiscalyear_amortized': fiscalyear
                        }
                        line_id = line_obj.create(cr, uid, values, context=context)
                        # Actualiza la informacion de la utilidad
                        util = utility_obj.browse(cr, uid, util_id, context=context)
                        fiscalyear = util.last_fiscalyear
                        if len(util.line_ids) > 0:
                            fiscalyear += 1
                    
                    #print "************* fiscalyear aplicado amortizacion *********** ", fiscalyear
                    amount = float(reg[2])
                    # Agrega el nuevo registro sobre la utilidad
                    values = {
                        'utility_id': util.id,
                        'remnant_before': util.remnant,
                        'inpc_id1': util.last_inpc_id.id,
                        'inpc_id2': util.next_inpc_id.id,
                        'remnant_amortized': amount,
                        'fiscalyear_amortized': fiscalyear
                    }
                    line_id = line_obj.create(cr, uid, values, context=context)
                        
        finally:
            cr.close()
        return True
    
    def action_import_utility_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_utility_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_utility_ok':True}, context=context)
        return True
    
    def onchange_import_rate(self, cr, uid, ids, import_rate, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_rate:
            return {'value':{'import_rate_ok': False}}
        return {}
    
    def import_rate_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        rate_obj = self.pool.get('account.fiscal.rate')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_rate, line)
        #print "********** import data *********** ", import_data
        
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            #print "**************** registro a validar *************** ", reg
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
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un codigo (Linea: %s, columna: 0)"%(line,))
            
            # Valida que haya un indice fiscal con el codigo especificado
            rate_ids = rate_obj.search(cr, uid, [('code','=',reg[0])])
            if not rate_ids:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un codigo valido (Linea: %s, columna: 0)"%(line,))
            
            # Valida que tenga si tiene un valor sea numerico
            if reg[2] != '':
                try:
                   # Valida que sea un valor flotante
                   float(reg[2])
                except:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor original valido (Linea: %s, columna: 2)"%(line,))
            
            # Incrementa la linea recorrida
            line += 1
        try:
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                if reg[2] != '':
                    # Obtiene el id del registro
                    rate_ids = rate_obj.search(cr, uid, [('code','=',reg[0])])
                    #print "****************** rate_ids ****************** ", rate_ids
                    #print "****************** value ****************** ", float(reg[2])
                    if rate_ids:
                        # Actualiza el valor del registro
                        rate_obj.write(cr, uid, rate_ids, {'value': float(reg[2])})
        finally:
            cr.close()
        return True
            
    def action_import_rate_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_rate_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_rate_ok':True}, context=context)
        return True
    
    def onchange_import_partner(self, cr, uid, ids, import_partner, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_partner:
            return {'value':{'import_partner_ok': False}}
        return {}
    
    def import_partner_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        par_obj = self.pool.get('res.partner')
        data_obj = self.pool.get('ir.model.data')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        categ_obj = self.pool.get('res.partner.account.category')
        if context is None:
            context = {}
        country_id = False
        state_id = False
        uid = 1
        line = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_partner, line)
        #print "********** import data *********** ", import_data
        
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            #print "**************** registro a validar *************** ", reg
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
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un id (Linea: %s, columna: 0)"%(line,))
            
            # Valida que el id no este registrado
            try:
                register_model, register_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
            except (orm.except_orm, ValueError):
                register_id = False
            if register_id:
                raise osv.except_osv("Error Validacion","El id externo ya esta registrado en la base de datos, revise que no se haya importado el registro anteriormente (Linea: %s, columna: 0)"%(line,))
            
            # Valida que tenga un nombre
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un nombre (Linea: %s, columna: 0)"%(line,))
            
            # Incrementa la linea recorrida
            line += 1
        try:
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                
                # Crea un diccionario con la informacion que debe llevar el nuevo registro
                partner_data = {
                    'is_company': True,
                    'name': reg[1],
                    'phone': reg[2],
                    'mobile': reg[3],
                    'email': reg[4],
                    'rfc': reg[5],
                    'vat': reg[5],
                    'street': reg[6],
                    'street2': reg[7],
                    'l10n_mx_street3': reg[8],
                    'l10n_mx_street4': reg[9],
                    'city': reg[10],
                    'l10n_mx_city2': reg[11],
                    'country_id': False,
                    'state_id': False,
                    'zip': reg[14],
                    'supplier': True if reg[15] == 'True' or reg[15] == 'true' else False,
                    'customer': True if reg[16] == 'True' or reg[16] == 'true' else False
                }
                
                # Obtiene el id del pais
                if reg[12]: 
                    # Revisa si pais es diferente de mexico, sino retorna el id
                    if reg[12] == 'Mexico' or reg[12] == 'México' or reg[12] == 'MEXICO':
                        country_ids = country_obj.search(cr, uid, [('code', '=', 'MX'),])
                    else:
                        country_ids = country_obj.search(cr, uid, [('name', '=', reg[12]),])
                    if country_ids:
                        partner_data['country_id'] = country_ids[0]
                # Obtiene el id del estado
                if reg[13]:
                    # Busca el id del estad, si no existe lo da de alta
                    state_ids = state_obj.search(cr, uid, [('name', '=', reg[13]),])
                    if state_ids:
                        # Agrega el id al registro
                        partner_data['state_id'] = state_ids[0]
                
                # Agrega el RFC
                if partner_data.get('rfc','') != '':
                    partner_data['vat'] = 'MX%s'%(partner_data.get('rfc',''),)
                
                # Pone la categoria del cliente como cliente nacional
                try:
                    categ_id = data_obj.get_object(cr, uid, 'account_fiscal', 'partner_acc_category_01').id
                    partner_data['acc_categ_id'] = categ_id
                    categ = categ_obj.browse(cr, uid, categ_id, context=context)
                    # Agrega la informacion sobre las cuentas relacionadas a la categoria sobre el contacto
                    partner_data['property_account_receivable'] = categ.property_account_receivable.id or False
                    partner_data['property_account_payable'] = categ.property_account_payable.id or False
                    partner_data['property_account_advance_customer'] = categ.property_account_advance_customer.id or False
                    partner_data['property_account_advance_supplier'] = categ.property_account_advance_supplier.id or False
                    partner_data['property_account_asset'] = categ.property_account_asset.id or False
                except:
                    pass
                
                # Agrega el nuevo registro
                res_id = par_obj.create(cr, uid, partner_data, context=context)
                # Agrega la informacion del id externo sobre el registro
                data_obj.create(cr, uid, {
                        'name': reg[0],
                        'module': 'admon',
                        'model': 'res.partner',
                        'res_id': res_id
                    }, context=context)
        finally:
            cr.close()
        return True
            
    def action_import_partner_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_partner_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_partner_ok':True}, context=context)
        return True
    
    def onchange_import_asset(self, cr, uid, ids, import_asset, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_asset:
            return {'value':{'import_asset_ok': False}}
        return {}
    
    def import_asset_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        asset_obj = self.pool.get('account.asset.asset')
        asset_categ_obj = self.pool.get('account.asset.category')
        product_obj = self.pool.get('product.product')
        categ_obj = self.pool.get('product.category')
        uom_obj = self.pool.get('product.uom')
        inventry_obj = self.pool.get('stock.inventory')
        inventry_line_obj = self.pool.get('stock.inventory.line')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_asset, line)
        #print "********** import data *********** ", import_data
        
        n = 0
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            #print "**************** registro a validar *************** ", reg
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
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un id (Linea: %s, columna: 0)"%(line,))
            
            # Valida que el id no este registrado
            try:
                register_model, register_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
            except (orm.except_orm, ValueError):
                register_id = False
            if register_id:
                raise osv.except_osv("Error Validacion","El id externo ya esta registrado en la base de datos, revise que no se haya importado el registro anteriormente (Linea: %s, columna: 0)"%(line,))
            
            # Valida que tenga un nombre
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Nombre (Linea: %s, columna: 1)"%(line,))
            
            # Valida que tenga agregada una cantidad de productos que componen el activo
            if reg[2] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan la cantidad (Linea: %s, columna: 2)"%(line,))
            
            # Valida que tenga agregada una categoria
            if reg[3] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una categoria (Linea: %s, columna: 3)"%(line,))
            # Obtiene el id de la categoria del activo
            if reg[3]: 
                categ_ids = asset_categ_obj.search(cr, uid, [('name', '=', reg[3]),])
                if categ_ids:
                    import_data[n][3] = categ_ids[0]
                else:
                    raise osv.except_osv("Error Validacion","Revise que la categoria sea valida (Linea: %s, columna: 3)"%(line,))
            
            # Valida la fecha de compra
            if reg[4] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de compra (Linea: %s, columna: 4)"%(line,))
            # Valida que la fecha sea correcta
            try:
                date = datetime.strptime(reg[4] , '%Y-%m-%d')
            except Exception:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de compra valida (Linea: %s, columna: 4)"%(line,))
            
            # Valida la fecha de inicio de depreciacion
            if reg[5] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de inicio de depreciacion (Linea: %s, columna: 5)"%(line,))
            # Valida que la fecha sea correcta
            try:
                date = datetime.strptime(reg[5] , '%Y-%m-%d')
            except Exception:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de inicio de depreciacion valida (Linea: %s, columna: 5)"%(line,))
            
            # Valida la fecha de continuacion
            if reg[6] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de continuacion de depreciacion (Linea: %s, columna: 6)"%(line,))
            # Valida que la fecha sea correcta
            try:
                date = datetime.strptime(reg[6] , '%Y-%m-%d')
            except Exception:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una fecha de continuacion de depreciacion valida (Linea: %s, columna: 6)"%(line,))
            
            # Valida que tenga el valor original
            if reg[7] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor original (Linea: %s, columna: 7)"%(line,))
            try:
               # Valida que sea un valor flotante
               float(reg[7])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor original valido (Linea: %s, columna: 7)"%(line,))
            
            # Valida que tenga el valor contable
            if reg[8] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor contable (Linea: %s, columna: 8)"%(line,))
            try:
               # Valida que sea un valor flotante
               float(reg[8])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un valor contable valido (Linea: %s, columna: 8)"%(line,))
            
            # Valida que tenga el numero de depreciaciones faltantes
            if reg[9] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan depreciaciones faltantes (Linea: %s, columna: 9)"%(line,))
            try:
               # Valida que sea un valor flotante
               int(reg[9])
            except:
                raise osv.except_osv("Error Validacion","Revise que todos los registros que contengan depreciaciones faltantes sea valido (Linea: %s, columna: 9)"%(line,))
            
            # Valida el MDV en caso de contenerlo
            if reg[10] != '':
                try:
                # Valida que sea un valor flotante
                    float(reg[10])
                except:
                    raise osv.except_osv("Error Validacion","Revise que el MDV registrado sea un valor numerico (Linea: %s, columna: 10)"%(line,))
            
            
            # Incrementa la linea recorrida
            line += 1
            n += 1
        try:
            #print "**************** import data con ids de categoria ************* ", import_data
            
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                
                # Revisa si ya existe un producto dado de alta con el nombre solicitado
                product_ids = product_obj.search(cr, uid, [('name','=',reg[1])])
                if product_ids:
                    product_id = product_ids[0]
                else:
                    # Crea el nuevo producto
                    product_data = {
                        'name': reg[1],
                        'categ_id': False,
                        'standard_price': float(reg[7]) /float(reg[2]),
                        'list_price': 0.0,
                        'default_code': '',
                        'valuation': 'real_time',
                        'purchase_line_warn': 'no-message',
                        'sale_line_warm': 'no-message',
                        'cost_method': 'standard',
                        'procure_method': 'make_to_stock',
                        'supply_method': 'buy'
                    }
                    
                    # Obtiene el id de la categoria del producto
                    if reg[3]: 
                        categ_ids = categ_obj.search(cr, uid, [('default_asset_category_id', '=', reg[3]),('is_asset','=',True)])
                        if categ_ids:
                            product_data['categ_id'] = categ_ids[0]
                        else:
                            try:
                                # Si no encuentra la categoria del producto, pone la categoria por default
                                product_data['categ_id'] = data_obj.get_object_reference(cr, uid, 'product', 'product_category_all')[1]
                            except ValueError:
                                product_data['categ_id'] = False
                        # Si hay una categoria para el producto, actualiza la informacion del producto en base a la categoria
                        if product_data['categ_id']:
                            categ = categ_obj.browse(cr, uid, product_data['categ_id'])
                            if categ.type_product:
                                produt_data['type'] = categ.type_product
                            if product_data.get('uom_id',False) == False:
                                product_data['uom_id'] = categ.uom_id.id or False
                                if categ.uom_po_id:
                                    product_data['uom_po_id'] = categ.uom_po_id.id or False
                            product_data['sale_ok'] = categ.sale_ok
                            product_data['purchase_ok'] = categ.purchase_ok
                            product_data['hr_expense_ok'] = categ.hr_expense_ok
                            product_data['is_asset'] = categ.is_asset
                            if product_data['is_asset']:
                                product_data['default_asset_category_id'] = categ.default_asset_category_id.id or False
                            if categ.cost_method:
                                product_data['cost_method'] = categ.cost_method
                            if categ.valuation:
                                product_data['valuation'] = categ.valuation
                            if categ.taxes_id:
                                tax_ids = []
                                for tax in categ.taxes_id:
                                    tax_ids.append(tax.id)
                                product_data['taxes_id'] = [[6,False, tax_ids]]
                            if categ.supplier_taxes_id:
                                tax_ids = []
                                for tax in categ.supplier_taxes_id:
                                    tax_ids.append(tax.id)
                                product_data['supplier_taxes_id'] = [[6, False, tax_ids]]
                    # Agrega el nuevo registro
                    product_id = product_obj.create(cr, uid, product_data, context=context)
                    # Agrega la informacion del id externo sobre el registro
                    data_obj.create(cr, uid, {
                            'name': 'product_%s'%(reg[0],),
                            'module': 'admon',
                            'model': 'product.product',
                            'res_id': product_id
                        }, context=context)
                
                # Crea un diccionario con la informacion que debe llevar el nuevo registro
                asset_data = {
                    'name': reg[1],
                    'product_qty': int(reg[2]),
                    'category_id': reg[3],
                    'date': reg[4],
                    'depreciation_date': reg[5],
                    'purchase_date': reg[6],
                    'purchase_value': float(reg[7]),
                    'original_value': float(reg[7]) / float(reg[2]),
                    'salvage_value': float(reg[8]),
                    'method_number': int(reg[9]),
                    'product_id': product_id,
                    'state': 'draft',
                    'original_salvage': float(reg[8])/ float(reg[2]),
                    'method': 'linear',
                    'method_time': 'number',
                    'method_period': 1,
                    'origin': 'purchase'
                }
                # Si aplica el mdv lo agrega al activo
                if reg[10] != '':
                    asset_data['mdv'] = float(reg[10])
                
                #print "******************** asset_data ******************** ", asset_data
                # Agrega el nuevo registro
                res_id = asset_obj.create(cr, uid, asset_data, context=context)
                # Agrega la informacion del id externo sobre el registro
                data_obj.create(cr, uid, {
                        'name': reg[0],
                        'module': 'admon',
                        'model': 'account.asset.asset',
                        'res_id': res_id
                    }, context=context)
                # Confirma el activo
                asset_obj.validate(cr, uid, [res_id], context=context)
                
        finally:
            cr.close()
        return True
    
    def action_import_asset_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_asset_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_asset_ok':True}, context=context)
        return True
    
    def onchange_import_product(self, cr, uid, ids, import_product, context=None):
        """
            Si se elimina el archivo importado quita la confirmacion de que se importo
        """
        if not import_product:
            return {'value':{'import_product_ok': False}}
        return {}
    
    def import_product_to_db(self, info, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Inicializa variables
        product_obj = self.pool.get('product.product')
        categ_obj = self.pool.get('product.category')
        uom_obj = self.pool.get('product.uom')
        inventry_obj = self.pool.get('stock.inventory')
        inventry_line_obj = self.pool.get('stock.inventory.line')
        data_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        uid = 1
        line = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        db_name = info.database_id.code
        cr = self.conect_to_db(db_name)
        
        # Obtiene la informacion del archivo
        import_data, line = self.get_import_data(info.import_product, line)
        print "********** import data *********** ", import_data
        
        # Recorre los archivos importados y valida que la informacion recabada sea correcta
        for reg in import_data:
            print "**************** registro a validar *************** ", reg
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
            
            # Valida que exista un id sobre el registro para agregarlo
            if reg[0] == '' and reg[1] == '':
                continue
            elif reg[0] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un id (Linea: %s, columna: 0)"%(line,))
            
            # Valida que el id no este registrado
            try:
                register_model, register_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'admon', reg[0])
            except (orm.except_orm, ValueError):
                register_id = False
            if register_id:
                raise osv.except_osv("Error Validacion","El id externo ya esta registrado en la base de datos, revise que no se haya importado el registro anteriormente (Linea: %s, columna: 0)"%(line,))
            
            # Valida que tenga un nombre
            if reg[1] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un Nombre (Linea: %s, columna: 1)"%(line,))
            
            # Valida que tenga agregada una categoria
            if reg[2] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una categoria (Linea: %s, columna: 2)"%(line,))
            
            # Valida que tenga agregada una unidad de medida
            if reg[7] == '':
                raise osv.except_osv("Error Validacion","Revise que todos los registros contengan una unidad de medida (Linea: %s, columna: 7)"%(line,))
            
            # Valida el codigo ean13 en caso de que lo tenga
            if reg[6] != '':
                ean = check_ean(reg[6])
                #print "*************** ean ****************** ", ean
                if ean == False:
                    raise osv.except_osv("Error Validacion","Revise que todos los registros contengan un codigo EAN13 (Linea: %s, columna: 6)"%(line,))
            
            # Incrementa la linea recorrida
            line += 1
        try:
            try:
                location_model, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
            except (orm.except_orm, ValueError):
                location_id = False
            
            # Recorre los archivos importados y hace la importacion de los registros
            for reg in import_data:
                # Valida que la linea tenaga sus datos principales
                if reg[0] == '' and reg[1] == '':
                        continue
                
                # Crea un diccionario con la informacion que debe llevar el nuevo registro
                product_data = {
                    'name': reg[1],
                    'categ_id': False,
                    'standard_price': reg[3],
                    'list_price': reg[4],
                    'default_code': reg[5],
                    'uom_id': False,
                    'uom_po_id': False,
                    'valuation': 'real_time',
                    'purchase_line_warn': 'no-message',
                    'sale_line_warm': 'no-message',
                    'cost_method': 'standard',
                    'procure_method': 'make_to_stock',
                    'supply_method': 'buy'
                }
                # Si hay un codigo ean13 lo agrega a la informacion del producto
                if reg[6] != '':
                    product_data['ean13'] = reg[6]
                    
                # Obtiene el monto disponible sobre el producto
                disp = 0
                if reg[8] != '':
                    disp = int(reg[8])
                
                # Obtiene el id de la unidad de medida del producto
                if reg[7]: 
                    uom_ids = uom_obj.search(cr, uid, [('name', '=', reg[7]),])
                    if uom_ids:
                        product_data['uom_id'] = uom_ids[0]
                        product_data['uom_po_id'] = uom_ids[0]
                        #print "***************** oum_id *************** ", product_data['uom_id']
                
                # Obtiene el id de la categoria del producto
                if reg[2]: 
                    categ_ids = categ_obj.search(cr, uid, [('complete_name', '=', reg[2]),])
                    if categ_ids:
                        product_data['categ_id'] = categ_ids[0]
                    else:
                        try:
                            # Si no encuentra la categoria del producto, pone la categoria por default
                            product_data['categ_id'] = data_obj.get_object_reference(cr, uid, 'product', 'product_category_all')[1]
                        except ValueError:
                            product_data['categ_id'] = False
                    
                    # Si hay una categoria para el producto, actualiza la informacion del producto en base a la categoria
                    if product_data['categ_id']:
                        categ = categ_obj.browse(cr, uid, product_data['categ_id'])
                        if categ.type_product:
                            produt_data['type'] = categ.type_product
                        if product_data.get('uom_id',False) == False:
                            product_data['uom_id'] = categ.uom_id.id or False
                            if categ.uom_po_id:
                                product_data['uom_po_id'] = categ.uom_po_id.id or False
                        product_data['sale_ok'] = categ.sale_ok
                        product_data['purchase_ok'] = categ.purchase_ok
                        product_data['hr_expense_ok'] = categ.hr_expense_ok
                        product_data['is_asset'] = categ.is_asset
                        if product_data['is_asset']:
                            product_data['default_asset_category_id'] = categ.default_asset_category_id.id or False
                        if categ.cost_method:
                            product_data['cost_method'] = categ.cost_method
                        if categ.valuation:
                            product_data['valuation'] = categ.valuation
                        if categ.taxes_id:
                            tax_ids = []
                            for tax in categ.taxes_id:
                                tax_ids.append(tax.id)
                            product_data['taxes_id'] = [[6,False, tax_ids]]
                        if categ.supplier_taxes_id:
                            tax_ids = []
                            for tax in categ.supplier_taxes_id:
                                tax_ids.append(tax.id)
                            product_data['supplier_taxes_id'] = [[6, False, tax_ids]]
                
                #print "******************** product_data ******************** ", product_data
                # Agrega el nuevo registro
                res_id = product_obj.create(cr, uid, product_data, context=context)
                # Agrega la informacion del id externo sobre el registro
                data_obj.create(cr, uid, {
                        'name': reg[0],
                        'module': 'admon',
                        'model': 'product.product',
                        'res_id': res_id
                    }, context=context)
                
                #print "******************* producto disponible ************* ", disp
                
                # Valida que haya producto disponible
                if disp > 0:
                    # Agrega las existencias al inventario
                    inventory_id = inventry_obj.create(cr , uid, {'name': _('INV: %s') % tools.ustr(reg[1])}, context=context)
                    line_data ={
                        'inventory_id' : inventory_id,
                        'product_qty' : disp,
                        'location_id' : location_id,
                        'product_id' : res_id,
                        'product_uom' : product_data['uom_id']
                    }
                    inventry_line_obj.create(cr , uid, line_data, context=context)
                    inventry_obj.action_confirm(cr, uid, [inventory_id], context=context)
                    inventry_obj.action_done(cr, uid, [inventory_id], context=context)
                
        finally:
            cr.close()
        return True
    
    def action_import_product_to_db(self, cr, uid, ids, context=None):
        """
            Revisa el csv cargado y hace una carga inicial de datos sobre el sistema
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            self.import_product_to_db(info)
        # Pone que el archivo fue importado
        self.write(cr, uid, ids, {'import_product_ok':True}, context=context)
        return True
    
    def get_certificate_info(self, cr, uid, ids, context=None):
        certificate = self.browse(cr, uid, ids, context=context)[0]
        cer_der_b64str = certificate.certificate_file
        key_der_b64str = certificate.certificate_key_file
        password = certificate.certificate_password
        data = self.onchange_certificate_info(
            cr, uid, ids, cer_der_b64str, key_der_b64str, password, context=context)
        if data['warning']:
            raise osv.except_osv(data['warning'][
                                 'title'], data['warning']['message'])
        return self.write(cr, uid, ids, data['value'], context)

    def onchange_certificate_info(self, cr, uid, ids, cer_der_b64str,
        key_der_b64str, password, context=None):
        """
        @param cer_der_b64str : File .cer in Base 64
        @param key_der_b64str : File .key in Base 64
        @param password : Password inserted in the certificate configuration
        """
        certificate_lib = self.pool.get('facturae.certificate.library')
        value = {}
        warning = {}
        certificate_file_pem = False
        certificate_key_file_pem = False
        invoice_obj = self.pool.get('account.invoice')
        if cer_der_b64str and key_der_b64str and password:
            
            fname_cer_der = certificate_lib.b64str_to_tempfile(
                cer_der_b64str, file_suffix='.der.cer',
                file_prefix='openerp__' + (False or '') + '__ssl__', )
            fname_key_der = certificate_lib.b64str_to_tempfile(
                key_der_b64str, file_suffix='.der.key',
                file_prefix='openerp__' + (False or '') + '__ssl__', )
            fname_password = certificate_lib.b64str_to_tempfile(
                base64.encodestring(password), file_suffix='der.txt',
                file_prefix='openerp__' + (False or '') + '__ssl__', )
            fname_tmp = certificate_lib.b64str_to_tempfile(
                '', file_suffix='tmp.txt', file_prefix='openerp__' + (
                False or '') + '__ssl__', )

            cer_pem = certificate_lib._transform_der_to_pem(
                fname_cer_der, fname_tmp, type_der='cer')
            cer_pem_b64 = base64.encodestring(cer_pem)

            key_pem = certificate_lib._transform_der_to_pem(
                fname_key_der, fname_tmp, fname_password, type_der='key')
            key_pem_b64 = base64.encodestring(key_pem)

            # date_fmt_return='%Y-%m-%d %H:%M:%S'
            date_fmt_return = '%Y-%m-%d'
            serial = False
            try:
                serial = certificate_lib._get_param_serial(
                    fname_cer_der, fname_tmp, type='DER')
                value.update({
                    'serial_number': serial,
                })
            except:
                pass
            date_start = False
            date_end = False
            try:
                dates = certificate_lib._get_param_dates(fname_cer_der,
                    fname_tmp, date_fmt_return=date_fmt_return, type='DER')
                date_start = dates.get('startdate', False)
                date_end = dates.get('enddate', False)
                value.update({
                    'date_start': date_start,
                    'date_end': date_end,
                })

            except:
                pass
            os.unlink(fname_cer_der)
            os.unlink(fname_key_der)
            os.unlink(fname_password)
            os.unlink(fname_tmp)

            if not key_pem_b64 or not cer_pem_b64:
                warning = {
                    'title': _('Warning!'),
                    'message': _('You certificate file, key file or password is incorrect.\nVerify uppercase and lowercase')
                }
                value.update({
                    'certificate_file_pem': False,
                    'certificate_key_file_pem': False,
                })
            else:
                value.update({
                    'certificate_file_pem': cer_pem_b64,
                    'certificate_key_file_pem': key_pem_b64,
                })
        return {'value': value, 'warning': warning}
    
    def onchange_state(self, cr, uid, ids, state_id, context=None):
        if state_id:
            country_id = self.pool.get('res.country.state').browse(cr, uid, state_id, context).country_id.id
            return {'value':{'country_id':country_id}}
        return {}
    
    def onchange_email(self, cr, uid, ids, email, context=None):
        if email:
            return {'value':{'sf_email':email}}
        return {}
    
    def update_info_company(self, db_name, vals, reg):
        """
            Actualiza la informacion de la compañia de la base de datos
        """
        # Inicializa variables
        user_obj = self.pool.get('res.users')
        com_obj = self.pool.get('res.company')
        par_obj = self.pool.get('res.partner')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        reg_obj = self.pool.get('regimen.fiscal')
        context = {}
        country_id = False
        state_id = False
        re_id = False
        uid = 1
        
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        cr = self.conect_to_db(db_name)
        
        try:
            # Obtiene la informacion de la compañia
            company = user_obj.browse(cr, uid, uid, context=context).company_id
            
            if vals.get('rfc',False):
                # Actualiza la informacion de la compañia
                com_obj.write(cr, uid, [company.id], {'company_registry': vals.get('rfc','')}, context=context)
            
            # Obtiene el id del pais
            if reg.get('country',False):
                # Revisa si pais es diferente de mexico, sino retorna el id
                if reg.get('country',False) == 'Mexico' or reg.get('country',False) == 'México' or reg.get('country',False) == 'MEXICO':
                    country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                else:
                    country_ids = country_obj.search(cr, uid, [('name', '=', reg.get('country',False)),])
                    if not country_ids:
                        code = str(reg.get('country',False))
                        # Si no esta dado de alta el pais crea el nuevo registro
                        country_id = country_obj.create(cr, uid, {'name': code, 'code': code[:2], })
                    else:
                        country_id = country_ids[0]
                # Agrega el id del pais
                vals['country_id'] = country_id
                #print "*********** country_id ************** ", country_id
            # Obtiene el id del estado
            if reg.get('state',False):
                # Busca el id del estad, si no existe lo da de alta
                state_ids = state_obj.search(cr, uid, [('name', '=', reg.get('state',False)),])
                if not state_ids:
                    # Revisa si hay un pais asignado sino obtiene el de mexico
                    if not country_id:
                        country_ids = country_obj.search(cr, uid, [('code', '=', 'MX'),])
                        if not country_ids:
                            country_id = country_obj.create(cr, uid, {'name': 'México', 'code': 'MX', })
                        else:
                            country_id = country_ids[0] 
                    
                    #~ Si no esta el estado registrado, crea el nuevo registro
                    code = str(reg.get('state',False))
                    code = code[:3]
                    state_id = state_obj.create(cr, uid, {'name': reg.get('state',False), 'code': code, 'country_id': country_id })
                else:
                    state_id = state_ids[0]
                # Agrega el id al cliente
                vals['state_id'] = state_id
                #print "******************* state_id *********** ", state_id
            # Obtiene el id del regimen fiscal
            if reg.get('regimen_fiscal',False):
                # Revisa si existe el regimen fiscal
                reg_ids = country_obj.search(cr, uid, [('name', '=', reg.get('regimen_fiscal',False)),])
                if not reg_ids:
                    # Si no esta dado de alta el regimen fiscal, crea el nuevo registro
                    reg_id = reg_obj.create(cr, uid, {'name': reg.get('regimen_fiscal',False)})
                else:
                    reg_id = reg_ids[0]
                # Agrega el id del regimen fiscal
                vals['regimen_fiscal_id'] = reg_id
                #print "*************** regimen fiscal ************ ", reg_id
            # Agrega el RFC
            if vals.get('rfc','') != '':
                vals['vat'] = 'MX%s'%(vals.get('rfc',''),)
                #print "**************** vat *************** ", vals['vat']
            
            # Actualiza la informacion del contacto de la compañia
            par_obj.write(cr, uid, [company.partner_id.id], vals, context=context)
        finally:
            cr.close()
        return True
    
    def action_update_company(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de la compañia
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            # Genera un diccionario con la informacion a actualizar
            vals = {
                'name': info.name,
                'image': info.image,
                'website': info.website,
                'email': info.email,
                'phone': info.phone,
                'mobile': info.mobile,
                'rfc': info.vat,
                'street': info.street,
                'street2': info.street2,
                'city': info.city,
                'zip': info.zip,
                'l10n_mx_street3': info.l10n_mx_street3,
                'l10n_mx_street4': info.l10n_mx_street4,
                'l10n_mx_city2': info.l10n_mx_city2
            }
            reg = {}
            if info.state_id:
                reg['state'] = info.state_id.name
            if info.country_id:
                reg['country'] = info.country_id.name
            if info.regimen_fiscal_id:
                reg['regimen_fiscal'] = info.regimen_fiscal_id.name
            db_name = info.database_id.code
            # Actualiza la informacion de la compañia
            self.update_info_company(db_name, vals, reg)
        return True
    
    def get_config_pac_sf(self, cr, uid, context=None):
        """
            Obtiene la configuracion para generar el pac de sf
        """
        config_id = False
        res = {
            'url_webservice': False,
            'namespace': False,
            'certificate_link': False
        }
        cr.execute(
            """ select id as id
                from admon_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        #print "************* dat ************ ", dat
        config_id = dat and dat[0]['id'] or False
        # Obtiene la configuracion de la base de datos
        if config_id:
            config = self.pool.get('admon.config.settings').browse(cr, uid, config_id, context=context)
            res['url_webservice'] = config.url_webservice
            res['namespace'] = config.namespace
            res['certificate_link'] = config.certificate_link
        return res
    
    def update_info_pac_sf(self, db_name, vals):
        """
            Actualiza la informacion de los parametros de SF
        """
        # Inicializa variables
        pac_obj = self.pool.get('params.pac')
        user_obj = self.pool.get('res.users')
        context = {}
        uid = 1
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        cr = self.conect_to_db(db_name)
        
        try:
            # Obtiene la informacion de la compañia
            company = user_obj.browse(cr, uid, uid, context=context).company_id
            # Agrega el id de la compañia al registro
            vals['company_id'] = company.id
            vals['sequence'] = 10
            
            # Busca si hay pac's activos y los pasa a inactivos
            pac_ids = pac_obj.search(cr, uid, [('active','=',True)], context=context)
            if pac_ids:
                pac_obj.write(cr, uid, pac_ids, {'active':False}, context=context)
            
            # Crea un nuevo registro con la informacion del nuevo certificado para firmar
            vals['name'] = 'PAC SF - Firmar'
            vals['method_type'] = 'pac_sf_firmar'
            pac_obj.create(cr, uid, vals, context=context)
            # Crea un nuevo registro con la informacion del nuevo certificado para cancelar
            vals['name'] = 'PAC SF - Cancelar'
            vals['method_type'] = 'pac_sf_cancelar'
            pac_obj.create(cr, uid, vals, context=context)
        finally:
            cr.close()
        return True
    
    def action_update_pac_sf(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion del certificado
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            # Genera un diccionario con la informacion a actualizar
            vals = self.get_config_pac_sf(cr, uid, context=context)
            
            print "********* actualizar usuario y password ********* ", info.sf_email, " ** ", info.sf_password
            
            vals['user'] = '%s'%(info.sf_email,),
            vals['password'] = '%s',(info.sf_password,),
            vals['active'] = True
            reg = {}
            db_name = info.database_id.code
            
            #print "********** vals *********** ", vals
            
            # Actualiza la informacion de la compañia
            self.update_info_pac_sf(db_name, vals)
        return True
    
    def update_info_certificate(self, db_name, vals, reg):
        """
            Actualiza la informacion del certificado
        """
        # Inicializa variables
        user_obj = self.pool.get('res.users')
        cer_obj = self.pool.get('res.company.facturae.certificate')
        context = {}
        uid = 1
        # Obtiene el nombre de la base de datos y crea la conexion a la bd
        cr = self.conect_to_db(db_name)
        
        try:
            # Obtiene la informacion de la compañia
            company = user_obj.browse(cr, uid, uid, context=context).company_id
            # Agrega el id de la compañia al registro
            vals['company_id'] = company.id
            
            # Busca si hay certificados activos y los pasa a inactivos
            cer_ids = cer_obj.search(cr, uid, [('active','=',True)], context=context)
            if cer_ids:
                cer_obj.write(cr, uid, cer_ids, {'active':False}, context=context)
            
            # Crea un nuevo registro con la informacion del nuevo certificado
            cer_obj.create(cr, uid, vals, context=context)
        finally:
            cr.close()
        return True
    
    def action_update_certificate(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion del certificado
        """
        # Recorre los registros
        for info in self.browse(cr, uid, ids, context=context):
            # Genera un diccionario con la informacion a actualizar
            vals = {
                'certificate_file': info.certificate_file,
                'certificate_key_file': info.certificate_key_file,
                'certificate_password': info.certificate_password,
                'certificate_file_pem': info.certificate_file_pem,
                'certificate_key_file_pem': info.certificate_key_file_pem,
                'serial_number': info.serial_number,
                'company_registry': info.vat,
                'date_start': info.date_start,
                'date_end': info.date_end,
                'active': True
            }
            reg = {}
            db_name = info.database_id.code
            # Actualiza la informacion de la compañia
            self.update_info_certificate(db_name, vals, reg)
        return True
    
admon_database_info()
