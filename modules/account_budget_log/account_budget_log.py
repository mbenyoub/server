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
class account_budget_log_moments(osv.Model):
    _name = "account.budget.log.moments"

    def get_crossovered_budget_line(self, cr, uid, cros_budget_id, account_analytic_id, context=None):
        """
            Obtiene una linea del presupuesto en base a un presupuesto y una cuenta analitica
        """

        cros_budget_lines_obj = self.pool.get('crossovered.budget.lines')
        if context is None: context = {}
        account_analytic_obj = self.pool.get('account.analytic.account')
        account_analytic = account_analytic_obj.browse(cr, uid, account_analytic_id, context=context)

        #~ Obtiene la linea del presupuesto en base a los parametros
        args = [('crossovered_budget_id', '=' , cros_budget_id), ('analytic_account_id', '=', account_analytic_id)]
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        args.append(('company_id', '=', company_id))
        ids = cros_budget_lines_obj.search(cr, uid, args, context=context)

        print "************* Ids de lineas de pedido en la busqueda del presupuesto ********* ", ids

        if not ids:
            raise osv.except_osv(_('Error!'), _('No hay lineas del presupuesto para la cuenta analitica "' + account_analytic.name + '".'))
        cros_budget_lines_id = ids and ids[0] or False

        #~ Valida que se haya obtenido una linea de presupesto
        if cros_budget_lines_id == False:
            raise osv.except_osv(_('Error!'), _('No hay lineas del presupuesto para la cuenta analitica "' + account_analytic.name + '".'))

        return cros_budget_lines_id

    def get_crossovered_budget(self, cr, uid, dt=None, context=None):
        """
            Obtiene un presupuesto en base a una fecha
        """

        cros_budget_obj = self.pool.get('crossovered.budget')

        #~ Obtiene la fecha si no recibe el parametro
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self,cr,uid,context=context)

        #~ Obtiene la informacion del presupuesto en base a la fecha
        args = [('date_from', '<=' ,dt), ('date_to', '>=', dt), ('state', '!=', 'cancel')]
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        args.append(('company_id', '=', company_id))
        ids = cros_budget_obj.search(cr, uid, args, context=context)
        if not ids:
            raise osv.except_osv(_('Error!'), _('No hay presupuestos dados de alta a la fecha ' + dt + '.'))
        cros_budget_id = ids and ids[0] or False

        #~ Valida que se haya obtenido un presupesto
        if cros_budget_id == False:
            raise osv.except_osv('Error!','No hay registrado un presupuesto para la fecha ' + dt + '.')

        #~ Valida que el presupuesto este activo
        cros_budget = cros_budget_obj.browse(cr, uid, cros_budget_id, context=context)

        print "****************** Presupuesto ******************* ", cros_budget

        if cros_budget.state == 'draft':
            raise osv.except_osv('Error!','El presupuesto "' + cros_budget.name + '" no se ha confirmado.')
        if cros_budget.state == 'confirm':
            raise osv.except_osv('Error!','El presupuesto "' + cros_budget.name + '" no se ha validado.')
        if cros_budget.state == 'done':
            raise osv.except_osv('Error!','El presupuesto "' + cros_budget.name + '" ya esta cerrado.')

        return cros_budget_id

    def get_account_movement(self, cr, uid, state, context=None):
        """
            Obtiene la informacion de las cuentas segun el estado en el que se encuentra
        """

        budget_settings_obj = self.pool.get('account.budget.log.settings')
        args = [('config_active', '=' , True)]
        ids = budget_settings_obj.search(cr, uid, args, context=context)
        print "*********************** obtener config prespuesto ************* ", ids
        #~ Valida que haya configuracion registrada para el presupuesto
        if not ids:
            raise osv.except_osv('Error!','No estan configuradas las cuentas financieras del presupuesto.')
        budget_settings = budget_settings_obj.browse(cr, uid, ids[0], context=context)
        #~ Valida que haya un diario para las cuentas del presupuesto
        if not budget_settings.journal_budget_id.id:
            raise osv.except_osv('Error!','No esta configurado el diario financiero para los movimientos del presupuesto.')

        print "************** estado presupuesto ************ ", state

        if state == 'approve':
            #~ Valida que este la configuracion de las cuentas
            print "********* cuentas *********** aprobado ", budget_settings.account_approve.id, " por ejercer ", budget_settings.account_to_exercised.id
            if not budget_settings.account_approve.id or not budget_settings.account_to_exercised.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para afectar el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_approve.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_to_exercised.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'adjusted' or  state == 'inclusion' or state == 'extension':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_modify.id or not budget_settings.account_to_exercised.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para afectar el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_modify.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_to_exercised.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'decrease':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_modify.id or not budget_settings.account_to_exercised.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para afectar el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_to_exercised.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_modify.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'committed':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_to_exercised.id or not budget_settings.account_committed.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para comprometer el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_to_exercised.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_committed.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'accrued':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_committed.id or not budget_settings.account_accrued.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para devengar el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_committed.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_accrued.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'exercised':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_exercised.id or not budget_settings.account_accrued.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para ejercer el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_accrued.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_exercised.id, #~ Cuenta al Haber - Abono
            }
        elif state == 'paid':
            #~ Valida que este la configuracion de las cuentas
            if not budget_settings.account_paid.id or not budget_settings.account_exercised.id:
                raise osv.except_osv('Error!','No están configuradas las cuentas financieras para ejercer el prespuesto.')
            account_info = {
                'journal_id': budget_settings.journal_budget_id.id,
                'account_debit_id': budget_settings.account_exercised.id, #~ Cuenta al Debe - Cargo
                'account_credit_id': budget_settings.account_paid.id, #~ Cuenta al Haber - Abono
            }
        else:
            raise osv.except_osv('Error!','No hay informacion de cuentas disponible para afectar el presupuesto financiero.')

        return account_info

    def get_period_id(self, cr, uid, date, context=None):
        """
            Obtiene un periodo contable en base a una fecha
        """
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.find(cr, uid, date, context=context)
        period_id = period_ids and period_ids[0] or False

        print "*************** period *********** ", period_id, " *******  ", period_ids

        #~ Valida que se haya obtenido un periodo
        if period_id == False:
            raise osv.except_osv('Error!','No hay registrado un periodo para la fecha ' + date + '.')
        return period_id

    def conciliate_account_movement(self, cr, uid, params, context=None):
        """
            Aplica las afectaciones contables al movimiento seleccionado
        """

        account_obj = self.pool.get('account.account')
        cur_obj = self.pool.get('res.currency')
        move_obj = self.pool.get('account.move')
        line_move = []
        print "**************** Crea variables movimiento ***************************"

        #~ Recorre las lineas de pedido
        for line in params['line']:

            #~ Agrega movimiento al debe
            move_line_debit = (0,0,{
                'analytic_account_id': False,
                'tax_code_id': False,
                'name': params['reference'],
                'period_id': params['period_id'],
                'analytic_lines': [],
                'tax_amount': False,
                'ref': False,
                'asset_id': False,
                'analytics_id': False,
                'currency_id': False,
                'credit': False,
                'product_id': line['product_id'],
                'date_maturity': False,
                'debit': line['amount_total'],
                'date': params['date'],
                'amount_currency': 0,
                'product_uom_id': line['product_uom'],
                'quantity': line['quantity'],
                'partner_id': params['partner_id'],
                'account_id': params['account_debit_id']
            })

            #~ Agrega movimiento al haber
            move_line_credit = (0,0,{
                'analytic_account_id': False,
                'tax_code_id': False,
                'name': params['reference'],
                'period_id': params['period_id'],
                'analytic_lines': [],
                'tax_amount': False,
                'ref': False,
                'asset_id': False,
                'analytics_id': False,
                'currency_id': False,
                'credit': line['amount_total'],
                'product_id': line['product_id'],
                'date_maturity': False,
                'debit': False,
                'date': params['date'],
                'amount_currency': 0,
                'product_uom_id': line['product_uom'],
                'quantity': line['quantity'],
                'partner_id': params['partner_id'],
                'account_id': params['account_credit_id']
            })

            #~ Agrega los apuntes a las lineas del movimiento
            line_move.append(move_line_credit)
            line_move.append(move_line_debit)

        print "***************** cuenta que falla valor read ****************** ", account_obj.read(cr, uid, params['account_debit_id'], ['active'])
        print "***************** cuenta que falla valor read ****************** ", account_obj.read(cr, uid, params['account_credit_id'], ['active'])
        print "******************** lineas de movimiento *********************** ", line_move

        #~ Genera diccionario con la informacion del movimiento
        move = {
            'ref': params['reference'],
            'line_id': line_move,
            'journal_id': params['journal_id'],
            'date': params['date'],
            'narration':"Asientos generados por movimientos del presupuesto contable",
            'period_id': params['period_id'],
        }

        print "**************** Movimiento ******************* ", move

        #~ Crea la poliza con los movimientos
        move_id = move_obj.create(cr, uid, move, context=context)
        new_move_name = move_obj.browse(cr, uid, move_id, context=context).name
        # Pone los movimientos como asentados
        move_obj.post(cr, uid, [move_id], context=context)
        return True

    def create_log_movement(self, cr, uid, order, order_line, context=None):
        """
            Registra los movimimientos en la bitacora del presupuesto
        """

        print "************************* order *************************** ", order
        print "************************* order line *************************** ", order_line

        #~ Obtiene el nombre generico del movimiento
        name = "Movimiento/%s " %(order['state'])
        if order['document']:
            name = name + "/%s " %(order['document'])
        if order['reference'] != '':
            name = name + "/%s" %(order['reference'])

        log_ids = []

        #~ Recorre las lineas de pedido
        for line in order_line:
            name_line = name + "/%d" %(line['account_analytic_id'])

            #~ Valida que el monto tenga valor para registrarlo
            if line['amount_total'] == 0.0:
                continue

            # Agrega registro con el movimiento
            move = {
                'name': name_line,
                'account_analytic_id': line['account_analytic_id'],
                'amount': line['amount_total'],
                'reference': order['reference'],
                'state': order['state'],
                'move': True,
                'budget_id': order['budget']
            }

            print "**************************************************************************************"
            print move

            #~ Agrega el registro a la bitacora de movimientos
            log_ids.append(self.create(cr, uid, move, context=context))
            print "*********************", log_ids
        return log_ids

    def update_amount_budget_lines(self, cr, uid, order, order_line, context=None):
        """
            Actualiza los momentos de las lineas del presupuesto en base a la solicitud especificada
        """

        print "*********************** Acutualiza el presupuesto ************************ "

        cros_budget_lines_obj = self.pool.get('crossovered.budget.lines')

        #~ Obtiene el id del presupuesto
        cros_budget_id = self.get_crossovered_budget(cr, uid, order['date'], context=context)
        moment = "amount_" + order['state']

        #~ Recorre las lineas de pedido
        for line in order_line:
            #~ Obtiene la linea del presupuesto por la cuenta analitica
            cros_budget_lines_id = self.get_crossovered_budget_line(cr, uid, cros_budget_id, line['account_analytic_id'], context=None)
            cros_budget_lines = cros_budget_lines_obj.browse(cr, uid, cros_budget_lines_id, context=context)

            print "***************** id cuenta analitica ******************** ", cros_budget_lines.analytic_account_id

            print "***************** amount_adjusted ************************ ", cros_budget_lines.amount_adjusted
            print "***************** moment **********", moment, " ************** ", cros_budget_lines[moment]
            print "***************** total moment **********", moment,  "************** ", cros_budget_lines[moment] + line['amount_total']

            amount = float(cros_budget_lines[moment]) + float(line['amount_total'])

            #~ Valida que el monto a aplicar sea menor que el ajustado
            if float(cros_budget_lines.amount_adjusted) < amount:
                disponible = cros_budget_lines.amount_adjusted - cros_budget_lines[moment]
                account_analytic_obj = self.pool.get('account.analytic.account')
                account_analytic = account_analytic_obj.browse(cr, uid, line['account_analytic_id'], context=context)
                raise osv.except_osv('Error!','El monto del gasto rebasa el disponible en la cuenta analitica "' + account_analytic.name + '" (DISPONIBLE: ' + str(disponible) + ').')

            vals = {}
            vals[moment] = amount

            print "*************** Hace afectacion a linea del presupuesto ****************** "

            #~ Hace la afectacion en la linea del presupuesto
            cros_budget_lines_obj.write(cr, uid, cros_budget_lines_id, vals, context=context)
        return cros_budget_id


    def action_budget_log_movement(self, cr, uid, order, order_line, context=None):
        """
            Esta funcion agrega un registro con el monto del movimiento y afecta a las cuentas respectivas
        """

        print "***************************  budget_log  ******** ", order['state']

        #~ Obtiene el periodo en el que aplica para el presupuesto
        period_id = self.get_period_id(cr, uid, order['date'], context)
        print "***************************  obtiene el periodo *********************  ", period_id

        print "*********  Campos necesarios para contabilidad financiera se generan de manera directa para pruebas ************"

        #~ Obtiene la informacion de las cuentas segun el estado al que se aplica
        account_info = self.get_account_movement(cr, uid, order['state'], context)
        amount = order['total']

        """
            Afectaciones al presupuesto contable
        """

        #~ Crea arreglo con los parametros que se necesitan
        params_move = {
            'period_id' : period_id,
            'account_credit_id' : account_info['account_credit_id'],
            'account_debit_id' : account_info['account_debit_id'],
            'journal_id' : account_info['journal_id'],
            'amount' : amount,
            'reference' : order['reference'],
            'date' : order['date'],
            'partner_id': order['partner_id'],
            'line': order_line
        }

        #~ Genera las afectaciones contables sobre el presupuesto
        self.conciliate_account_movement(cr, uid, params_move, context)

        """
            Registra los movimientos en la bitacora
        """

        print "************************ Actualiza el presupuesto *************************** "

        #~ Actualiza los montos de las lineas de presupuesto
        budget_id = self.update_amount_budget_lines(cr, uid, order, order_line, context=context)
        order['budget'] = budget_id

        print "*************************** Registra los movimientos por cuenta analitica ***********************"

        #~ Registra los movimientos en la bitacora por producto
        self.create_log_movement(cr, uid, order, order_line, context=context)

        return True

    _columns = {
        'name' : fields.char(string="Nombre", size=256, required=True, help='Movimiento', readonly=True),
        'account_analytic_id' : fields.many2one('account.analytic.account', string='Cuenta Analitica', required=True, readonly=True, help="Cuenta analitica donde se esta afectando el momento presupuestal."),
        'date' : fields.date(string='Fecha', required=True, readonly=True),
        'amount' : fields.float(string='Monto', digits_compute=dp.get_precision('Account'), required=True, readonly=True),
        'reference': fields.char(string='Referencia', size=64, help="Referencia del movimiento sobre otro documento.", readonly=True),
        'state' : fields.selection([('approve','Presupuesto Aprobado'),
                                    ('adjusted','Modificación presupuesto'),
                                    ('inclusion','Inclusión presupuesto'),
                                    ('extension','Amplicación presupuesto'),
                                    ('decrease','Disminución presupuesto'),
                                    ('transfer','Transferencia presupuesto'),
                                    ('committed','Comprometido'),
                                    ('accrued','Devengado'),
                                    ('exercised','Ejercido'),
                                    ('paid','Pagado')],string="Estado", required=True, readonly=True),
        'description' : fields.text(string="Comentario", help='Información adicional sobre el movimiento'),
        'move': fields.boolean("Movimiento"),
        'budget_id': fields.many2one('crossovered.budget', 'Presupuesto', size=32, select=True, required=True, readonly=True),
    }

    _defaults = {
        'date' : fields.date.today,
        'move': True
    }

    _order = 'id desc'

    _sql_constraints = [
        (
            'name_description_check',
            'CHECK(name <> description)',
            'La descripción debe ser diferente del nombre del movimiento'
        ),
    ]
