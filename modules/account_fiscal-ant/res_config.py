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
class account_fiscal_config_settings(osv.Model):
    _name = 'account.fiscal.config.settings'
    _inherit = 'res.config.settings'
    _order = "id desc"

    _columns = {
        # Configuracion perdidas
        'code_id': fields.many2one('account.fiscal.code', 'Utilidad/Perdida', ondelete="restrict", required=True),
        'result_code_id': fields.many2one('account.fiscal.code', 'Total a Pagar', ondelete="restrict", required=True),
        'balance_code_id': fields.many2one('account.fiscal.code', 'Saldo Fiscal', ondelete="restrict", domain=[('apply_balance','=',True)], required=True),
        'balance_code_id2': fields.many2one('account.fiscal.code', 'Saldo por pagos provisionales del año', ondelete="restrict", domain=[('apply_balance','=',True)], required=True, help="Si la utilidad es negativa, evalua los pagos provicionales del año para generar el saldo fiscal"),
        # Configuracion saldos
        'balance_type_statement_id': fields.many2one('account.fiscal.statement.type', string='Tipo Movimiento', domain=[('type','=','income')], required=True),
        # Configuracion deducciones
        'category_id_deduction': fields.many2one('account.account.category','Deducciones Rubro fiscal', select="1", help="Rubro fiscal que se aplicara por default a la hora de aplicar las deducciones"),
    }
    
    def _check_balance_tax_id(self, cr, uid, ids, context=None):
        """
            Valida que tenga registrado un codigo de impuesto sobre el codigo fiscal de saldo
        """
        for config in self.browse(cr, uid, ids, context):
            if not config.balance_code_id.tax_code_id:
                return False
        return True
    
    #_constraints = [(_check_balance_tax_id, "El codigo del saldo fiscal debe tener configurado un Tipo de Impuesto!", ['balance_code_id']),]
    
    def get_default_code_id(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            code_id = self.browse(cr, uid, data).code_id
        return {'code_id': code_id and code_id.id or False}
    
    def get_default_result_code_id(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            code_id = self.browse(cr, uid, data).result_code_id
        return {'result_code_id': code_id and code_id.id or False}

    def get_default_balance_code_id(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            code_id = self.browse(cr, uid, data).balance_code_id
        return {'balance_code_id': code_id and code_id.id or False}

    def get_default_balance_code_id2(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            code_id = self.browse(cr, uid, data).balance_code_id2
        return {'balance_code_id2': code_id and code_id.id or False}

    def get_default_balance_type_statement_id(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            type_id = self.browse(cr, uid, data).balance_type_statement_id
        return {'balance_type_statement_id': type_id and type_id.id or False}

    def get_default_category_id_deduction(self, cr, uid, fields, context=None):
        code_id = False
        cr.execute(
            """ select max(id) as code_id from account_fiscal_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('code_id',False) or False
        if data:
            category_id = self.browse(cr, uid, data).category_id_deduction
        return {'category_id_deduction': category_id and category_id.id or False}

account_fiscal_config_settings()

# Configuracion sobre cierre de periodo fiscal:
class account_period_config_settings(osv.Model):
    _name = 'account.period.config.settings'
    _inherit = 'res.config.settings'
    _order = "id desc"

    _columns = {
        # Para el cierre del periodo
        'account_category_id': fields.many2one('account.account.category', 'Resultado Ingresos', ondelete="restrict", help="Obtiene el valor del resultado de ingresos para aplicar sobre el cierre del periodo"),
        'account_credit_id': fields.many2one('account.account', 'Cuenta de cierre periodo', ondelete="restrict", domain=[('type','=','other')]),
        'account_debit_id': fields.many2one('account.account', 'Cuenta de orden', ondelete="restrict", domain=[('type','=','other')], help="Si la utilidad es negativa, evalua los pagos provicionales del año para generar el saldo fiscal"),
        'journal_id': fields.many2one('account.journal', string='Diario de cierre', domain=[('type','=','period')]),
        # Configuracion deducciones
        'apply_to_exercise': fields.boolean('Aplicar sobre ejercicio'),
    }
    
    def get_default_account_category_id(self, cr, uid, fields, context=None):
        reg_id = False
        cr.execute(
            """ select max(id) as id from account_period_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('id',False) or False
        if data:
            reg_id = self.browse(cr, uid, data).account_category_id
        return {'account_category_id': reg_id and reg_id.id or False}
    
    def get_default_account_credit_id(self, cr, uid, fields, context=None):
        reg_id = False
        cr.execute(
            """ select max(id) as code_id from account_period_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('id',False) or False
        if data:
            reg_id = self.browse(cr, uid, data).account_credit_id
        return {'account_credit_id': reg_id and reg_id.id or False}
    
    def get_default_account_debit_id(self, cr, uid, fields, context=None):
        reg_id = False
        cr.execute(
            """ select max(id) as code_id from account_period_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('id',False) or False
        if data:
            reg_id = self.browse(cr, uid, data).account_debit_id
        return {'account_debit_id': reg_id and reg_id.id or False}
    
    def get_default_journal_id(self, cr, uid, fields, context=None):
        reg_id = False
        cr.execute(
            """ select max(id) as code_id from account_period_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('id',False) or False
        if data:
            reg_id = self.browse(cr, uid, data).journal_id
        return {'journal_id': reg_id and reg_id.id or False}
    
    def get_default_apply_to_exercise(self, cr, uid, fields, context=None):
        reg_id = False
        cr.execute(
            """ select max(id) as code_id from account_period_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0].get('id',False) or False
        if data:
            reg_id = self.browse(cr, uid, data).apply_to_exercise
        return {'apply_to_exercise': reg_id or False}
    
account_period_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
