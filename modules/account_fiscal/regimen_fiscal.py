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
from openerp import netsvc

class regimen_fiscal(osv.Model):
    _inherit = "regimen.fiscal"
    
    def onchange_title(self, cr, uid, ids, title, context=None):
        """
            Pone que se aplica la deduccion sobre el pago para cuando el titulo sea igual a 4
        """
        values = {}
        if title == 'title_4':
            values = {'apply_deduction': True}
        return {'value': values}
    
    _columns = {
        'apply_deduction': fields.boolean('Aplicar deduccion al pago'),
        'category_id': fields.many2one('account.account.category', 'Rubro Fiscal', domain=[('exclude_deduction  ','=',True)], help="Rubro fiscal que aplica a este regimen fiscal sobre los pagos"),
        'title': fields.selection([
                        ('title_2','Titulo 2'),
                        ('title_4','Titulo 4')], 'Titulo', required=True),
        'apply_deduction_sale': fields.boolean('Aplicar deducciones al cobro'),
        'category_id_sale': fields.many2one('account.account.category', 'Rubro Fiscal', domain=[('exclude_cum_income','=',True)], help="Rubro fiscal que aplica a este regimen fiscal sobre los cobros"),
    }
    
    def _get_default_apply_deduction(self, cr, uid, context=None):
        """
            Obtiene de la compañia el si aplica deduccion por pago
        """
        if context is None: context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        return company.apply_deduction
    
    def _get_default_apply_deduction_sale(self, cr, uid, context=None):
        """
            Obtiene de la compañia el si aplica deduccion por pago
        """
        if context is None: context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        return company.apply_deduction_sale
    
    defaults = {
        'title': 'title_2',
        'apply_deduction': _get_default_apply_deduction,
        'apply_deduction_sale': _get_default_apply_deduction_sale
    }

regimen_fiscal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
