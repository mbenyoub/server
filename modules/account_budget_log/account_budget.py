# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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

"""
    Herencia sobre modulo de compras en el area de solicitud para aplicar momento comprometido
"""

import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

def strToDate(dt):
    dt_date=datetime.date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))
    return dt_date

# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------

class crossvered_budget(osv.Model):
    """Inherited crossovered.budget"""

    def budget_cancel_validate(self, cr, uid, ids, context=None):
        """
            Valida que al cancelar el presupuesto no se encuentre en un estado validado o hecho
        """

        #~ Obtiene el presupesto
        cros_budget = self.browse(cr, uid, ids[0], context=context)

        print "******** id del presupuesto a cancelar ************* ", id
        print "********* budget a cancelar ******************", cros_budget
        print "********* budget estado ******************", cros_budget.state

        #~ Valida el estado del presupuesto
        if cros_budget.state == 'validate' or cros_budget.state == 'done':
            raise osv.except_osv('Error!','El presupuesto "' + cros_budget.name + '" no se puede eliminar porque se encuentra en estado "' + cros_budget.state + '".')

        return True

    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que el presupuesto no se pueda borrar si esta en estado validadon o Hecho
        """
        print "**************** funcion unlink ************************** "

        #~ Valida que el presupuesto a borrar no se encuentre en estado validado
        for cros_budget in self.browse(cr, uid, ids, context=context):
            if cros_budget.state == 'validate' or cros_budget.state == 'done':
               raise osv.except_osv('Error!','El presupuesto "' + cros_budget.name + '" no se puede eliminar porque se encuentra en estado "' + cros_budget.state + '".')

            print "***************** Eliminando presupuesto ", cros_budget.name, " estado ******** ", cros_budget.state

        return super(crossvered_budget, self).unlink(cr, uid, ids, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        """
            Duplicar la informacion del presupuesto
        """

        default = {} if default is None else default.copy()

        #~ Le agrega el simbolo de copia al nombre
        cros_budget = self.browse(cr, uid, id, context=context)
        new_name = "%s (Copy" % cros_budget.name
        # =like is the original LIKE operator from SQL - Regresa una lista de ids por el filtro aplicado
        others_count = self.search(cr, uid, [('name', '=like', new_name+'%')], count=True, context=context)
        if others_count > 0:
            new_name = "%s %s)" % (new_name, others_count+1)
        else:
            new_name = new_name + ")"

        default['name'] = new_name
        default['code'] = ''

        # en el copy hace un retorno con toda la informacion en base al id marcado
        return super(crossvered_budget, self).copy(cr, uid, id, default, context=context)

    def wkf_draft_budget(self, cr, uid, ids, context=None):
        """
            Pone el documento en estado borrador y limpia las lineas de presupuesto en los momentos
        """

        print "*********** Confirmado ***************"

        cros_budget_lines_obj = self.pool.get('crossovered.budget.lines')
        for crossvered_budget in self.browse(cr, uid, ids, context=context):
            print "************** Actualiza lineas por presupuesto *******************"

            crossvered_budget_line_ids = []

            for line in crossvered_budget.crossovered_budget_line:
                crossvered_budget_line_ids.append(line.id)

            #~ Recorre las lineas de pedido
            for cros_budget_lines in cros_budget_lines_obj.browse(cr, uid, crossvered_budget_line_ids, context=context):
                cros_budget_lines_obj.write(cr, uid, cros_budget_lines.id, {
                        'amount_approve': 0.0,
                        'amount_adjusted': 0.0,
                        'amount_committed': 0.0,
                        'amount_accrued': 0.0,
                        'amount_exercised': 0.0,
                        'amount_paid': 0.0,
                    })
        #~ Cambia el estado a borrador
        self.write(cr, uid, ids, {
            'state': 'draft',
        })

        return True

    def get_analytic_account_in_budget(self, cr, uid, budget_id, analytic_account, context=None):
        """
            Verifica si la cuenta analitica esta en las lineas de pedido del presupuesto, sino retorna false
        """

        print "**************** obtiene linea del presupuesto con cuenta analitica *********************"

        budget_lines_obj = self.pool.get('crossovered.budget.lines')
        budget = self.browse(cr, uid, budget_id, context=context)
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

        #~ Obtiene los ids de las lineas del presupuesto con la cuenta analitica
        args = [('crossovered_budget_id', '=' , budget_id), ('analytic_account_id', '=' , analytic_account)]
        lines_ids = budget_lines_obj.search(cr, uid, args, context=context)

        #~ Valida si encontro una linea del presupuesto con la cuenta analitica
        if len(lines_ids) > 0:
            #~ Retorna un diccionario con el detalle de la linea de presupuesto
            line = budget_lines_obj.browse(cr, uid, lines_ids[0], context=context)
            return {
                'line_id': line.id,
                'budget_id': line.general_budget_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'amount_approve': line.amount_approve,
                'amount_adjusted': line.amount_adjusted,
                'amount_available': round(float(line.amount_adjusted) - float(line.amount_committed), decimal_precision),
            }

        return False

    def wkf_budget_approve_amount(self, cr, uid, ids, context=None):
        """
            Actualiza el monto aprobado en las lineas del presupuesto
        """
        account_budget_log_obj = self.pool.get('account.budget.log.moments')
        cros_budget_lines_obj = self.pool.get('crossovered.budget.lines')
        date = fields.date.context_today(self,cr,uid,context=context)
        #~ Recorre los presupuestos para aprobar el monto en cada linea
        for cros_budget in self.browse(cr, uid, ids, context=context):
            #~ Obtiene los ids de las lineas de presupuesto
            args = [('crossovered_budget_id', '=' , cros_budget.id)]
            lines_ids = cros_budget_lines_obj.search(cr, uid, args, context=context)

            #~ Recorre las lineas de presupuesto
            for cros_budget_lines in cros_budget_lines_obj.browse(cr, uid, lines_ids, context=context):
                #~ Actualiza los campos de la linea de presupuesto
                cros_budget_lines_obj.write(cr, uid, cros_budget_lines.id, {
                    'amount_approve': cros_budget_lines.planned_amount,
                    'amount_adjusted': cros_budget_lines.planned_amount,
                })

                #~ Obtiene el periodo en el que aplica para el presupuesto
                period_id = account_budget_log_obj.get_period_id(cr, uid, date, context)
                #~ Obtiene la informacion de las cuentas segun el estado al que se aplica
                account_info = account_budget_log_obj.get_account_movement(cr, uid, 'approve', context)

                """
                    Afectaciones al presupuesto contable
                """

                #~ Crea arreglo con los parametros que se necesitan
                params_move = {
                    'period_id' : period_id,
                    'account_credit_id' : account_info['account_credit_id'],
                    'account_debit_id' : account_info['account_debit_id'],
                    'journal_id' : account_info['journal_id'],
                    'amount' : cros_budget_lines.planned_amount,
                    'reference' : cros_budget.name,
                    'date' : date,
                    'partner_id': None,
                    'line': [{
                        'product_id': None,
                        'product_uom': None,
                        'quantity': None,
                        'amount_total': cros_budget_lines.planned_amount
                    },]
                }

                #~ Genera las afectaciones contables sobre el presupuesto
                account_budget_log_obj.conciliate_account_movement(cr, uid, params_move, context)

                """
                    Afectaciones al presupuesto analitico
                """

                #~ Actualiza la bitacora
                name = "Presupuesto/Approve/" + str(cros_budget.code) + "/" + str(cros_budget_lines.analytic_account_id.id)
                account_budget_log_obj.create(cr, uid, {
                    'name': name,
                    'account_analytic_id': cros_budget_lines.analytic_account_id.id,
                    'amount': cros_budget_lines.planned_amount,
                    'reference': cros_budget.name,
                    'state': 'approve',
                    'move': False,
                    'budget_id': cros_budget.id
                }, context=context)

        return True

    def account_budget_adjusted_amount(self, cr, uid, lines, context=None):
        """
            Actualiza el monto ajustado en las lineas del presupuesto
        """
        account_budget_log_obj = self.pool.get('account.budget.log.moments')
        budget_lines_obj = self.pool.get('crossovered.budget.lines')
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        date = fields.date.context_today(self,cr,uid,context=context)
        #~ Recorre las lineas del prespuesto
        for line in lines:
            #~ Actualiza el monto ajustado en la linea del presupuesto
            amount_adjusted = round(float(line['amount_adjusted']) + float(line['extension_amount']), decimal_precision)
            budget_lines_obj.write(cr, uid, line['line_id'], {'amount_adjusted': amount_adjusted}, context=context)
            cros_budget = self.browse(cr, uid, line['budget_id'], context=context)

            #~ Obtiene el periodo en el que aplica para el presupuesto
            period_id = account_budget_log_obj.get_period_id(cr, uid, date, context)
            #~ Obtiene la informacion de las cuentas segun el estado al que se aplica
            account_info = account_budget_log_obj.get_account_movement(cr, uid, line['state'], context)

            """
                Afectaciones al presupuesto contable
            """

            if line['state'] == 'decrease':
                amount = line['extension_amount'] * -1
            else:
                amount = line['extension_amount']

            #~ Crea arreglo con los parametros que se necesitan
            params_move = {
                'period_id' : period_id,
                'account_credit_id' : account_info['account_credit_id'],
                'account_debit_id' : account_info['account_debit_id'],
                'journal_id' : account_info['journal_id'],
                'amount' : amount,
                'reference' : cros_budget.name,
                'date' : date,
                'partner_id': None,
                'line': [{
                    'product_id': None,
                    'product_uom': None,
                    'quantity': None,
                    'amount_total': amount
                },]
            }

            #~ Genera las afectaciones contables sobre el presupuesto
            account_budget_log_obj.conciliate_account_movement(cr, uid, params_move, context)

            """
                Afectaciones al presupuesto analitico
            """

            #~ Actualiza la bitacora
            name = "Presupuesto/" + line['state'] + "/" + str(cros_budget.code) + "/" + str(line['analytic_account_id'])
            name = name + "-" + str(line['destiny']) if line['state'] == 'transfer' else name
            print "****************** new log **************** ", name
            account_budget_log_obj.create(cr, uid, {
                'name': name,
                'account_analytic_id': line['analytic_account_id'],
                'amount': line['extension_amount'],
                'reference': cros_budget.name,
                'state': line['state'],
                'move': False,
                'budget_id': cros_budget.id,
            }, context=context)

        return True

    def _check_account_analytic_not_repeat(self, cr, uid, ids, context=None):
        """
            Valida que el presupuesto no tenga cuentas analiticas repetidas en las lineas del presupuesto
        """

        print "***************** Valida que no haya cuentas analiticas repetidas ******************** "

        #~ Recorre el presupuesto
        for budget in self.browse(cr, uid, ids, context=context):
            #~ Valida que no haya cuentas analiticas repetidas en las lineas del presupuesto
            cr.execute("select count(id) as cantidad from crossovered_budget_lines where crossovered_budget_id='" + str(budget.id) + "' group by analytic_account_id having count(id) > 1")
            if cr.fetchone():
                return False
        return True

    def _check_period_budget(self, cr, uid, ids, context=None):
        """
            Valida que el periodo del presupuesto no se cruce con otro
        """

        print "***************** Valida que el periodo no se cruce con otro ******************** "

        #~ Recorre el presupuesto
        for budget in self.browse(cr, uid, ids, context=context):
            if budget.company_id:
                company_id = budget.company_id.id
            else:
                company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id

            #~ Valida que la fecha inicial no choque con el presupuesto
            args = [('date_from', '<=' ,budget.date_from), ('date_to', '>=', budget.date_from), ('id', '!=', budget.id), ('state', '!=', 'cancel')]
            args.append(('company_id', '=', company_id))
            print "***************** args ************************ ", args
            ids = self.search(cr, uid, args, context=context)
            if ids:
                print "************** ids ********************** ", ids
                return False
            #~ Valida que la fecha final no choque con el presupuesto
            args = [('date_from', '<=' ,budget.date_to), ('date_to', '>=', budget.date_to), ('id', '!=', budget.id), ('state', '!=', 'cancel')]
            args.append(('company_id', '=', company_id))
            print "***************** args ************************ ", args
            ids = self.search(cr, uid, args, context=context)
            if ids:
                print "************** ids ********************** ", ids
                return False
        return True

    def _check_date_period_budget(self, cr, uid, ids, context=None):
        """
            Valida que la fecha inicial no sea mayor a la fecha final en el presupuesto
        """

        print "***************** Valida fechas presupuesto ******************** "

        from datetime import datetime

        #~ Recorre el presupuesto
        for budget in self.browse(cr, uid, ids, context=context):
            date_from = datetime.strptime(budget.date_from, '%Y-%m-%d')
            date_to = datetime.strptime(budget.date_to, '%Y-%m-%d')

            print "*************** fecha tipo ************* ", type(date_to)

            if date_from >= date_to:
                print "****************** fecha incorrecta *********************** "
                return False
        return True

    _inherit = 'crossovered.budget'

    _columns = {
    }

    _constraints = [
        (_check_account_analytic_not_repeat, "No puede haber cuentas analiticas repetidas en las lineas del presupuesto",   ['crossovered_budget_line']),
        (_check_period_budget, "El periodo del presupuesto choca con otro periodo ya registrado",   ['date_from','date_to']),
        (_check_date_period_budget, "El periodo seleccionado para el presupuesto es incorrecto",   ['date_from','date_to']),
    ]

class crossovered_budget_lines(osv.Model):
    """Inherited crossovered.budget.lines"""

    def copy(self, cr, uid, id, default, context=None):
        """
            Duplicar la informacion de la linea de presupuesto
        """

        print "********** Lines Default *************** ", default

        default_get = super(crossovered_budget_lines, self).default_get(cr, uid, ['amount_approve','amount_adjusted','amount_committed'], context=context)

        print "************* Lines default get ***********", default_get

        # en el copy hace un retorno con toda la informacion en base al id marcado
        return super(crossovered_budget_lines, self).copy(cr, uid, id, default_get, context=context)


    def _get_date_from_budget(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la fecha del presupuesto y la guarda en la linea
        """
        crossovered_budget_obj = self.pool.get('crossovered.budget')
        res = {}
        #~ Recorre las lineas del presupuesto
        for line in self.browse(cr, uid, ids, context=context):
            budget_id = line.crossovered_budget_id.id
            #~ Valida que se encuentre ligado a un presupuesto
            if line.crossovered_budget_id:
                #~ Actualiza la fecha en base al presupuesto
                budget = crossovered_budget_obj.browse(cr, uid, budget_id, context=context)
                res[line.id] = budget.date_from
            else:
                raise osv.except_osv('Error!','Tiene que seleccionar el periodo del presupuesto.')
        return res

    def _get_date_to_budget(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene la fecha del presupuesto y la guarda en la linea
        """
        crossovered_budget_obj = self.pool.get('crossovered.budget')
        res = {}
        #~ Recorre las lineas del presupuesto
        for line in self.browse(cr, uid, ids, context=context):
            budget_id = line.crossovered_budget_id.id
            #~ Valida que se encuentre ligado a un presupuesto
            if line.crossovered_budget_id:
                #~ Actualiza la fecha en base al presupuesto
                budget = crossovered_budget_obj.browse(cr, uid, budget_id, context=context)
                res[line.id] = budget.date_to
            else:
                raise osv.except_osv('Error!','Tiene que seleccionar el periodo del presupuesto.')
        return res

    _inherit = 'crossovered.budget.lines'

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', required=True),
        'date_from': fields.function(_get_date_from_budget, string='Start_Date', type='date'),
        'date_to': fields.function(_get_date_to_budget, string='End_Date', readonly=True, type='date'),
        'planned_amount': fields.float(string='Monto Planeado', required=True, digits_compute=dp.get_precision('Account')),
        'amount_approve': fields.float(string='Monto aprobado', readonly=True, digits_compute=dp.get_precision('Account')),
        'amount_adjusted': fields.float(string='Monto ajustado', readonly=True, digits_compute=dp.get_precision('Account')),
        'amount_committed': fields.float(string='Monto comprometido', readonly=True, digits_compute=dp.get_precision('Account')),
        'amount_accrued': fields.float(string='Monto devengado', readonly=True, digits_compute=dp.get_precision('Account')),
        'amount_exercised': fields.float(string='Monto ejercido', readonly=True, digits_compute=dp.get_precision('Account')),
        'amount_paid': fields.float(string='Monto pagado', readonly=True, digits_compute=dp.get_precision('Account')),
        'state' : fields.selection([('draft','Draft'),('cancel', 'Cancelled'),('confirm','Confirmed'),('validate','Validated'),('done','Done')], 'Status', select=True, required=True, readonly=True),
    }

    _defaults = {
        'planned_amount': 0.0,
        'amount_approve': 0.0,
        'amount_adjusted': 0.0,
        'amount_committed': 0.0,
        'amount_accrued': 0.0,
        'amount_exercised': 0.0,
        'amount_paid': 0.0,
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.budget.post', context=c),
    }

crossovered_budget_lines()
