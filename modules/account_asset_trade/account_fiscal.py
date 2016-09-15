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

from datetime import datetime
import time
import netsvc
import tools

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account fiscal INPC 
# ---------------------------------------------------------

class account_fiscal_inpc(osv.Model):
    _name = 'account.fiscal.inpc'
    
    def get_inpc_value(self, cr, uid, period_id, context=None):
        """
            Obtiene el inpc del periodo
        """
        result = 0.0
        cr.execute("""
            select
                value
            from
                account_fiscal_inpc
            where 
                period = (select extract(month from date_start) from account_period where id = %s)
                and fiscalyear = (select extract(year from date_start) from account_period where id = %s)"""%(period_id,period_id))
        for value in cr.fetchall():
            result = value[0]
            break
        return result
    
    def get_inpc_month_value(self, cr, uid, month, year, context=None):
        """
            Obtiene el inpc del periodo por el año y el ejercicio
        """
        result = 0.0
        cr.execute("""
            select
                value
            from
                account_fiscal_inpc
            where 
                period = %s and fiscalyear = %s"""%(month, year))
        for value in cr.fetchall():
            result = value[0]
            break
        return result
    
    def get_inpc_to_date(self, cr, uid, date, context=None):
        """
            Obtiene el inpc id del inpc por una fecha
        """
        result = False
        cr.execute("""
            select
                id
            from
                account_fiscal_inpc
            where 
                name = to_char(date('%s'), 'mm/YYYY')
            limit 1 """%(date))
        for value in cr.fetchall():
            result = value[0]
            break
        return result
    
    def get_inpc(self, cr, uid, month, year, context=None):
        """
            Obtiene el inpc id del inpc por el año y el ejercicio
        """
        result = False
        cr.execute("""
            select
                id
            from
                account_fiscal_inpc
            where 
                period = %s and fiscalyear = %s"""%(month, year))
        for value in cr.fetchall():
            result = value[0]
            break
        return result
    
    def get_value(self, cr, uid, inpc_id, context=None):
        """
            Obtiene el valor del inpc por medio de su id
        """
        result = 0.0
        if not inpc_id:
            return result
        cr.execute("""
            select
                value
            from
                account_fiscal_inpc
            where 
                id = %s"""%(inpc_id))
        for value in cr.fetchall():
            result = value[0]
            break
        return result
    
    def _get_name(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el nombre del registro
        """
        result = {}
        # Recorre los registros
        for inpc in self.browse(cr, uid, ids, context=context):
            name = str(inpc.period)
            name = '0' + name if len(name) == 1 else name 
            name = name + '/' + str(inpc.fiscalyear)
            result[inpc.id] = name
        return result
    
    def _get_period_char(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el periodo en su formato de texto
        """
        result = {}
        # Recorre los registros
        for inpc in self.browse(cr, uid, ids, context=context):
            period = str(inpc.period)
            period = '0' + period if len(period) < 2 else period
            result[inpc.id] = period
        return result
    
    def _get_period_default(self, cr, uid, ids, context=None):
        """
            Retorna el valor del mes por default
        """
        date = int(time.strftime('%m'))
        return date
    
    def _get_fiscalyear_default(self, cr, uid, ids, context=None):
        """
            Retorna el valor del año por default
        """
        date = int(time.strftime('%Y'))
        return date
    
    _order = "id desc"
    
    _columns = {
        #'name': fields.char('Codigo', size=64, required=True),
        'name': fields.function(_get_name, type='char', size=64, string='Codigo', store=True),
        'period': fields.integer('Periodo', size=2, required=True),
        'period_char': fields.function(_get_period_char, string='Periodo', size=2, type="char", store=True),
        'fiscalyear': fields.integer('Ejercicio Fiscal', size=4, required=True),
        'value': fields.float('Valor', digits=(16,12))
    }
    
    _defaults = {
        'value': 0.0,
        'period': _get_period_default,
        'fiscalyear': _get_fiscalyear_default
    }
    
    _sql_constraints = [
        (
            'name_unique', 
            'UNIQUE(name)', 
            'No se pueden dar de alta INPC con periodos repetidos'
        ),
    ]
    
    def _check_fiscalyear(self, cr, uid, ids, context=None):
        for inpc in self.browse(cr, uid, ids, context=context):
            if len(str(inpc.fiscalyear)) < 4:
                return False
            return True
    
    def _check_period(self, cr, uid, ids, context=None):
        for inpc in self.browse(cr, uid, ids, context=context):
            if int(inpc.period) < 0 or int(inpc.period) > 12:
                return False
            return True
    
    _constraints = [
        (_check_period, 'El periodo es incorrecto', ['period']),
        (_check_fiscalyear, 'El ejercicio fiscal debe contener 4 digitos', ['fiscalyear'])]

    
account_fiscal_inpc()

# ---------------------------------------------------------
# Account fiscal INPC - Informe
# ---------------------------------------------------------

class account_fiscal_inpc_report(osv.osv):
    _name = "account.fiscal.inpc.report.view"
    _description = "Reporte resultados INPC"
    _auto = False
    
    _columns = {
        'fiscalyear': fields.char('Ejercicio Fiscal'),
        'value_01': fields.float('Enero', digits=(16,12)),
        'value_02': fields.float('Febrero', digits=(16,12)),
        'value_03': fields.float('Marzo', digits=(16,12)),
        'value_04': fields.float('Abril', digits=(16,12)),
        'value_05': fields.float('Mayo', digits=(16,12)),
        'value_06': fields.float('Junio', digits=(16,12)),
        'value_07': fields.float('Julio', digits=(16,12)),
        'value_08': fields.float('Agosto', digits=(16,12)),
        'value_09': fields.float('Septiembre', digits=(16,12)),
        'value_10': fields.float('Octubre', digits=(16,12)),
        'value_11': fields.float('Noviembre', digits=(16,12)),
        'value_12': fields.float('Diciembre', digits=(16,12)),
    }

    _order = 'fiscalyear desc'
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_fiscal_inpc_report_view')
        tools.drop_view_if_exists(cr, 'account_fiscal_inpc_report_base_view')
        cr.execute("""
            -- Obtencion tabla de INPC
            
            CREATE OR REPLACE view account_fiscal_inpc_report_base_view as

            select 
            row_number() over() as id,
            i.fiscalyear,    
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=1) as value_01,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=2) as value_02,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=3) as value_03,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=4) as value_04,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=5) as value_05,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=6) as value_06,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=7) as value_07,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=8) as value_08,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=9) as value_09,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=10) as value_10,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=11) as value_11,
            (select value from account_fiscal_inpc as p where p.fiscalyear=i.fiscalyear and period=12) as value_12

            from account_fiscal_inpc as i
            group by i.fiscalyear
            order by i.fiscalyear;

            CREATE OR REPLACE view account_fiscal_inpc_report_view as
            select 
            id, 
            fiscalyear,
            (case when value_01 is null then 0.0 else value_01 end) as value_01,
            (case when value_02 is null then 0.0 else value_02 end) as value_02,
            (case when value_03 is null then 0.0 else value_03 end) as value_03,
            (case when value_04 is null then 0.0 else value_04 end) as value_04,
            (case when value_05 is null then 0.0 else value_05 end) as value_05,
            (case when value_06 is null then 0.0 else value_06 end) as value_06,
            (case when value_07 is null then 0.0 else value_07 end) as value_07,
            (case when value_08 is null then 0.0 else value_08 end) as value_08,
            (case when value_09 is null then 0.0 else value_09 end) as value_09,
            (case when value_10 is null then 0.0 else value_10 end) as value_10,
            (case when value_11 is null then 0.0 else value_11 end) as value_11,
            (case when value_12 is null then 0.0 else value_12 end) as value_12
        
            from account_fiscal_inpc_report_base_view;
        """)
    
account_fiscal_inpc_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
