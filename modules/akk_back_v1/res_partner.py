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

# ---------------------------------------------------------
# Partner
# ---------------------------------------------------------

class res_partner(osv.Model):
    _inherit='res.partner'
    
    def _address_fields(self, cr, uid, context=None):
        """
            Devuelve la lista de los campos de direccion que se sincronizan
            desde el padre cuando se establece la bandera `use_parent_address.
        """
        res = super(res_partner, self)._address_fields(cr, uid, context=None)
        res.extend(['rfc','name',])
        return res

    def onchange_rfc(self, cr, uid, ids, rfc, context=None):
        """
            Agrega el MX al RFC en el campo vat
        """
        vat = ''
        if rfc != '':
            vat = 'MX%s'%(rfc,)
        return {'value': {'vat': vat}}
    
    _columns = {
        'rfc': fields.char('RFC', size=32)
    }
    
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
    
    _defaults = {
        'property_payment_term': _get_payment_term_default,
        'property_supplier_payment_term': _get_payment_term_default
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
