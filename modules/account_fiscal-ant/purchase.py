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

from openerp.osv import osv
from openerp.tools.translate import _

# ---------------------------------------------------------
# Compra
# ---------------------------------------------------------
#
#class purchase_order(osv.Model):
#    _inherit = 'purchase.order'
#    
#    def _choose_account_from_po_line(self, cr, uid, po_line, context=None):
#        """
#            Hace que seleccione la categoria del producto segun el producto y la categoria
#        """
#        fiscal_obj = self.pool.get('account.fiscal.position')
#        property_obj = self.pool.get('ir.property')
#        if po_line.product_id:
#            acc_id = po_line.product_id.property_account_expense.id
#            if not acc_id:
#                acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
#            if not acc_id:
#                raise osv.except_osv(_('Error!'), _('Cuenta de gasto no definida: "%s" (id:%d).')%(po_line.product_id.name, po_line.product_id.id,))
#        else:
#            acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category').id
#        fpos = po_line.order_id.fiscal_position or False
#        return fiscal_obj.map_account(cr, uid, fpos, acc_id)
#    
#purchase_order()

# ---------------------------------------------------------
# Wizard para crear facturas
# ---------------------------------------------------------

class purchase_line_invoice(osv.osv_memory):
    """ To create invoice for purchase order line"""
    _inherit = 'purchase.order.line_invoice'
    _description = 'Purchase Order Line Make Invoice'

    def makeInvoices(self, cr, uid, ids, context=None):
        """
            Agrega la referencia sobre la nueva factura
        """
        # Funcion original sobre creacion de detalle de facturas
        res = super(purchase_line_invoice, self).makeInvoices(cr, uid, ids, context=context)
        
        if context is None:
            context={}
        
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        invoice_line_obj = self.pool.get('account.invoice.line')
        account_jrnl_obj = self.pool.get('account.journal')
        invoice_obj = self.pool.get('account.invoice')
        link_obj = self.pool.get('links.get.request')
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'purchase.order', 'Compra', context=None)
        
        # Valida que haya regsitros sobre lineas de compra
        record_ids =  context.get('active_ids',[])
        if record_ids:
            res = False
            order_ids = []
            
            # Recorre las lineas de compra y obtiene el listado de los pedidos de venta
            for line in purchase_line_obj.browse(cr, uid, record_ids, context=context):
                try:
                    order_ids.index(line.order_id.id)
                    continue
                except:
                    order_ids.append(line.order_id.id)
            
            # Recorre los pedidos de venta 
            for purchase in purchase_obj.browse(cr, uid, order_ids, context=context):
                # Obtiene las facturas del pedido
                invoice_ids = []
                for inv in purchase.invoice_ids:
                    invoice_ids.append(inv.id)
                
                # Referencia sobre pedido de venta
                reference = 'purchase.order,%s'%(purchase.id,)
                
                # Actualiza la referencia sobre el pedido de venta en la factura
                invoice_obj.write(cr, uid, invoice_ids, {'ref': reference})
            
        return res
    
purchase_line_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
