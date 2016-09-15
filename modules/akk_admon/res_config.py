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

from openerp.osv import fields, osv
from openerp import pooler

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

#class account_fiscal_config_settings(osv.TransientModel):
class admon_config_settings(osv.Model):
    _name = 'admon.config.settings'
    _inherit = 'res.config.settings'
    _order = "id desc"

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
        # Configuracion Duplicado base de datos
        'db_list': fields.selection(_get_method_db_selection,
            "Base de Datos", type='char', size=64, required=True),
        # Configuracion timbrado
        'url_webservice': fields.char('URL WebService', size=256, required=True,
            help='URL of WebService used for send to sign the XML to PAC'),
        'namespace': fields.char('NameSpace', size=256,
            help='NameSpace of XML of the page of WebService of the PAC'),
        'certificate_link': fields.char('Certificate link', size=256 , 
            help='PAC have a public certificate that is necessary by customers to check the validity of the XML and PDF'),
        'password': fields.char('Pasword Superusuario', size=32),
        # Plantillas para importacion de datos
        'import_partner': fields.binary('Contactos', filters='*.csv'),
        'import_product': fields.binary('Productos', filters='*.csv'),
        'import_asset': fields.binary('Activos', filters='*.csv'),
        'import_bank': fields.binary('Cuentas Bancarias', filters='*.csv'),
        'import_balance': fields.binary('Saldos Iniciales', filters='*.csv'),
        'import_payment': fields.binary('Cobros y pagos pendientes', filters='*.csv'),
        'import_rate': fields.binary('Saldos Fiscales', filters='*.csv'),
        'import_utility': fields.binary('Perdidas fiscales', filters='*.csv'),
        'import_tax': fields.binary('Impuestos a favor', filters='*.csv'),
    }
    
    def get_default_db_list(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).db_list
        return {'db_list': res or False}
    
    def get_default_url_webservice(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).url_webservice
        return {'url_webservice': res or False}

    def get_default_namespace(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).namespace
        return {'namespace': res or False}

    def get_default_certificate_link(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).certificate_link
        return {'certificate_link': res or False}

    def get_default_password(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).password
        return {'password': res or False}

    def get_default_import_partner(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_partner
        return {'import_partner': res or False}

    def get_default_import_product(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_product
        return {'import_product': res or False}

    def get_default_import_asset(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_asset
        return {'import_asset': res or False}

    def get_default_import_bank(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_bank
        return {'import_bank': res or False}

    def get_default_import_balance(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_balance
        return {'import_balance': res or False}

    def get_default_import_payment(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_payment
        return {'import_payment': res or False}

    def get_default_import_rate(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_rate
        return {'import_rate': res or False}

    def get_default_import_utility(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_utility
        return {'import_utility': res or False}

    def get_default_import_tax(self, cr, uid, fields, context=None):
        res = False
        cr.execute(
            """ select max(id) as reg_id from admon_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['reg_id'] or False
        if data:
            res = self.browse(cr, uid, data).import_tax
        return {'import_tax': res or False}

admon_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
