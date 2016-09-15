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

from openerp.addons.base_status.base_stage import base_stage
import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice(osv.Model):
    """ Inherit create invoice from accounts """
    
    _inherit = "account.invoice"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get')
        return links._links_get(cr, uid, context=context)

    def _have_ref(self, cr, uid, ids, name, args, context=None):
        """
            Revisa si se agrego la referencia para la factura
        """
        res = {}
        # Recorre las ventas recibidas en el parametro
        for invoice in self.browse(cr, uid, ids, context=context):
            # Inicializa valores como negativos
            res[invoice.id] = {
                'have_ref': False,
                'have_ref2': False,
            }
            # Valida si hay una relacion con un documento
            if invoice.ref.id:
                res[invoice.id]['have_ref'] = True
            if invoice.ref2.id:
                res[invoice.id]['have_ref2'] = True
            #print "***************** res ref ***************** ", res
        return res

    def _get_partner2(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el cliente del que se deriva la factura
        """
        res = {}
        # Recorre las facturas
        for invoice in self.browse(cr, uid, ids, context=context):
            # Valida si hay una relacion con un documento y si la hay busca el cliente del que proviene la factura
            if invoice.ref.id:
                try:
                    #print "*************** ref id ************* ", invoice.ref.id
                    if invoice.ref.partner_id:
                        res[invoice.id] = invoice.ref.partner_id.id
                except:
                    #print "*************** exep ref id ************* "
                    res[invoice.id] = invoice.partner_id.id
            elif invoice.ref2.id:
                try:
                    #print "*************** ref2 id ************* ", invoice.ref2.id
                    if invoice.ref2.partner_id:
                        print "*************** exep ref2 id ************* "
                        res[invoice.id] = invoice.ref2.partner_id.id
                except:
                    res[invoice.id] = invoice.partner_id.id
            else:
                res[invoice.id] = invoice.partner_id.id
        return res

    _columns = {
        'ref' : fields.reference('Documento Origen', selection=_links_get, size=128, readonly=True),
        'have_ref': fields.function(_have_ref, method=True, string='Tiene documento Origen?', readonly=True, multi="reference", type='boolean', help="Indica si tiene una referencia."),
        'ref2': fields.reference('Referencia del Cliente', selection=_links_get, size=128, readonly=True),
        'have_ref2': fields.function(_have_ref, method=True, string='Tiene referencia de cliente?', readonly=True, multi="reference", type='boolean', help="Indica si tiene una referencia."),
        'partner_id2': fields.function(_get_partner2, method=True, string='Cliente Origen', readonly=True, type='many2one', relation="res.partner", store=True, help="Cliente del que se origino la factura"),
    }
    
account_invoice()

class account_invoice_line(osv.osv):
    
    _inherit = "account.invoice.line"
    
    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Return the virtual avalaible quantity from products
        """
        product_obj = self.pool.get('product.product')
        res = {}
        
        #Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context) :
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                #Asigna la stock virtual del producto a la linea del pedido de compra.
                product_available = product_obj.browse( cr, uid, line.product_id.id, context=context).virtual_available
                res[line.id] = product_available
        return res
    
        
    _columns = {
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
    }
    