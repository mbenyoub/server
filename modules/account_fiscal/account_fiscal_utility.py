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
# Account fiscal utility - Perdida/Utilidad Fiscal
# ---------------------------------------------------------

class account_fiscal_utility(osv.Model):
    _name = 'account.fiscal.utility'
    
    def onchange_utility(self, cr, uid, ids, utility, context=None):
        """
            Actualiza el remanente
        """
        #print "************ utility *********** ", utility
        remnant = 0.0
        if utility < 0.0:
            remnant = utility * -1
            #print "************ remnant ******** ", remnant
        return {'value': {'remnant': remnant}}
    
    def get_config_code_id(self, cr, uid, context=None):
        """
            Obtiene el codigo fiscal que esta configurado para obtener la utilidad fiscal
        """
        code_id = False
        cr.execute(
            """ select id as id, code_id as code_id 
                from account_fiscal_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        #print "************* dat ************ ", dat
        code_id = dat and dat[0]['code_id'] or False
        #print "************ code_id ************** ", code_id
        return code_id or False
    
    def get_config_utility(self, cr, uid, context=None):
        """
            Obtiene la configuracion de los codigos fiscales que afectan la perdida/utilidad
        """
        config_id = False
        res = {
            'code_id': False,
            'result_code_id': False,
            'balance_code_id': False,
            'balance_code_id2': False
        }
        cr.execute(
            """ select id as id
                from account_fiscal_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        #print "************* dat ************ ", dat
        config_id = dat and dat[0]['id'] or False
        #print "************ id ************** ", config_id
        # Obtiene la configuracion de la utilidad
        if config_id:
            config = self.pool.get('account.fiscal.config.settings').browse(cr, uid, config_id, context=context)
            res['code_id'] = config.code_id.id
            res['result_code_id'] = config.result_code_id.id
            res['balance_code_id'] = config.balance_code_id.id
            res['balance_code_id2'] = config.balance_code_id2.id
        return res
    
    def get_value_code(self, cr, uid, code_id, fiscalyear, context=None):
        """
            Retorna el valor del codigo fiscal sobre el ejercicio
        """
        amount = 0.0
        # Obtiene el año fiscal actual sobre el historial
        cr.execute("""
            select
                case when sum(value) <> 0 then sum(value) else 0.0 end as value
            from
                account_fiscal_code_history_line
            where code_id = %s and period_id in (select id from account_period where fiscalyear_id = %s)"""%(code_id,fiscalyear))
        dat = cr.dictfetchall()
        if dat:
            amount = dat and dat[0]['value'] or False
        #print "**************** amount **************** ", amount
        return amount
    
    def get_remnant(self, cr, uid, context=None):
        """
            Obtiene el remanente disponible sobre perdida fiscal
        """
        # Obtiene el año del periodo
        period_id = self.get_period(cr, uid, context=context)
        year = self.get_year_period(cr, uid, period_id, context=context)
        year = year - 10
        remnant = 0.0
        # Obtiene el periodo actual
        util_ids = self.search(cr, uid, [('state','=','open'),('remnant','>',0.0),('fiscalyear','>=',year)], context=context)
        if util_ids:
            for util in self.browse(cr, uid, util_ids, context=context):
                remnant += util.remnant_update
        return remnant
    
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Cambia el estado del documento a abierto o cerrado
        """
        line_obj = self.pool.get('account.fiscal.utility.line')
        amortized_values = {}
        close_ids = []
        
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            # Busca que no se encuentre otro documento para el mismo ejercicio fiscal 
            util_ids = self.search(cr, uid, [('state','in',['open','close']),('fiscalyear', '=', util.fiscalyear)], context=context)
            # Valida si encontro documentos para ese ejercicio fiscal
            if util_ids:
                raise osv.except_osv('Error Validacion', 'Ya existe un documento de Perdida Fiscal con el periodo %s.'%(util.fiscalyear))
            
            # Valida que en el movimiento no haya ejercicios cerrados en las lineas de perdida fiscal
            line_ids = line_obj.search(cr, uid, [('fiscalyear_amortized','=',util.fiscalyear)])
            
            if util.remnant <= 0.0:
                # Recorre los registros de los montos amortizados
                for amortized in util.amortized_ids:
                    amortized_values[amortized.fiscalyear] = amortized.remnant_amortized
            
            # Recorre las lineas de los ejercicios
            for line in line_obj.browse(cr, uid, line_ids, context=context):
                # Valida que la linea no este cerrada
                if line.close == True:
                    if amortized_values.get(line.fiscalyear, False):
                        raise osv.except_osv('Error Validacion', 'El ejercicio %s no se puede aplicar porque la perdida fiscal del ejercicio ya esta cerrada.'%(line.fiscalyear))
                    continue
                # Actualiza el monto a amortizar
                line_obj.write(cr, uid, [line.id], {'close': True, 'remnant_amortized': amortized_values.get(line.fiscalyear, 0.0)}, context=context)
            
            state = 'open'
            # Valida si el registro tiene remanente
            if util.remnant <= 0.0:
                # Cambia el estatus a cerrado
                state = 'close'
            
            balance_id = False
            # Revisa si aplica el saldo fiscal en la utilidad
            if util.utility > 0.0 and util.balance <= 0.0:
                # Registra el saldo fiscal si el saldo es negativo y actualiza el registro de utilidad
                balance = util.balance * -1
                balance_id = self.create_fiscal_balance(cr, uid, balance, context=context)
                self.write(cr, uid, [util.id], {'state': state, 'balance_id': balance_id}, context=context)
            
            # Revisa si aplica el saldo fiscal en la perdida
            if util.utility <= 0.0 and util.balance2 >= 0.0:
                # Registra el saldo fiscal si el saldo es negativo y actualiza el registro de utilidad
                balance = util.balance2
                balance_id = self.create_fiscal_balance(cr, uid, balance, context=context)
                self.write(cr, uid, [util.id], {'state': state, 'balance_id': balance_id}, context=context)
            
            # Revisa si hay documentos sin cerrar y con utilidad en cero
            util_ids = self.search(cr, uid, [('state','in',['open'])], context=context)
            # Valida si encontro documentos para ese ejercicio fiscal
            if util_ids:
                for util in self.browse(cr, uid, util_ids, context=context):
                    if util.remnant == 0:
                        close_ids.append(util.id)
            if len(close_ids) > 0:
                self.write(cr, uid, close_ids, {'state': state}, context=context)
        return True
    
    def action_re_open(self, cr, uid, ids, context=None):
        """
            Cambia el estado a abierto del documento
        """
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            state = 'open'
            # Valida si el registro tiene remanente
            if util.remnant <= 0.0:
                # Cambia el estatus a cerrado
                state = 'close'
            self.write(cr, uid, [util.id], {'state': state}, context=context)
        return True
    
    def get_period(self, cr, uid, context=None):
        """Return default period value"""
        #print "************* get period **************"
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def get_period_ant(self, cr, uid, period_id, context=None):
        """
            Obtiene el valor del periodo anterior
        """
        cr.execute("""
            select
                id
            from
                account_period as p
            where
                extract(year from p.date_start) = (select extract(year from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                and extract(month from p.date_start) = (select extract(month from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                and p.special=False"""%(period_id,period_id))
        period_id = False
        for value in cr.fetchall():
            period_id = value[0]
            break
        return period_id
    
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
    
    def create_fiscal_balance(self, cr, uid, balance, context=None):
        """
            Crea un saldo fiscal sobre el saldo obtenido, de ser negativo y lo carga al impuesto preconfigurado
        """
        balance_id = False
        if balance > 0:
            # Obtiene el codigo fiscal del que se va a obtener la utilidad del ejercicio fiscal
            config = self.get_config_utility(cr, uid, context=context)
            
            # Valida que este registrado el codigo fiscal en la configuracion
            if config['balance_code_id'] == False:
                raise osv.except_osv('Error Validacion', u'Para continuar con la aplicacion, debe tener completa la configuracion de Perdida/Utilidad Fiscal. Revisar en configuracion de Codigos Fiscales ')
            
            # Obtiene del codigo si es anual, mensual y el periodo sobre el que aplica
            code = self.pool.get('account.fiscal.code').browse(cr, uid, config['balance_code_id'], context=context)
            
            type_code = 'year'
            if code.type == 'period':
                type_code = 'month'
            
            # Crea un nuevo registro sobre los saldos fiscales
            balance_id = self.pool.get('account.fiscal.balance').create(cr, uid, {
                'amount': balance,
                'balance': balance,
                'code_id': config['balance_code_id'],
                'type_code': type_code,
                'period_id': code.period_id.id,
                'fiscalyear_id': code.period_id.fiscalyear_id.id,
                'state': 'open',
                'type': 'code'
                }, context=context)
        return balance_id
    
    def update_utility(self, cr, uid, fiscalyear, fiscalyear_id, closed=True, context=None):
        """
            Actualiza la perdida fiscal de los ejercicios fiscales y registra el nuevo ejercicio
        """
        # Obtiene el codigo fiscal del que se va a obtener la utilidad del ejercicio fiscal
        config = self.get_config_utility(cr, uid, context=context)
        
        # Valida que este registrado el codigo fiscal en la configuracion
        if config['code_id'] == False or config['result_code_id'] == False or config['balance_code_id'] == False:
            raise osv.except_osv('Error Validacion', u'Para continuar con la aplicacion, debe tener completa la configuracion de Perdida/Utilidad Fiscal. Revisar en configuracion de Codigos Fiscales ')
        
        # Obtiene la utilidad del ejercicio fiscal, el total a pagar y el saldo
        utility = self.get_value_code(cr, uid, config['code_id'], fiscalyear_id, context=context)
        result = self.get_value_code(cr, uid, config['result_code_id'], fiscalyear_id, context=context)
        balance = self.get_value_code(cr, uid, config['balance_code_id'], fiscalyear_id, context=context)
        balance2 = self.get_value_code(cr, uid, config['balance_code_id2'], fiscalyear_id, context=context)
        
        # Inicializa variables
        line_obj = self.pool.get('account.fiscal.utility.line')
        amortized_obj = self.pool.get('account.fiscal.utility.amortized')
        inpc_obj = self.pool.get('account.fiscal.inpc')
        date = time.strftime('%Y-%m-%d')
        total = utility if utility > 0.0 else 0.0
        state = 'draft'
        close_ids = []
        month = 0
        balance_id = False
        
        # Obtiene el año del periodo
        period_id = self.get_period(cr, uid, context=context)
        year = self.get_year_period(cr, uid, period_id, context=context)
        limit_year = year - 10
        
        # Valida si se cierra el ejercicio fiscal o no
        if closed == True:
            state = 'open'
            # Revisa si aplica el saldo fiscal en la perdida
            if utility > 0.0 and balance < 0.0:
                balance = balance * -1
                # Registra el saldo fiscal si el saldo es negativo
                balance_id = self.create_fiscal_balance(cr, uid, balance, context=context)
            
            # Si la utilidad viene de una perdida revisa si hay saldo en positivo
            if utility < 0.0 and balance2 > 0.0:
                # Registra el saldo fiscal si el saldo es positivo
                balance_id = self.create_fiscal_balance(cr, uid, balance2, context=context)
        
        # Elimina los registros anteriores al documento registrado
        util_ids = self.search(cr, uid, [('state','in',['draft']),('fiscalyear', '=', fiscalyear)], context=context)
        # Valida si encontro documentos para ese ejercicio fiscal
        if util_ids:
            self.unlink(cr, uid, util_ids, context=context)
        line_ids = line_obj.search(cr, uid, [('fiscalyear_amortized', '=', fiscalyear)], context=context)
        # Valida si encontro documentos para ese ejercicio fiscal
        if line_ids:
            line_obj.unlink(cr, uid, line_ids, context=context)
        
        # Valida si se cierra el ejercicio fiscal o no
        if closed == True:
            state = 'open'
        
        # Si la utilidad es negativa registra una nueva perdida fiscal
        if utility < 0:
            values = {
                'fiscalyear': fiscalyear,
                'utility': utility,
                'remnant': utility * -1,
                'total': result,
                'balance': balance,
                'balance2': balance2,
                'state': state,
                'last_fiscalyear': fiscalyear,
                'date': date,
                'date_update': date,
                'balance_id': balance_id
            }
        # Actualiza el registro en base a la perdida fiscal obtenida
        else:
            values = {
                'fiscalyear': fiscalyear,
                'utility': utility,
                'total': result,
                'remnant': 0.0,
                'balance': balance,
                'balance2': balance2,
                'state': state,
                'last_fiscalyear': fiscalyear,
                'date': date,
                'date_update': date,
                'balance_id': balance_id
            }
        
        # Crea el nuevo registro
        util_id = self.create(cr, uid, values, context=context)
        
        # Obtiene el periodo actual
        util_ids = self.search(cr, uid, [('state','=','open')], context=context)
        if util_ids:
            for util in self.browse(cr, uid, util_ids, context=context):
                # Valida que la utilidad sea menor a 10 años o el remanente es igual a cero
                if (util.fiscalyear < limit_year) or util.remnant == 0.0:
                    close_ids.append(util.id)
                    continue
                
                # Valida que esten registrados los necesarios para actualizar la informacion
                if util.last_inpc_id == False or util.next_inpc_id == False:
                    raise osv.except_osv(_('Warning!'),_("Debe tener disponible la informacion de los inpc para poder actualizar el remanente!"))
                
                # Obtiene el mes aplicado en el inpc
                month = util.next_inpc_id.period
                if total > 0.0:
                    # Resta de la perdida actualizada la perdida a amortizar
                    if total < util.remnant_update:
                        # Actualiza la perdida
                        line_id = line_obj.create(cr, uid, {
                            'utility_id': util.id,
                            'remnant_before': util.remnant,
                            'inpc_id1': util.last_inpc_id.id,
                            'inpc_id2': util.next_inpc_id.id,
                            'remnant_amortized': total,
                            'fiscalyear_amortized': fiscalyear,
                            'close': closed}, context=context)
                        # Actualiza el valor amortizado en el documento donde dio positivo
                        amortized_id = amortized_obj.create(cr, uid, {
                            'utility_id': util_id,
                            'remnant_before': util.remnant_update,
                            'remnant_amortized': total,
                            'fiscalyear': util.fiscalyear
                        })
                        total = 0.0
                    # Si el total es mayor o igual actualiza el monto en base a la cantidad disponible
                    elif total >= util.remnant_update:
                        total = total - util.remnant_update
                        #print "************** total ", total, "  - remanente  ", util.remnant_update
                        # Actualiza la perdida
                        line_id = line_obj.create(cr, uid, {
                            'utility_id': util.id,
                            'remnant_before': util.remnant,
                            'inpc_id1': util.last_inpc_id.id,
                            'inpc_id2': util.next_inpc_id.id,
                            'remnant_amortized': util.remnant_update,
                            'fiscalyear_amortized': fiscalyear,
                            'close': closed }, context=context)
                        # Actualiza el valor amortizado en el documento donde dio positivo
                        amortized_id = amortized_obj.create(cr, uid, {
                            'utility_id': util_id,
                            'remnant_before': util.remnant_update,
                            'remnant_amortized': util.remnant_update,
                            'fiscalyear': util.fiscalyear
                        })
                        if closed == True:
                            # Actualiza el remanente del registro
                            self.write(cr, uid, [util.id], {
                                'state': 'close'}, context=context)
                # Actualiza la perdida fiscal
                else:
                    # Actualiza la perdida
                    line_id = line_obj.create(cr, uid, {
                        'utility_id': util.id,
                        'remnant_before': util.remnant,
                        'inpc_id1': util.last_inpc_id.id,
                        'inpc_id2': util.next_inpc_id.id,
                        'remnant_amortized': 0.0,
                        'fiscalyear_amortized': fiscalyear,
                        'close': closed }, context=context)
        
        # Actualiza fecha
        self.write(cr, uid, util_ids, {'date_update': date}, context=context)
        
        if len(close_ids) > 0:
            self.write(cr, uid, close_ids, {'state': 'close'}, context=context)
        
        # Actualiza el total de la utilidad
        #if total > 0.0:
        #    self.write(cr, uid, [util_id], {'total': total}, context=context)
        
        return util_id
    
    def _get_remnant_update(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el remanente actualizado de la perdida del ejercicio
        """
        # Inicializa variables
        inpc_obj = self.pool.get('account.fiscal.inpc')
        inpc_prev = 0.0
        inpc_cur = 0.0
        inpc2 = 0
        next_inpc = False
        update_factor = 0.0
        res = {}
        
        # Obtiene el mes actual y el año del periodo
        period_id = self.get_period(cr, uid, context=context)
        month = self.get_month_period(cr, uid, period_id, context=context)
        year = self.get_year_period(cr, uid, period_id, context=context)
        
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            # Valida que este confirmado el documento para generar el calculo
            if util.state != 'open' and util.state != 'draft':
                res[util.id] = {
                    'remnant_update': 0.0,
                    'next_inpc_id': next_inpc,
                }
                continue
            # Valida que haya utilidad negativa
            if util.utility > 0.0:
                res[util.id] = {
                    'remnant_update': 0.0,
                    'next_inpc_id': next_inpc,
                }
                continue
            # Obtiene el inpc del ejercicio fiscal
            if util.last_fiscalyear >= util.fiscalyear and len(util.line_ids) == 0:
                # Obtiene el inpc de diciembre del año del ejercicio fiscal
                inpc_ids = inpc_obj.search(cr, uid, [('fiscalyear','=',util.fiscalyear),('period','=',12)])
                next_inpc = inpc_ids[0] if inpc_ids else False
            else:
                # Obtiene el inpc de diciembre del año en curso
                inpc_ids = inpc_obj.search(cr, uid, [('fiscalyear','=',util.last_fiscalyear + 1),('period','=',6)])
                next_inpc = inpc_ids[0] if inpc_ids else False
            #print "************** next inpc *********** ", next_inpc
            
            # Valida si el año del ejercicio es igual al actual
            if util.last_fiscalyear >= year:
                res[util.id] = {
                    'remnant_update': util.remnant,
                    'next_inpc_id': next_inpc
                }
            elif util.last_fiscalyear < year:
                if util.last_fiscalyear == year - 1:
                    # Si el mes es menor a junio, deja el monto del remanente actual
                    if month < 6:
                        res[util.id] = {
                            'remnant_update': util.remnant,
                            'next_inpc_id': next_inpc
                        }
                        continue
                #    else:
                #        # Actualiza el valor del inpc sobre el ultimo periodo aplicado y junio del año en curso
                #        inpc2 = next_inpc
                #else:
                #    # Actualiza el valor del inpc sobre el ultimo periodo aplicado y junio del año en curso
                #    inpc2 = inpc_obj.get_inpc(cr, uid, 6, year-1, context=context)
            
            # Valida que esten registrados los inpc
            if next_inpc == False:
                raise osv.except_osv(_('Warning!'),_("Debe tener disponible la informacion de los inpc para poder actualizar el remanente!"))
                
            # Obtiene el valor de los inpc
            inpc_prev = util.last_inpc_id.value or 0.0
            inpc_cur = inpc_obj.get_value(cr, uid, next_inpc, context=context)
            #print "************** inpc_prev ********** ", inpc_prev
            #print "************** inpc_cur ********** ", inpc_cur
            
            # Actualiza el remanente
            if inpc_prev != 0:
                update_factor = inpc_cur/inpc_prev
            #print "************** factor de actualizacion ******* ", update_factor
            #print "************* perdida actualizada - ", util.fiscalyear, " ********* ", util.remnant * update_factor
            res[util.id] = {
                'remnant_update': util.remnant * update_factor,
                'next_inpc_id': next_inpc
            }
        return res
    
    def _get_last_fiscalyear(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el ultimo año de la depreciacion del ejercicio fiscal
        """
        inpc_obj = self.pool.get('account.fiscal.inpc')
        res = {}
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            fiscalyear = False
            have_lines = False
            last_inpc = False
            remnant = 0.0
            # Si tiene utilidad revisa cual es el año siguiente
            if util.utility < 0.0 and (util.state == 'draft' or util.state == 'open', util.state == 'close'):
                num_lines = len(util.line_ids)
                if num_lines > 0:
                    have_lines = True
                    cr.execute(
                        """ select fiscalyear_amortized as fiscalyear, inpc_id2, remnant 
                            from account_fiscal_utility_line where utility_id = %s 
                            order by fiscalyear desc limit 1 """%(util.id,))
                    dat = cr.dictfetchall()
                    #print "************ dat ********* ", dat
                    fiscalyear = dat and dat[0]['fiscalyear'] or False
                    last_inpc = dat and dat[0]['inpc_id2'] or False
                    remnant = dat and dat[0]['remnant'] or 0.0
                    
                if fiscalyear == False:
                    fiscalyear = util.fiscalyear
                if last_inpc == False:
                    remnant = util.utility * -1
                    have_lines = False
                    # Obtiene el inpc de julio del año en curso
                    inpc_ids = inpc_obj.search(cr, uid, [('fiscalyear','=',fiscalyear),('period','=',7)])
                    last_inpc = inpc_ids[0] if inpc_ids else False
            #print "********** remnant ********** ", remnant
            # Actualiza el resultado
            res[util.id] = {
                'last_fiscalyear': fiscalyear,
                'have_lines': have_lines,
                'last_inpc_id': last_inpc,
                'remnant': remnant
            }
        return res
    
    def _get_currency(self, cr, uid, context=None):
        """
            Obtiene la moneda de la compañia por default
        """
        res = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return res
    
    _columns = {
        'date': fields.date('Fecha creacion'),
        'fiscalyear': fields.integer('Ejercicio Fiscal', size=4),
        'utility': fields.float('Utilidad Fiscal', digits=(16,4)),
        #'remnant': fields.float('Remanente', digits=(16,4)),
        'remnant': fields.function(_get_last_fiscalyear, type='float', digits=(16,4), string='Remanente', store=False, multi='lastyear'),
        'total': fields.float('Total Pagado', digits=(16,4)),
        'balance': fields.float('Saldo Fiscal', digits=(16,4)),
        'balance2': fields.float('Saldo Fiscal', digits=(16,4)),
        'state': fields.selection([('draft','Borrador'),
                                    ('open','Abierto'),
                                    ('close','Cerrado'),
                                    ('cancel','Cancelado'),], 'Estado', required=True),
        'line_ids': fields.one2many('account.fiscal.utility.line', 'utility_id', 'Perdida Fiscal', ondelete='cascade'),
        'amortized_ids': fields.one2many('account.fiscal.utility.amortized', 'utility_id', 'Utilidad Fiscal amortizada', ondelete='cascade'),
        'info': fields.text('Comentarios'),
        # Calcular remanente actualizado
        'remnant_update': fields.function(_get_remnant_update, string="Perdida Actualizada", type='float', store=False, multi='rupdate'),
        #'inpc1': fields.function(_get_remnant_update, string="INPC1", type='integer', store=False, multi='rupdate'),
        #'inpc2': fields.function(_get_remnant_update, string="INPC2", type='integer', store=False, multi='rupdate'),
        'next_inpc_id': fields.function(_get_remnant_update, type='many2one', relation='account.fiscal.inpc', string='Siguiente INPC', store=False, multi='rupdate', select=True),
        'date_update': fields.date('Ultima actualizacion'),
        #'last_fiscalyear': fields.integer('Ultimo Ejercicio fiscal', size=4),
        'last_inpc_id': fields.function(_get_last_fiscalyear, type='many2one', relation='account.fiscal.inpc', string='Ultimo INPC aplicado', store=False, multi='lastyear', select=True),
        'last_fiscalyear': fields.function(_get_last_fiscalyear, string="Ultimo Ejercicio fiscal", type='integer', size=4, store=False, multi='lastyear'),
        'have_lines': fields.function(_get_last_fiscalyear, string="Tiene Perdida fiscal", type='boolean', size=4, store=False, multi='lastyear'),
        'currency_id': fields.many2one('res.currency', 'Moneda', readonly=True, track_visibility='always'),
        'balance_id': fields.many2one('account.fiscal.balance', 'Saldo', select=True, ondelete='restrict')
    }
    
    _defaults = {
        'date': fields.date.today,
        'currency_id': _get_currency,
        'state': 'draft'
    }
    
    _order = 'fiscalyear asc'
    
    def action_add_utility(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard para agregar una nueva perdida sobre el registro
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_utility_line_new_view')
        
        # Obtiene la informacion de la utilidad
        util = self.browse(cr, uid, ids[0], context=context)
        fiscalyear = util.last_fiscalyear
        if len(util.line_ids) > 0:
            fiscalyear += 1
        
        cur_year = time.strftime('%Y')
        
        # Valida que el año a agregar no sea el año en curso
        if cur_year == str(fiscalyear):
            raise osv.except_osv('Error Validacion', u'No puede agregar perdidas fiscales sobre el año en curso.')
        
        return {
            'name':_("Agregar Perdida Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.utility.line.new',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_utility_id': util.id,
                'default_fiscalyear_amortized': fiscalyear,
                'default_remnant_before': util.remnant,
                'default_inpc_id1': util.last_inpc_id.id,
                'default_remnant_amortized': 0.0,
                'default_inpc_id2': util.next_inpc_id.id
            }
        }
    
    def create(self, cr, uid, vals, context=None):
        """
            Crea la primera depreciacion sobre el año
        """
        # Funcion original de crear
        res = super(account_fiscal_utility, self).create(cr, uid, vals, context=context)
        
        # Obtiene el primer valor del remanente sobre el año
        line_obj = self.pool.get('account.fiscal.utility.line')
        
        # Obtiene la informacion de la utilidad
        util = self.browse(cr, uid, res, context=context)
        
        if util.utility < 0.0:
            # Agrega el nuevo registro
            values = {
                'utility_id': res,
                'remnant_before': util.remnant,
                'inpc_id1': util.last_inpc_id.id,
                'inpc_id2': util.next_inpc_id.id,
                'fiscalyear_amortized': util.fiscalyear
            }
            #print "**************** values ************** ", values
            line_id = line_obj.create(cr, uid, values, context=context)
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no pueda eliminar registros que no esten en borrador o cancelado
        """
        if type(ids) != list:
            ids = [ids]
        
        #print "**************** funcion unlink ************************** "
        util_ids = self.search(cr, uid, [('state','in',['open','close']),('id','in',ids)], context=context)
        # Valida si encontro documentos para ese ejercicio fiscal
        if util_ids:
            raise osv.except_osv('Error Validacion', u'No se pueden eliminar documentos en estado Abierto o Cerrado.')
        
        # Elimina los registros
        res = super(account_fiscal_utility, self).unlink(cr, uid, ids, context=context)
        return res
    
    def action_apply_utility_lost(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard que aplica la perdida del periodo
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_utility_validate_view')
        
        return {
            'name':_("Aplicar Perdida/Utilidad"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.utility.validate',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {}
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
            if not ids:
                ids = self.search(cr, user, [('fiscalyear', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context or {})
        return self.name_get(cr, user, ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        # Valida que sea un array
        if type(ids) != list:
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = 'Ejercicio ' + str(record.fiscalyear)
            res.append((record.id,name ))
        return res

account_fiscal_utility()

class account_fiscal_utility_line(osv.Model):
    _name = 'account.fiscal.utility.line'
    
    def action_delete_line(self, cr, uid, ids, context=None):
        """
            Elimina la linea del ejercicio de la perdida fiscal
        """
        line = self.read(cr, uid, ids[0], ['utility_id'], context=context)
        line_id = line['utility_id'][0]
        if type(ids) != list:
            ids = [ids]
        self.unlink(cr, uid, ids, context=context)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_utility_form')
        return {
            'name':_("Perdida Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.utility',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : line_id, # id of the object to which to redirected
        }
    
    def _get_remnant(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Obtiene el factor de actualizacion y el remanente actualizado
        """
        res = {}
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            # Calcula el factor de actualizacion
            update_factor = 0.0
            if util.inpc_id1.value != 0.0:
                update_factor = (util.inpc_id2.value/util.inpc_id1.value)
            # Calcula la perdida actualizada
            remnant_update = util.remnant_before * update_factor
            # Calcula el remanente
            remnant = remnant_update - util.remnant_amortized
            
            # Actualiza los resultados
            res[util.id] = {
                'update_factor': update_factor,
                'remnant_update': remnant_update,
                'remnant': remnant
            }
        return res
    
    def _check_modify(self, cr, uid, ids, field_name, arg, context=None):
        """
            Revisa si se puede modificar la linea
        """
        res = {}
        # Recorre los registros
        for util in self.browse(cr, uid, ids, context=context):
            edit = True
            # Valida que el estado del documento no sea cerrado o cancelado
            if util.utility_id.state == 'cancel' or util.utility_id.state == 'close':
                edit = False
            # Valida si se puede modificar
            elif util.close == True:
                edit = False
            elif util.fiscalyear_amortized != util.last_fiscalyear:
                edit = False
            res[util.id] = edit
        return res
    
    _columns = {
        'utility_id': fields.many2one('account.fiscal.utility', 'Perdida/Utilidad', ondelete='cascade', required=True),
        #'fiscalyear': fields.char('Ejercicio Fiscal', size=4),
        'fiscalyear': fields.related('utility_id', 'fiscalyear', type='char', size=4, string='Ejercicio Fiscal', store=True, readonly=True),
        'remnant_before': fields.float('Remanente Anterior', digits=(16,4)),
        'inpc_id1': fields.many2one('account.fiscal.inpc', 'INPC anterior', select=True),
        #'inpc_val1': fields.float('Valor INPC Anterior', digits=(16,4)),
        'inpc_val1': fields.related('inpc_id1', 'value', type='float', digits=(16,4), string='Valor INPC Anterior', store=True, readonly=True),
        'inpc_id2': fields.many2one('account.fiscal.inpc', 'INPC actual', select=True),
        'inpc_val2': fields.related('inpc_id2', 'value', type='float', digits=(16,4), string='Valor INPC Actual', store=True, readonly=True),
        #'inpc_val2': fields.float('Valor INPC Actual', digits=(16,4)),
        'update_factor': fields.function(_get_remnant, type='float', digits=(16,4), string='Factor de Actualizacion', store=True, multi='remnant'),
        'remnant_update': fields.function(_get_remnant, type='float', digits=(16,4), string='Perdida actualizada', store=True, multi='remnant'),
        'remnant_amortized': fields.float('Perdida amortizada', digits=(16,4)),
        'fiscalyear_amortized': fields.integer('Ejercicio Fiscal', size=4),
        'remnant': fields.function(_get_remnant, type='float', digits=(16,4), string='Remanente', store=True, multi='remnant'),
        'date': fields.date('Fecha Actualizacion'),
        'currency_id': fields.related('utility_id', 'currency_id', type='many2one', relation='res.currency', string='Moneda', store=True, readonly=True),
        'last_fiscalyear': fields.related('utility_id', 'last_fiscalyear', type='integer', string='Ultimo año registrado sobre el ejercicio', readonly=True),
        'close': fields.boolean('Ejercicio cerrado', readonly=True),
        'modify': fields.function(_check_modify, type='boolean', string='Valida modificacion')
    }
    
    _order = "fiscalyear_amortized,date"
    
    _defaults = {
        'date': fields.date.today
    }

account_fiscal_utility_line()

class account_fiscal_utility_amortized(osv.Model):
    _name = 'account.fiscal.utility.amortized'
    
    _columns = {
        'utility_id': fields.many2one('account.fiscal.utility', 'Perdida/Utilidad', ondelete='cascade', required=True),
        'fiscalyear': fields.integer('Ejercicio Fiscal', size=4),
        'remnant_before': fields.float('Remanente Anterior', digits=(16,4)),
        'remnant_amortized': fields.float('Utilidad aplicada', digits=(16,4)),
    }
    
    _order = "fiscalyear"

account_fiscal_utility_amortized()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
