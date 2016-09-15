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

class sale_order(osv.Model):
    _inherit = 'sale.order'
    
    def _get_payment_term_default(self, cr, uid, context=None):
        """
            Pone en el plazo de pago pago inmediato
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'account', 'account_payment_term_immediate').id
        except:
            pass
        return res
    
    _columns = {
        'payment_term': fields.many2one('account.payment.term', 'Payment Term', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True),
        'user_id': fields.many2one('res.users', 'Salesperson', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'),
    }
    
    _defaults = {
        'payment_term': _get_payment_term_default
    }
    
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
