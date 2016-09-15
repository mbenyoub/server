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
# Account fiscal - Codigos Fiscales
# ---------------------------------------------------------

class account_fiscal_code(osv.Model):
    _name = 'account.fiscal.code'
    
    def action_view_deduction_ref(self, cr, uid, ids, context=None):
        """
            Redirecciona al detalle de las deducciones de los rubros fiscales
        """
        # Obtiene las cuentas donde aplican los rubros fiscales
        code = self.browse(cr, uid, ids[0], context=context)
        # Obtiene la compañia
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        
        deduction_ids = []
        get_asset = ''
        if code.target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        category_id = code.reference.id
        fiscalyear = code.period_id.fiscalyear_id.id
        period_id = code.period_id.id
        date = code.period_id.date_start
        
        # Revisa si el flujo aplica por año
        if code.apply_year == True:
            # Valida si es un rubro fiscal o un rubro fiscal acumulable
            if code.type_code == 'acf_period':
                cr.execute("""
                    select id
                    from account_fiscal_deduction
                    where category_id = %s and type='purchase' and fiscalyear_id=%s"""%(category_id,fiscalyear))
            elif code.type_code == 'acf_cumulative':
                cr.execute("""
                    select id
                    from account_fiscal_deduction
                    where category_id = %s and period_id in (select id from account_period where fiscalyear_id in
                        (select id from account_fiscalyear where extract(year from date_start) =
                        (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = 1)))"""%(category_id,fiscalyear))
            else:
                return True
        else:
            # Valida si es un rubro fiscal o un rubro fiscal acumulable
            if code.type_code == 'acf_period':
                cr.execute("""
                    select id
                    from account_fiscal_deduction
                    where category_id = %s and type='purchase' and period_id=%s"""%(category_id,period_id))
            elif code.type_code == 'acf_cumulative':
                cr.execute("""
                    select sum(amount) as amount
                    from account_fiscal_deduction
                    where date < '%s' and category_id = %s  and period_id in (select id from account_period where fiscalyear_id = %s)"""%(date,category_id,fiscalyear))
            else:
                return True
            
        # Recorre los registros de la consulta y guarda los ids en un arreglo
        for deduction_id in cr.fetchall():
            deduction_ids.append(str(deduction_id[0]))
            
        # Convierte a string la lista de ids obtenida
        deduction_string = ",".join(deduction_ids)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_deduction_tree')
        return {
            'name':_("Deducciones aplicadas"),
            'view_mode': 'tree',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.deduction',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id','in',[%s])]"%(deduction_string,),
            'context': {}
        }
    
    def action_view_ref(self, cr, uid, ids, context=None):
        """
            Redirecciona al detalle del que se obtiene el codigo fiscal
        """
        # Obtiene las cuentas donde aplican los rubros fiscales
        code = self.browse(cr, uid, ids[0], context=context)
        # Obtiene la compañia
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        
        move_ids = []
        get_asset = ''
        if code.target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        category_id = code.reference.id
        fiscalyear = code.period_id.fiscalyear_id.id
        period_id = code.period_id.id
        date = code.period_id.date_start
        
        # Valida si se aplican deducciones sobre el rubro fiscal
        if code.reference.exclude_deduction and company.partner_id.title == 'title_2':
            # Revisa si el flujo aplica por año
            if code.apply_year == True:
                # Valida si es un rubro fiscal o un rubro fiscal acumulable
                if code.type_code == 'acf_period':
                    cr.execute("""
                        select
                            l.id 
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                            inner join res_partner as p on p.id=l.partner_id
                            inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                        where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,category_id,fiscalyear))
                elif code.type_code == 'acf_cumulative':
                    # Obtiene el año fiscal anterior
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                            inner join res_partner as p on p.id=l.partner_id
                            inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                        where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id in
                            (select id from account_fiscalyear where extract(year from date_start) =
                            (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(get_asset,category_id,fiscalyear))
                else:
                    return True
            else:
                # Valida si es un rubro fiscal o un rubro fiscal acumulable
                if code.type_code == 'acf_period':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                            inner join res_partner as p on p.id=l.partner_id
                            inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                        where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
                elif code.type_code == 'acf_cumulative':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                            inner join res_partner as p on p.id=l.partner_id
                            inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                        where l.date < '%s' and r.category_id = %s  and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,date,category_id,fiscalyear))
                else:
                    return True
        else:
            # Revisa si el flujo aplica por año
            if code.apply_year == True:
                # Valida si es un rubro fiscal o un rubro fiscal acumulable
                if code.type_code == 'acf_period':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                        where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,category_id,fiscalyear))
                    
                elif code.type_code == 'acf_cumulative':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                        where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id in
                            (select id from account_fiscalyear where extract(year from date_start) =
                            (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(get_asset,category_id,fiscalyear))
                else:
                    return True
                
            else:
                # Valida si es un rubro fiscal o un rubro fiscal acumulable
                if code.type_code == 'acf_period':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                        where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
                elif code.type_code == 'acf_cumulative':
                    cr.execute("""
                        select
                            l.id
                        from
                            account_move_line as l 
                            inner join account_account_category_rel as r on l.account_id=r.account_id
                            inner join account_move as m on m.id = l.move_id %s
                        where l.date < '%s' and r.category_id = %s  and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,date,category_id,fiscalyear))
                else:
                    return True
        line_ids = []
        # Recorre los registros de la consulta
        for move_id in cr.fetchall():
            line_ids.append(move_id[0])
        
        #print "******************* lineas ******************************** ", line_ids
        
        # Recorre los movimientos y valida si son conciliados o no conciliados
        if code.type_move == 'all':
            for line in line_ids:
                move_ids.append(str(line))
        elif code.type_move == 'reconciled' or code.type_move == 'not_reconciled':
            acc_move_line = self.pool.get('account.move.line')
            for move in acc_move_line.browse(cr, uid, line_ids, context=context):
                mcredit = 0.0
                mdebit = 0.0
                c_move_lines = []
                #print "********************* move ******************** ", move
                # Valida si tiene conciliaciones el movimientos y sobre que periodo se aplicaron
                if move.reconcile_id:
                    if apply_year == True:
                        c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('period_id.fiscal_year_id','=',move.period_id.fiscalyear_id)], context=context)
                    else:
                        c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('date','<=',date)], context=context)
                elif move.reconcile_partial_id:
                    if apply_year == True:
                        c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('period_id.fiscal_year_id','=',move.period_id.fiscalyear_id)], context=context)
                    else:
                        c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('date','<=',date)], context=context)
                
                # Obtiene el resultado de lo conciliado sobre el periodo
                mcredit += move.credit
                mdebit += move.debit
                for cline in acc_move_line.browse(cr, uid, c_move_lines, context=context):
                    mcredit += cline.credit
                    mdebit += cline.debit
                
                # Valida si se va a considerar movimientos conciliados o no conciliados
                if code.type_move == 'reconciled':
                    # Valida si el movimiento aplica sobre el haber
                    if move.debit == 0.0:
                        # Valida que la suma sobre el debe no rebase el resultado
                        if move.credit <= mdebit:
                            move_ids.append(str(move.id))
                        else:
                            move_ids.append(str(move.id))
                    # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                    else:
                        # Valida que la suma sobre el debe no rebase el resultado
                        if move.debit <= mcredit:
                            move_ids.append(str(move.id))
                        else:
                            move_ids.append(str(move.id))
                elif code.type_move == 'not_reconciled':
                     # Valida si el movimiento aplica sobre el haber
                    if move.debit == 0.0:
                        # Valida que la suma sobre el debe no rebase el resultado
                        if move.credit > mdebit:
                            move_ids.append(str(move.id))
                    # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                    else:
                        # Valida que la suma sobre el debe no rebase el resultado
                        if move.debit > mcredit:
                            move_ids.append(str(move.id))
        else:
            for line in line_ids:
                move_ids.append(str(line))
        #print "************* move ids *********** ", move_ids
        
        # Convierte a string la lista de ids obtenida
        move_string = ",".join(move_ids)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_tree')
        return {
            'name':_("Movimientos aplicados"),
            'view_mode': 'tree',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id','in',[%s])]"%(move_string,),
            'context': {}
        }
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
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
    
    def code_is_year(self, cr, uid, code_id, context=None):
        """
            Indica si la raiz del arbol en el codigo fiscal es de un proceso anual o mensual
        """
        code = self.browse(cr, uid, code_id, context=context)
        # Valida que no sea el codigo raiz o codigo padre principal
        if code.parent_id:
            c = 1
            parent = code.parent_id
            # Recorre los registros hasta llegar al codigo raiz
            while(c==1):
                if parent.parent_id:
                    parent = parent.parent_id
                else:
                    # Fin del flujo
                    c+= 1
        else:
            parent = code
        # Retorna si aplica por año o no
        return parent.apply_year
    
    def onchange_apply_year(self, cr, uid, ids, apply_year, context=None):
        """
            Aplica filtro sobre los padres que puede utilizar en los codigos fiscales segun aplique por año o por procesos mensaules
        """
        if apply_year == True:
            domain = {'parent_id': [('type_code','=','view'),('apply_year','=',True)]}
            values = {'parent_id': False}
        else:
            domain = {'parent_id': [('type_code','=','view'),('apply_year','=',False)]}
            values = {'parent_id': False}
        return {'domain':domain, 'value': values}
    
    def get_value_code_cumulative(self, cr, uid, date, code_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal
        """
        # Valida si el codigo fiscal es de tipo anual
        code_year = self.code_is_year(cr, uid, code_id, context=context)
        apply_year = code_year if code_year == True else apply_year
        #print "************* code_year get_value_code_cumulative *********** ", code_id, ' - ', code_year, " - ", apply_year
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el año fiscal anterior
            cr.execute("""
                select
                    case when sum(value) <> 0 then sum(value) else 0.0 end as value
                from
                    account_fiscal_code_history_line
                where code_id = %s and period_id in (select id from account_period where fiscalyear_id in
                    (select id from account_fiscalyear where extract(year from date_start) =
                    (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(code_id,fiscalyear))
        else:
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
    
    def get_value_code_period(self, cr, uid, period_id, code_id, fiscalyear, apply_year=False, apply='prev', target_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores sobre periodo o por año del codigo fiscal en el historial
        """
        #print "***************** apply ************** ", apply
        # Valida si el codigo fiscal es de tipo anual
        code_year = self.code_is_year(cr, uid, code_id, context=context)
        apply_year = code_year if code_year == True else apply_year
        #print "************* code_year get_value_code_period *********** ", code_id, ' - ', code_year, " - ", apply_year
        
        # Valida si se va a aplicar por año
        if apply_year == True:
            if apply == 'prev':
                # Obtiene el año fiscal anterior
                cr.execute("""
                    select
                        case when sum(value) <> 0 then sum(value) else 0.0 end as value
                    from
                        account_fiscal_code_history_line
                    where code_id = %s and period_id in (select id from account_period where fiscalyear_id in
                        (select id from account_fiscalyear where extract(year from date_start) =
                        (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(code_id,fiscalyear))
            else:
                # Obtiene el año fiscal actual sobre el historial
                cr.execute("""
                    select
                        case when sum(value) <> 0 then sum(value) else 0.0 end as value
                    from
                        account_fiscal_code_history_line
                    where code_id = %s and period_id in (select id from account_period where fiscalyear_id = %s)"""%(code_id,fiscalyear))
        else:
            if apply == 'prev':
                # Obtiene el valor del periodo anterior
                cr.execute("""
                    select
                        case when sum(l.value) <> 0 then sum(l.value) else 0.0 end as value
                    from
                        account_fiscal_code_history_line as l
                        inner join account_period as p on l.period_id=p.id
                    where l.code_id = %s
                        and extract(year from p.date_start) = (select extract(year from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                        and extract(month from p.date_start) = (select extract(month from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                        and p.special=False"""%(code_id,period_id,period_id))
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
    
    def get_value_account_cumulative_conciliated(self, cr, uid, base, date, category_id, fiscalyear, apply_year=False, target_move='all', type_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal, identificando lo conciliado y lo no conciliado segun sea el caso
        """
        acc_move_line = self.pool.get('account.move.line')
        get_asset = ''
        line_ids = []
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        res = {
            'debit': 0.0,
            'credit': 0.0
        }
        
        # Valida si se va a aplicar por año
        if apply_year == True:
            # Obtiene el año fiscal anterior
            cr.execute("""
                select l.id 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id in
                    (select id from account_fiscalyear where extract(year from date_start) =
                    (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(get_asset,category_id,fiscalyear))
        else:
            cr.execute("""
                select l.id 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where l.date < '%s' and r.category_id = %s  and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,date,category_id,fiscalyear))
        for credit, debit in cr.fetchall():
            line_ids.append(reg[0])
        
        #print "************ lineas calculo acumulado ****************** ", line_ids
        
        # Recorre los movimientos y valida si son conciliados o no conciliados
        for move in acc_move_line.browse(cr, uid, line_ids, context=context):
            mcredit = 0.0
            mdebit = 0.0
            c_move_lines = []
            # Valida si tiene conciliaciones el movimientos y sobre que periodo se aplicaron
            if move.reconcile_id:
                if apply_year == True:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('period_id.fiscal_year_id','=',move.period_id.fiscalyear_id)], context=context)
                else:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('date','<=',date)], context=context)
            elif move.reconcile_partial_id:
                if apply_year == True:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('period_id.fiscal_year_id','=',move.period_id.fiscalyear_id)], context=context)
                else:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('date','<=',date)], context=context)
            
            # Obtiene el resultado de lo conciliado sobre el periodo
            mcredit += move.credit
            mdebit += move.debit
            for cline in acc_move_line.browse(cr, uid, c_move_lines, context=context):
                mcredit += cline.credit
                mdebit += cline.debit
            
            # Valida si se va a considerar movimientos conciliados o no conciliados
            if type_move == 'reconciled':
                # Valida si el movimiento aplica sobre el haber
                if move.debit == 0.0:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.credit <= mdebit:
                        res['credit'] += move.credit
                    else:
                        res['credit'] += mdebit
                # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                else:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.debit <= mcredit:
                        res['debit'] += move.debit
                    else:
                        res['debit'] += mcredit
            elif type_move == 'not_reconciled':
                 # Valida si el movimiento aplica sobre el haber
                if move.debit == 0.0:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.credit <= mdebit:
                        res['credit'] += 0.0
                    else:
                        res['credit'] += move.credit - mdebit
                # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                else:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.debit <= mcredit:
                        res['debit'] += 0.0
                    else:
                        res['debit'] += move.debit - mcredit 
        
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
    
    def get_value_account_period_conciliated(self, cr, uid, base, period_id, category_id, fiscalyear, apply_year=False, target_move='all', type_move='all', context=None):
        """
            Retorna el valor del periodo sobre los movimientos del rubro fiscal, identificando lo conciliado y lo no conciliado segun sea el caso
        """
        acc_move_line = self.pool.get('account.move.line')
        get_asset = ''
        line_ids = []
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        res = {
            'debit': 0.0,
            'credit': 0.0
        }
        # Valida si se va a aplicar por año
        if apply_year == True:
            cr.execute("""
                select l.id
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,category_id,fiscalyear))
        else:
            cr.execute("""
                select l.id 
                from
                    account_move_line as l 
                    inner join account_account_category_rel as r on l.account_id=r.account_id
                    inner join account_move as m on m.id = l.move_id %s
                where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
        for reg in cr.fetchall():
            line_ids.append(reg[0])
        #print "************ lineas calculo periodo ", type_move, " ****************** ", line_ids
        
        # Recorre los movimientos y valida si son conciliados o no conciliados
        for move in acc_move_line.browse(cr, uid, line_ids, context=context):
            mcredit = 0.0
            mdebit = 0.0
            c_move_lines = []
            # Valida si tiene conciliaciones el movimientos y sobre que periodo se aplicaron
            if move.reconcile_id:
                if apply_year == True:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('period_id.fiscal_year_id','=',fiscalyear)], context=context)
                else:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_id','=',move.reconcile_id.id),('period_id','=',period_id)], context=context)
            elif move.reconcile_partial_id:
                if apply_year == True:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('period_id.fiscal_year_id','=',fiscalyear)], context=context)
                else:
                    c_move_lines = acc_move_line.search(cr, uid, [('id','!=',move.id),('reconcile_partial_id','=',move.reconcile_partial_id.id),('period_id','=',period_id)], context=context)
            #print "**************** movimientos conciliados ***************** ", c_move_lines
            
            # Obtiene el resultado de lo conciliado sobre el periodo
            mcredit += move.credit
            mdebit += move.debit
            for cline in acc_move_line.browse(cr, uid, c_move_lines, context=context):
                mcredit += cline.credit
                mdebit += cline.debit
            
            #print "*******************  credit - deibt ************ ", mcredit, " - ", mdebit
            #print "*******************  valor movimiento ************ ", move.credit, " - ", move.debit
            
            # Valida si se va a considerar movimientos conciliados o no conciliados
            if type_move == 'reconciled':
                # Valida si el movimiento aplica sobre el haber
                if move.debit == 0.0:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.credit <= mdebit:
                        res['credit'] += move.credit
                    else:
                        res['credit'] += mdebit
                # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                else:
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.debit <= mcredit:
                        res['debit'] += move.debit
                    else:
                        res['debit'] += mcredit
            elif type_move == 'not_reconciled':
                # Valida si el movimiento aplica sobre el haber
                if move.debit == 0.0:
                    #print "************* al haber ************ ", move.credit, " - ", mdebit
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.credit <= mdebit:
                        res['credit'] += 0.0
                    else:
                        res['credit'] += move.credit - mdebit
                # Si aplica sobre el debe valida que la suma del haber no rebase el resultado
                else:
                    #print "************* al debe ************ ", move.debit, " - ", mcredit
                    # Valida que la suma sobre el debe no rebase el resultado
                    if move.debit <= mcredit:
                        res['debit'] += 0.0
                    else:
                        res['debit'] += move.debit - mcredit
        
        #print "************* res ****************** ", res
        
        # Obtiene el resultado
        amount = 0.0
        if base == 'debit':
            amount = res['debit']
        elif base == 'credit':
            amount = res['credit']
        elif base == 'dif':
            amount = res['debit'] - res['credit']
        else:
            amount = res['credit'] - res['debit']
        #print "*************** monto ******************** ", amount
        return amount
    
    def get_value_account_cumulative(self, cr, uid, base, date, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal
        """
        get_asset = ''
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        
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
                where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id in
                    (select id from account_fiscalyear where extract(year from date_start) =
                    (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(get_asset,category_id,fiscalyear))
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
    
    def get_value_account_period(self, cr, uid, base, period_id, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor del periodo sobre los movimientos del rubro fiscal
        """
        get_asset = ''
        if target_move == 'posted':
            get_asset = " and m.state = 'posted'"
        # Valida si se va a aplicar por año
        if apply_year == True:
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
    
    def get_value_account_cumulative_deduction(self, cr, uid, base, date, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal excluyendo movimientos donde aplican deducciones
        """
        # Obtiene la compañia
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        amount = 0.0
        
        # Si la compañia es de titulo 2 obtiene los movimientos en base al proveedor (Titulo 4 solo deducciones)
        if company.partner_id.title == 'title_2':
            get_asset = ''
            if target_move == 'posted':
                get_asset = " and m.state = 'posted'"
            
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
                        inner join res_partner as p on p.id=l.partner_id
                        inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                    where r.category_id = %s and l.period_id in (select id from account_period where fiscalyear_id in
                        (select id from account_fiscalyear where extract(year from date_start) =
                        (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = %s)))"""%(get_asset,category_id,fiscalyear))
            else:
                cr.execute("""
                    select
                        case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                        case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                    from
                        account_move_line as l 
                        inner join account_account_category_rel as r on l.account_id=r.account_id
                        inner join account_move as m on m.id = l.move_id %s
                        inner join res_partner as p on p.id=l.partner_id
                        inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                    where l.date < '%s' and r.category_id = %s  and l.period_id in (select id from account_period where fiscalyear_id = %s)"""%(get_asset,date,category_id,fiscalyear))
            for credit, debit in cr.fetchall():
                res = {
                    'debit': debit,
                    'credit': credit
                }
                break;
            
            # Obtiene el monto segun aplique el caso
            amount = 0.0
            if base == 'debit':
                amount = res['debit']
            elif base == 'credit':
                amount = res['credit']
            elif base == 'dif':
                amount = res['debit'] - res['credit']
            else:
                amount = res['credit'] - res['debit']
            
        # Obtiene las deducciones del rubro fiscal
        if apply_year == True:
            cr.execute("""
                select sum(amount) as monto
                from account_fiscal_deduction
                where category_id = %s and period_id in (select id from account_period where fiscalyear_id in
                    (select id from account_fiscalyear where extract(year from date_start) =
                    (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = 1)))"""%(category_id,fiscalyear))
        else:
            cr.execute("""
                select sum(amount) as amount
                from account_fiscal_deduction
                where date <= '%s' and category_id = %s  and period_id in (select id from account_period where fiscalyear_id = %s)"""%(date,category_id,fiscalyear))
        for value in cr.fetchall():
            if value[0]:
                amount += value[0]
            break;
        return amount
    
    def get_value_account_period_deduction(self, cr, uid, base, period_id, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor del periodo sobre los movimientos del rubro fiscal aplicando las deducciones
        """
        # Obtiene la compañia
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        amount = 0.0
        
        #print "************* get_value_account_period_deduction *************** ", company.partner_id.title
        #print "************* get_value_account_period_deduction *************** ", company.partner_id.regimen_title
        #print "************* get_value_account_period_deduction - target_move *************** ", target_move
        #print "************* get_value_account_period_deduction - category_id *************** ", category_id
        #print "************* get_value_account_period_deduction - fiscalyear *************** ", fiscalyear
        
        # Si la compañia es de titulo 2 obtiene los movimientos en base al proveedor (Titulo 4 solo deducciones)
        if company.partner_id.title == 'title_2':
            get_asset = ''
            if target_move == 'posted':
                get_asset = " and m.state = 'posted'"
            # Valida si se va a aplicar por año
            if apply_year == True:
                cr.execute("""
                    select
                        case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                        case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
                    from
                        account_move_line as l 
                        inner join account_account_category_rel as r on l.account_id=r.account_id
                        inner join account_move as m on m.id = l.move_id %s
                        inner join res_partner as p on p.id=l.partner_id
                        inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
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
                        inner join res_partner as p on p.id=l.partner_id
                        inner join regimen_fiscal as f on p.regimen_fiscal_id=f.id and (f.apply_deduction=False or (f.apply_deduction=True and f.category_id!=r.category_id))
                    where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
            for credit, debit in cr.fetchall():
                res = {
                    'debit': debit,
                    'credit': credit
                }
                break;
            
            #print "**************** res *************** ", res
            if base == 'debit':
                amount = res['debit']
            elif base == 'credit':
                amount = res['credit']
            elif base == 'dif':
                amount = res['debit'] - res['credit']
            else:
                amount = res['credit'] - res['debit']
        
        # Obtiene las deducciones del rubro fiscal
        if apply_year == True:
            cr.execute("""
                select sum(amount) as monto
                from account_fiscal_deduction
                where category_id = %s and type='purchase' and fiscalyear_id=%s"""%(category_id,fiscalyear))
        else:
            cr.execute("""
                select sum(amount) as amount
                from account_fiscal_deduction
                where category_id = %s and type='purchase' and period_id=%s"""%(category_id,period_id))
        for value in cr.fetchall():
            #print "***************** value **************** ", value
            if value[0]:
                amount += value[0]
            break;
        return amount
    
    def get_value_account_cumulative_cum_income(self, cr, uid, base, date, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor de los movimientos anteriores a la fecha sobre el rubro fiscal excluyendo movimientos donde aplican ingresos acumulados
        """
        
        #print "************* get_value_account_cumulative_cum_income *************** ", base
        #print "************* get_value_account_cumulative_cum_income *************** ", date
        #print "************* get_value_account_cumulative_cum_income - category_id *************** ", category_id
        #print "************* get_value_account_cumulative_cum_income - fiscalyear *************** ", fiscalyear
        
        amount = 0.0
        # Obtiene los ingresos acumulados del rubro fiscal
        if apply_year == True:
            cr.execute("""
                select sum(amount) as monto
                from account_fiscal_deduction
                where category_id = %s and type='sale' and period_id in (select id from account_period where fiscalyear_id in
                    (select id from account_fiscalyear where extract(year from date_start) =
                    (select extract(year from (date_start - interval '1 year')) as Fecha from account_fiscalyear where id = 1)))"""%(category_id,fiscalyear))
        else:
            cr.execute("""
                select sum(amount) as amount
                from account_fiscal_deduction
                where date < '%s' and type='sale' and category_id = %s  and period_id in (select id from account_period where fiscalyear_id = %s)"""%(date,category_id,fiscalyear))
        for value in cr.fetchall():
            if value[0]:
                amount += value[0]
            break;
        return amount
    
    def get_value_account_period_cum_income(self, cr, uid, base, period_id, category_id, fiscalyear, apply_year=False, target_move='all', context=None):
        """
            Retorna el valor del periodo sobre los movimientos del rubro fiscal aplicando las deducciones
        """
        
        #print "************* get_value_account_period_cum_income - category_id *************** ", category_id
        #print "************* get_value_account_period_cum_income - fiscalyear *************** ", fiscalyear
        
        amount = 0.0
        # Obtiene las deducciones del rubro fiscal
        if apply_year == True:
            cr.execute("""
                select sum(amount) as monto
                from account_fiscal_deduction
                where category_id = %s and fiscalyear_id=%s"""%(category_id,fiscalyear))
        else:
            cr.execute("""
                select sum(amount) as amount
                from account_fiscal_deduction
                where category_id = %s and period_id=%s"""%(category_id,period_id))
        for value in cr.fetchall():
            #print "***************** value **************** ", value
            if value[0]:
                amount += value[0]
            break;
        return amount
    
    def _calculate_code_amount(self, cr, uid, amount, calculate_values, period_id, fiscalyear_id, context=None):
        """
            Aplica al monto las ecuaciones para el calculo del registro
        """
        # Obtiene el mes del periodo
        cr.execute(""" select extract(month from date_start) as Mes from account_period where id=%s"""%(period_id,))
        for value in cr.fetchall():
            month = float(value[0])
            break
        # Obtiene el año del ejercicio fiscal
        cr.execute(""" select extract(year from date_start) as Anio from account_fiscalyear where id=%s"""%(fiscalyear_id,))
        for value in cr.fetchall():
            year = float(value[0])
            break
        # Recorre los registros
        for cal in calculate_values:
            val = 0.0
            # Obtiene el valor a aplicar
            if cal.type == 'anio':
                val = year
            elif cal.type == 'per':
                val = month
            else:
                val = cal.value
            # Calcula el valor sobre el monto segun sea el caso
            if cal.factor == 'sum':
                #print "**************** amount sum ********** ", amount, " + ", val
                amount += val
            elif cal.factor == 'res':
                #print "**************** amount res ********** ", amount, " - ", val
                amount -= val
            elif cal.factor == 'mul':
                #print "**************** amount mul ********** ", amount, " * ", val
                amount = amount * val
            elif cal.factor == 'div' and val == 0:
                    amount = 0.0
            elif cal.factor == 'div':
                #print "**************** amount div ********** ", amount, " / ", val
                amount = amount / val
        # Regresa el valor del monto
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
    
    def _get_value_condition(self, cr, uid, result, child_ids, date, period_id, fiscalyear, target_move='all', context=None):
        """
            Calcula el valor del codigo aplicando cada una de las condiciones al resultado
        """
        amount = 0.0
        apply_condition = False
        values = {}
        # Recorre los hijos del codigo
        for child in child_ids:
            amount = 0.0
            if child.if_value == True and period_id:
                # Valida que la condicion 
                if child.condition == 'if':
                    # Hace que deje la condicion por aplicar
                    apply_condition = True
                elif child.condition == 'else' and apply_condition == False:
                    continue
                # Revisa la condicion del codigo fiscal
                condition = self._check_code_condition(cr, uid, child.condition, result, child.operator, child.condition_value)
                if condition == False:
                    # Continua con la siguiente condicion
                    continue
                else:
                    # Se pone como aplicada la condicion
                    apply_condition = False
                # Revisa el tipo de codigo y obtiene el resultado
                if child.type_code == 'view':
                    res = self._get_value_account_view(cr, uid, child.id, date, period_id, fiscalyear, target_move, 'period', context=context)
                    # Obtiene el valor del monto
                    amount = res['amount']
                    # Aplica validacion sobre el resultado de la vista
                    if child.if_apply:
                        condition = self._check_code_condition(cr, uid, 'if', amount, child.operator, child.condition_value)
                        if condition:
                            amount = 0.0
                    # Agrega a la lista principal los valores
                    for val in res['values']:
                        values[val] = res['values'][val]
                elif child.type_code == 'acf_period':
                    # Valida si los movimientos van sobre lo conciliado
                    if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                        amount = self.get_value_account_period_conciliated(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, child.type_move, context=context)
                    else:
                        # Valida si se aplican deducciones sobre el rubro fiscal
                        if child.reference.exclude_deduction:
                            amount = self.get_value_account_period_deduction(cr, uid, child.base, period_id, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                        # Valida si se aplican ingresos acumulados sobre el rubro fiscal
                        if child.reference.exclude_cum_income:
                            amount = self.get_value_account_period_cum_income(cr, uid, child.base, period_id, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                        else:
                            amount = self.get_value_account_period(cr, uid, child.base, period_id, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                elif child.type_code == 'acf_cumulative':
                    # Valida si los movimientos van sobre lo conciliado
                    if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                        amount = self.get_value_account_cumulative_conciliated(cr, uid, child.base, date, child.reference.id, fiscalyear, child.apply_year, target_move, child.type_move, context=context)
                    else:
                        # Valida si se aplican deducciones sobre el rubro fiscal
                        if child.reference.exclude_deduction:
                            amount = self.get_value_account_cumulative_deduction(cr, uid, child.base, date, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                        # Valida si se aplican ingresos acumulados sobre el rubro fiscal
                        if child.reference.exclude_cum_income:
                            amount = self.get_value_account_cumulative_cum_income(cr, uid, child.base, date, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                        else:
                            amount = self.get_value_account_cumulative(cr, uid, child.base, date, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                elif child.type_code == 'code_period':
                        amount = self.get_value_code_period(cr, uid, period_id, child.reference.id, fiscalyear, child.apply_year, child.apply, target_move, context=context)
                elif child.type_code == 'code_cumulative':
                    amount = self.get_value_code_cumulative(cr, uid, date, child.reference.id, fiscalyear, child.apply_year, target_move, context=context)
                elif child.type_code == 'frate':
                    if child.reference and child.reference.id:
                        #print "********monto frate *********** ", child.reference.result
                        amount = child.reference.result
                
                # Aplica el signo al resultado
                if child.type_code == 'view':
                    amount = (amount * child.sign)
                
                # Valida si debe aplicar algun calculo extra al codigo
                if child.compute and child.type_code != 'view':
                    amount = self._calculate_code_amount(cr, uid, amount, child.compute_ids, period_id, fiscalyear, context=context)
            
                #print "************* child name ************ ", child.name, " -  ", child.type_code
                if child.factor == 'sum':
                    #print "**************** amount sum ********** ", result, " + ", amount
                    result += amount
                elif child.factor == 'res':
                    #print "**************** amount res ********** ", result, " - ", amount
                    result -= amount
                elif child.factor == 'mul':
                    #print "**************** amount mul ********** ", result, " * ", amount
                    result = result * amount
                elif child.factor == 'div' and amount == 0:
                    result = 0.0
                elif child.factor == 'div':
                    #print "**************** amount div ********** ", result, " / ", amount
                    result = result / amount
                # No aplica nada si es nulo
            values[child.id] = amount
        #print "************ resultado condicion ************ ", result
        # Retorna los resultados
        return {
            'amount': result,
            'values': values
        }
    
    def _get_value_account_view(self, cr, uid, code_id, date, period_id, fiscalyear, target_move='all', is_year=False, type='period', context=None):
        """
            Calcula el valor del codigo de tipo vista y retorna sus ids y su valor
        """
        apply_condition = False
        count = 1
        amount = 0.0
        result = 0.0
        type_apply = type
        values = {}
        # Obtiene el codigo padre
        code = self.browse(cr, uid, code_id, context=context)
        # Recorre los hijos del codigo
        for child in code.child_ids:
            amount = 0.0
            if period_id:
                # Valida si el calculo es por mes o por año
                #if is_year == True:
                #    apply_year = True
                #else:
                apply_year = child.apply_year
                
                # Revisa el tipo de codigo y obtiene el resultado
                if child.type_code == 'view':
                    # Valida si el registro aplica por año
                    if apply_year == True and type_apply == 'period':
                        type_apply = 'year'
                    
                    res = self._get_value_account_view(cr, uid, child.id, date, period_id, fiscalyear, target_move, apply_year, type_apply, context=context)
                    #print "***************** resultado monto en vista ********** ", res['amount']
                    #print "***************** resultado valores en vista ********** ", res['values']
                    # Obtiene el valor del monto
                    amount = res['amount']
                    # Aplica validacion sobre el resultado de la vista
                    if child.if_apply:
                        condition = self._check_code_condition(cr, uid, 'if', amount, child.operator, child.condition_value)
                        if condition:
                            amount = 0.0
                    # Agrega a la lista principal los valores
                    for val in res['values']:
                        values[val] = {
                            'result': res['values'][val]['result'],
                            'type': res['values'][val]['type']
                        }
                elif child.type_code == 'acf_period':
                    # Valida si los movimientos van sobre lo conciliado
                    if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                        amount = self.get_value_account_period_conciliated(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, child.type_move, context=context)
                    else:
                        #print "************** child.reference *********** ", child.reference
                        #print "************** child.reference *********** ", child.reference.name
                        #print "************** child.reference *********** ", child.reference.exclude_deduction
                        #print "************** child.reference *********** ", child.reference.exclude_cum_income
                        
                        # Valida si se aplican deducciones sobre el rubro fiscal
                        if child.reference.exclude_deduction:
                            amount = self.get_value_account_period_deduction(cr, uid, child.base, period_id, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                        # Valida si se aplican ingresos acumulables sobre el rubro fiscal
                        if child.reference.exclude_cum_income:
                            amount = self.get_value_account_period_cum_income(cr, uid, child.base, period_id, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                        else:
                            amount = self.get_value_account_period(cr, uid, child.base, period_id, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                elif child.type_code == 'acf_cumulative':
                    # Valida si los movimientos van sobre lo conciliado
                    if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                        amount = self.get_value_account_cumulative_conciliated(cr, uid, child.base, date, child.reference.id, fiscalyear, child.apply_year, target_move, child.type_move, context=context)
                    else:
                        # Valida si se aplican deducciones sobre el rubro fiscal
                        if child.reference.exclude_deduction:
                            amount = self.get_value_account_cumulative_deduction(cr, uid, child.base, date, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                        # Valida si se aplican ingresos acumulables sobre el rubro fiscal
                        if child.reference.exclude_cum_income:
                            amount = self.get_value_account_cumulative_cum_income(cr, uid, child.base, date, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                        else:
                            amount = self.get_value_account_cumulative(cr, uid, child.base, date, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                elif child.type_code == 'code_period':
                    amount = self.get_value_code_period(cr, uid, period_id, child.reference.id, fiscalyear, apply_year, child.apply, target_move, context=context)
                elif child.type_code == 'code_cumulative':
                    amount = self.get_value_code_cumulative(cr, uid, date, child.reference.id, fiscalyear, apply_year, target_move, context=context)
                elif child.type_code == 'frate':
                    if child.reference and child.reference.id:
                        #print "********monto frate *********** ", child.reference.result
                        amount = child.reference.result
                #print "************ amount - ", child.name, " ************** ", amount
                
                # Valida si tiene que aplicar alguna condicion sobre el valor ya calculado
                if child.if_apply == True and child.type_code != 'view':
                    #print "**************** child if_apply ******************** "
                    res = self._get_value_condition(cr, uid, amount, child.child_ids, date, period_id, fiscalyear, target_move, context=context)
                    # Obtiene el valor del monto
                    amount = res['amount']
                    #print "*************** res ************* ", res
                    # Agrega a la lista principal los valores
                    for val in res['values']:
                        values[val] = {
                            'result': res['values'][val],
                            'type': type_apply
                        }
                
                # Aplica el signo al resultado
                if child.type_code == 'view':
                    amount = (amount * child.sign)
                
                # Valida si debe aplicar algun calculo extra al codigo
                if child.compute and child.type_code != 'view':
                    amount = self._calculate_code_amount(cr, uid, amount, child.compute_ids, period_id, fiscalyear, context=context)
            
            values[child.id] = {
                'result': amount,
                'type': type_apply
            }
            
            # Valida si tiene que aplicar alguna condicion sobre el valor ya calculado
            if child.if_apply2 == True and child.parent_id:
                # Valida que la condicion aplique en el resultado 
                if child.condition2 == 'if':
                    # Hace que deje la condicion por aplicar
                    apply_condition2 = True
                elif child.condition2 == 'else' and apply_condition == False:
                    continue
                # Obtiene la condicion por la que se va a aplicar el calculo
                condition = child.condition2
                if child.condition_res2 == 'res':
                    condition_res = amount
                elif child.condition_res2 == 'cum':
                    condition_res = result
                elif child.condition_res2 == 'per':
                    condition_res = self._get_month_period(cr, uid, period_id, context=context)
                else:
                    condition_res = self._get_num_period_fiscalyear(cr, uid, fiscalyear, context=context)
                # Obtiene el operador y el valor por el que se va a comparar la condicion
                operator = child.operator2 
                condition_val = child.condition_value2
                
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
            
            # Calcula el valor sobre los hijos sin considerar los tipos vista
            if count == 1:
                count += 1
                result = values[child.id]['result']
            else:
                #print "************* child name ************ ", child.name, " -  ", child.type_code
                if child.factor == 'sum':
                    #print "**************** amount sum ********** ", result, " + ", amount
                    result += amount
                elif child.factor == 'res':
                    #print "**************** amount res ********** ", result, " - ", amount
                    result -= amount
                elif child.factor == 'mul':
                    #print "**************** amount mul ********** ", result, " * ", amount
                    result = result * amount
                elif child.factor == 'div' and amount == 0:
                    result = 0.0
                elif child.factor == 'div':
                    #print "**************** amount div ********** ", result, " / ", amount
                    result = result / amount
                # No aplica nada si es nulo
                
        # Actualiza el monto en la lista de resultados
        values[code.id] = {
            'result': result,
            'type': type_apply
        }
        #print "************** result view ********* ", result
        #print "************** values view ********* ", values
        return {
            'amount': result,
            'values': values
        }
    
    def _get_value_code(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Calcula el valor del codigo
        """
        #print "****************** Calcula valores **************"
        result = {}
        # Inicializa valores
        for id in ids:
            result[id] = {
                'result': 0.0,
                'type': 'period'
            }
        #print "************** ids *********** ", ids
        #print "************** context *********** ", context
        #period = self.pool.get('account.period').read(cr, uid, context.get('period_id'), ['date_start','date_end'], context=context)
        #print "************** periodo fecha ************ ", period
        
        # Recorre los codigos de todos registros
        code_ids = self.search(cr, uid, [('parent_id','=',False)])
        #print "******************** code ids **************** ", code_ids
        for code in self.browse(cr, uid, code_ids, context=context):
            # Valida que el codigo contenga un periodo registrado
            if not code.period_id:
                return result
            is_year = False
            type = 'period'
            # Valida si el proceso es anual
            if code.apply_year == True:
                is_year = True
            if code.apply_year == True:
                type = 'year'
                
            # Recorre los hijos del codigo
            for child in code.child_ids:
                amount = 0.0
                if code.period_id:
                    # Valida si el calculo es por mes o por año
                    #if is_year == True:
                    #    apply_year = True
                    #else:
                    apply_year = child.apply_year
                    type_apply = type
                    
                    # Revisa el tipo de codigo y obtiene el resultado
                    if child.type_code == 'view':
                        if apply_year == True and type == 'period':
                            type_apply = 'year'
                        
                        res = self._get_value_account_view(cr, uid, child.id, code.period_id.date_start, code.period_id.id, code.period_id.fiscalyear_id.id, code.target_move, apply_year, type_apply, context=context)
                        # Obtiene el valor del monto
                        amount = res['amount']
                        # Aplica validacion sobre el resultado de la vista
                        if child.if_apply:
                            condition = self._check_code_condition(cr, uid, 'if', amount, child.operator, child.condition_value)
                            if condition:
                                amount = 0.0
                        # Agrega a la lista principal los valores
                        for val in res['values']:
                            result[val] = {
                                'result': res['values'][val]['result'],
                                'type': res['values'][val]['type']
                            }
                    elif child.type_code == 'acf_period':
                        # Valida si los movimientos van sobre lo conciliado
                        if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                            amount = self.get_value_account_period_conciliated(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, child.type_move, context=context)
                        else:
                            #print "***************** child.reference ************ ", child.reference
                            
                            # Valida si se aplican deducciones sobre el rubro fiscal
                            if child.reference.exclude_deduction:
                                amount = self.get_value_account_period_deduction(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                            # Valida si se aplican ingresos acumulables sobre el rubro fiscal
                            elif child.reference.exclude_cum_income:
                                amount = self.get_value_account_period_cum_income(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                            else:
                                amount = self.get_value_account_period(cr, uid, child.base, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                    elif child.type_code == 'acf_cumulative':
                        # Valida si los movimientos van sobre lo conciliado
                        if child.type_move == 'reconciled' or child.type_move == 'not_reconciled':
                            amount = self.get_value_account_cumulative_conciliated(cr, uid, child.base, code.period_id.date_start, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, child.type_move, context=context)
                        else:
                            # Valida si se aplican deducciones sobre el rubro fiscal
                            if child.reference.exclude_deduction:
                                amount = self.get_value_account_cumulative_deduction(cr, uid, child.base, code.period_id.date_start, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                            # Valida si se aplican deducciones sobre el rubro fiscal
                            elif child.reference.exclude_cum_income:
                                amount = self.get_value_account_cumulative_cum_income(cr, uid, child.base, code.period_id.date_start, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                            else:
                                amount = self.get_value_account_cumulative(cr, uid, child.base, code.period_id.date_start, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                    elif child.type_code == 'code_period':
                        amount = self.get_value_code_period(cr, uid, code.period_id.id, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, child.apply, code.target_move, context=context)
                    elif child.type_code == 'code_cumulative':
                        amount = self.get_value_code_cumulative(cr, uid, code.period_id.date_start, child.reference.id, code.period_id.fiscalyear_id.id, apply_year, code.target_move, context=context)
                    elif child.type_code == 'frate':
                        if child.reference and child.reference.id:
                            #print "********monto frate *********** ", child.reference.result
                            amount = child.reference.result
                    
                    # Valida si tiene que aplicar alguna condicion sobre el valor ya calculado
                    if child.if_apply == True and child.type_code != 'view':
                        #print "**************** child if_apply ******************** "
                        res = self._get_value_condition(cr, uid, amount, child.child_ids, code.period_id.date_start, code.period_id.id, code.period_id.fiscalyear_id.id, code.target_move, context=context)
                        # Obtiene el valor del monto
                        amount = res['amount']
                        # Agrega a la lista principal los valores
                        for val in res['values']:
                            result[val] = {
                                'result': res['values'][val],
                                'type': type_apply
                            }
                    
                    # Aplica el signo al resultado
                    if child.type_code == 'view':
                        amount = (amount * child.sign)
                    
                    # Valida si debe aplicar algun calculo extra al codigo
                    if child.compute and child.type_code != 'view':
                        amount = self._calculate_code_amount(cr, uid, amount, child.compute_ids, code.period_id.id, code.period_id.fiscalyear_id.id, context=context)
                    result[child.id] = {
                        'result': amount,
                        'type': type_apply
                    }
            #print "************* result ************** ", result
        return result
    
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=64),
        'info': fields.text('Descripcion'),
        'parent_id': fields.many2one('account.fiscal.code', 'Codigo Padre', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('account.fiscal.code', 'parent_id', 'Codigos hijos', ondelete='cascade'),
        'type_code': fields.selection([
                        ('view','Vista'),
                        ('acf_period','Rubro Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_period','Codigo Fiscal'),
                        ('code_cumulative','Codigo fiscal Acumulable'),
                        ('frate','Indice Fiscal')], 'Tipo Codigo', required=True),
        'sequence': fields.integer('Orden', help="Orden en el que se ejecutaran los calculos de codigos fiscales"),
        'sign': fields.float('Coeficiente Padre', required=True, help="Indica el coheficiente que se utilizara cuando se consolide el codigo de este con el codigo dentro de su padre (Usualmente 1 o -1)."),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division'),
                        ('none','Nulo')], 'Factor'),
        'base': fields.selection([
                        ('debit','Debe'),
                        ('credit','Haber'),
                        ('value','Valor'),
                        ('dif','Debe - Haber'),
                        ('dif2','Haber - Debe')], 'Calculo base'),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True, ondelete='restrict'),
        'code_year': fields.boolean('Codigo Fiscal Anual'),
        'result': fields.function(_get_value_code, type='float', digits=(16,4), string='Monto', store=True, multi='getvalue'),
        'type': fields.function(_get_value_code,  selection=[('period','Proceso Mensual'),
                ('year','Proceso Anual')],string='Tipo', type='selection', store=True, multi='getvalue'),
        
        'period_id': fields.many2one('account.period', 'Periodo'),
        'apply_year': fields.boolean('Obtener por año'),
        'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                        ('all', 'Todos los asientos'),
                                        ], 'Movimientos'),
        'compute_ids': fields.one2many('account.fiscal.code.compute', 'code_id', 'Calculos Extra', ondelete='cascade'),
        'compute': fields.boolean('Agregar Calculos extra'),
        'apply': fields.selection([
                        ('prev','Anterior'),
                        ('current','Actual')], 'Aplicar'),
        'is_year': fields.related('parent_id', 'apply_year', type='boolean', string='Aplica por año', readonly=True),
        # Aplicar condiciones
        'if_apply': fields.boolean('Aplicar condicion sobre result. calculo'),
        'if_value': fields.boolean('Condicion'),
        'condition': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'operator': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_value': fields.float('Valor'),
        # Aplicar condiciones sobre acumulador
        'if_apply2': fields.boolean('Aplicar condicion sobre acumulacion'),
        'condition2': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'condition_res2': fields.selection([
                        ('res','Resultado'),
                        ('cum','Valor acumulado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], 'condicion valor'),
        'operator2': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_value2': fields.float('Valor'),
        #'tax_code_id': fields.many2one('account.tax.code', 'Tipo de Impuestos', select=True, ondelete='restrict'),
        'apply_balance': fields.boolean('Aplica en Saldos Fiscales'),
        'type_move': fields.selection([
                        ('reconciled','Conciliado'),
                        ('not_reconciled','No conciliado'),
                        ('all','Todo')], 'Tipo Movimiento'),
    }
    
    _order = "sequence"
    
    _defaults = {
        'factor': 'sum',
        'base': 'value',
        'type_code': 'view',
        'sign': 1,
        'sequence': 0,
        'apply': 'current',
        'if_value': False,
        'condition': 'if',
        'operator': '=',
        'condition_value': 0.0,
        
        'if_apply2': False,
        'condition_res2': 'res',
        'condition2': 'if',
        'operator2': '=',
        'condition_value2': 0.0
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Elimina las condiciones de los codigos fiscales si ya no aplican
        """
        #print "************** valores ************* ", vals
        # Valida que no haya codigos fiscales de tipo vista para eliminar los hijos
        code_ids = self.search(cr, uid, [('id','in',ids),('type_code','=','view')])
        if not code_ids:
            # Si ya no aplica la condicion elimina los hijos en donde aplica
            if vals.get('if_apply',True) == False:
                vals['child_ids'] = [[6, 0, []]]
        
        # Funcion original de modificar
        super(account_fiscal_code, self).write(cr, uid, ids, vals, context=context)
        return True
    
    def action_view_code(self, cr, uid, ids, context=None):
        """
            Redirecciona a la vista formulario del codigo fiscal seleccionado
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_code_form')
        
        return {
            'name':_("Codigo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.code',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': ids[0]
        }
    
    def action_add_code(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con los movimientos posibles a relacionar
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_code_child_view')
        
        apply_year = False
        # Valida si el registro debe aplicar por año
        code = self.browse(cr, uid, ids[0], context=context)
        if code.apply_year:
            apply_year = True
        
        return {
            'name':_("Codigo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.code.child',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_parent_id': ids[0],
                'default_apply_year': apply_year,
                'default_is_year': apply_year
            }
        }
    
    def action_add_condition(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard para agregar una nueva condicion
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_fiscal_code_child_condition_view')
        
        return {
            'name':_("Condicion Codigo Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.code.child.condition',
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
            ids = self.search(cr, user, [('info', operator, name)] + args, limit=limit, context=context)
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

account_fiscal_code()

class account_fiscal_code_compute(osv.Model):
    _name = 'account.fiscal.code.compute'
    
    _columns = {
        'code_id': fields.many2one('account.fiscal.code', 'Codigo', select=True, ondelete='cascade'),
        'sequence': fields.integer('Orden', help="Orden en el que se ejecutaran los codigos para el calculo de impuesto"),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division')], 'Factor'),
        'type': fields.selection([
                        ('val','Valor Fijo'),
                        ('anio','No. año fiscal'),
                        ('per','No. Mes periodo')], 'Tipo'),
        'value': fields.float('Valor', digits=(16,4)),
    }
    
    _order = 'sequence'
    
    _defaults = {
        'sequence': 0,
        'type': 'val',
        'factor': 'sum',
        'value': 0.0
    }
    
account_fiscal_code_compute()

# ---------------------------------------------------------
# Account fiscal code history - Historial Codigos Fiscales
# ---------------------------------------------------------

class account_fiscal_code_history(osv.Model):
    _name = 'account.fiscal.code.history'
    
    _columns = {
        'name': fields.char('Nombre', size=64),
        'line_ids': fields.one2many('account.fiscal.code.history.line', 'history_id', 'Historial Codigos', ondelete='cascade'),
        'date': fields.date('Fecha'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True, ondelete="cascade"),
        'fiscalyear_id': fields.related('period_id', 'fiscalyear_id', type='many2one', relation='account.fiscalyear', string='Ejercicio Fiscal', store=True, readonly=True),
        'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                        ('all', 'Todos los asientos'),
                                        ], 'Movimientos', required=True),
        'type': fields.selection([('period','Proceso Mensual'),('year','Proceso Anual')],'Tipo', required=True),
        'cont': fields.integer('Saldos aplicados')
    }
    
    _defaults = {
        'date': fields.date.today,
        'type': 'period',
        'cont': 0.0
    }

account_fiscal_code_history()

class account_fiscal_code_history_line(osv.Model):
    _name = 'account.fiscal.code.history.line'
    
    def update_history_values(self, cr, uid, history_id, context=None):
        """
            Recalcula los totales de los montos
        """
        code_obj = self.pool.get('account.fiscal.code')
        apply_condition = False
        count = 1
        result = 0.0
        #print "************** actualiza registro padre ************ ", history_id
        
        # Obtiene el codigo padre
        history = self.browse(cr, uid, history_id, context=context)
        # Recorre los hijos del codigo
        for child in history.child_ids:
            # Valida si tiene que aplicar alguna condicion sobre el valor ya calculado
            if child.if_apply2 == True and child.parent_id:
                # Valida que la condicion aplique en el resultado 
                if child.condition2 == 'if':
                    # Hace que deje la condicion por aplicar
                    apply_condition2 = True
                elif child.condition2 == 'else' and apply_condition == False:
                    continue
                # Obtiene la condicion por la que se va a aplicar el calculo
                condition = child.condition2
                if child.condition_res2 == 'res':
                    condition_res = child.value
                elif child.condition_res2 == 'cum':
                    condition_res = result
                elif child.condition_res2 == 'per':
                    condition_res = code_obj._get_month_period(cr, uid, period_id, context=context)
                else:
                    condition_res = code_obj._get_num_period_fiscalyear(cr, uid, fiscalyear, context=context)
                # Obtiene el operador y el valor por el que se va a comparar la condicion
                operator = child.operator2 
                condition_val = child.condition_value2
                
                # Realiza la validacion de campos
                condition = code_obj._check_code_condition(cr, uid, condition, condition_res, operator, condition_val)
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
            
            # Calcula el valor sobre los hijos sin considerar los tipos vista
            if count == 1:
                count += 1
                result = child.value
            else:
                #print "************* child name ************ ", child.name, " -  ", child.type_code
                if child.factor == 'sum':
                    #print "**************** amount sum ********** ", result, " + ", child.value
                    result += child.value
                elif child.factor == 'res':
                    #print "**************** amount res ********** ", result, " - ", child.value
                    result -= child.value
                elif child.factor == 'mul':
                    #print "**************** amount mul ********** ", result, " * ", child.value
                    result = result * child.value
                elif child.factor == 'div' and child.value == 0:
                    result = 0.0
                elif child.factor == 'div':
                    #print "**************** amount div ********** ", result, " / ", child.value
                    result = result / child.value
                # No aplica nada si es nulo
        
        # Valida si aplica el resultado
        if history.if_apply:
            condition = code_obj._check_code_condition(cr, uid, 'if', result, history.operator, history.condition_value)
            if condition:
                result = 0.0
        
        #print "************ actualiza registro *************** ", history.id
        
        # Actualiza el valor del registro
        self.write(cr, uid, [history.id], {'value': result}, context=context)
        
        # Valida si hay algun otro registro padre
        if history.parent_id:
            self.update_history_values(cr, uid, history.parent_id.id, context=context)
        return True
    
    def get_code_period(self, cr, uid, code_id, period_id, context=None):
        """
            Obtiene el valor del historial sobre el periodo
        """
        cr.execute("""
            select id
            from account_fiscal_code_history_line
            where code_id = %s and period_id = %s and apply_balance != True"""%(code_id,period_id))
        code_id = False
        for value in cr.fetchall():
            code_id = value[0]
            break
        return code_id
    
    def get_code_fiscalyear(self, cr, uid, code_id, fiscalyear_id, context=None):
        """
            Obtiene el valor del historial sobre el ejercicio
        """
        cr.execute("""
            select id
            from account_fiscal_code_history_line
            where code_id = %s and fiscalyear_id = %s and apply_balance != True"""%(code_id,fiscalyear_id))
        code_id = False
        for value in cr.fetchall():
            code_id = value[0]
            break
        return code_id
    
    _columns = {
        'history_id': fields.many2one('account.fiscal.code.history', 'Historial', ondelete='cascade', required=True),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal', ondelete='set null'),
        'value': fields.float('Monto', digits=(16,4), required=True),
        'name': fields.char('Nombre', size=128),
        'code': fields.related('code_id', 'code', type='char', size=64, string='Codigo', store=True, readonly=True),
        'type_code': fields.related('code_id', 'type_code', type='selection', selection=[
                        ('view','Vista'),
                        ('acf_period','Rubro Fiscal'),
                        ('code_period','Codigo Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_cumulative','Codigo fiscal Acumulable'),
                        ('frate','Indice Fiscal')], string='Codigo', store=True, readonly=True),
        #'sequence': fields.related('code_id', 'sequence', type='integer', string='Orden', store=True, readonly=True),
        #'factor': fields.related('code_id', 'factor', type='selection', selection=[
        #                ('sum','Suma'),
        #                ('res','Resta'),
        #                ('mul','Multiplicacion'),
        #                ('div','Division'),
        #                ('none','Nulo')], string='Factor', store=True, readonly=True),
        'sequence': fields.integer('Orden', help="Orden en el que se ejecutaran los calculos de codigos fiscales"),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division'),
                        ('none','Nulo')], 'Factor'),
        
        'base': fields.related('code_id', 'base', type='selection', selection=[
                        ('debit','Debe'),
                        ('credit','Haber'),
                        ('value','Valor'),
                        ('dif','Debe - Haber'),
                        ('dif2','Haber - Debe')], string='Base', store=True, readonly=True),
        'sign': fields.related('code_id', 'sign', type='float', string='Signo', store=True, readonly=True),
        'apply_year': fields.related('code_id', 'apply_year', type='boolean', string='Obtener por año', store=True, readonly=True),
        'period_id': fields.related('history_id', 'period_id', type='many2one', relation='account.period', string='Periodo', store=True, readonly=True),
        'fiscalyear_id': fields.related('history_id', 'fiscalyear_id', type='many2one', relation='account.fiscalyear', string='Ejercicio Fiscal', store=True, readonly=True),
        'target_move': fields.related('history_id', 'target_move', type='selection', selection=[
                        ('posted', 'Todos los asientos asentados'),
                        ('all', 'Todos los asientos')], string='Movimientos', store=True, readonly=True),
        'type': fields.related('history_id', 'type', type='selection', selection=[('period','Proceso Mensual'),('year','Proceso Anual')], string='Tipo', store=True, readonly=True),
        'parent_id': fields.many2one('account.fiscal.code.history.line', 'Codigo Padre', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('account.fiscal.code.history.line', 'parent_id', 'Codigos hijos', ondelete='cascade'),
        'apply_balance': fields.boolean('Aplicacion de saldo'),
        
        # Aplicar condiciones
        'if_apply': fields.related('code_id', 'if_apply', type='boolean', string='Aplicar condicion sobre result. calculo', store=True),
        'if_value': fields.related('code_id', 'if_value', type='boolean', string='Condicion', store=True),
        'condition': fields.related('code_id', 'condition', type='selection', selection=[
                        ('if','Si'),
                        ('else','Sino'),], string='Condicion', store=True),
        'operator': fields.related('code_id', 'operator', type='selection', selection=[
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], string='Operador', store=True),
        'condition_value': fields.related('code_id', 'condition_value', type='float', string='Valor', store=True),
        # Aplicar condiciones sobre acumulador
        'if_apply2': fields.related('code_id', 'if_apply2', type='boolean', string='Aplicar condicion sobre acumulacion', store=True),
        'condition2': fields.related('code_id', 'condition2', type='selection', selection=[
                        ('if','Si'),
                        ('else','Sino'),],string='Condicion', store=True),
        'condition_res2': fields.related('code_id', 'condition_res2', type='selection', selection=[
                        ('res','Resultado'),
                        ('cum','Valor acumulado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], string='condicion valor', store=True),
        'operator2': fields.related('code_id', 'operator2', type='selection', selection=[
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),],string='Operador', store=True),
        'condition_value2': fields.related('code_id', 'condition_value2', type='float', string='Valor', store=True),
    }
    
    _defaults = {
        'apply_balance': False,
        'sequence': 0,
        'factor': 'sum'
    }
    
    _order = "period_id,sequence"
    
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
        for record in self.browse(cr, uid, ids, context=context):
            name = record.code + '- ' + record.name if record.code else record.name
            if record.type_code == 'view' and not record.parent_id:
                if record.period_id:
                    name = name + '- ' + record.period_id.name
            res.append((record.id,name ))
        return res

account_fiscal_code_history_line()

# ---------------------------------------------------------
# Account fiscal - Deducciones de Codigos Fiscales
# ---------------------------------------------------------

class account_fiscal_deduction(osv.Model):
    _name='account.fiscal.deduction'

    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'description': fields.text('Notas'),
        'date': fields.date('Fecha'),
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account')),
        'category_id': fields.many2one('account.account.category','Rubro fiscal', select="1"),
        'period_id': fields.many2one('account.period', 'Periodo de registro'),
        'fiscalyear_id': fields.related('period_id', 'fiscalyear_id', type='many2one', relation='account.fiscalyear', string='Ejercicio Fiscal', store=True, readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Factura'),
        'voucher_id': fields.many2one('account.voucher', 'Pago', ondelete="cascade"),
        'type': fields.selection([
                        ('sale','Ventas'),
                        ('purchase','Compras')], 'Tipo', required=True),
    }
    
    _defaults = {
        'date': fields.date.today,
        'amount': 0.0,
        'type': 'purchase'
    }

account_fiscal_deduction()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
