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
# Account fiscal Rate - Indices Fiscales
# ---------------------------------------------------------

class account_fiscal_rate(osv.Model):
    _name = 'account.fiscal.rate'
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        #print "************* get period **************"
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def _get_period_ant(self, cr, uid, period_id, context=None):
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
        return month
    
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
    
    def _get_fiscalyear(self, cr, uid, period_id, apply='current', context=None):
        """
            Obtiene el ejercicio fiscal ya sea del año actual o anterior
        """
        fiscalyear_id = 0
        if apply == 'prev':
            cr.execute("""
                select
                        id
                    from
                        account_fiscalyear
                    where extract(year from date_start) = (select extract(year from (date_start - interval '1 year')) from account_period where id = %s)"""%(period_id))
            for value in cr.fetchall():
                fiscalyear_id = value[0]
                break
            #print "*********** fiscalyear prev *********** ", fiscalyear_id
        else:
            # Obtiene el id del año fiscal y la fecha inicial del periodo
            period = self.pool.get('account.period').read(cr, uid, period_id, ['fiscalyear_id','date_start'], context=context)
            fiscalyear_id = period['fiscalyear_id'][0]
            #print "*************** period ********** ", period
            #print "*************** fiscalyear_id ********** ", fiscalyear_id
        return fiscalyear_id
    
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
    
    def _get_asset_values(self, cr, uid, fiscalyear_id, type_asset='all', context=None):
        """
            Obtiene el valor total sobre los activos en el ejercicio fiscal
        """
        asset_obj = self.pool.get('account.asset.asset')
        result = 0.0
        ids = []
        where = ""
        # Valida si se obtienen los activos vendidos o no vendidos
        if type_asset == 'sold':
            where = """ and a.state = 'sold' and extract(year from a.sale_date) <=
                    (select extract(year from date_start) from account_fiscalyear where id=%s)"""%(fiscalyear_id,)
        elif type_asset == 'open':
            where = """ and (a.sale_date is Null or extract(year from a.sale_date) >
                    (select extract(year from date_start) from account_fiscalyear where id=%s))"""%(fiscalyear_id,)
        
        # Obtiene el listado de los activos disponibles sobre el año o anteriores
        cr.execute("""
            select id
                from account_asset_asset as a 
                where
                    extract(year from a.purchase_date) <=
                    (select extract(year from date_start) from account_fiscalyear where id=%s) %s """%(fiscalyear_id, where))
        for value in cr.fetchall():
            ids.append(value[0])
        
        # Valida que se hayan encontrado registros
        if not ids:
            return result
        
        # Recorre los registros
        for asset in asset_obj.browse(cr, uid, ids, context=context):
            # Obtiene el valor fiscal del activo sobre el ejercicio (Solo si no fue vendido o cerrado varia el proceso)
            amount = asset_obj.get_value_fiscal(cr, uid, asset.id, fiscalyear_id, context=context)
            result += amount
        return result
    
    def get_value_code_cumulative(self, cr, uid, period_id, fiscalyear, code_id, apply_year=False, context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal
        """
        # Valida si el codigo fiscal es de tipo anual
        code_year = self.pool.get('account.fiscal.code').code_is_year(cr, uid, code_id, context=context)
        apply_year = code_year if code_year == True else apply_year
        
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el año fiscal anterior
            cr.execute("""
                select
                    case when sum(value) <> 0 then sum(value) else 0.0 end as value
                from
                    account_fiscal_code_history_line
                where code_id = %s and period_id in (select id from account_period where fiscalyear_id = %s)"""%(code_id,fiscalyear))
        else:
            # Obtiene la fecha inicial del periodo
            period = self.pool.get('account.period').read(cr, uid, period_id, ['date_start'], context=context)
            date = period['date_start']
            
            # Obtiene los anterior al periodo sobre el año fiscal
            cr.execute("""
                select
                    case when sum(value) <> 0 then sum(value) else 0.0 end as value
                from
                    account_fiscal_code_history_line
                where code_id = %s and period_id in (select id from account_period where date_start < '%s' and fiscalyear_id = %s)"""%(code_id,date,fiscalyear))
        amount = 0.0
        for value in cr.fetchall():
            amount = value[0]
            break
        #print "**************** amount **************** ", amount
        return amount
    
    def get_value_code_period(self, cr, uid, period_id, fiscalyear, code_id, apply='current', apply_year=False, context=None):
        """
            Retorna el valor de los movimientos anteriores sobre periodo o por año del rubro fiscal
        """
        # Valida si el codigo fiscal es de tipo anual
        code_year = self.pool.get('account.fiscal.code').code_is_year(cr, uid, code_id, context=context)
        apply_year = code_year if code_year == True else apply_year
        
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el id del año fiscal y la fecha inicial del periodo
            #period = self.pool.get('account.period').read(cr, uid, period_id, ['fiscalyear_id','date_start'], context=context)
            #fiscalyear = period['fiscalyear_id']
            
            # Obtiene el año fiscal actual sobre el historial
            cr.execute("""
                select
                    case when sum(value) <> 0 then sum(value) else 0.0 end as value
                from
                    account_fiscal_code_history_line
                where code_id = %s and period_id in (select id from account_period where fiscalyear_id = %s)"""%(code_id,fiscalyear))
        else:
            # Obtiene el valor del periodo actual sobre el historial
            cr.execute("""
                select
                    case when sum(l.value) <> 0 then sum(l.value) else 0.0 end as value
                from
                    account_fiscal_code_history_line as l
                    inner join account_period as p on l.period_id=p.id
                where l.code_id = %s
                    and period_id = %s
                    and p.special=False"""%(code_id,period_id))
        amount = 0.0
        for value in cr.fetchall():
            amount = value[0]
            break
        #print "**************** amount **************** ", amount
        return amount
    
    def get_value_account_period(self, cr, uid, base, period_id, fiscalyear, category_id, apply_year=False, target_move='posted', context=None):
        """
            Retorna el valor del periodo sobre los movimientos del rubro fiscal
        """
        get_asset = ''
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el id del año fiscal
            #period = self.pool.get('account.period').read(cr, uid, period_id, ['fiscalyear_id'], context=context)
            #fiscalyear = period['fiscalyear_id']
            #print "******** fiscalyear rubro fiscal *********** ", fiscalyear
            # Obtiene el resultado de movimientos sobre el año fiscal
            cr.execute("""
                select
                    case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                    case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,category_id,fiscalyear))
        else:
            cr.execute("""
                select
                    case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                    case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
        for credit, debit in cr.fetchall():
            res = {
                'debit': debit,
                'credit': credit
            }
            break;
        
        #print "**************** res *************** ", res
        amount = 0.0
        if base == 'debit':
            amount = res['debit']
        elif base == 'credit':
            amount = res['credit']
        elif base == 'dif':
            amount = res['debit'] - res['credit']
        else:
            amount = res['credit'] - res['debit']
        return amount
    
    def get_value_account_cumulative(self, cr, uid, base, period_id, fiscalyear, category_id, apply_year=False, target_move='posted', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha del periodo sobre el rubro fiscal
        """
        get_asset = ''
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        
        # Obtiene el id del año fiscal y la fecha inicial del periodo
        period = self.pool.get('account.period').read(cr, uid, period_id, ['fiscalyear_id','date_start'], context=context)
        #fiscalyear = period['fiscalyear_id']
        date = period['date_start']
        
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el año fiscal anterior
            cr.execute("""
                select
                    case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                    case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,category_id,fiscalyear))
        else:
            cr.execute("""
                select
                    case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                    case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where l.date < '%s' and r.category_id = %s  and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,date,category_id,fiscalyear))
        for credit, debit in cr.fetchall():
            res = {
                'debit': debit,
                'credit': credit
            }
            break;
        
        #print "**************** res *************** ", res
        amount = 0.0
        if base == 'debit':
            amount = res['debit']
        elif base == 'credit':
            amount = res['credit']
        elif base == 'dif':
            amount = res['debit'] - res['credit']
        else:
            amount = res['credit'] - res['debit']
        return amount
    
    def _check_code_condition(self, cr, uid, condition, result, operator, value):
        """
            Valida si la condicion es verdadera o falsa segun el operador
        """
        res = False
        # Compara operadores
        if operator == '=' and result == value:
            res = True
        elif operator == '<>' and result <> value:
            res = True
        elif operator == '>' and result > value:
            res = True
        elif operator == '>=' and result >= value:
            res = True
        elif operator == '<' and result < value:
            res = True
        elif operator == '<=' and result <= value:
            res = True
        # Valida si hay operador
        if not operator:
            res = True
        return res
    
    def action_update(self, cr, uid, ids, context=None):
        """
            Actualiza el resultado del registro
        """
        date = time.strftime('%Y-%m-%d')
        self.write(cr, uid, ids, {'date': date}, context=context)
        return True
    
    def _get_value_rate(self, cr, uid, ids, field, arg, context=None):
        """
            Calcula el valor del Indice fiscal
        """
        result = {}
        # Inicializa valores
        for id in ids:
            result[id] = 0.0
        
        # Obtiene el periodo actual
        period_id = self._get_period(cr, uid, context=context)
        fiscalyear_id = self._get_fiscalyear(cr, uid, period_id, apply='current', context=context)
        # Obtiene el periodo anterior
        period_ant_id = self._get_period_ant(cr, uid, period_id, context=context)
        fiscalyear_ant_id = self._get_fiscalyear(cr, uid, period_ant_id, apply='prev', context=context)
        #print "************** periodo *************** ", period_id
        #print "*********** periodo ant ************** ", period_ant_id
        
        # Recorre los codigos de todos registros
        rate_ids = self.search(cr, uid, [('type_rate','=','view'),('id','in',ids)])
        #print "******************** rate ids **************** ", rate_ids
        for rate in self.browse(cr, uid, rate_ids, context=context):
            # Verifica si es un proceso manual o calculado
            if rate.mode == 'manual':
                result[rate.id] = rate.value
            else:
                apply_condition = False
                count = 1
                # Recorre los hijos del indice
                for child in rate.child_ids:
                    if child.type_rate != 'asset':
                        # Obtiene el parametro del periodo periodo segun sea el caso
                        if child.apply == 'current':
                            p_id = period_id
                        elif child.apply == 'prev':
                            p_id = period_ant_id
                        elif child.apply == 'esp':
                            if child.period_id:
                                p_id = child.period_id.id
                        
                        # Obtiene el año fiscal segun sea el caso
                        if child.apply_year == True:
                            if child.apply == 'prev':
                                fyear = fiscalyear_ant_id
                            elif child.apply == 'esp':
                                fyear = self._get_fiscalyear(cr, uid, p_id, apply='current', context=context)
                            else:
                                fyear = fiscalyear_id
                        else:
                            fyear = fiscalyear_id
                        
                        #print "*************+ fyear ************ ", fyear
                    
                    amount = 0.0
                    # Obtiene el resultado del acumulador
                    if child.type_rate == 'acf_period':
                        #print "***************** reference ************ ", child.reference
                        amount = self.get_value_account_period(cr, uid, child.base, p_id, fyear, child.reference.id, child.apply_year, context=context)
                    elif child.type_rate == 'acf_cumulative':
                        amount = self.get_value_account_cumulative(cr, uid, child.base, p_id, fyear, child.reference.id, child.apply_year, context=context)
                    elif child.type_rate == 'code_period':
                        amount = self.get_value_code_period(cr, uid, p_id, fyear, child.reference.id, child.apply_year, context=context)
                    elif child.type_rate == 'code_cumulative':
                        amount = self.get_value_code_cumulative(cr, uid, p_id, fyear, child.reference.id, child.apply_year, context=context)
                    elif child.type_rate == 'frate':
                        if child.reference and child.reference.id:
                            #print "********monto frate *********** ", child.reference.result
                            amount = child.reference.result
                            # Cambiar a result
                    elif child.type_rate == 'inpc':
                        if child.apply == 'prev' or child.apply == 'current':
                            amount = self.get_inpc_value(cr, uid, p_id, context=context)
                        else:
                            amount = child.inpc_id.value
                    elif child.type_rate == 'val':
                        amount = child.value
                    elif child.type_rate == 'per':
                        amount = self._get_month_period(cr, uid, p_id, context=context)
                    elif child.type_rate == 'utility':
                        amount = self.pool.get('account.fiscal.utility').get_remnant(cr, uid, context)
                    elif child.type_rate == 'asset':
                        # Obtiene el año fiscal segun sea el caso
                        if child.apply == 'prev':
                            fyear = fiscalyear_ant_id
                        elif child.apply == 'esp':
                            fyear = child.fiscalyear_id.id
                        else:
                            fyear = fiscalyear_id
                            
                        # Obtiene el valor de los activos sobre el periodo
                        amount = self._get_asset_values(cr, uid, fyear, child.type_asset, context=context)
                        
                    # Guarda el resultado
                    result[child.id] = amount
                    
                    # Valida si tiene que aplicar alguna condicion sobre el valor ya calculado
                    if child.if_apply == True and child.type_rate != 'view':
                        # Valida que la condicion aplique en el resultado 
                        if child.condition == 'if':
                            # Hace que deje la condicion por aplicar
                            apply_condition = True
                        elif child.condition == 'else' and apply_condition == False:
                            continue
                        
                        condition = child.condition
                        if child.condition_res == 'res':
                            condition_res = amount
                        elif child.condition_res == 'cum':
                            condition_res = result[rate.id]
                        elif child.condition_res == 'per':
                            condition_res = self._get_month_period(cr, uid, p_id, context=context)
                        else:
                            condition_res = self._get_num_period_fiscalyear(cr, uid, fyear, context=context)
                        operator = child.operator 
                        if child.condition_type == 'val':
                            condition_val = child.condition_value
                        elif child.condition_type == 'res':
                            condition_val = amount
                        elif child.condition_type == 'per':
                            condition_val = self._get_month_period(cr, uid, p_id, context=context)
                        else:
                            condition_val = self._get_num_period_fiscalyear(cr, uid, fyear, context=context)
                        # Realiza la validacion de campos
                        condition = self._check_code_condition(cr, uid, condition, condition_res, operator, condition_val)
                        # Valida la condicion
                        if condition == False:
                            # Continua con la siguiente condicion
                            continue
                        else:
                            # Se pone como aplicada la condicion
                            apply_condition = False
                    # Si no hay condicion continua con el proceso
                    else:
                        apply_condition = False
                    
                    # Actualiza el resultado
                    if count == 1:
                        result[rate.id] = amount
                        count += 1
                    else:
                        #print "************* child name ************ ", child.name, " -  ", child.type_rate
                        if child.factor == 'sum':
                            #print "**************** amount sum ********** ", result[rate.id], " + ", amount
                            result[rate.id] += amount
                        elif child.factor == 'res':
                            #print "**************** amount res ********** ", result[rate.id], " - ", amount
                            result[rate.id] -= amount
                        elif child.factor == 'mul':
                            #print "**************** amount mul ********** ", result[rate.id], " * ", amount
                            result[rate.id] = result[rate.id] * amount
                        elif child.factor == 'div' and amount == 0:
                            result[rate.id] = 0.0
                        elif child.factor == 'div':
                            #print "**************** amount div ********** ", result[rate.id], " / ", amount
                            result[rate.id] = result[rate.id] / amount
            # Valida el indice fiscal
            if rate.if_apply:
                condition = self._check_code_condition(cr, uid, 'if', result[rate.id], rate.operator, rate.condition_value)
                if condition:
                    amount = 0.0
        return result
    
    _columns = {
        # Informacion de Indices fiscales
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32),
        'sequence': fields.integer('Orden', help="Orden en el que se ejecutaran los calculos"),
        'parent_id': fields.many2one('account.fiscal.rate','Indice Fiscal', select="1", ondelete='set null', domain=[('type_rate','=','view')]),
        'child_ids': fields.one2many('account.fiscal.rate', 'parent_id', 'Indices Fiscales', ondelete='cascade'),
        'date': fields.date('Ultima actualizacion'),
        'mode': fields.selection([
                        ('manual','Manual'),
                        ('calc','Calculado')], 'Modo', required=True),
        'value': fields.float('Valor', digits=(16,12)),
        'description': fields.text('Descripcion'),
        'type_rate': fields.selection([
                        ('view','Vista'),
                        ('acf_period','Rubro Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_period','Codigo Fiscal'),
                        ('frate','Indice Fiscal'),
                        ('inpc','INPC'),
                        ('asset','Activo Fijo'),
                        ('utility','Perdida Fiscal'),
                        ('per','No. Mes Periodo'),
                        ('val','Valor')], 'Tipo Codigo', required=True),
        # Obtencion de valores para acumuladores especificos
        'period_id': fields.many2one('account.period','Periodo', select="1"),
        'fiscalyear_id': fields.many2one('account.fiscalyear','Ejercicio Fiscal', select="1"),
        'type_asset': fields.selection([
                        ('sold','Vendido'),
                        ('open','No Vendido'),
                        ('all','Obtener Todo')], 'Obtener Activo'),
        'inpc_id': fields.many2one('account.fiscal.inpc', 'INPC', select=True),
        # Campos para obtencion valores calculados
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division')], 'Factor'),
        'base': fields.selection([
                        ('debit','Debe'),
                        ('credit','Haber'),
                        ('value','Valor'),
                        ('dif','Debe - Haber'),
                        ('dif2','Haber - Debe')], 'Calculo base'),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True, ondelete='restrict'),
        'code_year': fields.boolean('Codigo Fiscal Anual'),
        # Aplicacion sobre periodo o año para campos calculados
        'apply_year': fields.boolean('Obtener por año'),
        'apply': fields.selection([
                        ('prev','Anterior'),
                        ('current','Actual'),
                        ('esp','Especifico')], 'Aplicar'),
        'apply_prev': fields.float('Anterior a'),
        # Aplicar condiciones
        'if_apply': fields.boolean('Aplicar condicion'),
        'condition': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'condition_res': fields.selection([
                        ('res','Resultado'),
                        ('cum','Valor acumulado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], 'condicion valor'),
        'operator': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_type': fields.selection([
                        ('val','Valor'),
                        ('res','Resultado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], 'condicion valor'),
        'condition_value': fields.float('Valor'),
        # Historial
        'log_ids': fields.one2many('account.fiscal.rate.log', 'rate_id', 'Historial', ondelete='cascade', readonly=True),
        'result': fields.function(_get_value_rate, type='float', digits=(16,12), string='Monto', store=True),
    }
    _order = 'sequence,name'
    
    _defaults = {
        'date': fields.datetime.now,
        'mode': 'manual',
        'sequence': 0,
        'factor': 'sum',
        'base': 'value',
        'type_rate': 'view',
        'apply': 'current',
        'if_apply': False,
        'condition_type': 'val',
        'value': 0.0,
        'operator': '='
    }
    
    def action_add_rate(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con las opciones para generar calculos en los indices fiscales
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_rate_child_view')
        
        return {
            'name':_("Indice Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.rate.child',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_parent_id': ids[0]
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
            ids = self.search(cr, user, [('code', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
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
        for record in self.read(cr, uid, ids, ['name','code'], context=context):
            name = record['code'] + '- ' + record['name'] if record['code'] else record['name']
            res.append((record['id'],name ))
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza los registros del historial
        """
        # Recorre los registros
        for rate in self.browse(cr, uid, ids, context=context):
            # Si es un indice fiscal actualiza el historial
            if rate.type_rate == 'view':
                values = {
                    'rate_id': rate.id,
                    'date': rate.date,
                    'value': rate.result
                }
                # Crea un nuevo registro
                log_id = self.pool.get('account.fiscal.rate.log').create(cr, uid, values, context=context)
        
        # Si no trae la fecha de actualizacion la actualiza
        if vals.get('date',False) == False:
            vals['date'] = time.strftime('%Y-%m-%d')
        
        # Funcion original de modificar
        super(account_fiscal_rate, self).write(cr, uid, ids, vals, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no este relacionado con un codigo fiscal
        """
        #print "**************** funcion unlink ************************** "
        
        #Recorre los registros a eliminar
        for id in ids:
            reference = 'account.fiscal.rate,' + str(id)
            #~ Valida que el presupuesto a borrar no se encuentre en estado validado
            cr.execute("""
                        select id 
                        from account_fiscal_code
                        where reference ='%s'"""%(reference,))
            if cr.fetchone():
                raise osv.except_osv(_('Error!'),_("No se puede eliminar el indice fiscal porque esta relacionado con codigos fiscales!"))
        
        return super(account_fiscal_rate, self).unlink(cr, uid, ids, context=context)

account_fiscal_rate()

class account_fiscal_rate_log(osv.Model):
    """ Registro de Bitacora sobre contabilidad fiscal """
    _name = 'account.fiscal.rate.log'
    
    _columns = {
        'rate_id': fields.many2one('account.fiscal.rate','Indice Fiscal', select="1", ondelete='cascade', required=True),
        'name': fields.related('rate_id', 'name', type='char', string='Nombre', store=True, readonly=True),
        'code': fields.related('rate_id', 'code', type='char', string='Codigo', store=True, readonly=True),
        'mode': fields.related('rate_id', 'mode', type='selection', selection=[('manual','Manual'),('calc','Calculado')], string='Tipo', store=True, readonly=True),
        'date': fields.date('Fecha'),
        'period_id': fields.related('rate_id', 'period_id', type='many2one', relation='account.period', string='Periodo', store=True, readonly=True),
        'value': fields.float('Valor', digits=(16,4)),
    }
    _order = 'date desc'
    
    _defaults = {
        'date': fields.datetime.now,
        'value': 0.0
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
            ids = self.search(cr, user, [('code', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
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
        for record in self.read(cr, uid, ids, ['name','code'], context=context):
            name = record['code'] + '- ' + record['name'] if record['code'] else record['name']
            res.append((record['id'],name ))
        return res
    
account_fiscal_rate_log()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
