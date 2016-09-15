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
    _inherit = 'res.partner'
    
    _columns = {
        'property_account_receivable_note': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta a cobrar Nota de Venta",
            view_load=True,
            domain="[('type', '=', 'receivable')]"),
    }
    
    def _get_account_receivable_note_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta de Notas de venta (CXC)
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','4111001000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    _defaults = {
        'property_account_receivable_note': _get_account_receivable_note_default,
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
