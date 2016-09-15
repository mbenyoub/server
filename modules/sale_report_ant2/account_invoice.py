# -*- coding: utf-8 -*-
from osv import osv, fields
import openerp.addons.decimal_precision as dp
from datetime import datetime, date, time, timedelta
import calendar

class account_invoice_line_inherit(osv.Model):
    _inherit = 'account.invoice.line'

    def action_redirect_invoice(self, cr, uid, ids, context=None):
        """
            Redirecciona a la factura del registro
        """
        # Obtiene el objeto a cargar
        invoice_line = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
        
        return {
            'name':_("Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': invoice_line.invoice_id.id or False
        }

    def _get_more_that(self, cr, uid, ids, field_name, args, context=None):
        """
           Compara si el precio unitario es menor que precio original
        """
        res = {}

        # Recorre los registros obtenidos
        for line in self.browse(cr, uid, ids, context=context):
            # Valida si el precio unitario es menor que el precio original
            if line.price_unit < line.price_original:
                res[line.id] = 'less'
            else:
                res[line.id] = 'more'

            # Validando si los valores son iguales
            if line.price_unit == line.price_original:
                res[line.id] = 'equal'
        return res

    def _amount_line_tax(self, cr, uid, line, context=None):
        """
            Calculando el total con impuestos
        """
        val = 0.0

        # Se llama para redondear la cantindad
        cur_obj = self.pool.get('res.currency')

        # Calculando impuestos
        for c in self.pool.get('account.tax').compute_all(cr, uid,
            line.invoice_line_tax_id, line.price_unit * (1 - (line.discount or
                0.0) / 100.0), line.quantity, line.product_id,
                line.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        cur = line.invoice_id.currency_id or 0.0

        print """"""""""""""""cur:  """, cur

        if cur:
            # Regresando el valor de los impuestos redondeado
            return cur_obj.round(cr, uid, cur, val)
        else:
            return 0.0

    def _compute_line_all(self, cr, uid, ids, field_names, args, context=None):
        """
            Calculando total con impuestos por producto
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'price_unit_discount': 0.0,
                'price_subtotal2': 0.0,
                'diference': 0.0,
                'total_cost': 0.0,
                'utility': 0.0,
                'utility_percent': 0.0,
            }
            
            # Se obtiene el importe o subtotal
            price = line.price_unit * line.quantity
            
            # Actualiza el importe sin descuentos
            res[line.id]['price_subtotal2'] = price
            
            # Calculamos el precio del producto con descuentos aplicados
            res[line.id]['price_unit_discount'] = (line.price_subtotal / line.quantity)
            
            # Calculamos la diferencia de importes
            res[line.id]['diference'] = price - line.price_subtotal
            
            # Obtiene el costo total
            res[line.id]['total_cost'] = line.standard_price * line.quantity
            
            # Calcula la utilidad
            utility = line.price_subtotal - res[line.id]['total_cost']
            res[line.id]['utility'] = utility
            res[line.id]['utility_percent'] = (utility/line.price_subtotal)*100 if utility != 0 else 0.0
        return res
    
    def _get_week(self, cr, uid, ids, field_name, args, context=None):
        """
            Obtiene el número de semana a la que pertenece una fecha
        """
        res = {}
        
        for move in self.browse(cr, uid, ids, context=context):
            if move.date_invoice:
                date_invoice = datetime.strptime(move.date_invoice, "%Y-%m-%d")
                res[move.id] = date_invoice.strftime("%W")
        
        return res

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', 'Tarifa'),
        'price_original': fields.float('Precio original', digits=(2, 3)),
        'type': fields.related('invoice_id', 'type', type='char', string='Tipo', store=True),
        'shop_id': fields.related('invoice_id', 'shop_id', type='many2one', relation='sale.shop', string='Tienda',
            store=True),
        'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string='Fecha Factura', store=True),
        'week_invoice': fields.function(_get_week, type='integer', string='Semana', store=True),
        'state': fields.related('invoice_id', 'state', type='selection',
            selection=[
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
            ],
            string='Estado', store=True),
        'journal_id': fields.related('invoice_id', 'journal_id',
            type='many2one', relation="account.journal", string="Diario",
            store=True),
        'period_id': fields.related('invoice_id', 'period_id',
            type='many2one', relation='account.period', string="Periodo",
            store=True),
        'user_id': fields.related('invoice_id', 'user_id', type='many2one',
            relation="res.users", string="Vendedor", store=True),
        'default_id': fields.related('user_id', 'default_section_id', type='many2one', relation='crm.case.section',
            string="Equipo de ventas", store=True),
        'city': fields.char('Ciudad'),
        
        # Campos para reporte de ventas
        'price_unit_discount': fields.function(_compute_line_all, type='float',
            digits_compute=dp.get_precision('Account'), string='Precio C/Desc (unitario)', method=True, store=True,
            multi='amount_all'),
        'price_subtotal2':fields.function(_compute_line_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Importe C/Desc', method=True, store=True, multi='amount_all'),
        'diference':fields.function(_compute_line_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Diferencia', method=True, store=True, multi='amount_all'),
        'total_cost': fields.function(_compute_line_all, type='float', digits_compute= dp.get_precision('Account'),
            store=True, string='Total costo', method=True, multi="amount_all"),
        'utility':fields.function(_compute_line_all, type='float', digits_compute=dp.get_precision('Account'),
            string='Utilidad', store=True, method=True, multi="amount_all"),
        'utility_percent':fields.function(_compute_line_all, type='float', digits_compute=dp.get_precision('Account'),
            string='%Utilidad', method=True, store=True, multi='amount_all'),
    }
