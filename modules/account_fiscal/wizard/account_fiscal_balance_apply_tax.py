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

class account_fiscal_balance_apply_tax(osv.osv_memory):
    """ Aplicar Saldo a impuesto """
    _name = 'account.fiscal.balance.apply.tax'
    _description = 'Aplicar Saldo a impuesto'
    
    def onchange_lines(self, cr, uid, ids, line_ids, context=None):
        """
            Recalcula los montos por pagar de las lineas
        """
        history_obj = self.pool.get('account.tax.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        lines = []
        vals = {}
        
        for reg in line_ids:
            line = reg[2]
            #print "**************** line ************* ", line
            if line:
                if line['apply']:
                    # Valida que el monto no sea mayor al monto  por pagar
                    if line['history_value2'] < line['amount']:
                        raise osv.except_osv('Error Validacion', u'El monto no puede ser mayor al monto por pagar.')
                    # Actualiza que el valor del monto a pagar si hay codigos repetidos
                    if vals.get(line['tax_code_id'], False):
                        line['history_value'] = line['history_value2'] - vals.get(line['tax_code_id'], 0.0)
                        vals[line['tax_code_id']] += line['amount']
                        # Valida que el monto pagado sea menor al monto por pagar
                        if line['history_value2'] < vals.get(line['tax_code_id'],0.0):
                            raise osv.except_osv('Error Validacion', u'El monto no puede ser mayor al monto por pagar.')
                    else:
                        vals[line['tax_code_id']] = line['amount']
                else:
                    # Revisa si ya se aplico un monto sobre el codigo
                    if vals.get(line['tax_code_id'], False):
                        line['history_value'] = line['history_value2'] - vals.get(line['tax_code_id'], 0.0)
                    else:
                        line['history_value'] = line['history_value2']
                lines.append(line)
        
        return {'value': {'line_ids': lines}}
    
    def onchange_period_id(self, cr, uid, ids, period_id, context=None):
        """
            Obtiene los saldos sobre el periodo
        """
        history_obj = self.pool.get('account.tax.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        lines = []
        #print "***************** period_id *************** ", period_id
        
        if context.get('update',False) and context.get('default_period_id',False) == period_id:
            return {'value': {'line_ids': context.get('default_line_ids',[])}}
        
        if period_id:
            # Obtiene el monto del codigo de impuesto
            balance_ids = balance_obj.search(cr, uid, [('state','=','open'),('type','=','tax'),('balance','>',0.0)], context=context)
            #print "*************** balance_ids ************* ", balance_ids
            if balance_ids:
                # Busca los saldos pendientes sobre el periodo
                for balance in balance_obj.browse(cr, uid, balance_ids, context=context):
                    #print "**************** periodo ************** ", balance.period_id, ' > ', period_id
                    if balance.period_id:
                        # Valida que el periodo sea menor
                        check = balance_obj.validate_period_apply(cr, uid, period_id, balance.period_id.id, context=context)
                        #print "**************** check ***************** ", check
                        if check == False:
                            continue
                    # Obtiene el valor del historico del periodo
                    history_id = history_obj.get_code_tax_period(cr, uid, balance.tax_code_id.id, period_id, context=context)
                    #print "*************** codigo ************* ", balance.tax_code_id.id
                    #print "**************** balance ", balance.name, "  ********* ", balance.tax_code_id.name
                    
                    #print "******************* history_id **************** ", history_id
                    if not history_id:
                        raise osv.except_osv('Error Validacion', u'No esta registrado el codigo %s sobre el periodo seleccionado.'%(balance.tax_code_id.name,))
                    # Actualiza la informacion sobre los registros
                    history = history_obj.read(cr, uid, history_id, ['sum_period'], context=context)
                    
                    #print "*************** history ************** ", history
                    amount = 0.0
                    # Obtiene el valor del monto
                    if history['sum_period'] <= 0.0:
                        amount = 0.0
                    elif balance.balance_update >= history['sum_period']:
                        amount = history['sum_period']
                    else:
                        amount = balance.balance_update
                    
                    values = {
                        'apply': False,
                        'tax_code_id': balance.tax_code_id.id,
                        'period_id': period_id,
                        'period_id_apply': balance.period_id.id,
                        'balance_id': balance.id,
                        'balance_update': balance.balance_update,
                        'history_id': history_id,
                        'history_value': history['sum_period'],
                        'history_value2': history['sum_period'],
                        'amount': amount
                    }
                    
                    #print "************** values ************ ", values
                    
                    lines.append(values)
        #print "*********** lines *************** ", lines
        return {'value': {'line_ids': lines}}
    
    def action_update_lines(self, cr, uid, ids, context=None):
        """
            Actualiza el valor
        """
        cont = 0
        val = self.browse(cr, uid, ids[0], context=context)
        
        history_obj = self.pool.get('account.tax.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        lines = []
        vals = {}
        
        if val.line_ids:
            for reg in val.line_ids:
                line = {
                    'apply': reg.apply,
                    'tax_code_id': reg.tax_code_id.id,
                    'period_id': reg.period_id.id,
                    'period_id_apply': reg.period_id_apply.id,
                    'balance_id': reg.balance_id.id,
                    'balance_update': reg.balance_update,
                    'history_id': reg.history_id.id,
                    'history_value': reg.history_value,
                    'history_value2': reg.history_value2,
                    'amount': reg.amount
                }
                
                #print "**************** line ************* ", line
                if line:
                    if line['apply']:
                        # Valida que el monto no sea mayor al monto  por pagar
                        if line['history_value2'] < line['amount']:
                            raise osv.except_osv('Error Validacion', u'El monto no puede ser mayor al monto por pagar.')
                        # Actualiza que el valor del monto a pagar si hay codigos repetidos
                        if vals.get(line['tax_code_id'], False):
                            line['history_value'] = line['history_value2'] - vals.get(line['tax_code_id'], 0.0)
                            vals[line['tax_code_id']] += line['amount']
                            # Valida que el monto pagado sea menor al monto por pagar
                            if line['history_value2'] < vals.get(line['tax_code_id'],0.0):
                                raise osv.except_osv('Error Validacion', u'El monto no puede ser mayor al monto por pagar.')
                        else:
                            vals[line['tax_code_id']] = line['amount']
                    else:
                        # Revisa si ya se aplico un monto sobre el codigo
                        if vals.get(line['tax_code_id'], False):
                            line['history_value'] = line['history_value2'] - vals.get(line['tax_code_id'], 0.0)
                        else:
                            line['history_value'] = line['history_value2']
                    lines.append(line)
        
        # return {'value': {'line_ids': lines}}
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
                'default_period_id': val.period_id.id,
                'default_date': val.date,
                'default_line_ids': lines,
                'update': True
            }
        }
    
    def action_balance_apply(self, cr, uid, ids, context=None):
        """
            Genera aplicacion sobre el saldo
        """
        #print "***************** applicar saldo impuesto ***************** "
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
            # Revisa si tiene saldos para aplicar
            if apply.line_ids:
                #print "************** line_ids *************** ", apply.line_ids
                # Recorre los registros para aplicar los saldos
                for line in apply.line_ids:
                    #print "*************** line_applly ********** ", line.apply
                    if line.apply:
                        # Valida que el monto no sea mayor al monto por pagar
                        if line.history_value < line.amount:
                            raise osv.except_osv('Error Validacion', u'El saldo aplicado es mayor que el monto por pagar del codigo %s.'%(line.tax_code_id.name,))
                        # Valida que el monto no sea mayor al saldo actual
                        if line.balance_update < line.amount:
                            raise osv.except_osv('Error Validacion', u'El saldo disponible es menor que el monto por pagar del codigo %s.'%(line.tax_code_id.name,))
                        # Valida que el monto no sea negativo
                        if line.amount <= 0.0:
                            raise osv.except_osv('Error Validacion', u'El monto del codigo %s no puede ser negativo o cero.'%(line.tax_code_id.name,))
                        
                        # Valida que el periodo a aplicar sea menor al periodo actual
                        if line.balance_id.period_id:
                            check = balance_obj.validate_period_apply(cr, uid, line.period_id.id, line.balance_id.period_id.id, context=context)
                            if check == False:
                                raise osv.except_osv('Error Validacion', u'El periodo del saldo debe ser menor que el periodo donde se aplica el saldo (Periodo: %s).'%(line.balance_id.period_id.name,))
                        
                        name = 'Aplicacion saldo -' + line.tax_code_id.name
                        if line.balance_id.period_id:
                            name = name + ' - ' + str(line.balance_id.period_id.name)
                        
                        #print "************* saldo ", name, " valido *************** "
                        
                        # Actualiza el resultado sobre el historial de impuestos
                        hline_id = hline_obj.create(cr, uid, {
                            'name': name,
                            'history_id': line.history_id.history_id.id,
                            'code_id': line.tax_code_id.id,
                            'company_id': line.history_id.company_id.id,
                            'sequence': 0,
                            'percent': 0,
                            'sum_period': line.amount * -1,
                            'sum_year': 0.0,
                            'base_period': 0.0,
                            'base_year': 0.0,
                            'parent_id': line.history_id.id,
                            'apply_balance': True}, context=context)
                        
                        history = line.history_id
                        n = 1
                        while(n == 1):
                            # Actualiza el resultado
                            hline_obj.write(cr, uid, [history.id], {'sum_period': history.sum_period - line.amount}, context=context)
                            
                            # Actualiza el resultado de los registros del historial
                            if history.parent_id:
                                history = history.parent_id
                            else:
                                n = 0
                        
                        # Marca en el historial que hay registros sobre el saldo
                        history_obj.write(cr, uid, [line.history_id.history_id.id], {'cont': line.history_id.history_id.cont+1}, context=context)
                        
                        reference = 'account.tax.code.history.line,' + str(hline_id)
                        reference2 = 'account.tax.code.history.line,' + str(line.history_id.id)
                        
                        # Agrega un registro en las lineas del saldo fiscal
                        bline_id = bline_obj.create(cr, uid, {
                            'balance_id': line.balance_id.id,
                            'period_id': line.period_id.id,
                            'balance_before': line.balance_id.balance,
                            'amount': line.amount,
                            'type': 'apply',
                            'next_inpc_id': line.balance_id.next_inpc_id.id,
                            'last_inpc_id': line.balance_id.last_inpc_id.id,
                            'inpc': line.balance_id.inpc.id,
                            'state': 'done',
                            'reference': reference,
                            'reference2': reference2}, context=context)
                        #print "**************** bline_id ***************** ", bline_id
                        
                        balance_id = line.balance_id.id
                        
        # Si no se aplico ningun saldo solo cierra el wizard
        if not balance_id:
            #print "****************** return True ************** "
            return True
        
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
        #'amount': fields.float('Monto', digits_compute=dp.get_precision('Account'), help="Monto a Devolver"),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'line_ids': fields.one2many('account.fiscal.balance.apply.tax.line', 'apply_id', 'Saldos a aplicar', ondelete='cascade'),
        'date': fields.date('Fecha'),
        #'cont': fields.integer('Valor')
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
    
    _defaults = {
        'period_id': _get_period,
        'date': fields.datetime.now,
        #'con': 0
    }

account_fiscal_balance_apply_tax()

class account_fiscal_balance_apply_tax_line(osv.osv_memory):
    """ Aplicar Saldos sobre impuestos """
    _name = 'account.fiscal.balance.apply.tax.line'
    _description = 'Aplicar Saldo a impuesto'
    
    _columns = {
        'apply_id': fields.many2one('account.fiscal.balance.apply.tax', 'Aplicacion de Saldo', ondelete='cascade'),
        'tax_code_id': fields.many2one('account.tax.code', 'Codigo de Impuesto'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo Fiscal'),
        'balance_update': fields.float('Saldo actual', digits_compute=dp.get_precision('Account'), help="Saldo disponible"),
        'period_id_apply': fields.many2one('account.period', 'Periodo'),
        'history_id': fields.many2one('account.tax.code.history.line', 'Historial'),
        'history_value': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        'history_value2': fields.float('Por pagar', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account'), help="Monto a Devolver"),
        'apply': fields.boolean('Aplicar')
    }
    
    _defaults = {
        'amount': 0.0,
        'balance_update': 0.0
    }

account_fiscal_balance_apply_tax_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
