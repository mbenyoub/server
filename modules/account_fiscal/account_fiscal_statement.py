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
# Account statement
# ---------------------------------------------------------


class account_fiscal_statement_type(osv.osv):
    _name = "account.fiscal.statement.type"
    _description = "Statement Type"
    
    def _get_amount_tax(self, cr, uid, ids, context=None):
        """
            Obtiene el monto a aplicar con los impuestos
        """
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = line.base * line.percent
        return result
    
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'sequence': fields.integer('aplicar prioridad sobre tipo de movimiento'),
        'account_id':fields.many2one('account.account', 'Cuenta', required=True),
        'tax_ids': fields.many2many('account.tax', 'account_fiscal_statement_type_tax', 'category_id', 'tax_id', 'Impuestos', domain=[('parent_id','=',False)], help="Impuestos que se aplicaran a la cuenta"),
        'type':fields.selection([
            ('income','Ingreso'),
            ('expense','Egreso')],'Tipo', required=True),
        'active': fields.boolean('Activo'),
        'description': fields.text('Descripcion')
    }
    
    _defaults = {
        'active': True,
        'sequence': 10
    }
    
    _order = "sequence,name"
    
account_fiscal_statement_type()

class account_fiscal_statement(osv.osv):
    _name='account.fiscal.statement'
    _table='account_fiscal_statement'
    
    def action_validate_expense(self, cr, uid, ids, context=None):
        """ 
            Esta funcion Genera los asientos para el egreso
        """
        # Actualiza los impuestos
        self.action_update(cr,uid, ids, context=context)
        # Asignacion inicial de variables
        aft_obj = self.pool.get('account.fiscal.statement.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        date = time.strftime('%Y-%m-%d')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        
        #print "*************** Actualiza pagos conciliacion **************** "
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.fiscal.statement', 'Income/Expense', context=None)
        
        # Recorre los egresos
        for exp in self.browse(cr, uid, ids, context=context):
            # Valida que no haya un movimiento ya ligado al egreso
            if exp.move_id:
                continue
            
            ctx = context.copy()
            # Si hay un contacto seleccionado obtiene el lenguaje--
            if exp.partner_id:
                ctx.update({'lang': exp.partner_id.lang})
            
            # Inicializa las variables para generar el movimiento
            mov_lines = []
            
            # Obtiene el numero de la secuencia del movimiento
            exp_number = obj_seq.next_by_code(cr, uid, 'account.fiscal.statement.expense', context=ctx)
            mov_number = '/'
            if exp.journal_id.sequence_id:
                mov_number = obj_seq.next_by_id(cr, uid, exp.journal_id.sequence_id.id, context=ctx)
            
            #print "************* serie mov ************* ", mov_number
            #print "************* serie exp ************* ", exp_number
            
            # Genera el asiento contable
            mov = {
                'name': mov_number,
                'ref': exp_number,
                'journal_id': exp.journal_id.id,
                'period_id': exp.period_id.id,
                'date': exp.date,
                'narration': exp.notes,
                'company_id': exp.company_id.id,
                'to_check': False,
                'reference': 'account.fiscal.statement,' + str(exp.id)
            }
            move_id = move_obj.create(cr, uid, mov, context=ctx)
            
            # Genera las lineas de movimiento sobre el egreso
            move_line = {
                'journal_id': exp.journal_id.id,
                'period_id': exp.period_id.id,
                'name': '/',
                'account_id': exp.journal_id.default_debit_account_id.id,
                'move_id': move_id,
                'partner_id': exp.partner_id.id or False,
                'amount_currency': 0.0,
                'quantity': 1,
                'credit': exp.amount_total,
                'debit': 0.0,
                'date': exp.date,
                'ref': exp_number,
                'reference': 'account.fiscal.statement,' + str(exp.id)
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=ctx)
            mov_lines.append(new_id)
            move_line = {
                'journal_id': exp.journal_id.id,
                'period_id': exp.period_id.id,
                'name': mov_number or '/',
                'account_id': exp.account_id.id,
                'move_id': move_id,
                'partner_id': exp.partner_id.id or False,
                'amount_currency': 0.0,
                'quantity': 1,
                'credit': 0.0,
                'debit': exp.amount_untaxed,
                'date': exp.date,
                'ref': exp_number,
                'reference': 'account.fiscal.statement,' + str(exp.id)
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=ctx)
            mov_lines.append(new_id)
            # Agrega las lineas de movimiento sobre los impuestos
            for tax_line in exp.tax_line:
                move_line = {
                    'journal_id': exp.journal_id.id,
                    'period_id': exp.period_id.id,
                    'name': tax_line.name or '/',
                    'account_id': tax_line.account_id.id,
                    'move_id': move_id,
                    'partner_id': exp.partner_id.id or False,
                    'amount_currency': 0.0,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': tax_line.amount,
                    'date': exp.date,
                    'ref': exp_number,
                    'tax_code_id': tax_line.tax_id.tax_code_id.id,
                    'tax_amount': tax_line.amount,
                    'base': tax_line.base,
                    'reference': 'account.fiscal.statement,' + str(exp.id)
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=ctx)
                mov_lines.append(new_id)
            
            # Actualiza en el egreso el asiento contable y el estatus
            self.write(cr, uid, [exp.id], {'move_id': move_id, 'state': 'posted', 'date_posted': date, 'name': exp_number, 'number': exp_number}, context=context)
            
        return True
    
    def action_validate_income(self, cr, uid, ids, context=None):
        """ 
            Esta funcion Genera los asientos para el ingreso
        """
        # Actualiza los impuestos
        self.action_update(cr,uid, ids, context=context)
        # Asignacion inicial de variables
        aft_obj = self.pool.get('account.fiscal.statement.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        date = time.strftime('%Y-%m-%d')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.fiscal.statement', 'Income/Expense', context=None)
        
        # Recorre los ingresos
        for inc in self.browse(cr, uid, ids, context=context):
            # Valida que no haya un movimiento ya ligado al ingreso
            if inc.move_id:
                continue
            
            ctx = context.copy()
            # Si hay un contacto seleccionado obtiene el lenguaje--
            if inc.partner_id:
                ctx.update({'lang': inc.partner_id.lang})
            
            # Inicializa las variables para generar el movimiento
            mov_lines = []
            
            # Obtiene el numero de la secuencia del movimiento
            inc_number = obj_seq.next_by_code(cr, uid, 'account.fiscal.statement.income', context=ctx)
            mov_number = '/'
            if inc.journal_id.sequence_id:
                mov_number = obj_seq.next_by_id(cr, uid, inc.journal_id.sequence_id.id, context=ctx)
            
            #print "************* serie mov ************* ", mov_number
            #print "************* serie inc ************* ", inc_number
            
            # Genera el asiento contable
            mov = {
                'name': mov_number,
                'ref': inc_number,
                'journal_id': inc.journal_id.id,
                'period_id': inc.period_id.id,
                'date': inc.date,
                'narration': inc.notes,
                'company_id': inc.company_id.id,
                'to_check': False,
                'reference': 'account.fiscal.statement,' + str(inc.id)
            }
            move_id = move_obj.create(cr, uid, mov, context=context)
            
            # Genera las lineas de movimiento sobre el ingreso
            move_line = {
                'journal_id': inc.journal_id.id,
                'period_id': inc.period_id.id,
                'name': '/',
                'account_id': inc.journal_id.default_debit_account_id.id,
                'move_id': move_id,
                'partner_id': inc.partner_id.id or False,
                'amount_currency': 0.0,
                'quantity': 1,
                'credit': 0.0,
                'debit': inc.amount_total,
                'date': inc.date,
                'ref': inc_number,
                'reference': 'account.fiscal.statement,' + str(inc.id)
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=context)
            mov_lines.append(new_id)
            move_line = {
                'journal_id': inc.journal_id.id,
                'period_id': inc.period_id.id,
                'name': mov_number or '/',
                'account_id': inc.account_id.id,
                'move_id': move_id,
                'partner_id': inc.partner_id.id or False,
                'amount_currency': 0.0,
                'quantity': 1,
                'credit': inc.amount_untaxed,
                'debit': 0.0,
                'date': inc.date,
                'ref': inc_number,
                'reference': 'account.fiscal.statement,' + str(inc.id)
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=context)
            mov_lines.append(new_id)
            # Agrega las lineas de movimiento sobre los impuestos
            for tax_line in inc.tax_line:
                move_line = {
                    'journal_id': inc.journal_id.id,
                    'period_id': inc.period_id.id,
                    'name': tax_line.name or '/',
                    'account_id': tax_line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inc.partner_id.id or False,
                    'amount_currency': 0.0,
                    'quantity': 1,
                    'credit': tax_line.amount,
                    'debit': 0.0,
                    'date': inc.date,
                    'ref': inc_number,
                    'tax_code_id': tax_line.tax_id.tax_code_id.id,
                    'tax_amount': tax_line.amount,
                    'base': tax_line.base,
                    'reference': 'account.fiscal.statement,' + str(inc.id)
                }
                new_id = move_line_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
            
            # Actualiza en el ingreso el asiento contable y el estatus
            self.write(cr, uid, [inc.id], {'move_id': move_id, 'state': 'posted', 'date_posted': date, 'name': inc_number, 'number': inc_number}, context=context)
            
            # Si tiene relacionado un balance cambia el estado del saldo a aplicado
            if inc.balance_line_id:
                self.pool.get('account.fiscal.balance.line').write(cr, uid, [inc.balance_line_id.id], {'state': 'done'}, context=context)
        return True
    
    def action_cancel_income(self, cr, uid, ids, context=None):
        """ 
            Esta funcion elimina la poliza y pone el registro como cancelado
        """
        move_obj = self.pool.get('account.move')
        for reg in self.browse(cr, uid, ids, context=context):
            if reg.state == 'posted':
                move_id = False
                if reg.move_id:
                    move_id = reg.move_id.id
                # Elimina la relacion con el movimiento y cambia el estado a cancelado
                self.write(cr, uid, [reg.id], {'state': 'cancel', 'move_id': False}, context=context)
                
                # Elimina la poliza
                move_obj.button_cancel(cr, uid, [move_id], context=context)
                move_obj.unlink(cr, uid, [move_id], context=context)
        return True
    
    def action_cancel_to_draft(self, cr, uid, ids, context=None):
        """ 
            Esta funcion Cambia un documento cancelado a borrador
        """
        self.write(cr, uid, ids, {'state': 'draft', 'date_posted': False}, context=context)
        return True
    
    def _get_period(self, cr, uid, context=None):
        """
            Obtiene el periodo actual
        """
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    
    def _get_type_statement_default(self, cr, uid, context=None):
        """
            Obtiene el tipo de movimiento por default
        """
        if context is None: context = {}
        #print "************ context ********* ", context
        res = self.pool.get('account.fiscal.statement.type').search(cr, uid, [('type','=', context.get('default_type', 'Income')),('active','=',True)], context=context)
        return res and res[0] or False
    
    def _get_amount_total(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Regresa el total a pagar enl los ingresos
        """
        res = {}
        
        for income in self.browse(cr, uid, ids, context=context):
            res[income.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': income.amount
            }
            amount_tax = 0.0
            
            # Recorre las lineas de impuestos y calcula el total
            for tax in income.tax_line:
                amount_tax += tax.amount
            # Actualiza el total de impuestos y monto total
            res[income.id]['amount_tax'] = amount_tax
            res[income.id]['amount_untaxed'] = income.amount - amount_tax
        return res
    
    def onchange_statement(self, cr, uid, ids, type_statement_id, amount, tax_line, context=None):
        """
            Actualiza la informacion que proviene del tipo de ingreso/egreso
        """
        type_statement = self.pool.get('account.fiscal.statement.type').browse(cr, uid, type_statement_id, context=context)
        values = {}
        
        # Obtiene la cuenta del tipo de ingreso
        try:
            values['account_id'] = type_statement.account_id.id
            result_values = []
            percent_total = 1
            # Obtiene el porcentaje total del total del importe mas impuestos
            for tax in type_statement.tax_ids:
                percent_total += tax.amount
            #print "*************** percent_total ****** ", percent_total
            
            # Obtiene los impuestos y los agrega
            for tax in type_statement.tax_ids:
                # Genera los impuestos para el modelo
                base = amount/percent_total
                amount_tax = (amount * tax.amount)/percent_total
                result_values.append([0, False, {'name': tax.name, 'tax_id': tax.id, 'percent': tax.amount, 'account_id': tax.account_collected_id_apply.id, 'base': base, 'amount': amount_tax}])
            #print "****** tax line *************** ", tax_line
            #Elimina las lineas anteriores de la lista
            for line in tax_line:
                if line[0] != 0:
                    result_values.append([2, line[1], line[2]])
            
            values['tax_line'] = result_values
            return {'value': values}
        except Exception:
             return {}
    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        """
            Actualiza la moneda del ingreso segun el diario
        """
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        values = {}
        currency_id = journal.default_debit_account_id.currency_id.id
        if not currency_id:
            currency_ids = self.pool.get('res.currency').search(cr, uid, [('name', '=', 'MXN'),])
            if currency_ids:
                currency_id = currency_ids[0]
        if currency_id:
            values['currency_id'] = currency_id
        # Obtiene la moneda
        return {'value': values}
    
    def onchange_amount(self, cr, uid, ids, amount, tax_line, context=None):
        """
            Actualiza la moneda del ingreso segun el diario
        """
        values = {}
        #print "********** onchange amount ************ "
        #print "***************** amount **************** ", amount
        #print "***************** tax_line **************** ", tax_line
        
        if amount == 0 and tax_line == []:
            return {}
        
        percent_total = 1
        amount_tax = 0.0
        tax_ids = []
        
        # Recorre las lineas de impuestos y calcula el porcentaje total
        for line in tax_line:
            #print "*************** line *********** ", line
            if line[0] == 0:
                percent_total += line[2].get('percent',0.0)
            elif line[0] == 4 or line[0] == 1:
                #print "************ es modificado ************ "
                if not line[2] or line[2]['percent']:
                    #print "*************** obtiene la linea de impuesto ********* "
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    percent_total += statement_tax.percent
                else:
                    #print "************ obtiene de la linea el valor ********** ", line[2].get('percent',0.0)
                    percent_total += line[2].get('percent',0.0)
                
        #print "********** total percent *********** ", percent_total
        for line in tax_line:
            retorno = 0
            # Valida si es nuevo registro
            if line[0] == 0:
                value = line[2]
            # Valida si es un registro modificado o guardado
            elif line[0] == 4 or line[0] == 1:
                # Valor de retorno para el detalle
                retorno = 1
                # Valida que sea un registro y que contenga el valor que necesita
                if not line[2]:
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    #print "************** statement tax ********************* ", statement_tax
                    value = {
                        'base': statement_tax.base,
                        'amount': statement_tax.amount,
                        'percent': statement_tax.percent
                    }
                elif not line[2]['percent']:
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    #print "************** statement tax ********************* ", statement_tax
                    value = {
                        'base': statement_tax.base,
                        'amount': statement_tax.amount,
                        'percent': statement_tax.percent
                    }
                else:
                    value = line[2]
            else:
                continue
            
            #print "************* value *************** ", value
            
            base = amount/percent_total
            amount_tax_line = (amount * value['percent'])/percent_total
            
            value['base'] = base
            value['amount'] = amount_tax_line
            amount_tax += amount_tax_line
            tax_ids.append([retorno, line[1], value])
        values['tax_line'] = tax_ids 
        values['amount_untaxed'] = amount - amount_tax
        values['amount_tax'] = amount_tax
        values['amount_total'] = amount
        # Obtiene la moneda
        return {'value': values}
    
    def action_update(self, cr, uid, ids, context=None):
        """
            Actualiza la tabla de impuestos y recalcula el total
        """
        stmt_tax_obj = self.pool.get('account.fiscal.statement.tax')
        percent_total = 1.0
        amount_tax = 0.0
        # Recorre los registros
        for stmt in self.browse(cr, uid, ids, context=context):
            # Obtiene el total de porcentaje de impuestos
            for line in stmt.tax_line:
                percent_total += line.percent
            # Recalcula por cada linea su impuesto
            for line in stmt.tax_line:
                base = stmt.amount/percent_total
                amount_tax_line = (stmt.amount * line.percent)/percent_total
                amount_tax += amount_tax_line
                stmt_tax_obj.write(cr, uid, [line.id], {'base': base, 'amount': amount_tax_line})
        self.write(cr, uid, ids, {}, context=context)
        return True
    
    def onchange_tax_line(self, cr, uid, ids, amount, tax_line, context=None):
        """
            Actualiza los totales del ingreso
        """
        #print "********** get total tax line ************ "
        values = {}
        percent_total = 1
        amount_tax = 0.0
        tax_ids = []
        
        if amount == 0 and tax_line == []:
            return {}
        
        #print "***************** amount **************** ", amount
        #print "***************** tax_line **************** ", tax_line
        
        # Recorre las lineas de impuestos y calcula el porcentaje total
        for line in tax_line:
            #print "************* line *************** ", line
            if line[0] == 0:
                percent_total += line[2].get('percent',0.0)
            elif line[0] == 4 or line[0] == 1:
                if not line[2] or line[2]['percent']:
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    percent_total += statement_tax.percent
                else:
                    percent_total += line[2].get('percent',0.0)
        
        for line in tax_line:
            retorno = 0
            # Valida si es nuevo registro
            if line[0] == 0:
                value = line[2]
            # Valida si es un registro modificado o guardado
            elif line[0] == 4 or line[0] == 1:
                # Valor de retorno para el detalle
                retorno = 1
                # Valida que sea un registro y que contenga el valor que necesita
                if not line[2]:
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    value = {
                        'base': statement_tax.base,
                        'amount': statement_tax.amount,
                        'percent': statement_tax.percent
                    }
                elif not line[2]['percent']:
                    statement_tax = self.pool.get('account.fiscal.statement.tax').browse(cr, uid, line[1], context=context)
                    value = {
                        'base': statement_tax.base,
                        'amount': statement_tax.amount,
                        'percent': statement_tax.percent
                    }
                else:
                    value = line[2]
            else:
                continue
            
            base = amount/percent_total
            amount_tax_line = (amount * value['percent'])/percent_total
            
            value['base'] = base
            value['amount'] = amount_tax_line
            amount_tax += amount_tax_line
            tax_ids.append([retorno, line[1], value])
        values['tax_line'] = tax_ids 
        values['amount_untaxed'] = amount - amount_tax
        values['amount_tax'] = amount_tax
        values['amount_total'] = amount
        # Obtiene la moneda
        return {'value': values}
    
    def _check_statement(self, cr, uid, ids, field, arg, context=None):
        """
            Indica True si ya fue conciliado con los movimientos del banco
        """
        result = {}
        # Recorre los registros
        for statement in self.browse(cr, uid, ids, context=context):
            # Obtiene la base del impuesto
            result[statement.id] = True if statement.statement_id else False
        return result
    
    _columns = {
        'name': fields.char('Nombre', size=64, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Diario', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'amount': fields.float('Importe', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'amount_untaxed': fields.function(_get_amount_total, string='Subtotal', type="float", multi="total", store=True, digits_compute= dp.get_precision('Account')),
        'amount_tax': fields.function(_get_amount_total, string='Impuestos', type="float", multi="total", store=True, digits_compute= dp.get_precision('Account')),
        'amount_total': fields.function(_get_amount_total, string='Total', type="float", multi="total", store=True, digits_compute= dp.get_precision('Account')),
        'period_id': fields.many2one('account.period', 'Periodo', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'account_id':fields.many2one('account.account', 'Cuenta', required=True, readonly=True, states={'draft':[('readonly',False)]}, help="Cuenta donde se registra el ingreso."),
        'type':fields.selection([
            ('income','Ingreso'),
            ('expense','Egreso')],'Tipo', readonly=True),
        'state':fields.selection(
            [('draft','Borrador'),
             ('cancel','Cancelado'),
             ('posted','Aplicado')
            ], 'Estatus', readonly=True, size=32, track_visibility='onchange',
            help=' * The \'Borrador\' Estado utilizado para indicar nuevos ingresos. \
                        \n* The \'Aplicado\' El estado esta aplicado en la contabilidad \
                        \n* The \'Cancelado\' El estado es utilizado cuando se cancela el ingreso (No puedes cancelar ingresos aplicados).'),
        'date': fields.date('Fecha', required=True, readonly=True, states={'draft':[('readonly',False)]}, select=True),
        'date_posted': fields.date('Fecha Validacion', readonly=True, select=True),
        'partner_id': fields.many2one('res.partner', 'Contacto', readonly=True, states={'draft':[('readonly',False)]}),
        'currency_id': fields.many2one('res.currency', 'Moneda', required=True, readonly=True, states={'draft':[('readonly',False)]}, track_visibility='always'),
        'tax_line': fields.one2many('account.fiscal.statement.tax', 'statement_id', 'Lineas de Impuestos', readonly=True, states={'draft':[('readonly',False)]}),
        'move_id': fields.many2one('account.move', 'Asiento Contable', readonly=True, select=1, ondelete='restrict'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Apuntes Contables', readonly=True),
        'number': fields.related('move_id','name', type='char', readonly=True, size=64, relation='account.move', store=True, string='Numero'),
        'type_statement_id': fields.many2one('account.fiscal.statement.type', string='Tipo Movimiento', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'notes': fields.text('Notas'),
        'ref': fields.char('Referencia', size=128),
        'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'statement_id': fields.many2one('account.bank.statement', 'Statement', select=True, ondelete='restrict', help="conciliacion sobre el pago"),
        'concilie_bank': fields.function(_check_statement, type="boolean", store=True, string="Conciliado"),
        # Informacion sobre saldo
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo', select=True, ondelete='cascade', readolny=True),
        'balance_line_id': fields.many2one('account.fiscal.balance.line', 'Linea de Saldo', select=True, ondelete='cascade', readonly=True)
    }
    
    _defaults = {
        'name': '/',
        'type': 'income',
        'state': 'draft',
        'period_id': _get_period,
        'date': fields.date.context_today,
        'amount': 0.0,
        'amount_tax': 0.0,
        'amount_total': 0.0,
        'concilie_bank': False,
        'type_statement_id': _get_type_statement_default
    }

account_fiscal_statement()

class account_fiscal_statement_tax(osv.osv):
    _name = "account.fiscal.statement.tax"
    _description = "Statement Tax"
    
    def _get_amount_tax(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el monto a aplicar con los impuestos
        """
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = line.base * line.percent
        return result
    
    def onchange_tax(self, cr, uid, ids, tax_id, context=None):
        """
            Actualiza los campos relacionados con los impuestos
        """
        base_amount = context.get('base_amount', 0.0)
        tax = self.pool.get('account.tax').browse(cr, uid, tax_id, context=context)
        values = {}
        values['name'] = tax.name
        values['percent'] = tax.amount
        values['account_id'] = tax.account_collected_id_apply.id
        #values['base'] = base_amount
        #values['amount'] = base_amount * values['percent']
        #print "******************* values ********************* ", values
        # Obtiene la moneda
        return {'value': values}
    
    _columns = {
        'statement_id': fields.many2one('account.fiscal.statement', 'Invoice Line', ondelete='cascade', select=True),
        'name': fields.char('Nombre', size=64, required=True),
        'account_id': fields.many2one('account.account', 'Cuenta', required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account'), readonly=True),
        'amount': fields.function(_get_amount_tax, type='float', store=True, string="Importe", digits_compute=dp.get_precision('Account')), 
        'tax_id': fields.many2one('account.tax', 'Impuesto', required=True, help="Impuesto a aplicar al gasto."),
        'percent': fields.float('Porcentaje', digits_compute=dp.get_precision('Account'))  
    }
    
    _defaults = {
        'base': 0.0,
        'amount': 0.0,
    }
    
account_fiscal_statement_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
