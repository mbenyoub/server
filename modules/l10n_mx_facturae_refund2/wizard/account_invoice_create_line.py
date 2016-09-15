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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_invoice_create_line(osv.osv_memory):
    _name = 'account.invoice.create.line'
    _description = 'Agregar detalle factura'
    
    def action_create_invoice_line(self, cr, uid, ids, context=None):
        """
            Agrega el codigo hijo al indice fiscal
        """
        line_obj = self.pool.get('account.invoice.line')
        # Recorre los registros
        for line in self.browse(cr, uid, ids, context=context):
            # Obtiene los ids de los impuestos
            tax_list = []
            for tax in line.invoice_line_tax_id:
                tax_list.append(tax.id)
            # Agrega el nuevo registro
            values = {
                'name': line.name,
                'invoice_id': line.invoice_id.id or False,
                'ous_id': line.uos_id.id or False,
                'product_id': line.product_id.id or False,
                'account_id': line.account_id.id or False,
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'discount': line.discount,
                'invoice_line_tax_id': [(6,0, tax_list)],
                'account_analytic_id': line.account_analytic_id.id or False
            }
            # Crea el nuevo registro
            line_id = line_obj.create(cr, uid, values, context=context)
        return True
    
    def _price_unit_default(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('check_total', False):
            t = context['check_total']
            for l in context.get('invoice_line', {}):
                if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                    tax_obj = self.pool.get('account.tax')
                    p = l[2].get('price_unit', 0) * (1-l[2].get('discount', 0)/100.0)
                    t = t - (p * l[2].get('quantity'))
                    taxes = l[2].get('invoice_line_tax_id')
                    if len(taxes[0]) >= 3 and taxes[0][2]:
                        taxes = tax_obj.browse(cr, uid, list(taxes[0][2]))
                        for tax in tax_obj.compute_all(cr, uid, taxes, p,l[2].get('quantity'), l[2].get('product_id', False), context.get('partner_id', False))['taxes']:
                            t = t - tax['amount']
            return t
        return 0
    
    _columns = {
        'name': fields.text('Descripcion', required=True),
        'invoice_id': fields.many2one('account.invoice', 'Factura Referencia'),
        'uos_id': fields.many2one('product.uom', 'Unidad de medida'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'account_id': fields.many2one('account.account', 'Cuenta', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The income or expense account related to the selected product."),
        'price_unit': fields.float('Precio unitario', required=True, digits_compute= dp.get_precision('Product Price')),
        'quantity': fields.float('Cantidad', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'discount': fields.float('Descuento (%)', digits_compute= dp.get_precision('Discount')),
        'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_line_create_tax', 'invoice_line_id', 'tax_id', 'Impuestos', domain=[('parent_id','=',False)]),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Cuenta analitica'),
        'type_invoice': fields.related('invoice_id','type',type='char',string='type', readonly=True),
        'company_id': fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', readonly=True),
        'partner_id': fields.related('invoice_id','partner_id',type='many2one',relation='res.partner',string='Partner'),
        'journal_id': fields.related('invoice_id','journal_id',type='many2one',relation='account.journal',string='Journal'),
        'fiscal_position': fields.related('invoice_id','fiscal_position',type='many2one',relation='account.fiscal.position',string='Fiscal position'),
        'currency_id': fields.related('invoice_id','currency_id',type='many2one',relation='res.currency',string='Currency'),
    }

    def _default_account_id(self, cr, uid, context=None):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        if context is None:
            context = {}
        if context.get('type') in ('out_invoice','out_refund'):
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
        else:
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category', context=context)
        return prop and prop.id or False

    _defaults = {
        'quantity': 1,
        'discount': 0.0,
        'price_unit': _price_unit_default,
        'account_id': _default_account_id,
    }
    
    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        if context is None:
            context = {}
        company_id = company_id if company_id != None else context.get('company_id',False)
        context = dict(context)
        context.update({'company_id': company_id, 'force_company': company_id})
        if not partner_id:
            raise osv.except_osv(_('No Partner Defined!'),_("You must first select a partner!") )
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain':{'product_uom':[]}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain':{'product_uom':[]}}
        part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        fpos_obj = self.pool.get('account.fiscal.position')
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False

        if part.lang:
            context.update({'lang': part.lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        if type in ('out_invoice','out_refund'):
            a = res.property_account_income.id
            if not a:
                a = res.categ_id.property_account_income_categ.id
        else:
            a = res.property_account_expense.id
            if not a:
                a = res.categ_id.property_account_expense_categ.id
        a = fpos_obj.map_account(cr, uid, fpos, a)
        if a:
            result['account_id'] = a

        if type in ('out_invoice', 'out_refund'):
            taxes = res.taxes_id and res.taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        else:
            taxes = res.supplier_taxes_id and res.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)

        if type in ('in_invoice', 'in_refund'):
            result.update( {'price_unit': price_unit or res.standard_price,'invoice_line_tax_id': tax_id} )
        else:
            result.update({'price_unit': res.list_price, 'invoice_line_tax_id': tax_id})
        result['name'] = res.partner_ref

        result['uos_id'] = uom_id or res.uom_id.id
        if res.description:
            result['name'] += '\n'+res.description

        domain = {'uos_id':[('category_id','=',res.uom_id.category_id.id)]}

        res_final = {'value':result, 'domain':domain}

        if not company_id or not currency_id:
            return res_final

        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        currency = self.pool.get('res.currency').browse(cr, uid, currency_id, context=context)

        if company.currency_id.id != currency.id:
            if type in ('in_invoice', 'in_refund'):
                res_final['value']['price_unit'] = res.standard_price
            new_price = res_final['value']['price_unit'] * currency.rate
            res_final['value']['price_unit'] = new_price

        if result['uos_id'] and result['uos_id'] != res.uom_id.id:
            selected_uom = self.pool.get('product.uom').browse(cr, uid, result['uos_id'], context=context)
            new_price = self.pool.get('product.uom')._compute_price(cr, uid, res.uom_id.id, res_final['value']['price_unit'], result['uos_id'])
            res_final['value']['price_unit'] = new_price
        return res_final

    def uos_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        if context is None:
            context = {}
        company_id = company_id if company_id != None else context.get('company_id',False)
        context = dict(context)
        context.update({'company_id': company_id})
        warning = {}
        res = self.product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id, fposition_id, price_unit, currency_id, context=context)
        if not uom:
            res['value']['price_unit'] = 0.0
        if product and uom:
            prod = self.pool.get('product.product').browse(cr, uid, product, context=context)
            prod_uom = self.pool.get('product.uom').browse(cr, uid, uom, context=context)
            if prod.uom_id.category_id.id != prod_uom.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure is not compatible with the unit of measure of the product.')
                }
                res['value'].update({'uos_id': prod.uom_id.id})
            return {'value': res['value'], 'warning': warning}
        return res
    
    def onchange_account_id(self, cr, uid, ids, product_id, partner_id, inv_type, fposition_id, account_id):
        if not account_id:
            return {}
        unique_tax_ids = []
        fpos = fposition_id and self.pool.get('account.fiscal.position').browse(cr, uid, fposition_id) or False
        account = self.pool.get('account.account').browse(cr, uid, account_id)
        if not product_id:
            taxes = account.tax_ids
            unique_tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
        else:
            product_change_result = self.product_id_change(cr, uid, ids, product_id, False, type=inv_type,
                partner_id=partner_id, fposition_id=fposition_id,
                company_id=account.company_id.id)
            if product_change_result and 'value' in product_change_result and 'invoice_line_tax_id' in product_change_result['value']:
                unique_tax_ids = product_change_result['value']['invoice_line_tax_id']
        return {'value':{'invoice_line_tax_id': unique_tax_ids}}

account_invoice_create_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
