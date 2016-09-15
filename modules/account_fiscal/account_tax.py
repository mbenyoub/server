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
# Account tax - Documentos para Impuestos
# ---------------------------------------------------------

class account_tax(osv.Model):
    _inherit = 'account.tax'
    
    _columns = {
        'name': fields.char(string="Nombre", size=128, required=True, traslate=False),
        'description': fields.char(string="Codigo", size=32, required=True),
        'type_tax_use': fields.selection([('sale','Venta'),('purchase','Compra'),('income','Otros Ingresos'),('expense','Otros Egresos'),('all','Todos')], 'Aplicacion de Impuestos', required=True),
    }
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Valor con el que se va a visualizar el impuesto
        """
        if not ids:
            return []
        res = []
        for record in self.read(cr, uid, ids, ['description','name'], context=context):
            name = record['name']
            res.append((record['id'],name ))
        return res

account_tax()

class account_tax_code(osv.Model):
    _inherit = 'account.tax.code'
    
    #def _base_year(self, cr, uid, ids, field, arg, context=None):
    #    """
    #        Obtiene la base del año para el codigo del impuesto
    #    """
    #    result = {}
    #    # Recorre los codigos de todos los impuestos
    #    code_ids = self.search(cr, uid, [])
    #    for code in self.browse(cr, uid, code_ids, context=context):
    #        # Omite el proceso si es padre de otro codigo de impuesto
    #        if len(code.child_ids):
    #            # Si no esta en el diccionario lo inicializa
    #            if not result.get(code.id, False):
    #                result[code.id] = 0.0
    #            continue
    #        # Obtiene la base del impuesto
    #        result[code.id] = 0.0
    #        if code.percent:
    #            amount = float(code.sum) / code.percent
    #            result[code.id] = amount
    #            # Sumarisa el valor sobre los padres relacionados al impuesto
    #            if code.parent_id:
    #                parent = code.parent_id
    #                amount = amount
    #                sign = code.sign
    #                while(parent):
    #                    if result.get(parent.id, False):
    #                        result[parent.id] += (amount * sign)
    #                    else:
    #                        result[parent.id] = (amount * sign)
    #                    sign = parent.sign
    #                    parent = parent.parent_id
    #    return result
    
    #def _base_period(self, cr, uid, ids, field, arg, context=None):
    #    """
    #        Obtiene la base del periodo para el codigo del impuesto
    #    """
    #    result = {}
    #    # Recorre los codigos de todos los impuestos
    #    code_ids = self.search(cr, uid, [])
    #    for code in self.browse(cr, uid, code_ids, context=context):
    #        # Omite el proceso si es padre de otro codigo de impuesto
    #        if len(code.child_ids):
    #            if not result.get(code.id, False):
    #                result[code.id] = 0.0
    #            continue
    #        # Obtiene la base del impuesto
    #        result[code.id] = 0.0
    #        if code.percent:
    #            amount = float(code.sum_period) / code.percent
    #            result[code.id] = amount
    #            # Sumarisa el valor sobre los padres relacionados al impuesto
    #            if code.parent_id:
    #                parent = code.parent_id
    #                amount = amount
    #                sign = code.sign
    #                while(parent):
    #                    if result.get(parent.id, False):
    #                        result[parent.id] += (amount * sign)
    #                    else:
    #                        result[parent.id] = (amount * sign)
    #                    sign = parent.sign
    #                    parent = parent.parent_id
    #    return result

    def _sum(self, cr, uid, ids, name, args, context, where ='', where_params=()):
        parent_ids = tuple(self.search(cr, uid, [('parent_id', 'child_of', ids)]))
        if context.get('based_on', 'invoices') == 'payments':
            query = 'SELECT line.tax_code_id, sum(line.tax_amount) \
                    FROM account_move_line AS line, \
                        account_move AS move \
                        LEFT JOIN account_invoice invoice ON \
                            (invoice.move_id = move.id) \
                    WHERE line.tax_code_id IN %s '+where+' \
                        AND move.id = line.move_id \
                        AND ((invoice.state = \'paid\') \
                            OR (invoice.id IS NULL)) \
                            GROUP BY line.tax_code_id'
            print "********* iva query1 ************ ", query
            cr.execute(query,(parent_ids,) + where_params)
        else:
            query = 'SELECT line.tax_code_id, sum(line.tax_amount) \
                    FROM account_move_line AS line, \
                    account_move AS move \
                    WHERE line.tax_code_id IN %s '+where+' \
                    AND move.id = line.move_id \
                    GROUP BY line.tax_code_id'
            print "********* iva query2 ************ ", query
            cr.execute(query,(parent_ids,) + where_params)
        res=dict(cr.fetchall())
        obj_precision = self.pool.get('decimal.precision')
        res2 = {}
        for record in self.browse(cr, uid, ids, context=context):
            def _rec_get(record):
                amount = res.get(record.id, 0.0)
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            res2[record.id] = round(_rec_get(record), obj_precision.precision_get(cr, uid, 'Account'))
        return res2

    def _sum_year(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la suma sobre el acumulado de los ivas
        """
        if context is None:
            context = {}
        move_state = ('posted', )
        if context.get('state', 'all') == 'all':
            move_state = ('draft', 'posted', )
        if context.get('fiscalyear_id', False):
            fiscalyear_id = [context['fiscalyear_id']]
        else:
            fiscalyear_id = self.pool.get('account.fiscalyear').finds(cr, uid, exception=False)
        
        where = ''
        where_params = ()
        # Agrega la fecha final del periodo para que obtenga los datos como acumulado
        if context.get('period_id', False):
            period_id = context['period_id']
            date_stop = self.pool.get('account.period').read(cr, uid, period_id, ['date_stop'])['date_stop']
            print "******** date stop iva ************ ", date_stop
            where = where + " AND line.date <= '%s' "%(date_stop,)
        if fiscalyear_id:
            pids = []
            for fy in fiscalyear_id:
                pids += map(lambda x: str(x.id), self.pool.get('account.fiscalyear').browse(cr, uid, fy).period_ids)
            if pids:
                where = where + ' AND line.period_id IN %s AND move.state IN %s '
                where_params = (tuple(pids), move_state)
        return self._sum(cr, uid, ids, name, args, context, where=where, where_params=where_params)

    def _sum_base(self, cr, uid, ids, name, args, context, where ='', where_params=()):
        """
            Proceso para obtener la base de los movimientos
        """
        parent_ids = tuple(self.search(cr, uid, [('parent_id', 'child_of', ids)]))
        if context.get('based_on', 'invoices') == 'payments':
            query = 'SELECT line.tax_code_id, sum(line.base) \
                    FROM account_move_line AS line, \
                        account_move AS move \
                        LEFT JOIN account_invoice invoice ON \
                            (invoice.move_id = move.id) \
                    WHERE line.tax_code_id IN %s '+where+' \
                        AND move.id = line.move_id \
                        AND ((invoice.state = \'paid\') \
                            OR (invoice.id IS NULL)) \
                            GROUP BY line.tax_code_id'
            print "********* query1 base *********** ", query
            cr.execute(query,(parent_ids,) + where_params)
        else:
            query = 'SELECT line.tax_code_id, sum(line.base) \
                    FROM account_move_line AS line, \
                    account_move AS move \
                    WHERE line.tax_code_id IN %s '+where+' \
                    AND move.id = line.move_id \
                    GROUP BY line.tax_code_id'
            print "************+ query2 base ************ ", query
            cr.execute(query,(parent_ids,) + where_params)
        res=dict(cr.fetchall())
        obj_precision = self.pool.get('decimal.precision')
        res2 = {}
        for record in self.browse(cr, uid, ids, context=context):
            def _rec_get(record):
                amount = res.get(record.id, 0.0)
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            res2[record.id] = round(_rec_get(record), obj_precision.precision_get(cr, uid, 'Account'))
        return res2
    
    def _base_year(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la base del año para el codigo del impuesto
        """
        if context is None:
            context = {}
        move_state = ('posted', )
        if context.get('state', 'all') == 'all':
            move_state = ('draft', 'posted', )
        if context.get('fiscalyear_id', False):
            fiscalyear_id = [context['fiscalyear_id']]
        else:
            fiscalyear_id = self.pool.get('account.fiscalyear').finds(cr, uid, exception=False)
        
        where = ''
        where_params = ()
        # Agrega la fecha final del periodo para que obtenga los datos como acumulado
        if context.get('period_id', False):
            period_id = context['period_id']
            date_stop = self.pool.get('account.period').read(cr, uid, period_id, ['date_stop'])['date_stop']
            where = where + " AND line.date <= '%s' "%(date_stop,)
        if fiscalyear_id:
            pids = []
            for fy in fiscalyear_id:
                pids += map(lambda x: str(x.id), self.pool.get('account.fiscalyear').browse(cr, uid, fy).period_ids)
            if pids:
                where = where + ' AND line.period_id IN %s AND move.state IN %s '
                where_params = (tuple(pids), move_state)
        return self._sum_base(cr, uid, ids, name, args, context, where=where, where_params=where_params)

    def _base_period(self, cr, uid, ids, name, args, context):
        """
            Obtiene la base del periodo para el codigo del impuesto
        """
        if context is None:
            context = {}
        move_state = ('posted', )
        if context.get('state', False) == 'all':
            move_state = ('draft', 'posted', )
        if context.get('period_id', False):
            period_id = context['period_id']
        else:
            ctx = dict(context, account_period_prefer_normal=True)
            period_id = self.pool.get('account.period').find(cr, uid, context=ctx)
            if not period_id:
                return dict.fromkeys(ids, 0.0)
            period_id = period_id[0]
        return self._sum_base(cr, uid, ids, name, args, context,
                where=' AND line.period_id=%s AND move.state IN %s', where_params=(period_id, move_state))
    
    _order = "parent_id desc,sequence,code"
    
    _columns = {
        'base': fields.function(_base_year, string="Base del Año"),
        'base_period': fields.function(_base_period, string="Base del Periodo"),
        'percent': fields.float('Porcentaje base', help="Porcentaje de impuesto aplicado sobre la base"),
        'apply_balance': fields.boolean('Aplica en Saldos Fiscales'),
        'visible': fields.boolean('Mostrar en reporte'),
        'name': fields.char('Nombre del codigo impuesto', size=64, required=True),
        'code': fields.char('Codigo', size=32, required=True),
        'sum': fields.function(_sum_year, string="Year Sum"),
    }
    
    _defaults = {
        'percent': 1.0,
        'visible': True,
        'sequence': 5
    }
    
account_tax_code()

#----------------------------------------------------------
# Historial sobre codigos de impuestos
#----------------------------------------------------------

class account_tax_code_history(osv.osv):
    
    _name = 'account.tax.code.history'
    _description = 'History Tax Code'
    
    _columns = {
        'name': fields.char('Nombre', size=64),
        'line_ids': fields.one2many('account.tax.code.history.line', 'history_id', 'Historial Codigos', ondelete='cascade'),
        'date': fields.date('Fecha'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'fiscalyear_id': fields.related('period_id', 'fiscalyear_id', type='many2one', relation='account.fiscalyear', string='Ejercicio Fiscal', store=True, readonly=True),
        'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                        ('all', 'Todos los asientos'),
                                        ], 'Movimientos', required=True),
        'cont': fields.integer('Saldos aplicados')
    }
    
    _defaults = {
        'cont': 0
    }

account_tax_code_history()

class account_tax_code_history_line(osv.osv):
    """
    A code for the tax object.

    This code is used for some tax declarations.
    """
    _name = 'account.tax.code.history.line'
    _description = 'History Tax Code'
    
    def get_code_tax_period(self, cr, uid, code_id, period_id, context=None):
        """
            Obtiene el valor del historial sobre el periodo
        """
        cr.execute("""
            select id
            from account_tax_code_history_line
            where code_id = %s and period_id = %s and apply_balance != True"""%(code_id,period_id))
        code_id = False
        for value in cr.fetchall():
            code_id = value[0]
            break
        return code_id
    
    _columns = {
        'history_id': fields.many2one('account.tax.code.history', 'Historial', ondelete='cascade', required=True),
        'code_id': fields.many2one('account.tax.code', 'Codigo de impuesto', ondelete='set null'),
        'name': fields.char('Tax Case Name', size=64, required=True, translate=True),
        'code': fields.char('Codigo', size=32),
        'parent_id': fields.many2one('account.tax.code.history.line', 'Parent Code', select=True),
        'child_ids': fields.one2many('account.tax.code.history.line', 'parent_id', 'Child Codes'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'sequence': fields.integer('Sequence', help="Determine the display order in the report 'Accounting \ Reporting \ Generic Reporting \ Taxes \ Taxes Report'"),
        'percent': fields.float('Porcentaje base', help="Porcentaje de impuesto aplicado sobre la base"),
        'base_period': fields.float('Base periodo'),
        'sum_period': fields.float('Suma periodo'),
        'base_year': fields.float('Base periodo'),
        'sum_year': fields.float('Suma periodo'),
        'period_id': fields.related('history_id', 'period_id', type='many2one', relation='account.period', string='Periodo', store=True, readonly=True),
        'fiscalyear_id': fields.related('history_id', 'fiscalyear_id', type='many2one', relation='account.fiscalyear', string='Ejercicio Fiscal', store=True, readonly=True),
        'apply_balance': fields.boolean('Aplicacion de saldo')
    }
    
    _defaults = {
        'apply_balance': False
    }

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = self.search(cr, user, ['|',('name',operator,name),('code',operator,name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','code'], context, load='_classic_write')
        return [(x['id'], (x['code'] and (x['code'] + ' - ') or '') + x['name']) \
                for x in reads]

    _order = "period_id,code,sequence,id"

account_tax_code_history_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
