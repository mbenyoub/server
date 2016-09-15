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

class account_invoice_refund(osv.osv_memory):
    _inherit='account.invoice.refund'

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        """
            Relaciona el reintegro de la factura con la factura anterior y la cancela
        """
        inv_obj = self.pool.get('account.invoice')
        # Obtiene el id de la factura
        inv_id = context['active_id'] 
        # Valida que la factura no tenga ya una factura relacionada
        invoice = inv_obj.browse(cr, uid, inv_id, context=None)
        if invoice.invoice_id:
            raise osv.except_osv(_('Factura Relacionada!'), \
                                            _('No se puede realizar este movimiento porque ya existe una factura relacionada.'))
        
        #print "************** ids **************** ", ids
        #print "************** mode ***************** ", mode
        #print "************** context *************** ", context
        result = super(account_invoice_refund, self).compute_refund(cr, uid, ids, mode, context=context)
        #print "************** result *************** ", result
        # Obtiene los ids de la factura y devolucion
        dev_id = 0
        for domain in result['domain']:
            if domain[0] == 'id':
                dev_id = domain[2][0]
                
        #print "*********** id factura *************** ", inv_id
        #print "*********** id devolucion *************** ", dev_id
        
        # Relaciona la factura con la devolucion
        inv_obj.write(cr, uid, [dev_id], {'invoice_id': inv_id})
        
        return result 

account_invoice_refund()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
