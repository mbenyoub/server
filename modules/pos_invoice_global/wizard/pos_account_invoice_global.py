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
from openerp import netsvc

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

# ---------------------------------------------------------
# Creacion de Facturacion Global
# ---------------------------------------------------------

class pos_account_invoice_global(osv.osv_memory):
    """
        Generacion de factura global sobre notass de venta
    """
    _name = "pos.account.invoice.global.wizard"
    
    def onchange_journal_id(self, cr, uid, ids, journal_id, pos_config_id, context=None):
        """
            Aplica filtro sobre los padres que puede utilizar en los codigos fiscales segun aplique por año o por procesos mensaules
        """
        order_obj = self.pool.get('pos.order')
        res = []
        if journal_id:
            search = [('sale_journal','=',journal_id),('state','=','done'),('global_invoice','=',False)]
            # Valida si va a filtrar por una terminal de punto de venta
            if pos_config_id:
                search.append(('session_id.config_id','=',pos_config_id))
            
            # Obtiene las notas de venta que se van facturar
            order_ids = order_obj.search(cr, uid, search, context=context)
            
            for order in order_obj.browse(cr, uid, order_ids, context=context):
                res.append({
                    'name': order.name,
                    'order_id': order.id,
                    'session_id': order.session_id.id,
                    'state': order.state,
                    'date': order.date_order,
                    'partner_id': order.partner_id.id or False
                })
            
        return {'value': {'line_ids': res}}
    
    def _get_journal_cfdi(self, cr, uid, context=None):
        """
            Obtiene el diario por default para facturacion
        """
        if context is None:
            context = {}
        type_inv = context.get('type', 'out_invoice')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = context.get('company_id', user.company_id.id)
        type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
        journal_obj = self.pool.get('account.journal')
        domain = [('company_id', '=', company_id),('note_sale','=',False)]
        if isinstance(type_inv, list):
            domain.append(('type', 'in', [type2journal.get(type) for type in type_inv if type2journal.get(type)]))
        else:
            domain.append(('type', '=', type2journal.get(type_inv, 'sale')))
        res = journal_obj.search(cr, uid, domain, limit=1)
        return res and res[0] or False

    def _get_journal(self, cr, uid, context=None):
        """
            Obtiene el diario por default para notas de ventas
        """
        if context is None:
            context = {}
        type_inv = context.get('type', 'out_invoice')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = context.get('company_id', user.company_id.id)
        type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
        journal_obj = self.pool.get('account.journal')
        domain = [('company_id', '=', company_id),('note_sale','=',True)]
        if isinstance(type_inv, list):
            domain.append(('type', 'in', [type2journal.get(type) for type in type_inv if type2journal.get(type)]))
        else:
            domain.append(('type', '=', type2journal.get(type_inv, 'sale')))
        res = journal_obj.search(cr, uid, domain, limit=1)
        return res and res[0] or False
    
    def _get_currency(self, cr, uid, context=None):
        """
            Obtiene la moneda que esta por default
        """
        res = False
        journal_id = self._get_journal(cr, uid, context=context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            res = journal.currency and journal.currency.id or journal.company_id.currency_id.id
        return res
    
    _columns = {
        'pos_config_id': fields.many2one('pos.config', 'Terminal de Punto de Venta', ondelete="set null", domain=[('state','=','active')], help="Seleccionar la terminal de punto de venta donde se van a obtener los pedidos para la generacion de la factura global."),
        'journal_id': fields.many2one('account.journal', 'Diario Notas de Venta', required=True, ondelete="cascade", domain=[('note_sale','=',True),('type','=','sale')], help="Indicar el diario de donde se van a obtener las notas de venta ."),
        'journal_cfdi_id': fields.many2one('account.journal', 'Diario', ondelete="cascade", required=True, domain=[('note_sale','=',False),('type','=','sale')], help = "Diario sobre el que se va a generar la nueva factura."),
        'partner_id': fields.many2one('res.partner', 'Cliente', ondelete="cascade", required=True, help="Cliente sobre el que se va a generar la factura global."),
        'currency_id': fields.many2one('res.currency', 'Moneda', ondelete="cascade", required=True, help="Moneda de las notas de venta"),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True),
        'line_ids': fields.one2many('pos.account.invoice.global.line.wizard', 'wizard_id', 'Notas de venta')
    }
    
    _defaults = {
        'journal_id': _get_journal,
        'journal_cfdi_id': _get_journal_cfdi,
        'currency_id': _get_currency,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
    }
    
    def _create_invoice_global(self, cr, uid, invoice_data, note_ids=[], context=None):
        """
            Crea una factura global con la informacion de todos los registros obtenidos de cada factura
        """
        obj_journal = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        order_obj = self.pool.get('pos.order')
        order_line_obj = self.pool.get('pos.order.line')
        
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        
        date = time.strftime('%Y-%m-%d')
        # Agrega a la informacion de factura datos generales
        invoice_data.update({
            'type': 'out_invoice',
            'global_invoice': True,
            'pos_global_invoice': True,
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            'shop_id': 1
        })
        
        # Crea la nueva factura
        invoice_id = inv_obj.create(cr, uid, invoice_data, context=context)
        
        print "************* note ids ***************** ", note_ids
        
        # Valida que haya notas de venta para insertar sobre la factura global
        if not note_ids:
            raise osv.except_osv(_('Aviso!'),_("No hay pedidos de venta disponibles para aplicar sobre la factura global!"))
        line_ids = order_line_obj.search(cr, uid, [('order_id','in',note_ids)])
        
        print "********* line ids *********** ", line_ids
        
        # Recorre las lineas de las notas de venta
        for line in order_line_obj.browse(cr, uid, line_ids, context=context):
            # Crea el nuevo registro sobre la linea de factura
            vals = {
                'product_id': line.product_id.id or False,
                'name': '%s (%s)'%(line.name,line.order_id.name),
                'quantity': line.qty,
                'uos_id': line.product_id.uom_id.id or False,
                'price_unit': line.price_unit,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.product_id.taxes_id])],
                'invoice_id': invoice_id
            }
            account_id = False
            # Obtiene la cuenta del producto
            if line.product_id:
                account_id = inv_obj.get_account_product(cr, uid, line.product_id.id, line.order_id.sale_journal.id, context=context)
            # Si no encuentra la cuenta del producto aplica la cuenta de la linea de factura
            if not account_id:
                account_id = line.account_id.id or False
            # Actualiza la cuenta en la linea de factura
            vals['account_id'] = account_id
            inv_line_obj.create(cr, uid, vals, context=context)
        
        # Relaciona las notas de venta con la factura global
        #order_obj.write(cr, uid, note_ids, {'global_invoice_id':invoice_id, 'global_invoice': True}, context=context)
        order_obj.write(cr, uid, note_ids, {'global_invoice_id':invoice_id}, context=context)
        
        # Pasa la factura a abierto
        wf_service.trg_validate(uid, 'account.invoice', \
                                     invoice_id, 'invoice_open', cr)
        
        # Salda la nota de venta con la factura global
        #inv_obj.generate_voucher_invoice_global(cr, uid, note_ids, context=context)
        inv_obj.pos_generate_voucher_invoice_global(cr, uid, note_ids, context=context)
        
        # Salda factura global 
        
        return invoice_id
    
    def action_create_invoice_global(self, cr, uid, ids, context=None):
        """
            Crea una factura Global en base a las notas de ventas pendientes por registrar
        """
        inv_id = False
        # Obtiene la informacion para la creacion de la factura
        data = self.browse(cr, uid, ids[0], context=context)
        
        # Crea el diccionario con la informacion para crear la factura global
        invoice = {
            'name': 'Factura Global',
            'date_due': time.strftime('%Y-%m-%d'),
            'partner_id': data.partner_id.id,
            'company_id': data.company_id.id or False,
            'account_id': data.partner_id.property_account_receivable.id,
            'currency_id': data.currency_id.id,
            'user_id': uid,
            'journal_id': data.journal_cfdi_id.id
        }
        # listado de notas de venta
        note_ids = []
        for line in data.line_ids:
            note_ids.append(line.order_id.id)
        
        # Crea la factura global
        inv_id = self._create_invoice_global(cr, uid, invoice, note_ids, context=context)
        
        # Redirecciona a la factura creada
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')

        return {
            'name':_("Factura Global"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : inv_id, # id of the object to which to redirected
        }
    
pos_account_invoice_global()

class pos_account_invoice_global_line(osv.osv_memory):
    """
        Facturas a aplicar sobre la global
    """
    _name = "pos.account.invoice.global.line.wizard"
    
    _columns = {
        'name': fields.char('Numero'),
        'wizard_id': fields.many2one('pos.account.invoice.global.wizard', 'Wizard', ondelete="cascade"),
        'order_id': fields.many2one('pos.order', 'Pedido de Venta', ondelete="cascade"),
        'session_id' : fields.many2one('pos.session', 'Sesion',  select=1, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Cliente'),
        'state': fields.selection([
            ('done','Contabilizado'),
            ('invoiced','Facturado'),
            ],'Estado'),
        'date': fields.date('Fecha Factura')
    }
    
pos_account_invoice_global_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
