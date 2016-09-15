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
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_invoice(osv.osv):
    """ Inherits partner and add extra information invoice """
    _inherit = 'account.invoice'

    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el total del registro
        """
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            # Suma el subtotal y los impuestos
            res[invoice.id] = invoice.amount_untaxed2 + invoice.amount_tax2
        return res

    _columns = {
        'account_id': fields.many2one('account.account', 'Account', required=False, readonly=True, states={'draft':[('readonly',False)]}, help="The partner account used for this invoice."),
        'journal_id': fields.many2one('account.journal', 'Journal', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        # Agregados para webservice
        'mov': fields.char('Movimiento'),
        'date_invoice': fields.date('Fecha Emision'),
        'currency_id': fields.many2one('res.currency', 'Moneda', readonly=True),
        'notes': fields.text('Observaciones'),
        'status': fields.selection([
                                    ('CANCELADO', 'Cancelado'),
                                    ('CONCLUIDO', 'Concluido'),
                                    ('CONFIRMAR', 'Confirmado'),
                                    ('PENDIENTE', 'Pendiente'),
                                    ('SINAFECTAR', 'Sin Afectar')], 'Estatus'),
        'partner_id': fields.many2one('res.partner', 'Enviar a', change_default=True),
        'partner_id2': fields.many2one('res.partner', 'Cliente', change_default=True),
        'date_req': fields.date('Fecha Requerida'),
        'condition': fields.char('Condicion', size=128),
        'date_expired': fields.date('Vencimiento'),
        'discount': fields.char('Descuento', size=128),
        'global_discount': fields.char('Descuento Global', size=128),
        'amount_untaxed2': fields.float('Verification Total', digits_compute=dp.get_precision('Account'), readonly=True),
        'amount_tax2': fields.float('Verification Total', digits_compute=dp.get_precision('Account'), readonly=True),
        'amount_total2': fields.function(_amount_total, digits_compute=dp.get_precision('Account'), type="float", string='Total', store=True),
        'exercise': fields.char('Ejercicio', size=128),
        'period': fields.char('Periodo', size=128),
        'date_start': fields.date('Fecha Registro'),
        'date_finish': fields.date('Fecha Conclusion'),
        'price_list_esp': fields.char('Lista Precio Especial', size=128),
        'branch': fields.char('Sucursal', size=128),
        'branch_sale': fields.char('Sucursal Venta', size=128),
         # Campos para webservice
        'ws_id': fields.char('Id webservice', size=64),
        'branch_id': fields.related('partner_id2', 'branch_id', type="many2one", relation="crm.access.branch", store=True, string="Sucursal", readonly=True),
        # Usuario relacionado con el cliente
        'user_id2': fields.related('partner_id2', 'user_id', type="many2one", relation="res.users", store=True, string="Vendedor", readonly=True),
    }
    
    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(account_invoice, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        # Actualiza la actividad de los partners
        invoice = self.browse(cr, uid, res, context=context)
        if invoice.partner_id2:
            partner_obj = self.pool.get('res.partner')
            if invoice.partner_id2.is_company == True:
                partner_obj._reset_date_notify(cr, uid, invoice.partner_id2.id, context=context)
                partner_obj._reset_date_notify_sale(cr, uid, invoice.partner_id2.id, context=context)
                # Revisa si es recomendado
                if invoice.partner_id2.parent_id2:
                    partner_obj._reset_date_notify(cr, uid, invoice.partner_id2.parent_id2.id, context=context)
                    partner_obj._reset_date_notify_sale(cr, uid, invoice.partner_id2.parent_id2.id, context=context)
            elif invoice.partner_id2.parent_id:
                partner_obj._reset_date_notify(cr, uid, invoice.partner_id2.parent_id.id, context=context)
                partner_obj._reset_date_notify_sale(cr, uid, invoice.partner_id2.parent_id.id, context=context)
                # Revisa si es recomendado
                if invoice.partner_id2.parent_id.parent_id2:
                    partner_obj._reset_date_notify(cr, uid, invoice.partner_id2.parent_id.parent_id2.id, context=context)
                    partner_obj._reset_date_notify_sale(cr, uid, invoice.partner_id2.parent_id.parent_id2.id, context=context)
        return res
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class account_invoice_line(osv.osv):
    """ Inherits partner and add extra information invoice line"""
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
            'name': "Factura",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': invoice_line.invoice_id.id
        }
    
    _columns = {
        # Campos para vista reporte de detalle de factura
        'partner_id': fields.related('invoice_id', 'partner_id2', type="many2one", relation="res.partner", store=True, string="Cliente", readonly=True),
        'branch_id': fields.related('invoice_id', 'branch_id', type="many2one", relation="crm.access.branch", store=True, string="Sucursal", readonly=True),
        'user_id': fields.related('invoice_id', 'user_id2', type="many2one", relation="res.users", store=True, string="Vendedor", readonly=True),
        'currency_id': fields.related('invoice_id', 'currency_id', type="many2one", relation="res.currency", store=True, string="Moneda", readonly=True),
        'date_finish': fields.related('invoice_id','date_finish', type='date', readonly=True, store=True, string='Fecha de conclusion'),
        'exercise': fields.related('invoice_id','exercise', type='char', readonly=True, store=True, string='Ejercicio'),
        'period': fields.related('invoice_id','period', type='char', readonly=True, store=True, string='Periodo'),
        
        'stock': fields.char('Almacen', size=128),
         # Campos para webservice
        'ws_id': fields.char('Id webservice', size=64),

    }
    
account_invoice_line()
