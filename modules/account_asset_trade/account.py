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


class account_account(osv.Model):
    _inherit='account.account'
    _order = 'code'
    
account_account()
# ---------------------------------------------------------
# Account Period
# ---------------------------------------------------------

class account_period(osv.Model):
    _inherit='account.period'
    
    def _get_period_default(self, cr, uid, context=None):
        """Return default period value"""
        #print "************* get period **************"
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def _get_month_period(self, cr, uid, period_id, context=None):
        """
            Obtiene el mes del periodo
        """
        cr.execute("""
            select
                extract(month from p.date_start) as month
            from
                account_period as p
            where p.id = %s"""%(period_id))
        month = 0.0
        for value in cr.fetchall():
            month = value[0]
            break
        return int(month)
    
    def _get_year_period(self, cr, uid, period_id, context=None):
        """
            Obtiene el año del periodo
        """
        cr.execute("""
            select
                extract(year from p.date_start) as month
            from
                account_period as p
            where p.id = %s"""%(period_id))
        year = 0.0
        for value in cr.fetchall():
            year = value[0]
            break
        return int(year)
    
account_period()
    
# ---------------------------------------------------------
# Account Fiscalyear
# ---------------------------------------------------------

class account_fiscalyear(osv.Model):
    _inherit='account.fiscalyear'
    
    def _get_num_period_fiscalyear(self, cr, uid, fiscalyear_id, context=None):
        """
            Obtiene el numero de periodos del año fiscal
        """
        cr.execute("""
            select
                count(id) as period
            from
                account_period as p
            where
                fiscalyear_id = %s
                and p.special=False"""%(fiscalyear_id))
        period_id = False
        for value in cr.fetchall():
            period_id = value[0]
            break
        return period_id
    
    def _get_type(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el Tipo de ejercicio (Regular/Irregular) segun sea el caso
        """
        res = {}
        # Inicializa valores
        for id in ids:
            num = self._get_num_period_fiscalyear(cr, uid, id, context=context)
            if num == 12:
                res[id] = 'reg'
            else:
                res[id] = 'irreg'
        return res
    
    def get_year(self, cr, uid, fiscalyear_id, context=None):
        """
            Obtiene el valor del año del ejercicio fiscal
        """
        cr.execute("""
            select
                extract(year from f.date_start) as year
            from
                account_fiscalyear as f
            where f.id = %s"""%(fiscalyear_id))
        year = 0.0
        for value in cr.fetchall():
            year = value[0]
            break
        return int(year)
    
    _columns = {
        'type': fields.function(_get_type, type='selection', string="Tipo Ejercicio", selection=[('reg','Regular'),('irreg','Irregular')])
    }

account_fiscalyear()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
