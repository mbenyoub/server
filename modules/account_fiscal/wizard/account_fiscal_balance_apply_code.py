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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_fiscal_balance_apply_code(osv.osv_memory):
    """ Aplicar Saldo a codigo fiscal """
    _name = 'account.fiscal.balance.apply.code'
    _description = 'Aplicar Saldo a Codigo Fiscal'
    
    def onchange_type_code(self, cr, uid, ids, type_code, context=None):
        """
            Obtiene los saldos sobre el periodo
        """
        
        values = {}
        domain = {}
        
        # Revisa el tipo de codigo
        if type_code:
            domain['code_id'] = [('type','=',type_code),('parent_id','!=',False),('apply_balance','=',True)]
        
        values = {
            'history_id': False,
            'code_id': False,
            'history_value': 0.0,
            'amount': 0.0
        }
        
        return {'value': values, 'domain': domain}
    
    def onchange_tax_code_id(self, cr, uid, ids, period_id, tax_code_id, update_amount, context=None):
        """
            Obtiene los saldos sobre el periodo de los impuestos
        """
        balance_obj = self.pool.get('account.fiscal.balance')
        history_obj = self.pool.get('account.tax.code.history')
        hline_obj = self.pool.get('account.tax.code.history.line')
        values = {}
        domain = {}
        history = []
        
        # Revisa que tenga un periodo seleccionado y codigo para aplicar
        if not period_id or not tax_code_id:
            values = {
                'history_tax_id': False,
                'history_tax_value': 0.0,
                'history_tax_value2': 0.0,
                'amount': 0.0
            }
        else:
            #print "**************** tax_code_id ************* ", tax_code_id
            #print "**************** period_id ************* ", period_id
            
            # Busca en el historial de los impuestos si esta registrado el codigo sobre el periodo
            history_id = hline_obj.get_code_tax_period(cr, uid, tax_code_id, period_id, context=context)
            #print "**************** history_id ************** ", history_id
            if not history_id:
                raise osv.except_osv('Error Validacion', u'No esta registrado el impuesto el periodo, actualice el historial de impuestos para continuar.')
            # Actualiza la informacion sobre los registros
            history = hline_obj.read(cr, uid, history_id, ['sum_period'], context=context)
            
            amount = 0.0
            # Obtiene el valor del monto
            if history['sum_period'] <= 0.0:
                amount = 0.0
            elif update_amount >= history['sum_period']:
                amount = history['sum_period']
            else:
                amount = update_amount
            
            values = {
                'history_tax_id': history_id,
                'history_tax_value': history['sum_period'],
                'history_tax_value2': history['sum_period'],
                'amount': amount
            }
        
        return {'value': values, 'domain': domain}
    
    def onchange_code_id(self, cr, uid, ids, type_code, period_id, fiscalyear_id, code_id, update_amount, context=None):
        """
            Obtiene los saldos sobre el periodo
        """
        balance_obj = self.pool.get('account.fiscal.balance')
        history_obj = self.pool.get('account.fiscal.code.history')
        hline_obj = self.pool.get('account.fiscal.code.history.line')
        values = {}
        domain = {}
        history = []
        
        # Revisa el tipo de codigo
        #if type_code:
        #    domain['code_id'] = [('type','=',type_code)]
        
        # Revisa que tenga un periodo seleccionado y codigo para aplicar
        if type_code == 'period':
            if not period_id or not code_id:
                values = {
                    'history_id': False,
                    'history_value': 0.0,
                    'history_value2': 0.0,
                    'amount': 0.0
                }
            else:
                #print "**************** code_id ************* ", code_id
                #print "**************** period_id ************* ", period_id
                
                # Busca en el historial de los codigos fiscales si esta registrado el codigo sobre el periodo
                history_id = hline_obj.get_code_period(cr, uid, code_id, period_id, context=context)
                #print "**************** history_id ************** ", history_id
                if not history_id:
                    raise osv.except_osv('Error Validacion', u'No esta registrado el codigo sobre el periodo, actualice el historial de codigos fiscales para continuar.')
                # Actualiza la informacion sobre los registros
                history = hline_obj.read(cr, uid, history_id, ['value'], context=context)
                
                amount = 0.0
                # Obtiene el valor del monto
                if history['value'] <= 0.0:
                    amount = 0.0
                elif update_amount >= history['value']:
                    amount = history['value']
                else:
                    amount = update_amount
                
                values = {
                    'history_id': history_id,
                    'history_value': history['value'],
                    'history_value2': history['value'],
                    'amount': amount
                }
        else:
            if not fiscalyear_id or not code_id:
                values = {
                    'history_id': False,
                    'history_value': 0.0,
                    'history_value2': 0.0,
                    'amount': 0.0
                }
            else:
                # Busca en el historial de los codigos fiscales si esta registrado el codigo sobre el periodo
                history_id = hline_obj.get_code_fiscalyear(cr, uid, code_id, fiscalyear_id, context=context)
                if not history_id:
                    raise osv.except_osv('Error Validacion', u'No esta registrado el codigo sobre el ejercicio, actualice el historial de codigos fiscales para continuar.')
                # Actualiza la informacion sobre los registros
                history = hline_obj.read(cr, uid, history_id, ['value'], context=context)
                
                amount = 0.0
                # Obtiene el valor del monto
                if history['value'] <= 0.0:
                    amount = 0.0
                elif update_amount >= history['value']:
                    amount = history['value']
                else:
                    amount = update_amount
                
                values = {
                    'history_id': history_id,
                    'history_value': history['value'],
                    'history_value2': history['value'],
                    'amount': amount
                }
        return {'value': values, 'domain': domain}
    
    def onchange_period_id(self, cr, uid, ids, apply_to, tax_code_id, type_code, period_id, fiscalyear_id, code_id, update_amount, context=None):
        """
            Obtiene los saldos sobre el periodo segun aplique para impuestos o codigos fiscales
        """
        res = {}
        if apply_to == 'code':
            res = self.onchange_code_id(cr, uid, ids, type_code, period_id, fiscalyear_id, code_id, update_amount, context=context)
        else:
            res = self.onchange_tax_code_id(cr, uid, ids, period_id, tax_code_id, update_amount, context=context)
        return res
    
    def balance_apply_code(self, cr, uid, ids, context=None):
        """
            Genera aplicacion sobre el saldo a codigos fiscales
        """
        history_obj = self.pool.get('account.fiscal.code.history')
        hline_obj = self.pool.get('account.fiscal.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        bline_obj = self.pool.get('account.fiscal.balance.line')
        link_obj = self.pool.get('links.get.request')
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.fiscal.code.history.line', 'Historico Codigo Fiscal', context=None)
        
        # Recorre los registros
        for apply in self.browse(cr, uid, ids, context=context):
            # Valida que el monto no sea mayor al monto por pagar
            if apply.history_value < apply.amount:
                raise osv.except_osv('Error Validacion', u'El saldo aplicado es mayor que el monto por pagar del codigo %s.'%(apply.code_id.name,))
            # Valida que el monto no sea mayor al saldo actual
            if apply.update_amount < apply.amount:
                raise osv.except_osv('Error Validacion', u'El saldo disponible es menor que el monto por pagar del codigo %s.'%(apply.code_id.name,))
            # Valida que el monto no sea negativo
            if apply.amount <= 0.0:
                raise osv.except_osv('Error Validacion', u'El monto del codigo %s no puede ser negativo o cero.'%(apply.code_id.name,))
            
            #print "************** type code wizard ************* ", apply.type_code
            #print "************** type code balance ************* ", apply.balance_id.type_code
            
            # Revisa si el tipo es anual o mensual
            if apply.type_code == 'year' and apply.balance_id.type_code == 'year':
                # Valida que el ejercicio a aplicar sea menor al ejercicio actual
                if apply.balance_id.fiscalyear_id:
                    year1 = balance_obj.get_year_fiscalyear(cr, uid, apply.balance_id.fiscalyear_id.id, context=context)
                    year2 = balance_obj.get_year_fiscalyear(cr, uid, apply.fiscalyear_id.id, context=context)
                    #print "************ year-year *********** ", year1, ' >= ', year2
                    if year1 >= year2:
                        raise osv.except_osv('Error Validacion', u'El ejercicio del saldo debe ser menor que el ejercicio donde se aplica el saldo (Ejercicio: %s).'%(apply.balance_id.fiscalyear_id.name,))
            elif apply.type_code == 'period' and apply.balance_id.type_code == 'year':
                # Valida que el ejercicio a aplicar sea menor al ejercicio actual
                if apply.balance_id.fiscalyear_id:
                    year1 = balance_obj.get_year_fiscalyear(cr, uid, apply.balance_id.fiscalyear_id.id, context=context)
                    year2 = balance_obj.get_year_period(cr, uid, apply.period_id.id, context=context)
                    #print "************ period-year *********** ", year1, ' >= ', year2
                    if year1 >= year2:
                        raise osv.except_osv('Error Validacion', u'El ejercicio del saldo debe ser menor que el ejercicio donde se aplica el saldo (Ejercicio: %s).'%(apply.balance_id.fiscalyear_id.name,))
            elif apply.type_code == 'year' and apply.balance_id.type_code == 'month':
                # Valida que el ejercicio a aplicar sea menor al ejercicio actual
                if apply.balance_id.period_id:
                    year1 = balance_obj.get_year_period(cr, uid, apply.balance_id.period_id.id, context=context)
                    year2 = balance_obj.get_year_fiscalyear(cr, uid, apply.fiscalyear_id.id, context=context)
                    #print "************ year-period *********** ", year1, ' >= ', year2
                    if year1 >= year2:
                        raise osv.except_osv('Error Validacion', u'El ejercicio del saldo debe ser menor que el ejercicio donde se aplica el saldo (Periodo: %s).'%(apply.balance_id.period_id.name,))
            elif apply.type_code == 'period' and apply.balance_id.type_code == 'month':
                # Valida que el periodo a aplicar sea menor al periodo actual
                if apply.balance_id.period_id:
                    check = balance_obj.validate_period_apply(cr, uid, apply.period_id.id, apply.balance_id.period_id.id, context=context)
                    #print "************ period-period *********** ", check, '  ', apply.period_id.id, ' ', apply.balance_id.period_id.id
                    if check == False:
                        raise osv.except_osv('Error Validacion', u'El periodo del saldo debe ser menor que el periodo donde se aplica el saldo (Periodo: %s).'%(apply.balance_id.period_id.name,))
            
            name = 'Aplicacion saldo -' + apply.code_id.name
            if apply.balance_id.type == 'year':
                if apply.balance_id.fiscalyear_id:
                    name = name + ' - ' + str(apply.balance_id.fiscalyear_id.name)
            else:
                if apply.balance_id.period_id:
                    name = name + ' - ' + str(apply.balance_id.period_id.name)
            
            # Actualiza el resultado sobre el historial de impuestos
            hline_id = hline_obj.create(cr, uid, {
                'name': name,
                'history_id': apply.history_id.history_id.id,
                'code_id': apply.code_id.id,
                'value': apply.amount,
                'parent_id': apply.history_id.id,
                'factor': 'res',
                'sequence': 1000,
                'apply_balance': True}, context=context)
            
            #print "************ hiline_id ********** ", hline_id
            
            # Actualiza el valor del registro
            history = apply.history_id
            #print "****************** history ******** ", history
            #print "****************** apply amount **** ", history.value, ' - ', apply.amount
            hline_obj.write(cr, uid, [history.id], {'value': history.value - apply.amount}, context=context)
            
            #print "**************** registro modificado *************** ", history.id
            
            # Valida si hay algun otro registro padre
            if history.parent_id:
                hline_obj.update_history_values(cr, uid, history.parent_id.id, context=context)
            
            # Marca en el historial que hay registros sobre el saldo
            history_obj.write(cr, uid, [history.history_id.id], {'cont': history.history_id.cont+1}, context=context)
            
            reference = 'account.fiscal.code.history.line,' + str(hline_id)
            reference2 = 'account.fiscal.code.history.line,' + str(apply.history_id.id)
            
            # Agrega un registro en las lineas del saldo fiscal
            bline_id = bline_obj.create(cr, uid, {
                'balance_id': apply.balance_id.id,
                'period_id': apply.period_id.id,
                'balance_before': apply.balance_id.balance,
                'amount': apply.amount,
                'type': 'apply',
                'next_inpc_id': apply.balance_id.next_inpc_id.id,
                'last_inpc_id': apply.balance_id.last_inpc_id.id,
                'inpc': apply.balance_id.inpc.id,
                'state': 'done',
                'reference': reference,
                'reference2': reference2}, context=context)
            #print "**************** bline_id ***************** ", bline_id
        return True
    
    def balance_apply_tax(self, cr, uid, ids, context=None):
        """
            Genera aplicacion sobre el saldo
        """
        history_obj = self.pool.get('account.tax.code.history')
        hline_obj = self.pool.get('account.tax.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        bline_obj = self.pool.get('account.fiscal.balance.line')
        link_obj = self.pool.get('links.get.request')
        balance_id = False
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.tax.code.history.line', 'Historico Impuestos', context=None)
        
        # Recorre los registros
        for apply in self.browse(cr, uid, ids, context=context):
            # Valida que el monto no sea mayor al monto por pagar
            if apply.history_tax_value < apply.amount:
                raise osv.except_osv('Error Validacion', u'El saldo aplicado es mayor que el monto por pagar del codigo %s.'%(apply.tax_code_id.name,))
            # Valida que el monto no sea mayor al saldo actual
            if apply.update_amount < apply.amount:
                raise osv.except_osv('Error Validacion', u'El saldo disponible es menor que el monto por pagar del codigo %s.'%(apply.tax_code_id.name,))
            # Valida que el monto no sea negativo
            if apply.amount <= 0.0:
                raise osv.except_osv('Error Validacion', u'El monto del codigo %s no puede ser negativo o cero.'%(apply.tax_code_id.name,))
            
            # Valida que el periodo a aplicar sea menor al periodo actual
            if apply.balance_id.period_id:
                check = balance_obj.validate_period_apply(cr, uid, apply.period_id.id, apply.balance_id.period_id.id, context=context)
                if check == False:
                    raise osv.except_osv('Error Validacion', u'El periodo del saldo debe ser menor que el periodo donde se aplica el saldo (Periodo: %s).'%(apply.balance_id.period_id.name,))
            
            name = 'Aplicacion saldo -' + apply.balance_id.code_id.name
            if apply.balance_id.period_id:
                name = name + ' - ' + str(apply.balance_id.period_id.name)
            
            #print "************* saldo ", name, " valido *************** "
            
            # Actualiza el resultado sobre el historial de impuestos
            hline_id = hline_obj.create(cr, uid, {
                'name': name,
                'history_id': apply.history_tax_id.history_id.id,
                'code_id': apply.tax_code_id.id,
                'company_id': apply.history_tax_id.company_id.id,
                'sequence': 0,
                'percent': 0,
                'sum_period': apply.amount * -1,
                'sum_year': 0.0,
                'base_period': 0.0,
                'base_year': 0.0,
                'parent_id': apply.history_tax_id.id,
                'apply_balance': True}, context=context)
            
            history = apply.history_tax_id
            n = 1
            while(n == 1):
                # Actualiza el resultado
                hline_obj.write(cr, uid, [history.id], {'sum_period': history.sum_period - apply.amount}, context=context)
                
                # Actualiza el resultado de los registros del historial
                if history.parent_id:
                    history = history.parent_id
                else:
                    n = 0
            
            # Marca en el historial que hay registros sobre el saldo
            history_obj.write(cr, uid, [apply.history_tax_id.history_id.id], {'cont': apply.history_tax_id.history_id.cont+1}, context=context)
            
            reference = 'account.tax.code.history.line,' + str(hline_id)
            reference2 = 'account.tax.code.history.line,' + str(apply.history_tax_id.id)
            
            # Agrega un registro en las lineas del saldo fiscal
            bline_id = bline_obj.create(cr, uid, {
                'balance_id': apply.balance_id.id,
                'period_id': apply.period_id.id,
                'balance_before': apply.balance_id.balance,
                'amount': apply.amount,
                'type': 'apply',
                'next_inpc_id': apply.balance_id.next_inpc_id.id,
                'last_inpc_id': apply.balance_id.last_inpc_id.id,
                'inpc': apply.balance_id.inpc.id,
                'state': 'done',
                'reference': reference,
                'reference2': reference2}, context=context)
            #print "**************** bline_id ***************** ", bline_id
            
            balance_id = apply.balance_id.id
                        
        return True
    
    def action_balance_apply(self, cr, uid, ids, context=None):
        """
            Genera aplicacion sobre el saldo
        """
        apply_tax = []
        apply_code = []
        balance_id = False
        # Recorre los registros y agrupa por saldos de impuestos y de codigos fiscales
        for apply in self.browse(cr, uid, ids, context=context):
            # Valida que el monto no sea mayor al monto por pagar
            if apply.apply_to == 'code':
                apply_code.append(apply.id)
            else:
                apply_tax.append(apply.id)
        # Aplica saldos sobre codigos fiscales
        if len(apply_code) > 0:
            self.balance_apply_code(cr, uid, ids, context=context)
        # Aplica saldos sobre impuestos
        if len(apply_tax) > 0:
            self.balance_apply_tax(cr, uid, ids, context=context)
            balance_id = apply.balance_id.id
        
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
    
    _columns = {
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account'), help="Monto a Devolver"),
        'update_amount': fields.float('Saldo actual', digits_compute=dp.get_precision('Account'), help="Saldo disponible"),
        'date': fields.date('Fecha'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo Fiscal'),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal a aplicar'),
        'type_code': fields.selection([('period','Mensual'),
                                    ('year','Anual'),], 'Tipo codigo Fiscal'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio de registro'),
        'history_id': fields.many2one('account.fiscal.code.history.line', 'Historial'),
        'history_value': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        'history_value2': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        # Campos para mostrar el ejercicio o el periodo sobre el que aplica el saldo
        'type_code_balance': fields.selection([('month','Mensual'),
                                    ('year','Anual'),], 'Tipo codigo Fiscal'),
        'period_id_balance': fields.many2one('account.period', 'Periodo', required=True),
        'fiscalyear_id_balance': fields.many2one('account.fiscalyear', 'Ejercicio de registro'),
        'apply_to': fields.selection([('code','Codigo Fiscal'),
                                    ('tax','Impuesto'),], 'Aplicar a'),
        'tax_code_id': fields.many2one('account.tax.code', 'Impuesto a aplicar'),
        'history_tax_id': fields.many2one('account.tax.code.history.line', 'Historial'),
        'history_tax_value': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        'history_tax_value2': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
    }
    
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
    
    def _get_fiscalyear(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        fiscalyear_id = False
        if period_ids:
           period = self.pool.get('account.period').browse(cr, uid, period_ids[0], context=context)
           fiscalyear_id = period.fiscalyear_id.id
        return fiscalyear_id
    
    _defaults = {
        'period_id': _get_period,
        'fiscalyear_id': _get_fiscalyear,
        'date': fields.datetime.now,
        'type_code': 'period',
        'apply_to': 'code'
    }

account_fiscal_balance_apply_code()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
