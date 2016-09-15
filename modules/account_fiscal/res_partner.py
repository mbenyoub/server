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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Partner
# ---------------------------------------------------------

class res_partner_account_category(osv.Model):
    _name = 'res.partner.account.category'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'
    
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _columns = {
        'name': fields.char('Nombre', size=128),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Nombre'),
        'parent_id': fields.many2one('res.partner.account.category','Categoria padre', domain=[('type','=','view')], select=True, ondelete='cascade'),
        'child_id': fields.one2many('res.partner.account.category', 'parent_id', string='Categorias Hijas'),
        'sequence': fields.integer('Secuencia', select=True),
        'type': fields.selection([('view','Vista'), ('normal','Normal')], 'Tipo', help="Las categorias de vista se utilizan para generar una relacion de arbol como categorias padre."),
        'parent_left': fields.integer('Padre Izquierdo', select=1),
        'parent_right': fields.integer('Padre derecho', select=1),
        
        'property_account_payable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta a pagar",
            view_load=True,
            domain="[('type', '=', 'payable')]"),
        'property_account_receivable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta a cobrar",
            view_load=True,
            domain="[('type', '=', 'receivable')]"),
        'property_account_asset': fields.many2one('account.account', 'Cuenta Acreedora venta de activo', domain="[('type', '=', 'receivable')]", help="Seleccione una cuenta acreedora para utilizarla para cargar el monto de la venta de los activos, en caso de no seleccionar una cuenta utiliza la cuenta por cobrar del cliente"),
        'property_account_advance_customer': fields.many2one('account.account', 'Cuenta Anticipo a cobro', domain="[('type', '=', 'receivable')]"),
        'property_account_advance_supplier': fields.many2one('account.account', 'Cuenta Anticipo a pago', domain="[('type', '=', 'payable')]"),
        'note': fields.text('Comentarios'),
        'active': fields.boolean('Activo'),
        'property_account_receivable_note': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta a cobrar Nota de Venta",
            view_load=True,
            domain="[('type', '=', 'receivable')]"),
    }
    
    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from res_partner_account_category where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error! No se pueden crear categorias recursivas.', ['parent_id'])
    ]
    
    def _get_account_asset_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta acredora por default para la venta de los activos
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','1129009000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    def _get_account_advance_customer_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta de anticipos para clientes
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','2131001000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    def _get_account_advance_supplier_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta de anticipos para proveedor
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','1129008000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    _defaults = {
        'type' : lambda *a : 'normal',
        'property_account_asset': _get_account_asset_default,
        'property_account_advance_customer': _get_account_advance_customer_default,
        'property_account_advance_supplier': _get_account_advance_supplier_default,
        'active': True
    }

res_partner_account_category()

class res_partner(osv.Model):
    _inherit = 'res.partner'
    
    def _get_voucher_amount(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el total de los montos
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False
        
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        account_type = 'receivable'
        res = {}
        
        # Recorre los registros
        for partner in self.browse(cr, uid, ids, context=context):
            to_pay = 0.0 # Lo que debe al cliente
            to_collect = 0.0 # Lo que el cliente debe pagar
            currency_id = partner.company_id.currency_id.id
            
            # Obtiene los movimientos y los clasifica para ver si el monto es por pagar o pagado
            move_ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner.id)], context=context)
            
            for line in move_line_pool.browse(cr, uid, move_ids, context=context):
                if _remove_noise_in_o2m():
                    continue
                
                #total_credit += line.credit and line.amount_currency or 0.0
                #total_debit += line.debit and line.amount_currency or 0.0
                
                if not line.currency_id or (line.currency_id and currency_id == line.currency_id.id):
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                    #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    amount_original = currency_pool.compute(cr, uid, currency_id, line.currency_id.id, line.credit or line.debit or 0.0, context=context)
                    amount_unreconciled = currency_pool.compute(cr, uid, currency_id, line.currency_id.id, abs(line.amount_residual), context=context)
                
                line_type = line.credit and 'dr' or 'cr'
                
                if line_type == 'cr':
                    to_pay += amount_unreconciled
                else:
                    to_collect += amount_unreconciled
                
            res[partner.id] = {
                'to_pay': to_pay,
                'to_collect': to_collect
            }
        return res
    
    def onchange_acc_categ_id(self, cr, uid, ids, categ_id, context=None):
        """
            Actualiza la informacion del contacto en base a la categoria seleccionada
        """
        categ_obj = self.pool.get('res.partner.account.category')
        if not categ_id:
            return {}
        res = {}
        category = categ_obj.browse(cr, uid, categ_id, context=context)
        
        if category.property_account_payable:
            res['property_account_payable'] = category.property_account_payable.id
        if category.property_account_receivable:
            res['property_account_receivable'] = category.property_account_receivable.id
        if category.property_account_asset:
            res['property_account_asset'] = category.property_account_asset.id
        if category.property_account_advance_customer:
            res['property_account_advance_customer'] = category.property_account_advance_customer.id
        if category.property_account_advance_supplier:
            res['property_account_advance_supplier'] = category.property_account_advance_supplier.id
        if category.property_account_receivable_note:
            res['property_account_receivable_note'] = category.property_account_receivable_note.id
        
        return {'value': res}
    
    _columns = {
        'regimen_title': fields.related('regimen_fiscal_id', 'title', type='selection', selection=[
                        ('title_2','Titulo 2'),
                        ('title_4','Titulo 4')], string='Titulo', readonly=True),
        'title2': fields.char('Titulo', size=8),
        'to_pay': fields.function(_get_voucher_amount, string="Saldo a cargo", type='float', digits_compute= dp.get_precision('Account'), store=False, multi='voucher'),
        'to_collect': fields.function(_get_voucher_amount, string="Saldo a favor", type='float', digits_compute= dp.get_precision('Account'), store=False, multi='voucher'),
        
        'property_account_advance_customer': fields.many2one('account.account', 'Cuenta Anticipo a cobro', domain="[('type', '=', 'receivable')]"),
        'property_account_advance_supplier': fields.many2one('account.account', 'Cuenta Anticipo a pago', domain="[('type', '=', 'payable')]"),
        'acc_categ_id': fields.many2one('res.partner.account.category', 'Categoria', domain=[('type','=','normal')]),
    }
    
    def _get_account_advance_customer_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta de anticipos para clientes
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','2131001000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    def _get_account_advance_supplier_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta de anticipos para proveedor
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','1129008000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    def _get_pay_method_default(self, cr, uid, context=None):
        """
            Obtiene no identificado por default
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'l10n_mx_payment_method', 'pay_method_none').id
        except:
            pass
        return res
    
    def _get_acc_categ_id_default(self, cr, uid, context=None):
        """
            Obtiene la categoria por default para los contactos
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'account_fiscal', 'partner_acc_category_01').id
        except:
            pass
        return res
    
    _defaults = {
        'type': 'invoice',
        'title2': 'title_8',
        'pay_method_id': _get_pay_method_default,
        'property_account_advance_customer': _get_account_advance_customer_default,
        'property_account_advance_supplier': _get_account_advance_supplier_default,
        'acc_categ_id': _get_acc_categ_id_default
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
