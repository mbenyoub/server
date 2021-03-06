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
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp
from openerp import netsvc

#----------------------------------------------------------
# Accounts
#----------------------------------------------------------

class account_account_sat(osv.osv):
    _order = "parent_left,code"
    _parent_order = "code"
    _name = "account.account.sat"
    _description = "Account"
    _parent_store = True

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}
        pos = 0

        while pos < len(args):
            if args[pos][0] == 'code' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('code', '=like', tools.ustr(args[pos][2].replace('%', ''))+'%')
            if args[pos][0] == 'journal_id':
                if not args[pos][2]:
                    del args[pos]
                    continue
                #jour  = self.pool.get('account.journal').browse(cr, uid, args[pos][2], context=context)
                #if (not (jour.account_control_ids or jour.type_control_ids)) or not args[pos][2]:
                #    args[pos] = ('type','not in',('view'))
                #    continue
                #ids3 = map(lambda x: x.id, jour.type_control_ids)
                #ids1 = super(account_account_sat, self).search(cr, uid, [('user_type', 'in', ids3)])
                #ids1 += map(lambda x: x.id, jour.account_control_ids)
                #args[pos] = ('id', 'in', ids1)
            pos += 1

        return super(account_account_sat, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def _get_account_balance(self, cr, uid, account, context=None):
        """
            Obtiene el resultado del cargo y abono sobre cuentas de tipo regular
        """
        # Inicializa la variable de retorno
        res = {
            'balance': 0.0,
            'credit': 0.0,
            'debit': 0.0
        }
        # Valida que la cuenta sea de tipo regular, sino regresa el resultado en ceros
        if account.type == 'other':
            # Recorre las cuentas del plan contable que estan relacionadas al mismo y obtiene el resultado
            for acc in account.account_ids:
                # Suma a los totales
                res['credit'] += acc.credit
                res['debit'] += acc.debit
                res['balance'] += acc.balance
        return res

    def _get_account_view(self, cr, uid, account, res={}, context=None):
        """
            Obtiene el resultado del cargo y abono sobre cuentas de tipo vista
        """
        # Inicializa la variable de retorno
        res[account.id] = {
            'balance': 0.0,
            'credit': 0.0,
            'debit': 0.0
        }
        # Valida que la cuenta sea de tipo regular, sino regresa el resultado en ceros
        if account.type == 'view':
            # Recorre las cuentas del plan contable que estan relacionadas al mismo y obtiene el resultado
            for acc in account.child_parent_ids:
                # Valida que no se haya obtenido el resultado de la cuenta
                if res.get(acc.id, False) == False:
                    # Valida que la cuenta sea de tipo regular
                    if acc.type == 'other':
                        # Obtiene el valor de la cuenta
                        res[acc.id] = self._get_account_balance(cr, uid, acc, context=context)
                    # Si es de tipo vista obtiene el valor
                    elif acc.type == 'view':
                        # Obtiene el valor de la cuenta
                        res.update(self._get_account_view(cr, uid, acc, context=context))
                    
                # Actualiza el resultado de la vista
                res[account.id]['credit'] += res[acc.id]['credit']
                res[account.id]['debit'] += res[acc.id]['debit']
                res[account.id]['balance'] += res[acc.id]['balance']
                
        return res

    #def __compute(self, cr, uid, ids, field_names, arg=None, context=None, query='', query_params=()):
    #    """
    #        Calcula el Debe y el Haber de la cuenta en base a las cuentas seleccionadas del plan contable
    #    """
    #    res = {}
    #    # Inicializa los valores de retorno en ceros
    #    for id in ids:
    #        res[id] = {
    #            'balance': 0.0,
    #            'credit': 0.0,
    #            'debit': 0.0
    #        }
    #    
    #    # Obtiene las cuentas de tipo vista de los ids que se van a calcular
    #    acc_ids = self.search(cr, uid, [('id','in',ids),('type','=','view')], context=context)
    #    print "**************************** acc_ids ************** ", acc_ids
    #    # Agrega los ids de las cuentas que no tienen un padre o no se encuentra en la lista
    #    acc_reg_ids = self.search(cr, uid, [('id','in',ids),('type','=','other'),'|',('parent_id','=',None),('parent_id','not in',ids)], context=context)
    #    print "******************** acc_reg_ids *********************** ", acc_reg_ids
    #    acc_ids.extend(acc_reg_ids)
    #    print "*************************** acc_ids **************** ", acc_ids
    #    
    #    # Recorre los registros
    #    for account in self.browse(cr, uid, acc_ids, context=context):
    #        # Valida que no se haya obtenido el resultado de la cuenta
    #        if not res.get(account.id, False)['balance']:
    #            # Valida que la cuenta sea de tipo regular
    #            if account.type == 'other':
    #                # Obtiene el valor de la cuenta
    #                res[account.id] = self._get_account_balance(cr, uid, account, context=context)
    #            # Si es de tipo vista obtiene el valor
    #            elif account.type == 'view':
    #                # Obtiene el valor de la cuenta
    #                res.update(self._get_account_view(cr, uid, account, context=context))
    #    return res

    def _get_ctx_balance_init(self, cr, uid, context=None):
        """
            Obtiene la informacion para obtener la poliza de saldos iniciales
        """
        if context is None:
            context = {}
        ctx = context.copy()

        period_obj = self.pool.get('account.period')
        where = ""
        # Revisa los parametros para ver de donde se obtiene la informacion y genera una validacion para obtener el registro
        if ctx.get('periods',False):
            period_list = tuple(context.get('periods'))
            if len(context.get('periods')) == 1:
                period_list = '(%s)'%(context.get('periods')[0],)
            elif len(context.get('periods')) == 0:
                period_list = '()'
            where = "where id in %s "%(period_list,)
        elif ctx.get('period_from',False) and ctx.get('period_to'):
            where = "where id = %s "%(context.get('period_from',False))
        elif ctx.get('fiscalyear',False):
             where = "where fiscalyear_id = %s "%(context.get('fiscalyear',False))           

        cr.execute(" select id as id, date_start from account_period %s order by date_start asc "%(where))
        dat = cr.dictfetchall()
        date = dat and dat[0].get('date_start',False) or False
        if date:
            print "************** date ********** ", date
            # Obtiene todos los periodos anteriores al filtro aplicado
            ctx['periods'] = period_obj.search(cr, uid, [('date_stop','<=',date)])
        # Borra los datos ya no necesarios del context
        if ctx.has_key('period_from'):
            ctx.pop('period_from')
        if ctx.has_key('period_to'):
            ctx.pop('period_to')
        if ctx.has_key('fiscalyear'):
            ctx.pop('fiscalyear')
        return ctx

    def _get_children(self, cr, uid, ids, context=None):
        """
            Obtiene las cuentas hijas relacionadas a las cuentas recibidas
        """
        #this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)], context=context)
        ids3 = []
        if ids3:
            ids3 = self._get_children(cr, uid, ids3, context)
        return ids2 + ids3

    def __compute(self, cr, uid, ids, field_names, arg=None, context=None,
                  query='', query_params=()):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "CASE WHEN a.currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END as foreign_balance",
        }
        #get all the necessary accounts
        children = self._get_children(cr, uid, ids, context=context)
        #print "******************** cuentas hijas ************* ", children
        print "************* field names ************ ", field_names
        field_names = ['debit','credit','balance','foreign_balance','balance_init','balance_end']

        #compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        print "*************** null_result ************** ", null_result
        
        print "*************** null_result ************** ", null_result
        if children:
            print "****************** context ******************** ", context
            aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
            print "**************************** aml_query ****************** ", aml_query
            print "**************************** aml_query ****************** ", aml_query.strip()
            print "**************************** query ****************** ", query

            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            # Consulta para obtencion de informacion saldos cuentas
            request = ("SELECT a.account_sat_id as id, " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " INNER JOIN account_account as a on l.account_id=a.id" \
                       " WHERE a.account_sat_id IN %s " \
                            + filters +
                       " GROUP BY a.account_sat_id, a.currency_id")
            print "************ request ************** ", request
            params = (tuple(children),) + query_params
            print "************* params ***************** ", params
            cr.execute(request, params)
            for row in cr.dictfetchall():
                if accounts.get(row['id'],False):
                    accounts[row['id']]['credit'] += row['credit']
                    accounts[row['id']]['debit'] += row['debit']
                    accounts[row['id']]['balance'] += row['balance']
                    accounts[row['id']]['foreign_balance'] += row['foreign_balance']
                else:
                    accounts[row['id']] = {
                        'balance_init': 0.0,
                        'balance_end': 0.0,
                        'balance': row['balance'],
                        'credit': row['credit'],
                        'debit': row['debit'],
                        'foreign_balance': row['foreign_balance']
                    }

            # Valida que haya periodos disponibles para calcular el saldo de la cuenta
            ctx = self._get_ctx_balance_init(cr, uid, context=context)
            if ctx.get('periods'):
                # Agrega el saldo inicial sobre la cuenta
                print "****************** ctx balance inicial ******************** ", ctx
                aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)
                print "**************************** aml_query init ****************** ", aml_query
                print "**************************** aml_query init ****************** ", aml_query.strip()
                wheres = [""]
                if query.strip():
                    wheres.append(query.strip())
                if aml_query.strip():
                    wheres.append(aml_query.strip())
                filters = " AND ".join(wheres)
                # Consulta para obtencion de informacion saldos cuentas
                request = ("SELECT a.account_sat_id as id, " +\
                           ', '.join(mapping.values()) +
                           " FROM account_move_line l" \
                           " INNER JOIN account_account as a on l.account_id=a.id" \
                           " WHERE a.account_sat_id IN %s " \
                                + filters +
                           " GROUP BY a.account_sat_id, a.currency_id")
                print "************ request ************** ", request
                params = (tuple(children),) + query_params
                #print "************* params ***************** ", params
                cr.execute(request, params)
                for row in cr.dictfetchall():
                    if accounts.get(row['id'],False):
                        accounts[row['id']]['balance_init'] += row['balance']
                    else:
                        accounts[row['id']] = {
                            'balance_init': row['balance'],
                            'balance_end': 0.0,
                            'balance': 0.0,
                            'credit': 0.0,
                            'debit': 0.0,
                            'foreign_balance': 0.0
                        }

            # consolidate accounts with direct children
            children.reverse()
            brs = list(self.browse(cr, uid, children, context=context))
            sums = {}
            currency_obj = self.pool.get('res.currency')
            while brs:
                current = brs.pop(0)
                #print "************** field_names ************** ", field_names
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    for child in current.child_id:
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)
                #print "*************** sums **************** ", sums

            for id in ids:
                res[id] = sums.get(id, null_result)
                # Actualiza el saldo final
                res[id]['balance_end'] = res[id]['balance_init'] + res[id]['balance']
        else:
            for id in ids:
                res[id] = null_result
        return res

    def _get_company_currency(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la moneda de la compañia
        """
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            result[rec.id] = (rec.company_id.currency_id.id,rec.company_id.currency_id.symbol)
        return result

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el nivel de la cuenta
        """
        res = {}
        for account in self.browse(cr, uid, ids, context=context):
            #we may not know the level of the parent at the time of computation, so we
            # can't simply do res[account.id] = account.parent_id.level + 1
            level = 0
            parent = account.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            res[account.id] = level
        return res

    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene las cuentas hijas de la cuenta
        """
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.child_parent_ids:
                result[record.id] = [x.id for x in record.child_parent_ids]
            else:
                result[record.id] = []

        return result

    _columns = {
        'name': fields.char('Nombre', size=256, required=True, select=True),
        'code': fields.char('Codigo SAT', size=16, required=False, select=1),
        'number': fields.char('Numero de Cuenta', size=32, required=False, select=1),
        'type': fields.selection([
            ('view', 'Vista'),
            ('other', 'Regular')], 'Tipo cuenta', required=True, help="Las cuentas de vista son identificadas como cuentas agrupadoras. Las cuentas regulares trabajan sobre las subcuentas del plan contable"),
        'nature': fields.selection([
            ('D', 'Deudora'),
            ('A', 'Acreedora')], 'Naturaleza', required=True, help="Naturaleza de la cuenta"),
        'parent_id': fields.many2one('account.account.sat', 'Cuenta Padre', ondelete='cascade', domain=[('type','=','view')]),
        'child_parent_ids': fields.one2many('account.account.sat','parent_id','Cuentas Hijas'),
        'child_id': fields.function(_get_child_ids, type='many2many', relation="account.account.sat", string="Cuentas Hijas"),
        
        'balance': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Saldo', store=False, multi='balance'),
        'credit': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Haber', store=False, multi='balance'),
        'debit': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Debe', store=False, multi='balance'),
        'balance_init': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Saldo inicial', store=False, multi='balance'),
        'balance_end': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Saldo final', store=False, multi='balance'),
        
        'note': fields.text('Notas internas'),
        'currency_id': fields.function(_get_company_currency, type='many2one', relation='res.currency', string='Moneda'),
        'company_id': fields.many2one('res.company', 'Compañia', required=True),
        'active': fields.boolean('Active', select=2, help="Si el campo activo se establece en False, que le permitirá ocultar la cuenta sin eliminarla."),
        'parent_left': fields.integer('Parent Left', select=1),
        'parent_right': fields.integer('Parent Right', select=1),
        'level': fields.function(_get_level, string='Level', method=True, type='integer', store=True),
        'account_ids': fields.one2many('account.account','account_sat_id','Cuentas plan contable', domain=[('type','!=','view')]),
    }

    _defaults = {
        'type': 'other',
        'active': True,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
        'nature': 'D'
    }

    def _check_recursion(self, cr, uid, ids, context=None):
        """
            Valida que las cuentas no sean recursivas
        """
        obj_self = self.browse(cr, uid, ids[0], context=context)
        p_id = obj_self.parent_id and obj_self.parent_id.id
        if (p_id and (p_id is obj_self.id)):
            return False
        return True

    def _check_type(self, cr, uid, ids, context=None):
        """
            Valida el tipo de la cuenta
        """
        if context is None:
            context = {}
        accounts = self.browse(cr, uid, ids, context=context)
        for account in accounts:
            print "*************** checa tipo cuenta ***************** ", account.code
            #print "*************** tipo cuenta ***************** ", account.type
            print "*************** checa cuenta ***************** ", account.child_id
            if account.child_id and account.type not in ['view']:
                return False
        return True

    def _check_company_account(self, cr, uid, ids, context=None):
        """
            Valida que la cuenta sea de la misma compañia
        """
        for account in self.browse(cr, uid, ids, context=context):
            if account.parent_id:
                if account.company_id != account.parent_id.company_id:
                    return False
        return True

    def _check_code_uniq(self, cr, uid, ids, context=None):
        """
            Valida que el codigo no se repita en las cuentas
        """
        # Recorre los registros
        for account in self.browse(cr, uid, ids, context=context):
            # Si es vacio continua con el proceso
            if account.code == '' or account.code == False or account.code is None:
                continue
            print "********** cuenta ", account.name, "  ********* ", account.code
            
            # Busca si hay cuentas con el mismo codigo
            account_ids = self.search(cr, uid, [('code','=',account.code),('company_id','=',account.company_id.id or False),('id','!=', account.id)], context=context)
            if account_ids:
                return False
        return True

    def _check_number_uniq(self, cr, uid, ids, context=None):
        """
            Valida que el numero de cuenta no se repita
        """
        # Recorre los registros
        for account in self.browse(cr, uid, ids, context=context):
            print "********** cuenta ", account.name, "  ********* ", account.number
            
            # Busca si hay cuentas con el mismo numero de cuenta
            account_ids = self.search(cr, uid, [('number','=',account.number),('company_id','=',account.company_id.id or False),('id','!=', account.id)], context=context)
            if account_ids:
                return False
        return True

    _constraints = [
        (_check_recursion, 'Error!\nTu no puedes crear cuentas de forma recursiva.', ['parent_id']),
        (_check_type, 'Error de Configuracion!\nNo se puede definir a los hijos a una cuenta con el tipo interno diferente de "Vista".', ['type']),
        (_check_company_account, 'Error!\nNo se puede crear una cuenta que tiene en cuenta los padres de diferente empresa.', ['parent_id']),
        (_check_code_uniq, 'Error!\nEl codigo de la cuenta debe ser unico por compañia!.', ['code']),
        (_check_number_uniq, 'Error!\nEl Numero de cuenta debe ser unico por compañia!.', ['number']),
    ]
    _sql_constraints = [
        #('code_company_uniq', 'unique (code,company_id)', 'El codigo de la cuenta debe ser unico por compañia!')
    ]
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        try:
            if name and str(name).startswith('partner:'):
                part_id = int(name.split(':')[1])
                part = self.pool.get('res.partner').browse(cr, user, part_id, context=context)
                args += [('id', 'in', (part.property_account_payable.id, part.property_account_receivable.id))]
                name = False
            if name and str(name).startswith('type:'):
                type = name.split(':')[1]
                args += [('type', '=', type)]
                name = False
        except:
            pass
        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, ['|', ('code', '=like', name+"%"), '|', ('number', '=like', name+"%"), ('name', operator, name)]+args, limit=limit)
                if not ids and len(name.split()) >= 2:
                    #Separating code and name of account for searching
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit)
            else:
                ids = self.search(cr, user, ['&','!', ('code', '=like', name+"%"), ('name', operator, name)]+args, limit=limit)
                # as negation want to restric, do if already have results
                if ids and len(name.split()) >= 2:
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2), ('id', 'in', ids)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code', 'number'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['number']:
                name = '[%s] %s'%(record['number'],name) 
            if record['code']:
                name = '%s- %s'%(record['code'],name) 
            res.append((record['id'], name))
        return res

    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        """
            Modificacion de funcion duplicar
        """
        default = {} if default is None else default.copy()
        if done_list is None:
            done_list = []
        account = self.browse(cr, uid, id, context=context)
        new_child_ids = []
        default.update(code=_("%s (copy)") % (account['code'] or ''))
        default.update(number=_("%s (copy)") % (account['number'] or ''))
        
        print "**************** Default ***************** ", default
        
        if not local:
            done_list = []
        if account.id in done_list:
            return False
        done_list.append(account.id)
        
        if context.get('done_list',False):
            return False
        
        if account:
            # Hace que se omitan las cuentas hijas relacionadas con la cuenta a duplicar
            for child in account.child_id:
                done_list.append(child.id)
            context['done_list'] = done_list
        
        if account:
            for child in account.child_id:
                child_ids = self.copy(cr, uid, child.id, default, context=context, done_list=done_list, local=True)
                if child_ids:
                    new_child_ids.append(child_ids)
            default['child_parent_ids'] = [(6, 0, new_child_ids)]
        else:
            default['child_parent_ids'] = False
        return super(account_account_sat, self).copy(cr, uid, id, default, context=context)

    def _check_allow_type_change(self, cr, uid, ids, new_type, context=None):
        """
            Valida que no se pueda cambiar el tipo de una cuenta regular que tenga cuentas ya relacionadas
        """
        # Recorre los registros
        for account in self.browse(cr, uid, ids, context=context):
            old_type = account.type
            # Valida que los tipos sean diferentes al actual
            if old_type == new_type:
                continue
            
            # Valida que si el tipo es regular no tenga relaciones con cuentas 
            if old_type == 'other' and account.account_ids:
                raise osv.except_osv(_('Warning!'), _("No se puede cambiar el tipo de cuenta de '%s' a '%s' si las cuentas estan relacionadas con cuentas del plan contable!") % (old_type,new_type,))
            # Valida que sila cuenta es de vista no tenga relacion con otras cuentas hijas
            if old_type == 'view' and self.search(cr, uid, [('parent_id','=',account.id)], context=context):
                raise osv.except_osv(_('Warning!'), _("No se puede cambiar el tipo de cuenta de '%s' a '%s' si la cuenta sat se esta usando como cuenta padre!") % (old_type,new_type,))
        return True

    def _check_accounts(self, cr, uid, ids, method, context=None):
        """
            Si tiene cuentas del plan contable asignadas no deja inactivar la cuenta SAT
        """
        account_obj = self.pool.get('account.account')
        account_sat_ids = self.search(cr, uid, [('id', 'child_of', ids)])
        
        # valida que la cuenta no este relacionada sobre cuentas del plan contable
        if account_obj.search(cr, uid, [('account_sat_id', 'in', account_sat_ids)]):
            if method == 'write':
                raise osv.except_osv(_('Error!'), _('Tu no puedes desactivar cuentas sat relacionadas sobre el plan contable.'))
            elif method == 'unlink':
                raise osv.except_osv(_('Error!'), _('No se puede eliminar la cuenta si tiene relaciones sobre el plan contable.'))
        
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]

        # Dont allow changing the company_id when account_move_line already exist
        if 'company_id' in vals:
            move_lines = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', ids)])
            if move_lines:
                # Allow the write if the value is the same
                for i in [i['company_id'][0] for i in self.read(cr,uid,ids,['company_id'])]:
                    if vals['company_id']!=i:
                        raise osv.except_osv(_('Warning!'), _('You cannot change the owner company of an account that already contains journal items.'))
        if 'active' in vals and not vals['active']:
            self._check_accounts(cr, uid, ids, "write", context=context)
        if 'type' in vals.keys():
            self._check_allow_type_change(cr, uid, ids, vals['type'], context=context)
        return super(account_account_sat, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        self._check_accounts(cr, uid, ids, "unlink", context=context)
        return super(account_account_sat, self).unlink(cr, uid, ids, context=context)

account_account_sat()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
