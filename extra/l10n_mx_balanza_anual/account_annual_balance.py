# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields
import time
import netsvc
import tools

class account_monthly_balance(osv.Model):
    _name = "account.monthly_balance"
    _description = "Balanza de Comprobacion Mensual"
    _auto = False
    
    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.child_parent_ids:
                result[record.id] = [x.id for x in record.child_parent_ids]
            else:
                result[record.id] = []

            #if record.child_consol_ids:
            #    for acc in record.child_consol_ids:
            #        if acc.id not in result[record.id]:
            #            result[record.id].append(acc.id)

        return result
    
    _columns = {
        'name': fields.char('Nombre', size=128),
        'period_id': fields.many2one('account.period', 'Periodo'),
        'period_name': fields.char('Periodo Nombre', size=64),
        'account_id': fields.many2one('account.account', 'Cuenta'),
        'account_parent_id': fields.many2one('account.account', 'Cuenta Padre'),
        'account_code': fields.char('Codigo', size=64),
        'account_name': fields.char('Descripcion', size=250),
        'account_level': fields.integer('Nivel'),
        'account_type': fields.char('Tipo', size=64),
        'account_nature': fields.char('Naturaleza', size=64),
        'account_sign': fields.integer('Signo'),
        'initial_balance': fields.float('Saldo Inicial'),
        'debit': fields.float('Cargos'),
        'credit': fields.float('Abonos'),
        'ending_balance': fields.float('Saldo Final'),
        'moves': fields.boolean('Con Movimientos'),
        'child_id': fields.related('account_id', 'child_id', type="many2many", relation="account.account", string="Cuenta hija", readonly=True),
        'parent_id': fields.many2one('account.monthly_balance', 'Balance Padre'),
        'child_parent_ids': fields.one2many('account.monthly_balance','parent_id','Children'),
        'child_ids': fields.function(_get_child_ids, type='many2many', relation="account.monthly_balance", string="Child Accounts"),
    }
    
    _order = "period_name"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_monthly_balance')
        tools.drop_view_if_exists(cr, 'account_monthly_balance_base')
        cr.execute("""
            -- Función que devuelve los IDs de las cuentas hijo de la cuenta especificada
            CREATE OR REPLACE FUNCTION f_account_child_ids(account_id integer)
            RETURNS TABLE(id integer) AS
            $$

            WITH RECURSIVE account_ids(id) AS (
                SELECT id FROM account_account WHERE parent_id = $1
              UNION ALL
                SELECT cuentas.id FROM account_ids, account_account cuentas
                WHERE cuentas.parent_id = account_ids.id
                )
            SELECT id FROM account_ids 
            union
            select $1 id
            order by id;
            $$ LANGUAGE 'sql';
            /*
            select f_account_child_ids(12);

            */


            create or replace view account_monthly_balance_base as

            select account.id * 10000 + period.id id,
            period.id period_id, period.name period_name, account.code account_code, account.name account_name, account.level account_level, 
            account_type.name account_type,  
            case account_type.sign
            when 1 then 'Deudora'
            else 'Acreedora'
            end account_nature,
            account_type.sign account_sign,

            case date_part('month', period.date_start)
            when 1 then 
                account_type.sign * 
                (select COALESCE(sum(debit), 0.00) -  COALESCE(sum(credit), 0.00)
                from account_move_line line, account_journal journal
                where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                and line.journal_id = journal.id and journal.type='situation'
                and line.period_id = period.id
                )
            else 
                account_type.sign * 
                (select COALESCE(sum(debit), 0.00) -  COALESCE(sum(credit), 0.00)
                from account_move_line line, account_journal journal
                where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                and line.journal_id = journal.id --and journal.type='situation'
                and line.period_id in 
                (select id from account_period xperiodo 
                  where xperiodo.fiscalyear_id=fiscalyear.id 
                    and date_part('month', xperiodo.date_start) < date_part('month', period.date_start)
                )
                )
            end
            initial_balance,
            (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id)
            debit,
            --and date_part('month', period.date_start) = 1) debit1,
            (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id)
            credit, account.id account_id, account.parent_id account_parent_id, 
            (case when account.parent_id IS NOT NULL then (account.parent_id * 10000 + period.id) else NULL end) as parent_id,
            (period.name || ' - ' || account.name) as name

            from account_account account, account_account_type account_type, account_period period, account_fiscalyear fiscalyear
            where account.user_type=account_type.id and account.active = True
            and period.fiscalyear_id = fiscalyear.id
            --and period.name='01/2011'
            order by period.name, account.code;


            create or replace view account_monthly_balance as

            select id, period_id, period_name, account_code, account_name, account_level, account_type, account_nature, account_sign,
            initial_balance, debit, credit, initial_balance + (account_sign * (debit - credit)) ending_balance,
            (abs(initial_balance) + abs(debit) + abs(credit)) > 0.0 moves, account_id, account_parent_id, name, parent_id
            from account_monthly_balance_base;
    """)

account_monthly_balance()

class account_annual_balance(osv.osv):
    _name = "account.annual_balance"
    _description = "Balanza de Comprobacion Anual"
    _auto = False
    
    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.child_parent_ids:
                result[record.id] = [x.id for x in record.child_parent_ids]
            else:
                result[record.id] = []

            #if record.child_consol_ids:
            #    for acc in record.child_consol_ids:
            #        if acc.id not in result[record.id]:
            #            result[record.id].append(acc.id)

        return result
    
    _columns = {
        'name': fields.char('Nombre', size=128),
        'fiscalyear': fields.char('Periodo Fiscal', size=64),
        'account_id': fields.many2one('account.account', 'Cuenta'),
        'account_parent_id': fields.many2one('account.account', 'Cuenta Padre'),
        'account_code': fields.char('Codigo', size=64),
        'account_name': fields.char('Descripcion', size=250),
        'account_level': fields.integer('Nivel'),
        'account_type': fields.char('Tipo', size=64),
        'account_nature': fields.char('Naturaleza', size=64),
        'account_sign': fields.integer('Signo'),
        'initial_balance': fields.float('Saldo Inicial'),
        'debit1': fields.float('Cargo Enero'),
        'credit1': fields.float('Abono Enero'),
        'balance1': fields.float('SF Enero'),
        'debit2': fields.float('Cargo Febrero'),
        'credit2': fields.float('Abono Febrero'),
        'balance2': fields.float('SF Febrero'),
        'debit3': fields.float('Cargo Marzo'),
        'credit3': fields.float('Abono Marzo'),
        'balance3': fields.float('SF Marzo'),
        'debit4': fields.float('Cargo Abril'),
        'credit4': fields.float('Abono Abril'),
        'balance4': fields.float('SF Abril'),
        'debit5': fields.float('Cargo Mayo'),
        'credit5': fields.float('Abono Mayo'),
        'balance5': fields.float('SF Mayo'),
        'debit6': fields.float('Cargo Junio'),
        'credit6': fields.float('Abono Junio'),
        'balance6': fields.float('SF Junio'),
        'debit7': fields.float('Cargo Julio'),
        'credit7': fields.float('Abono Julio'),
        'balance7': fields.float('SF Julio'),
        'debit8': fields.float('Cargo Agosto'),
        'credit8': fields.float('Abono Agosto'),
        'balance8': fields.float('SF Agosto'),
        'debit9': fields.float('Cargo Septiembre'),
        'credit9': fields.float('Abono Septiembre'),
        'balance9': fields.float('SF Septiembre'),
        'debit10': fields.float('Cargo Octubre'),
        'credit10': fields.float('Abono Octubre'),
        'balance10': fields.float('SF Octubre'),
        'debit11': fields.float('Cargo Noviembre'),
        'credit11': fields.float('Abono Noviembre'),
        'balance11': fields.float('SF Noviembre'),
        'debit12': fields.float('Cargo Diciembre'),
        'credit12': fields.float('Abono Diciembre'),
        'balance12': fields.float('SF Diciembre'),
        'moves1': fields.boolean('Ene'),
        'moves2': fields.boolean('Feb'),
        'moves3': fields.boolean('Mar'),
        'moves4': fields.boolean('Abr'),
        'moves5': fields.boolean('May'),
        'moves6': fields.boolean('Jun'),
        'moves7': fields.boolean('Jul'),
        'moves8': fields.boolean('Ago'),
        'moves9': fields.boolean('Sep'),
        'moves10': fields.boolean('Oct'),
        'moves11': fields.boolean('Nov'),
        'moves12': fields.boolean('Dic'),
        'parent_id': fields.many2one('account.annual_balance', 'Balance Padre'),
        'child_parent_ids': fields.one2many('account.annual_balance','parent_id','Children'),
        'child_ids': fields.function(_get_child_ids, type='many2many', relation="account.annual_balance", string="Child Accounts"),
    }

    _order = 'fiscalyear,account_code'
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_annual_balance')
        tools.drop_view_if_exists(cr, 'account_annual_balance_prev')
        tools.drop_view_if_exists(cr, 'account_annual_balance_base')
        cr.execute("""
            -- Función que devuelve los IDs de las cuentas hijo de la cuenta especificada
            CREATE OR REPLACE FUNCTION f_account_child_ids(account_id integer)
              RETURNS TABLE(id integer) AS
            $$

                WITH RECURSIVE account_ids(id) AS (
                    SELECT id FROM account_account WHERE parent_id = $1
                  UNION ALL
                    SELECT cuentas.id FROM account_ids, account_account cuentas
                    WHERE cuentas.parent_id = account_ids.id
                    )
                SELECT id FROM account_ids 
                union
                select $1 id
                order by id;
            $$ LANGUAGE 'sql';
            /*
            select f_account_child_ids(12);

            */


            CREATE OR REPLACE view account_annual_balance_base as

            select account.id * 10000 + fiscalyear.id id,
            fiscalyear.name fiscalyear, account.code account_code, account.name account_name, account.level account_level, 
            account_type.name account_type,  
            case account_type.sign
            when 1 then 'Deudora'
            else 'Acreedora'
            end account_nature,
            account_type.sign account_sign,

            account_type.sign * (select COALESCE(sum(debit), 0.00) - COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type='situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 1
            ) initial_balance,

             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 1) debit1,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 1) credit1,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =2) debit2,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 2) credit2,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =3) debit3,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 3) credit3,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =4) debit4,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 4) credit4,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =5) debit5,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 5) credit5,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =6) debit6,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 6) credit6,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =7) debit7,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 7) credit7,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =8) debit8,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 8) credit8,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =9) debit9,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 9) credit9,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =10) debit10,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 10) credit10,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =11) debit11,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 11) credit11,
             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) =12) debit12,
             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and date_part('month', period.date_start) = 12) credit12,
            account.id account_id, account.parent_id account_parent_id,
            (case when account.parent_id IS NOT NULL then (account.parent_id * 10000 + fiscalyear.id) else NULL end) as parent_id,
            (fiscalyear.name || ' - ' || account.name) as name

            from account_account account, account_account_type account_type, account_fiscalyear fiscalyear
            where account.user_type=account_type.id and account.active = True
            order by fiscalyear.name, account.code;

            CREATE OR REPLACE view account_annual_balance_prev as
            select id, fiscalyear, account_code, account_name, account_level, account_type,  account_nature, account_sign, 
            initial_balance,
            debit1, credit1, 
            (initial_balance + account_sign * (debit1 - credit1)) balance1,
            debit2, credit2,
            (initial_balance + account_sign * (    debit1 + debit2 - 
                            credit1 - credit2)) balance2,
            debit3, credit3,
            (initial_balance + account_sign * (    debit1 + debit2 + debit3 - 
                            credit1 - credit2 - credit3)) balance3,
            debit4, credit4,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 - 
                            credit1 - credit2- credit3 - credit4)) balance4,
            debit5, credit5,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 - 
                            credit1 - credit2- credit3 - credit4 - credit5)) balance5,

            debit6, credit6,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6)) balance6,
            debit7, credit7,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7)) balance7,
            debit8, credit8,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8)) balance8,
            debit9, credit9,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 + debit9 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8 - credit9)) balance9,
            debit10, credit10,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 + debit9 + debit10 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8 - credit9 - credit10)) balance10,
            debit11, credit11,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 + debit9 + debit10 + debit11 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8 - credit9 - credit10 - credit11)) balance11,
            debit12, credit12,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 + debit9 + debit10 + debit11 + debit12 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8 - credit9 - credit10 - credit11 - credit12)) balance12,
            account_id, account_parent_id, parent_id, name 
        
            from account_annual_balance_base;
            
            CREATE OR REPLACE view account_annual_balance as
            select id, fiscalyear, account_code, account_name, account_level, account_type, account_nature, account_sign, initial_balance,
            debit1, credit1, balance1,
            debit2, credit2, balance2,
            debit3, credit3, balance3,
            debit4, credit4, balance4,
            debit5, credit5, balance5,
            debit6, credit6, balance6,
            debit7, credit7, balance7,
            debit8, credit8, balance8,
            debit9, credit9, balance9,
            debit10, credit10, balance10,
            debit11, credit11, balance11,
            debit12, credit12, balance12,
            (abs(initial_balance) + abs(credit1) + abs(debit1) <> 0.0) as moves1,
            (abs(balance1) + abs(credit2) + abs(debit2)<>0.0) as moves2,
            (abs(balance2) + abs(credit3) + abs(debit3)<>0.0) as moves3,
            (abs(balance3) + abs(credit4) + abs(debit4)<>0.0) as moves4,
            (abs(balance4) + abs(credit5) + abs(debit5)<>0.0) as moves5,
            (abs(balance5) + abs(credit6) + abs(debit6)<>0.0) as moves6,
            (abs(balance6) + abs(credit7) + abs(debit7)<>0.0) as moves7,
            (abs(balance7) + abs(credit8) + abs(debit8)<>0.0) as moves8,
            (abs(balance8) + abs(credit9) + abs(debit9)<>0.0) as moves9,
            (abs(balance9) + abs(credit10) + abs(debit10)<>0.0) as moves10,
            (abs(balance10) + abs(credit11) + abs(debit11)<>0.0) as moves11,
            (abs(balance11) + abs(credit12) + abs(debit12)<>0.0) as moves12,
            account_id, account_parent_id, parent_id, name

            from account_annual_balance_prev;
        """)
    
account_annual_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: