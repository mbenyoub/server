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
# Account fiscal - Saldos Fiscales
# ---------------------------------------------------------

class account_fiscal_balance(osv.Model):
    _name = 'account.fiscal.balance'
    
    def validate_period_apply(self, cr, uid, period_id1, period_id2, context=None):
        """
            Valida si el periodo 1 es mayor o igual al periodo 2
        """
        #~ Valida que no haya productos repetidos en la solicitud de compra
        cr.execute("""
                select (to_char(p.date_start,'yyyyMM'))::int as fecha 
                    from account_period as p where p.id = %s and (to_char(p.date_start,'yyyyMM'))::int >
                    (select (to_char(p.date_start,'yyyyMM'))::int as fecha 
                    from account_period as p where p.id = %s)"""%(period_id1,period_id2))
        if cr.fetchone():
            return True
        return False
    
    def get_year_period(self, cr, uid, period_id, context=None):
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
        return year
    
    def get_year_fiscalyear(self, cr, uid, fiscalyear_id, context=None):
        """
            Obtiene el mes del ejercicio
        """
        cr.execute("""
            select
                extract(year from y.date_start) as month
            from
                account_fiscalyear as y
            where y.id = %s"""%(fiscalyear_id))
        year = 0.0
        for value in cr.fetchall():
            year = value[0]
            break
        return year
    
    def get_config_type_statement_id(self, cr, uid, context=None):
        """
            Obtiene el tipo de ingreso que esta configurado para obtener la utilidad fiscal
        """
        code_id = False
        cr.execute(
            """ select id as id, balance_type_statement_id as type_id 
                from account_fiscal_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        #print "************* dat ************ ", dat
        type_id = dat and dat[0]['type_id'] or False
        #print "************ type_id ************** ", type_id
        return type_id or False
    
    def onchange_amount(self, cr, uid, ids, amount, context=None):
        """
            Actualiza el monto del saldo del producto
        """
        return {'value': {'balance': amount}}
    
    def onchange_type_code(self, cr, uid, ids, type_code, context=None):
        """
            Obtiene los saldos sobre el periodo
        """
        
        values = {}
        domain = {}
        
        type = 'year'
        if type_code == 'month':
            type = 'period'
        
        # Revisa el tipo de codigo
        if type_code:
            domain['code_id'] = [('type','=',type),('parent_id','!=',False),('apply_balance','=',True)]
        
        values = {
            'code_id': False,
        }
        
        return {'value': values, 'domain': domain}
    
    def onchange_code_id(self, cr, uid, ids, code_id, context=None):
        """
            Obtiene el codigo de impuesto relacionado con el codigo fiscal
        """
        values = {}
        if code_id:
            # Obtiene la informacion del codigo fiscal
            code = self.pool.get('account.fiscal.code').browse(cr, uid, code_id, context=context)
            if code.tax_code_id:
                values = {'tax_code_id': code.tax_code_id.id}
        return {'value': values}
    
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Cambia el estado del documento a abierto o cerrado
        """
        # Valida que el documento tenga saldo disponible
        for balance in self.browse(cr, uid, ids, context=context):
            if balance.amount <= 0:
                raise osv.except_osv('Error Validacion', 'Debe existir un saldo para poder confirmar el documento.')
            # Actualiza el documento
            self.write(cr, uid, [balance.id], {'state': 'open', 'balance': balance.amount}, context=context)
        return True
    
    def get_period(self, cr, uid, context=None):
        """Return default period value"""
        #print "************* get period **************"
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def get_month_period(self, cr, uid, period_id, context=None):
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
    
    def get_year_period(self, cr, uid, period_id, context=None):
        """
            Obtiene el año del periodo
        """
        cr.execute("""
            select
                extract(year from p.date_start) as year
            from
                account_period as p
            where p.id = %s"""%(period_id))
        year = 0.0
        for value in cr.fetchall():
            year = value[0]
            break
        return int(year)
    
    def validate_date(self, cr, uid, date, context=None):
        """
            Regresa Verdadero si el mes y año de la fecha es igual a la fecha actual
        """
        result = False
        cr.execute("""
            select to_char(date('%s'), 'mm/YYYY') """%(date))
        for value in cr.fetchall():
            period = value[0]
            break
        cur_date = time.strftime('%m/%Y')
        #print "**************** cur_date **************** ", cur_date, " - ", period
        if period == cur_date:
            result = True
        return result
    
    def _get_balance_update(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el balance actualizado
        """
        # Inicializa variables
        inpc_obj = self.pool.get('account.fiscal.inpc')
        inpc_prev = 0.0
        inpc_cur = 0.0
        next_inpc = False
        last_inpc = False
        update_factor = 0.0
        balance_update = 0.0
        res = {}
        
        # Obtiene el mes actual y el año del periodo
        period_id = self.get_period(cr, uid, context=context)
        month = self.get_month_period(cr, uid, period_id, context=context)
        year = self.get_year_period(cr, uid, period_id, context=context)
        
        if month-1 == 0:
            month = 12
            year = year-1
        else:
            month = month -1
        
        #print "************* month ************** ", month
        #print "************* year  ************** ", year
        
        # Obtiene el inpc del mes anterior al actual
        next_inpc = inpc_obj.get_inpc(cr, uid, month, year, context=context)
        
        # Recorre los registros
        for balance in self.browse(cr, uid, ids, context=context):
            # Valida que este confirmado el documento para generar el calculo
            if balance.state != 'open':
                res[balance.id] = {
                    'balance': 0.0,
                    'balance_update': 0.0,
                    'last_inpc_id': last_inpc,
                    'next_inpc_id': next_inpc,
                    'inpc': next_inpc
                }
                continue
            
            balance_amount = 0.0
            if not balance.line_ids:
                balance_amount = balance.amount
            else:
                cr.execute("""
                    select period_id, result
                    from account_fiscal_balance_line
                    where balance_id=%s
                    order by write_date desc
                    limit 1"""%(balance.id))
                for value in cr.fetchall():
                    #print "************ value *********** ", value
                    p_id = value[0]
                    balance_amount = value[1]
                    break
                # Valida que no se haya aplicado el factor de actualizacion sobre los registros
                if p_id == period_id:
                    res[balance.id] = {
                        'balance': balance_amount,
                        'balance_update': balance_amount,
                        'last_inpc_id': False,
                        'next_inpc_id': False,
                        'inpc': next_inpc
                    }
                    continue
                
            # Valida que haya saldo disponible
            if balance.amount <= 0.0:
                res[balance.id] = {
                    'balance': balance.amount,
                    'balance_update': 0.0,
                    'last_inpc_id': last_inpc,
                    'next_inpc_id': next_inpc,
                    'inpc': next_inpc
                }
                continue
            
            # Valida que la fecha del saldo sea diferente de la del mes actual
            result = self.validate_date(cr, uid, balance.date, context=context)
            if result:
                res[balance.id] = {
                    'balance': balance_amount,
                    'balance_update': balance_amount,
                    'last_inpc_id': False,
                    'next_inpc_id': False,
                    'inpc': next_inpc
                }
                continue
            
            # Obtiene el id del inpc sobre la fecha de adquisicion del saldo
            last_inpc = inpc_obj.get_inpc_to_date(cr, uid, balance.date, context=context)
            
            #print "****************** next_inpc ************* ", next_inpc
            #print "****************** last_inpc ************* ", last_inpc
            
            # Valida que esten registrados los inpc
            if next_inpc == False or last_inpc == False:
                raise osv.except_osv(_('Warning!'),_("Debe tener disponible la informacion de los inpc para poder actualizar el remanente!"))
            
            # Obtiene el valor de los inpc
            inpc_prev = inpc_obj.get_value(cr, uid, last_inpc, context=context)
            inpc_cur = inpc_obj.get_value(cr, uid, next_inpc, context=context)
            #print "************** inpc_prev ********** ", inpc_prev
            #print "************** inpc_cur ********** ", inpc_cur
            
            # Actualiza el remanente
            if inpc_cur != 0:
                update_factor = inpc_prev/inpc_cur
                balance_update = update_factor * balance_amount
            #print "************** factor de actualizacion ******* ", update_factor
            #print "************** monto actualizado ******* ", balance_update
            res[balance.id] = {
                'balance': balance_amount,
                'balance_update': balance_update,
                'last_inpc_id': last_inpc,
                'next_inpc_id': next_inpc,
                'inpc': next_inpc
            }
        return res
    
    def _get_name(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el nombre del saldo
        """
        res = {}
        for balance in self.browse(cr, uid, ids, context=context):
            if balance.type == 'tax':
                res[balance.id] = 'Saldo - %s'%(balance.tax_code_id.name,)
            else:
                res[balance.id] = 'Saldo - %s'%(balance.code_id.name,)
        return res
    
    _columns = {
        'name': fields.function(_get_name, string='Nombre', type='char', size=128),
        'date': fields.date('Fecha creacion', required=True),
        'date_update': fields.date('Ultima actualizacion'),
        'amount': fields.float('Saldo', digits=(16,4)),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal', ondelete='restrict'),
        'tax_code_id': fields.many2one('account.tax.code', 'Impuesto', ondelete='restrict'),
        'state': fields.selection([('draft','Borrador'),
                                    ('open','Abierto'),
                                    ('close','Cerrado'),
                                    ('cancel','Cancelado'),], 'Estado', required=True),
        'type': fields.selection([('tax','Impuesto'),
                                    ('code','Codigo Fiscal'),], 'Tipo', required=True),
        'line_ids': fields.one2many('account.fiscal.balance.line', 'balance_id', 'Saldos Aplicados', ondelete='cascade'),
        'info': fields.text('Comentarios'),
        
        'balance': fields.function(_get_balance_update, string="Saldo Fiscal", type='float', store=False, multi='bupdate', digits=(16,4)),
        'balance_update': fields.function(_get_balance_update, string="Saldo Actualizado", type='float', store=False, multi='bupdate', digits=(16,4)),
        'next_inpc_id': fields.function(_get_balance_update, type='many2one', relation='account.fiscal.inpc', string='Siguiente INPC', store=False, multi='bupdate', select=True),
        'last_inpc_id': fields.function(_get_balance_update, type='many2one', relation='account.fiscal.inpc', string='Ultimo INPC', store=False, multi='bupdate', select=True),
        'inpc': fields.function(_get_balance_update, type='many2one', relation='account.fiscal.inpc', string='Ultimo INPC', store=False, multi='bupdate', select=True),
        'period_id': fields.many2one('account.period', 'Periodo de registro'),
        'type_code': fields.selection([('month','Mensual'),
                                    ('year','Anual'),], 'Tipo codigo Fiscal'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio de registro'),
    }
    
    _order = "date"
    
    _defaults = {
        'date': fields.date.today,
        'state': 'draft',
        'type': 'tax',
        'type_code': 'month'
    }
    
    def action_apply_balance_apply_tax(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con el monto a aplicar el saldo sobre el impuesto
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_balance_apply_tax_view')
        
        return {
            'name':_("Aplicar Saldo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.balance.apply.tax',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                
            }
        }
    
    def action_apply_balance_apply_code(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con el monto a aplicar el saldo sobre el codigo fiscal
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_balance_apply_code_view')
        
        # Obtiene el saldo del registro
        balance = self.browse(cr, uid, ids[0], context=context)
        
        return {
            'name':_("Aplicar Codigo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.balance.apply.code',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_balance_id': ids[0],
                'default_update_amount': balance.balance_update,
                'default_type_code_balance': balance.type_code,
                'default_period_id_balance': balance.period_id.id,
                'default_fiscalyear_id_balance': balance.fiscalyear_id.id
            }
        }
    
    def action_apply_balance_return(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con el monto a devolver sobre el saldo
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_balance_return_view')
        
        # Obtiene el saldo del registro
        balance = self.browse(cr, uid, ids[0], context=context)
        
        return {
            'name':_("Devolucion de Saldo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.balance.return',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_balance_id': ids[0],
                'default_amount': balance.balance_update,
                'default_update_amount': balance.balance_update
            }
        }
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        """
        Returns a list of tupples containing id, name, as internally it is called {def name_get}
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param name: name to search
        @param args: other arguments
        @param operator: default operator is 'ilike', it can be changed
        @param context: context arguments, like lang, time zone
        @param limit: Returns first 'n' ids of complete result, default is 80.

        @return: Returns a list of tupples containing id and name
        """
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('info', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context or {})
        return self.name_get(cr, user, ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = ''
            if record.type == 'tax':
                name = 'Saldo Fiscal, impuesto ' + record.tax_code_id.name if record.tax_code_id else 'Saldo fiscal de impuesto'
                if record.period_id:
                    name = '%s - %s'%(name,record.period_id.name)
            else:
                name = 'Saldo Fiscal, codigo fiscal ' + record.code_id.name if record.code_id else 'Saldo fiscal de codigo fiscal'
                if record.type_code == 'year' and record.fiscalyear_id:
                    name = '%s - %s'%(name,record.fiscalyear_id.name)
                else:
                    name = '%s - %s'%(name,record.period_id.name)
            res.append((record.id,name ))
        return res

account_fiscal_balance()

class account_fiscal_balance_line(osv.Model):
    _name = 'account.fiscal.balance.line'
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    def _get_balance_update(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el balance actualizado
        """
        # Inicializa variables
        update_factor = 0.0
        balance_current = 0.0
        result = 0.0
        res = {}
        
        # Recorre los registros
        for line in self.browse(cr, uid, ids, context=context):
            #print "****************** lines inpc *********** ", not line.last_inpc_id, "  ", not line.next_inpc_id
            
            if not line.last_inpc_id == False or not line.next_inpc_id == False:
                update_factor = 1.0
            else:
                # Actualiza el remanente
                if line.last_inpc_val != 0:
                    update_factor = line.last_inpc_val/line.next_inpc_val
            # Obtiene el valor actual y el saldo restante
            balance_current = update_factor * line.balance_before
            result = balance_current - line.amount
            # Registra la informacion para retornarla en los campos
            res[line.id] = {
                'update_factor': update_factor,
                'balance_current': balance_current,
                'result': result,
            }
        return res
    
    def action_view_ref(self, cr, uid, ids, context=None):
        """
            Redirecciona al ingreso relacionado sobre el ingreso
        """
        line = self.browse(cr, uid, ids[0], context=context)
        if line.reference:
            statement_id = line.reference.id
        else:
            return True
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_statement_income_form')
        return {
            'name':_("Ingreso"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.statement',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {},
            'res_id' : statement_id, # id of the object to which to redirected
        }
    
    def action_confirm_line(self, cr, uid, ids, context=None):
        """
            Pone el ingreso como confirmado
        """
        line_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.reference and line.type == 'dev':
                line_ids.append(line.reference.id)
            
        self.pool.get('account.fiscal.statement').action_validate_income(cr, uid, line_ids, context=context)
        return True
    
    def action_delete_line(self, cr, uid, ids, context=None):
        """
            Elimina la informacion relacionada al registro
        """
        bline_obj = self.pool.get('account.fiscal.balance.line')
        inc_obj = self.pool.get('account.fiscal.statement')
        code_history_obj = self.pool.get('account.fiscal.code.history')
        code_hline_obj = self.pool.get('account.fiscal.code.history.line')
        tax_history_obj = self.pool.get('account.tax.code.history')
        tax_hline_obj = self.pool.get('account.tax.code.history.line')
        balance_id = False
        # Recorre los registros
        for line in self.browse(cr, uid, ids, context=context):
            balance_id = line.balance_id.id
            # Valida que haya una referencia sobre el registro
            if line.reference:
                # Revisa que tenga referencia y si el tipo de movimiento es una devolucion
                if line.type == 'dev':
                    #print "***************** state *********** ", line.reference.state
                    
                    # Valida que el ingreso no se encuentre aplicado
                    if line.reference.state == 'posted':
                        raise osv.except_osv('Error Validacion', u'Debe revisar que el ingreso no se encuentre confirmado para eliminar el registro.')
                    
                    # Elimina el ingreso relacionado
                    inc_obj.unlink(cr, uid, [line.reference.id], context=context)
                else:
                    # Valida si el saldo es de un codigo fiscal o de un impuesto
                    if line.balance_id.type == 'tax':
                        # Actualiza los valores sobre los registros padre
                        history = line.reference.parent_id
                        amount = line.reference.sum_period * -1
                        if history:
                            n = 1
                            while(n == 1):
                                #print "****************** historico ************** ", history.id
                                
                                # Actualiza el resultado
                                tax_hline_obj.write(cr, uid, [history.id], {'sum_period': history.sum_period + amount}, context=context)
                                
                                # Actualiza el resultado de los registros del historial
                                if history.parent_id:
                                    history = history.parent_id
                                else:
                                    n = 0
                        # Disminuye la cantidad de registros donde se afectan saldos en el historico
                        tax_history_obj.write(cr, uid, [line.reference.history_id.id], {'cont': line.reference.history_id.cont-1}, context=context)
                        
                        # Elimina el registro del historico
                        tax_hline_obj.unlink(cr, uid, [line.reference.id], context=context)
                    else:
                        history = line.reference.parent_id
                        # Elimina el registro del historico
                        code_hline_obj.unlink(cr, uid, [line.reference.id], context=context)
                        # Actualiza los registros padre
                        if history:
                            code_hline_obj.update_history_values(cr, uid, history.id, context=context)
                        
                        # Disminuye la cantidad de registros donde se afectan saldos en el historico
                        code_history_obj.write(cr, uid, [line.reference.history_id.id], {'cont': line.reference.history_id.cont-1}, context=context)
        
        # Elimina los registros del saldo
        self.unlink(cr, uid, ids, context=context)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_balance_form')
        return {
            'name':_("Saldo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.balance',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : balance_id, # id of the object to which to redirected
        }
    
    def _check_balance(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si es el ultimo registro sobre la linea
        """
        res = {}
        
        balance_id = False
        max_id = 0
        # Recorre los registros
        for bal in self.browse(cr, uid, ids, context=context):
            edit = False
            if balance_id != bal.balance_id.id:
                # Obtiene el ultimo id registrado sobre el balance
                cr.execute("""
                    select max(id)
                    from account_fiscal_balance_line
                    where balance_id = %s"""%(bal.balance_id.id))
                max_id = 0
                for value in cr.fetchall():
                    max_id = value[0]
                    break
            # Revisa si es el ultimo registro aplicado sobre el balance
            if bal.id == max_id:
                edit = True
            res[bal.id] = edit
        return res
    
    _columns = {
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo', select=True, ondelete='cascade'),
        
        'period_id': fields.many2one('account.period', 'Periodo'),
        'balance_before': fields.float('Balance anterior', digits=(16,4)),
        'amount': fields.float('Saldo aplicado', digits=(16,4)),
        'date': fields.date('Fecha Actualizacion'),
        'type': fields.selection([('dev','Devolucion'),
                                    ('apply','Aplicacion'),], 'Tipo', required=True),
        
        'next_inpc_id': fields.many2one('account.fiscal.inpc', 'INPC actual', select=True),
        'next_inpc_val': fields.related('next_inpc_id', 'value', type='float', digits=(16,4), string='Valor INPC Actual', store=True, readonly=True),
        'last_inpc_id': fields.many2one('account.fiscal.inpc', 'INPC anterior', select=True),
        'last_inpc_val': fields.related('last_inpc_id', 'value', type='float', digits=(16,4), string='Valor INPC Anterior', store=True, readonly=True),
        'inpc': fields.many2one('account.fiscal.inpc', 'INPC actual', select=True),
        
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True, ondelete='restrict'),
        
        'update_factor': fields.function(_get_balance_update, string="Factor de actualizacion", type='float', digits=(16,4), store=True, multi='bupdate'),
        'balance_current': fields.function(_get_balance_update, string="Saldo Actual", type='float', store=True, multi='bupdate'),
        'result': fields.function(_get_balance_update, string="Saldo pendiente", type='float', store=True, multi='bupdate'),
        'state': fields.selection([('pending','Pendiente'),
                                    ('done','Aplicado'),], 'Estado', required=True),
        'check_balance': fields.function(_check_balance, string='ultimo registro', type='boolean'),
        'reference2': fields.reference('Aplicado a', selection=_links_get, size=128, readonly=True, ondelete='restrict'),
    }
    
    _defaults = {
        'date': fields.date.today,
        'state': 'pending',
        'type': 'dev'
    }
    
account_fiscal_balance_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
