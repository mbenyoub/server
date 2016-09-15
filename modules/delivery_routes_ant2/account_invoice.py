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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import pytz

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_invoice(osv.Model):
    _inherit='account.invoice'
    
    def apply_invoice_stock(self, cr, uid, ids, context=None):
        """
            Actualiza la factura sobre el stock
        """
        picking_obj = self.pool.get('stock.picking')
        # Recorre los registros
        for inv in self.browse(cr, uid, ids, context=context):
            picking_ids = []
            # Valida si tiene una relacion sobre la factura
            if inv.ref:
                # Identifica si la relacion es sobre la compra o la venta
                if inv.type == 'out_invoice':
                    #print "****************************** es factura de venta ****************** "
                    # Busca compras relacionadas con el ingreso
                    reference = 'sale.order,%s'%(inv.ref.id,)
                    picking_ids = picking_obj.search(cr, uid, ['|',('sale_id','=', inv.ref.id),('reference','=',reference)], context=context)
                elif inv.type == 'in_invoice':
                    #print "******************************* es factura de compra ***************** "
                    # Busca compras relacionadas con el ingreso
                    reference = 'purchase.order,%s'%(inv.ref.id,)
                    picking_ids = picking_obj.search(cr, uid, ['|',('purchase_id','=', inv.ref.id),('reference','=',reference)], context=context)
            # Valida si la factura tiene un albaran relacionado con la factura
            pick_inv_ids = picking_obj.search(cr, uid, [('invoice_id','=', inv.id)], context=context)
            if pick_inv_ids:
                # Agrega la informacion de los albaranes relacionados a las facturas
                for pick_id in pick_inv_ids:
                    # Valida que no se encuentre ya registrado
                    if not (pick_id in picking_ids):
                        picking_ids.append(pick_id)
            
            # Actualiza el valor de la factura sobre la salida del almacen
            if picking_ids:
                picking_obj.write(cr, uid, picking_ids, {'invoice_id': inv.id}, context=context)
        return True
    
    def invoice_validate(self, cr, uid, ids, context=None):
        """
            Agrega la relacion de las salidas de almacen con la factura
        """
        # Actualiza el stock sobre el almacen
        self.apply_invoice_stock(cr, uid, ids, context=context)
        
        return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
