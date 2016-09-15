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
import decimal_precision as dp
from tools.translate import _


class account_account_type(osv.osv):
    _inherit="account.account.type"

    def _get_sign(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        sign= 1
        for acc_type in self.browse(cr, uid, ids, context=context):
            if acc_type.report_type in ('income','liability'):
                sign=-1
            res[acc_type.id] = sign
        return res

    _columns = {
                'sign'  : fields.function(_get_sign, method=True, type="integer", string='Sign', store=True),
    }


class account_monthly_balance_wizard(osv.osv_memory):
    _name = "account.monthly_balance_wizard"
    _description = "Generador de Balanza de Comprobacion"

    _columns = {
        'period_id'         : fields.many2one('account.period', 'Periodo', required=True),
        }


    def get_info(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created sales order.
        """
        if context is None:
            context = {}

        data = context and context.get('active_ids', []) or []

        for params in self.browse(cr, uid, ids, context=context):
            print "(", params.period_id.id, ") ", params.period_id.name

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


                drop function if exists f_get_mx_account_monthly_balance_base
                (x_period_id integer);


                CREATE OR REPLACE FUNCTION f_get_mx_account_monthly_balance_base
                (x_period_id integer)
                RETURNS TABLE
                (
                fiscalyear_id integer,
                period_id integer,
                account_id integer,
                account_code varchar(64),
                account_name varchar(128),
                account_level integer,
                account_type varchar(64),
                account_nature varchar(64),
                account_sign integer,
                initial_balance float,
                debit float, 
                credit float) 

                AS
                $BODY$

                BEGIN

                    return query
                            select 
                            period.fiscalyear_id as fiscalyear_id, period.id as period_id, account.id account_id, 
                            account.code account_code, account.name account_name, account.level account_level, 
                            account_type.name account_type,  
                            case account_type.sign
                            when 1 then 'Deudora'
                            else 'Acreedora'
                            end::varchar(64) account_nature,
                            account_type.sign account_sign,

                            case date_part('month', period.date_start)
                            when 1 then 
                                account_type.sign * 
                                (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                                from account_move_line line, account_journal journal
                                where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                                and line.journal_id = journal.id and journal.type='situation'
                                and line.period_id = period.id
                                )
                            else
                            account_type.sign * 
                            (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                            from account_move_line line, account_journal journal
                            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id --and journal.type='situation'
                            and line.period_id in 
                            (select id from account_period xperiodo 
                              where xperiodo.fiscalyear_id=fiscalyear.id 
                                and xperiodo.name < period.name 
                                )
                            )
                            end::float
                            initial_balance,
                            (select COALESCE(sum(line.debit), 0.00) 
                            from account_move_line line, account_journal journal
                            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id and journal.type<>'situation'
                            and line.period_id = period.id)::float
                            debit,
                            (select COALESCE(sum(line.credit), 0.00) 
                            from account_move_line line, account_journal journal
                            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id and journal.type<>'situation'
                            and line.period_id = period.id)::float
                            credit

                            from account_account account, account_account_type account_type, account_period period, account_fiscalyear fiscalyear
                            where account.user_type=account_type.id and account.active = True
                            and period.fiscalyear_id = fiscalyear.id
                            and period.id=x_period_id
                            order by account.code;

                END
                $BODY$
                LANGUAGE 'plpgsql';


                drop function if exists f_get_mx_account_monthly_balance
                (x_period_id integer, x_uid integer);

                CREATE OR REPLACE FUNCTION f_get_mx_account_monthly_balance
                (x_period_id integer, x_uid integer)
                RETURNS boolean 
                AS
                $BODY$
                BEGIN
                    delete from account_monthly_balance where create_uid = x_uid;
                    insert into account_monthly_balance
                    (create_uid, create_date, write_date, write_uid,
                    fiscalyear_id, period_id, account_id, account_code, account_name, account_level, account_type, account_nature, account_sign,
                        initial_balance, debit, credit, ending_balance, moves)
                    select 
                    x_uid as create_uid, LOCALTIMESTAMP as create_date, LOCALTIMESTAMP as write_date, x_uid as write_uid,
                    fiscalyear_id, period_id, account_id, account_code, account_name, account_level, account_type, account_nature, account_sign,
                            initial_balance, debit, credit, initial_balance + (account_sign * (debit - credit)) ending_balance,
                            (abs(initial_balance) + abs(debit) + abs(credit)) > 0.0 moves
                    from f_get_mx_account_monthly_balance_base(x_period_id);

                    return true;

                END
                $BODY$
                LANGUAGE 'plpgsql';


                select * from f_get_mx_account_monthly_balance(%s, %s);                    
                """, (params.period_id.id, uid,)
                )
            data = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not data[0]:
                raise osv.except_osv(
                        _('Error en script!'),
                        _('No se pudo generar la balanza de comprobacion, por favor verifique su configuracion y vuelva a intentarlo'))


            values = self.pool.get('account.monthly_balance').search(cr, uid, [('create_uid', '=', uid)])

        value = {
            'domain'    : "[('id','in', ["+','.join(map(str,values))+"])]",
            'name'      : _('Balanza de Comprobacion'),
            'view_type' : 'form',
            'view_mode' : 'tree,form',
            'res_model' : 'account.monthly_balance',
            'view_id'   : False,
            'type'      : 'ir.actions.act_window'
        }

        return value

account_monthly_balance_wizard()


class account_monthly_balance(osv.osv):
    _name = "account.monthly_balance"
    _description = "Balanza de Comprobacion Mensual"

    _columns = {
        'fiscalyear_id'     : fields.many2one('account.fiscalyear', 'Periodo Anual', readonly=True),
        'period_id'         : fields.many2one('account.period', 'Periodo', readonly=True),
        'account_id'        : fields.many2one('account.account', 'Cuenta Contable', readonly=True),
        'period_name'       : fields.char('Periodo Nombre', size=64, readonly=True),
        'account_code'      : fields.char('Codigo', size=64, readonly=True),
        'account_name'      : fields.char('Descripcion', size=250, readonly=True),
        'account_level'     : fields.integer('Nivel', readonly=True),
        'account_type'      : fields.char('Tipo', size=64, readonly=True),
        'account_nature'    : fields.char('Naturaleza', size=64, readonly=True),
        'account_sign'      : fields.integer('Signo', readonly=True),
        'initial_balance'   : fields.float('Saldo Inicial', readonly=True),
        'debit'             : fields.float('Cargos', readonly=True),
        'credit'            : fields.float('Abonos', readonly=True),
        'ending_balance'    : fields.float('Saldo Final Acumulado', readonly=True),
        'moves'             : fields.boolean('Con Movimientos', readonly=True),
        'create_uid'        : fields.many2one('res.users', 'Created by', readonly=True),
    }

    _order = 'account_code'

account_monthly_balance()




# Clase que define la estructura y vistas usadas para obtener la Balanza de Comprobación Anual
class account_annual_balance(osv.osv):
    _name = "account.annual_balance"
    _description = "Balanza de Comprobacion Anual"
    _auto = False
#    _log_access = True

    _columns = {
        'fiscalyear_id'    : fields.many2one('account.fiscalyear', 'Periodo Anual', readonly=True),
        'account_id'        : fields.many2one('account.account', 'Cuenta Contable', readonly=True),
        'fiscalyear': fields.char('Periodo Fiscal', size=64),
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
        'debit13': fields.float('Cargo Ajustes'),
        'credit13': fields.float('Abono Ajustes'),
        'balance13': fields.float('SF Ajustes'),
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
        'moves13': fields.boolean('Aju'),
        'period_id_start' : fields.many2one('account.period', 'Periodo Inicio', readonly=True),
        'period_id_stop'  : fields.many2one('account.period', 'Periodo Final', readonly=True),
    }

    _order = 'account_code'
    
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
            fiscalyear.id fiscalyear_id, account.id account_id,
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
            and period.name like '12%') --date_part('month', period.date_start) =12)
             debit12,


             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and period.name like '12%') --date_part('month', period.date_start) = 12) 
            credit12,

             (select COALESCE(sum(debit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and period.name like '13%') --date_part('month', period.date_start) =12)
             debit13,


             (select COALESCE(sum(credit), 0.00) 
            from account_move_line line, account_journal journal, account_period period
            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
            and line.journal_id = journal.id and journal.type<>'situation'
            and line.period_id = period.id and period.fiscalyear_id = fiscalyear.id
            and period.name like '13%') --date_part('month', period.date_start) = 12) 
             credit13



            from account_account account, account_account_type account_type, account_fiscalyear fiscalyear
            where account.user_type=account_type.id and account.active = True
            order by fiscalyear.name, account.code;


            CREATE OR REPLACE view account_annual_balance_prev as
            select id, 
            fiscalyear_id, account_id,
            fiscalyear, account_code, account_name, account_level, account_type,  account_nature, account_sign, 
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

        debit13, credit13,
            (initial_balance + account_sign * (    debit1 + debit2 +debit3 + debit4 + debit5 + debit6 + debit7 + debit8 + debit9 + debit10 + debit11 + debit12 + debit13 - 
                            credit1 - credit2- credit3 - credit4 - credit5 - credit6- credit7 - credit8 - credit9 - credit10 - credit11 - credit12 - credit13)) balance13


            from account_annual_balance_base;

            CREATE OR REPLACE view account_annual_balance as
            select id, fiscalyear_id, account_id,
            fiscalyear, account_code, account_name, account_level, account_type, account_nature, account_sign, initial_balance,
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
            debit13, credit13, balance13,
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
            (abs(balance12) + abs(credit13) + abs(debit13)<>0.0) as moves13,
            
            (select _inicial.id from account_period _inicial 
                where _inicial.fiscalyear_id = account_annual_balance_prev.fiscalyear_id and _inicial.special order by _inicial.id asc limit 1) period_id_start,

            (select _final.id from account_period _final 
                where _final.fiscalyear_id = account_annual_balance_prev.fiscalyear_id and _final.special order by _final.id desc limit 1) period_id_stop

            from account_annual_balance_prev;

        """)
account_annual_balance()



class account_account_lines(osv.osv):
    _name = "account.account_lines"
    _description = "Auxiliar de Cuentas"
#    _log_access = True

    _columns = {
        'name'              : fields.char('No se usa', size=64, readonly=True),
        'move_id'           : fields.many2one('account.move', 'Poliza', readonly=True),
        'user_id'           : fields.many2one('res.users', 'Usuario', readonly=True),
        'journal_id'        : fields.many2one('account.journal', 'Diario', readonly=True),
        'period_id'         : fields.many2one('account.period', 'Periodo', readonly=True),
        'fiscalyear_id'    : fields.many2one('account.fiscalyear', 'Periodo Anual', readonly=True),
        'account_id'        : fields.many2one('account.account', 'Cuenta Contable', readonly=True),
        'account_type_id'   : fields.many2one('account.account.type', 'Tipo Cuenta', readonly=True),

        'move_date'         : fields.date('Fecha Poliza', readonly=True),
        'move_name'         : fields.char('Poliza No.', size=120, readonly=True),
        'move_ref'          : fields.char('Referencia', size=120, readonly=True),
        'period_name'       : fields.char('xPeriodo Mensual', size=120, readonly=True),
        'fiscalyear_name'   : fields.char('xPeriodo Anual', size=120, readonly=True),
        'account_code'      : fields.char('Codigo Cuenta', size=60, readonly=True),
        'account_name'      : fields.char('Descripcion Cuenta', size=120, readonly=True),
        'account_level'     : fields.integer('Nivel', readonly=True),
        'account_type'      : fields.char('xTipo Cuenta', size=60, readonly=True),
        'account_sign'      : fields.integer('Signo', readonly=True),
        'journal_name'      : fields.char('xDiario', size=60, readonly=True),
        'initial_balance'   : fields.float('Saldo Inicial', readonly=True),
        'debit'             : fields.float('Cargos', readonly=True),
        'credit'            : fields.float('Abonos', readonly=True),
        'ending_balance'    : fields.float('Saldo Final', readonly=True),
        'product_id'        : fields.many2one('product.product', 'Producto', readonly=True),
        'qty'               : fields.float('Cantidad', readonly=True),
    
    }

    _order = 'period_name, move_date, account_code'

account_account_lines()


class account_account_lines_wizard(osv.osv_memory):
    _name = "account.account_lines_wizard"
    _description = "Auxiliar de Cuentas"

    _columns = {
        'fiscalyear_id'    : fields.many2one('account.fiscalyear', 'Periodo Anual'),
        'period_id_start'   : fields.many2one('account.period', 'Periodo Inicial'),
        'period_id_stop'    : fields.many2one('account.period', 'Periodo Final'),
        'account_id'        : fields.many2one('account.account', 'Cuenta Contable'),
        }

    def button_get_info(self, cr, uid, ids, context=None):
        print "Entrando a metodo get_info..."
        if context is None:
            context = {}

        data = context and context.get('active_ids', []) or []

        print "Antes de revisar los parámetros..."
        for params in self.browse(cr, uid, ids):
            print "Despues de revisar los parámetros..."
            print params.fiscalyear_id.id
            print params.period_id_start.id
            print params.period_id_stop.id
            print params.account_id.id

            cr.execute("""

            drop function if exists f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer);

            CREATE OR REPLACE FUNCTION f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer)
            RETURNS TABLE(
            id integer,
            create_uid integer,
            create_date date,
            write_date date,
            write_uid integer,
            name varchar(64),
            move_id integer,
            user_id integer,
            journal_id integer,
            period_id integer,
            fiscalyear_id integer,
            account_id integer,
            account_type_id integer,
            move_date date,
            move_name varchar(120),
            move_ref varchar(120),
            period_name  varchar(120),
            fiscalyear_name varchar(120),
            account_code varchar(60),
            account_name varchar(120),
            account_level integer,
            account_type varchar(60),
            account_sign integer,
            journal_name varchar(60),
            initial_balance float,
            debit float, 
            credit float,
            ending_balance float,
            product_id integer,
            qty float) 


            AS
            $BODY$
            DECLARE
                _cursor CURSOR FOR 
                    SELECT zx.id, zx.initial_balance, zx.debit, zx.credit, zx.ending_balance, zx.account_sign, zx.period_name, zx.move_date 
                        from hesatec_mx_auxiliar_borrame zx order by zx.period_name, zx.move_date;
                _result record;
                last_balance float = 0;
                _fiscalyear_id integer;
            BEGIN

                select fiscal.id into _fiscalyear_id
                from account_fiscalyear fiscal where fiscal.id = (select account_period.fiscalyear_id from account_period where account_period.id = $2);

                select 
                    case (select cast(left(account_period.name,2) as integer) from account_period where account_period.id = $2)
                    when 1 then (select account_annual_balance.initial_balance from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 2 then (select balance1 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 3 then (select balance2 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 4 then (select balance3 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 5 then (select balance4 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 6 then (select balance5 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 7 then (select balance6 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 8 then (select balance7 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 9 then (select balance8 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 10 then (select balance9 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 11 then (select balance10 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 12 then (select balance11 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    when 13 then (select balance12 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
                    end
                into last_balance;


                drop table if exists hesatec_mx_auxiliar_borrame;


                create table hesatec_mx_auxiliar_borrame AS 
                select move_line.id * 1000 + period.id as id, move.name as name, move.date move_date, move.name move_name, move.ref move_ref, period.name period_name, 
                fiscalyear.name fiscalyear_name, account.code account_code, account.name account_name, account.level account_level, account_type.name account_type,  
                account_type.sign account_sign,
                account.id account_id, account_type.id account_type_id,
                journal.name journal_name,
                move.id move_id, 
                move.create_uid user_id,
                journal.id journal_id,
                period.id period_id,
                fiscalyear.id fiscalyear_id,
                0.00::float initial_balance,
                coalesce(move_line.debit, 0.0)::float debit,
                coalesce(move_line.credit, 0.0)::float credit,
                0.00::float ending_balance,
                move_line.product_id,
                move_line.quantity::float qty
                from account_move move, account_move_line move_line, account_period period, account_fiscalyear fiscalyear,
                account_account account, account_account_type account_type,  account_journal journal
                where 
                move.id = move_line.move_id and 
                move_line.period_id = period.id and move_line.state='valid' and
                fiscalyear.id = period.fiscalyear_id and
                move_line.account_id = account.id and
                account.user_type = account_type.id and
                journal.id = move_line.journal_id and journal.type <> 'situation'
                and account.id  in (select f_account_child_ids($1))
                and period.date_start >= (select _periodo1.date_start from account_period _periodo1 where _periodo1.id=$2)
                and period.date_stop  <= (select _periodo2.date_stop from account_period _periodo2 where _periodo2.id=$3)

                order by period.name, move.date;



                FOR _record IN _cursor
                LOOP
                    update hesatec_mx_auxiliar_borrame xx
                    set     initial_balance = last_balance, 
                        ending_balance = last_balance + 
                            (xx.account_sign * (xx.debit - xx.credit))
                    where xx.id=_record.id;

                    last_balance = last_balance + (_record.account_sign * (_record.debit - _record.credit));
                END LOOP;
    
                return query 
                    select     zz.id, zz.user_id create_uid, current_date create_date, current_date write_date, 
                        zz.user_id write_uid, zz.name, zz.move_id, zz.user_id, zz.journal_id, zz.period_id, zz.fiscalyear_id,
                        zz.account_id, zz.account_type_id, zz.move_date, zz.move_name, zz.move_ref, 
                        zz.period_name, 
                        zz.fiscalyear_name, zz.account_code, zz.account_name, zz.account_level,    zz.account_type, 
                        zz.account_sign, zz.journal_name, 
                        zz.initial_balance, zz.debit, zz.credit, zz.ending_balance, zz.product_id, zz.qty
                    from hesatec_mx_auxiliar_borrame zz
                    order by period_name, move_date, account_code;


            END
            $BODY$
            LANGUAGE 'plpgsql' ;

                delete from account_account_lines;

                insert into account_account_lines 
                (id, create_uid, create_date, write_date, write_uid,
                name, move_id, user_id, journal_id, period_id,
                fiscalyear_id, account_id, account_type_id, move_date, move_name, 
                move_ref, period_name, fiscalyear_name, account_code, account_name, 
                account_level, account_type, account_sign, journal_name, initial_balance, debit, credit, ending_balance, product_id, qty)
                select id, create_uid, create_date, write_date, write_uid,
                name, move_id, user_id, journal_id, period_id,
                fiscalyear_id, account_id, account_type_id, move_date, move_name, 
                move_ref, period_name, fiscalyear_name, account_code, account_name, 
                account_level, account_type, account_sign, journal_name, initial_balance, debit, credit, ending_balance, product_id, qty 
                from f_account_mx_move_lines(%s, %s, %s)
                """, (params.account_id.id, params.period_id_start.id, params.period_id_stop.id)
                )

        value = {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.account_lines',
            'view_id': False,
            'type': 'ir.actions.act_window',
            }
        return value

account_account_lines_wizard()

# Configurador de reportes basados en la Balanza de Comprobacion Mensual
#
class account_mx_report_definition(osv.osv):
    _name = "account.mx_report_definition"
    _description = "Definición de Reportes basados en Balanza de Comprobación"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'name'              : fields.char('Nombre', size=64, required=True),
        'complete_name'     : fields.function(_name_get_fnc, method=True, type="char", size=300, string='Nombre Completo', store=True),
        'parent_id'         : fields.many2one('account.mx_report_definition','Parent Category', select=True),
        'child_id'          : fields.one2many('account.mx_report_definition', 'parent_id', string='Childs'),
        'sequence'          : fields.integer('Secuencia', help="Determina el orden en que se muestran los registros..."),
        'type'              : fields.selection([
                                            ('sum','Acumula'), 
                                            ('detail','Detalle'), 
                                        ], 'Tipo',required=True),
        'sign'              : fields.selection([
                                        ('positive', 'Positivo'), 
                                        ('negative', 'Negativo'), 
                                    ], 'Signo',required=True),
        'print_group_sum'   : fields.boolean('Titulo de Grupo', help="Indica si se imprime el título del grupo de reporte..."),
        'print_report_sum'  : fields.boolean('Suma Final', help="Indica si se imprime la sumatoria total del reporte..."),
        'internal_group'    : fields.char('Grupo Interno', size=64, required=True),
        'initial_balance'   : fields.boolean('Saldo Inicial Acum.'),
        'debit_and_credit'  : fields.boolean('Cargos y Abonos'),
        'ending_balance'    : fields.boolean('Saldo Final Acum.'),
        'debit_credit_ending_balance': fields.boolean('Saldo Final Periodo'),

        'account_ids'       : fields.many2many('account.account', 'account_account_mx_reports_rel', 'mx_report_definition_id', 'account_id', 'Accounts'),
        'report_id'         : fields.many2one('account.mx_report_definition','Usar Reporte'),
        'report_id_use_resume' : fields.boolean('Solo Resultado', help="Si activa este campo solo se obtendra el resultado del reporte, de lo contrario se obtendra el detalle de las cuentas y/o subreportes incluidos."),
        'report_id_account' : fields.char('Cuenta', size=64, help="Indique el numero de cuenta a mostrar en el reporte"),
        'report_id_label'   : fields.char('Descripcion', size=64, help="Indique la descripcion de la cuenta a mostrar en el reporte"),
        'report_id_show_result': fields.boolean('Mostrar Resultado', help="Active esta casilla si desea que se muestre el resultado del subreporte"),
        'active'            : fields.boolean('Activo'),

        }

    _defaults = {
        'type'                  : 'sum',
        'sign'                  : 'positive',
        'active'                : True,
        }

    _order = 'sequence'


    def _check_recursion(self, cr, uid, ids, context=None):
        level = 2
        while len(ids):
            cr.execute('select distinct parent_id from account_mx_report_definition where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    def _check_recursion_report(self, cr, uid, ids, context=None):
        for report in self.browse(cr, uid, ids):
            return not (report.id == report.report_id.id)

    _constraints = [
        (_check_recursion, 'Error ! You can not create recursive reports.', ['parent_id']),
        (_check_recursion_report, 'Error ! You can not create recursive reports.', ['report_id']),
    ]

    def child_get(self, cr, uid, ids):
        return [ids]


account_mx_report_definition()


# Clase donde se generan reportes configurados en la clase anterior
#

class account_mx_report_data(osv.osv):
    _name = "account.mx_report_data"
    _description = "Reportes Financieros"

    _columns = {
        'report_id'         : fields.many2one('account.mx_report_definition', 'Reporte'),# readonly=True),
        'report_group'      : fields.char('Grupo', size=64),# readonly=True),
        'report_section'    : fields.char('Seccion', size=64),# readonly=True),
        'sequence'          : fields.integer('Sequence'),
        'report_sign'       : fields.float('Signo en Reporte'),# readonly=True),
        'account_sign'      : fields.float('Signo para Saldo'),# readonly=True),
        'account_code'      : fields.char('Cuenta', size=64),# readonly=True),
        'account_name'      : fields.char('Descripcion', size=128),# readonly=True),
#        'account_id'        : fields.many2one('account.account', 'Cuenta Contable'),# readonly=True),
        'period_id'         : fields.many2one('account.period', 'Periodo'),# readonly=True),
        'initial_balance'   : fields.float('Saldo Inicial'),# readonly=True),
        'debit'             : fields.float('Cargos'),# readonly=True),
        'credit'            : fields.float('Abonos'),# readonly=True),
        'ending_balance'    : fields.float('Saldo Acumulado'),# readonly=True),
        'debit_credit_ending_balance': fields.float('Saldo Periodo'),# readonly=True),
    }
    _order = 'sequence, account_code'

account_mx_report_data()



class account_mx_report_data_wizard(osv.osv_memory):
    _name = "account.mx_report_data_wizard"
    _description = "Generador de Reporte Financiero"

    _columns = {
        'report_id'         : fields.many2one('account.mx_report_definition', 'Reporte Contable', required=True),
        'period_id'         : fields.many2one('account.period', 'Periodo', required=True),
        'report_type'       : fields.selection([('xls','XLS'),('pdf','PDF')
                                            ], 'Tipo'),
        }

    _defaults = {
            'report_type': lambda *a: 'pdf',
        }


    def get_info(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created sales order.
        """
        if context is None:
            context = {}

        data = context and context.get('active_ids', []) or []

        for params in self.browse(cr, uid, ids, context=context):
            print "(", params.report_id.id, ") ", params.report_id.name, " - Periodo: " ,params.period_id.name
#            print "(", params.period_id.id, ") ", params.period_id.name

            cr.execute("""
                drop function if exists f_get_mx_report_data_detail
                (x_report_id integer, x_period_id integer, x_uid integer, x_parent_id integer, x_parent_group varchar(64));


                CREATE OR REPLACE FUNCTION f_get_mx_report_data_detail
                (x_report_id integer, x_period_id integer, x_uid integer, x_parent_id integer, x_parent_group varchar(64))
                RETURNS TABLE
                (
                create_uid integer,
                create_date timestamp,
                write_date timestamp,
                write_uid integer,
                report_id integer,
                report_group varchar(64),
                report_section varchar(64),
                sequence integer,
                report_sign float,
                account_sign float,
                account_code varchar(64),
                account_name varchar(128),
                period_id integer,
                initial_balance float,
                debit float, 
                credit float) 

                AS
                $BODY$

                BEGIN

                    return query 
                    select 
                        x_uid, LOCALTIMESTAMP, LOCALTIMESTAMP, x_uid,
                        subreport.parent_id,
                        case char_length(x_parent_group) 
                        when 0 then subreport.internal_group 
                        else x_parent_group
                        end,
                        subreport.name,
                        subreport.sequence,
                        case subreport.sign
                        when 'positive' then 1.0
                        else -1.0
                        end::float,
                        account_type.sign::float, 

                        account.code, 
                        account.name, 
                        period.id,

                        case date_part('month', period.date_start)
                        when 1 then 
                            account_type.sign * 
                            (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                            from account_move_line line, account_journal journal
                            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id and journal.type='situation'
                            and line.period_id = period.id
                            )
                        else
                            account_type.sign * 
                            (select COALESCE(sum(line.debit), 0.00) -  COALESCE(sum(line.credit), 0.00)
                            from account_move_line line, account_journal journal
                            where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                            and line.journal_id = journal.id 
                            and line.period_id in 
                                (select xperiodo.id from account_period xperiodo 
                                where xperiodo.fiscalyear_id= (select fiscalyear.id from account_fiscalyear fiscalyear where period.fiscalyear_id = fiscalyear.id)
                                and xperiodo.name < period.name 
                                )
                            )
                        end::float,
                        (select COALESCE(sum(line.debit), 0.00) 
                        from account_move_line line, account_journal journal
                        where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                        and line.journal_id = journal.id and journal.type<>'situation'
                        and line.period_id = period.id)::float
                        ,
                        (select COALESCE(sum(line.credit), 0.00) 
                        from account_move_line line, account_journal journal
                        where line.state='valid' and line.account_id in (select f_account_child_ids(account.id))
                        and line.journal_id = journal.id and journal.type<>'situation'
                        and line.period_id = period.id)::float
                        
                        from account_period period, 
                        account_mx_report_definition subreport 
                            left join account_account_mx_reports_rel subreport_accounts on subreport_accounts.mx_report_definition_id = subreport.id
                            left join account_account account on subreport_accounts.account_id = account.id
                            left join account_account_type account_type on account.user_type=account_type.id    
                        where period.id=x_period_id and
                        case x_parent_id 
                        when 0 then subreport.id = x_report_id
                        else subreport.parent_id = x_parent_id
                        end
                        order by subreport.parent_id, subreport.sequence, account.code;




                END
                $BODY$
                LANGUAGE 'plpgsql';

                --select * from f_get_mx_report_data_detail(14, 24, 1, 2)

                drop function if exists f_get_mx_report_data
                (x_report_id integer, x_period_id integer, x_uid integer);


                CREATE OR REPLACE FUNCTION f_get_mx_report_data
                (x_report_id integer, x_period_id integer, x_uid integer)
                RETURNS boolean 

                AS
                $BODY$

                DECLARE
                _cursor CURSOR FOR 
                    SELECT _a.id, _a.report_id, _a.parent_id, _a.name as report_section, case _a.sign when 'positive' then 1.0::float else -1.00::float end sign,
                    _a.sequence, _a.report_id_use_resume, _a.report_id_account, _a.report_id_label, _a.report_id_show_result, _a.internal_group        
                    from account_mx_report_definition _a 
                        where _a.parent_id = x_report_id 
                        order by _a.sequence;
                _result record;

                BEGIN
                    delete from account_mx_report_data;    
                    FOR _record IN _cursor
                    LOOP
                        insert into account_mx_report_data
                        (
                            create_uid, create_date, write_date, write_uid,
                        report_id, report_group, report_section, sequence, report_sign, account_sign, 
                        account_code, account_name, --account_id, 
                        period_id, 
                        initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                            )

                        select 
                        create_uid, create_date, write_date, write_uid,
                        report_id, report_group, report_section, sequence, report_sign, account_sign, 
                        account_code, account_name, --account_id, 
                        period_id, 
                        initial_balance, debit, credit,
                        (initial_balance  + account_sign * (debit - credit)) ending_balance,
                        (account_sign * (debit - credit)) debit_credit_ending_balance
                        from f_get_mx_report_data_detail(_record.id, x_period_id, x_uid, 0, '');
                        
                        IF _record.report_id is not null THEN
                            --RAISE NOTICE 'Hay un subreporte para % y la casilla resumido está en %', _record.report_section, _record.report_id_use_resume;
    
                            IF not _record.report_id_use_resume THEN
                                --RAISE NOTICE 'Entramos a generar el detalle del subreporte';
                                insert into account_mx_report_data
                                (
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                                )
                                select 
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit,
                                (initial_balance  + account_sign * (debit - credit)) ending_balance,
                                (account_sign * (debit - credit)) debit_credit_ending_balance                
                                from f_get_mx_report_data_detail(0, x_period_id, x_uid, _record.report_id, _record.internal_group);
                            ELSE
                                --RAISE NOTICE 'Generando solo el resultado del subreporte';
                                insert into account_mx_report_data
                                (
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, report_section, sequence, report_sign, account_sign, 
                                account_code, account_name, --account_id, 
                                period_id, 
                                initial_balance, debit, credit, ending_balance, debit_credit_ending_balance
                                )
                                select 
                                create_uid, create_date, write_date, write_uid,
                                _record.parent_id as report_id, report_group, _record.report_section report_section, _record.sequence as sequence, _record.sign as report_sign, 1 as account_sign, 
                                _record.report_id_account::varchar(64) as account_code, _record.report_id_label::varchar(64) as account_name, period_id, 
                                --sum(initial_balance) initial_balance, sum(debit) debit, sum(credit) credit,
                        sum(initial_balance * report_sign) as initial_balance, 0.0::float as debit, 0.0::float as credit,
                                sum(report_sign * (initial_balance  + account_sign * (debit - credit))) ending_balance,
                                sum(report_sign * account_sign * (debit - credit)) debit_credit_ending_balance
                                from f_get_mx_report_data_detail(0, x_period_id, x_uid, _record.report_id, _record.internal_group)
                                group by 
                                create_uid, create_date, write_date, write_uid,
                                report_id, report_group, period_id;            
                            END IF;
                        END IF;

                    END LOOP;

                    return true;

                END
                $BODY$
                LANGUAGE 'plpgsql';
    
                select * from f_get_mx_report_data(""" + str(params.report_id.id) + "," + str(params.period_id.id) + "," +  str(uid) + ")")

            data = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not data[0]:
                raise osv.except_osv(
                        _('Error en script!'),
                        _('No se pudo generar la informacion para este reporte, por favor verifique su configuracion y vuelva a intentarlo'))


            values = self.pool.get('account.mx_report_data').search(cr, uid, [('id', '!=', 0)])
            print params.report_type
            value = {
                'type'          : 'ir.actions.report.xml',
                'report_name'   : 'ht_reportes_contables_pdf' if params.report_type == 'pdf' else 'ht_reportes_contables_xls',
#                'jasper_output' : params.report_type,
                'datas'         : {
                                    'model' : 'account.mx_report_data',
                                    'ids'   : values,
#                                    'report_type'   : params.report_type,
#                                    'jasper_output' : params.report_type,
                                    }
                    } 

        return value
account_mx_report_data_wizard()





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
