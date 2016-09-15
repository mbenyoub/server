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
from openerp.tools.translate import _

#class account_fiscal_config_settings(osv.TransientModel):
class account_diot_config_settings(osv.Model):
    _name = 'account.diot.config.settings'
    _inherit = 'res.config.settings'
    _order = "id desc"

    _columns = {
        # Configuracion de cuentas donde los impuestos donde se va a obtener la informacion de la DIOT
        'diot_account_id1': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id2': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id3': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id4': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id5': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id6': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id7': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id8': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id9': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id10': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id11': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id12': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id13': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id14': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
        'diot_account_id15': fields.many2one('account.tax.code', 'Codigo Impuesto', ondelete="restrict"),
    }
    
    def get_default_code_id1(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id1
        return {'diot_account_id1': reg_id and reg_id.id or False}
    
    def get_default_code_id2(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id2
        return {'diot_account_id2': reg_id and reg_id.id or False}
    
    def get_default_code_id3(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id3
        return {'diot_account_id3': reg_id and reg_id.id or False}
    
    def get_default_code_id4(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id4
        return {'diot_account_id4': reg_id and reg_id.id or False}
    
    def get_default_code_id5(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id5
        return {'diot_account_id5': reg_id and reg_id.id or False}
    
    def get_default_code_id6(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id6
        return {'diot_account_id6': reg_id and reg_id.id or False}
    
    def get_default_code_id7(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id7
        return {'diot_account_id7': reg_id and reg_id.id or False}
    
    def get_default_code_id8(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id8
        return {'diot_account_id8': reg_id and reg_id.id or False}
    
    def get_default_code_id9(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id9
        return {'diot_account_id9': reg_id and reg_id.id or False}
    
    def get_default_code_id10(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id10
        return {'diot_account_id10': reg_id and reg_id.id or False}
    
    def get_default_code_id11(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id11
        return {'diot_account_id11': reg_id and reg_id.id or False}
    
    def get_default_code_id12(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id12
        return {'diot_account_id12': reg_id and reg_id.id or False}
    
    def get_default_code_id13(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id13
        return {'diot_account_id13': reg_id and reg_id.id or False}
    
    def get_default_code_id14(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id14
        return {'diot_account_id14': reg_id and reg_id.id or False}
    
    
    def get_default_code_id15(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del codigo de impuesto
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from account_diot_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).diot_account_id15
        return {'diot_account_id15': reg_id and reg_id.id or False}
    
account_diot_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
