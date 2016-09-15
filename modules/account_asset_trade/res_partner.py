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
    
    _columns = {
        'property_account_asset': fields.many2one('account.account', 'Cuenta Acreedora venta de activo', domain="[('type', '=', 'receivable')]", help="Seleccione una cuenta acreedora para utilizarla para cargar el monto de la venta de los activos, en caso de no seleccionar una cuenta utiliza la cuenta por cobrar del cliente"),
        #=======================================================================
        # 'property_account_asset': fields.property(
        #     'account.account',
        #     type='many2one',
        #     relation='account.account',
        #     string="Account Payable",
        #     view_load=True,
        #     domain="[('type', '=', 'payable')]",
        #     help="This account will be used instead of the default one as the payable account for the current partner",
        #     required=True),
        #=======================================================================
    }
    
    def _get_account_asset_default(self, cr, uid, ids, context=None):
        """
            Revisa si existe la cuenta acredora por default para la venta de los activos
        """
        res = False
        # Busca entre la informacion de los activos
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','1129009000')], context=context)
        if acc_ids:
            res = acc_ids[0]
        return res
    
    _defaults = {
        'property_account_asset': _get_account_asset_default
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
