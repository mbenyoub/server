# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Ivan Macias <ivanfallen@gmail.com>"
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
from openerp.tools.translate import _


class sale_advance_payment_inv(osv.osv_memory):
    """ Inherit create invoice from sales order """

    _inherit = "sale.advance.payment.inv"

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        """
            Inherit _prepare_advance_invoice_vals - Agregar la relacion entre el documento venta con factura.
        """
        #print "*******************Funcion _prepare_advance_invoice_vals*************"
        valor = super(sale_advance_payment_inv, self)._prepare_advance_invoice_vals(cr, uid, ids, context=context)
        #print "*********  Valor funcion super sale *******", valor
        
        #~ Valida que el objeto  se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'sale.order'),])
        sale_ids = context.get('active_ids', [])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Ventas', 'object': 'sale.order', })
        
        #~ Relaciona el documento origen con la factura 
        invoice_obj = self.pool.get('account.invoice')
        data = context and context.get('active_ids', []) or []
        #print "+++++++++++++++++ data es igual a ", data
        cont = 0
        #Agrega la referencia a la venta
        for sale_id in sale_ids:
            valor[cont][1]['ref'] = 'sale.order,' + str(sale_id)
            #print "***************************", valor
            cont+=1
        return valor

sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
