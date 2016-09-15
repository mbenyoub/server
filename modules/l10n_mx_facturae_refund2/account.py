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
# Account - Plan de cuentas
# ---------------------------------------------------------

class account_chart_template(osv.osv):
    _inherit="account.chart.template"
    
    _columns = {
        'property_account_expense_refund_categ': fields.many2one('account.account.template', 'Cuenta categoria nota de credito de gastos'),
        'property_account_income_refund_categ': fields.many2one('account.account.template', 'Cuenta de la categoria notas de creditos de ingresos'),
    }
    
account_chart_template()

class account_journal(osv.osv):
    _inherit="account.journal"
    
    _columns = {
        'code': fields.char('Code', size=8, required=True, help="The code will be displayed on reports."),
        'type': fields.selection([
            ('sale', 'Sale'),
            ('sale_refund','Sale Refund'),
            ('sale_debit','Notas de cargo ventas'),
            ('purchase', 'Purchase'),
            ('purchase_refund','Purchase Refund'),
            ('purchase_debit','Notas de cargo proveedor'),
            ('cash', 'Cash'),
            ('bank', 'Bank and Checks'),
            ('general', 'General'),
            ('situation', 'Opening/Closing Situation')], 'Type', size=32, required=True,
                                 help="Select 'Sale' for customer invoices journals."\
                                 " Select 'Purchase' for supplier invoices journals."\
                                 " Select 'Cash' or 'Bank' for journals that are used in customer or supplier payments."\
                                 " Select 'General' for miscellaneous operations journals."\
                                 " Select 'Opening/Closing Situation' for entries generated for new fiscal years."),
    }
    
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
