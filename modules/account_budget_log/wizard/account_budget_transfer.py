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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_budget_log_create_transfer_budget_wizard(osv.TransientModel):
    _name = 'account.budget.log.create.transfer.budget.wizard'

    def action_add_transfer_budget(self, cr, uid, ids, context=None):
        """
            Aplica una transferencia sobre las lineas del presupuesto
        """
        print "******************** Transferencia al presupuesto *********************** "

        budget_obj = self.pool.get('crossovered.budget')
        budget_lines_obj = self.pool.get('crossovered.budget.lines')
        transfer = self.browse(cr, uid, ids[0], context=context)
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

        #~ Valida que haya un monto para aplicar al presupuesto
        if transfer.transfer_amount <= 0:
            print "************** no hay monto ******************* ", transfer.transfer_amount
            raise osv.except_osv(_('Error!'),_("El monto debe ser mayor a cero"))

        print "****************** presupuesto id **************** ", transfer.budget_id

        #~ Valida que el presupuesto este validado
        budget = transfer.budget_id
        print "****************** budget ************** ", budget
        if budget.state != 'validate':
            print "*********** presupuesto ********************* ", budget.state
            raise osv.except_osv(_('Error!'),_("El presupuesto no esta Validado"))

        #~ Valida que el presupuesto contenga la cuenta analitica origen
        line_origin = budget_obj.get_analytic_account_in_budget(cr, uid, transfer.budget_id.id, transfer.analytic_account_origin.id, context=context)
        if not line_origin:
            raise osv.except_osv(_('Error!'),_("El prespuesto no tiene registrada la cuenta analitica origen en las lineas del presupuesto"))

        #~ Valida que el presupuesto contenga la cuenta analitica destino
        line_destiny = budget_obj.get_analytic_account_in_budget(cr, uid, transfer.budget_id.id, transfer.analytic_account_destiny.id, context=context)
        if not line_destiny:
            raise osv.except_osv(_('Error!'),_("El prespuesto no tiene registrada la cuenta analitica destino en las lineas del presupuesto"))

        #~ Valida que haya monto disponible para disminuir del origen
        if line_destiny['amount_available'] < round(float(transfer.transfer_amount), decimal_precision):
            raise osv.except_osv(_('Error!'),_("La cuenta analitica origen no tiene suficiente monto disponible para realizar la transferencia (DISPONIBLE: " + str(line_destiny['amount_available']) + ")."))

        lines = []
        #~ Registra el ajuste en la bitacora para la transferencia origen
        line = {
            'line_id': line_origin['line_id'],
            'budget_id': transfer.budget_id.id,
            'analytic_account_id': transfer.analytic_account_origin.id,
            'amount_approve': line_origin['amount_approve'],
            'amount_adjusted': line_origin['amount_adjusted'],
            'amount_available': line_origin['amount_available'],
            'extension_amount': round(float(transfer.transfer_amount) * -1.0, decimal_precision),
            'state': 'transfer',
            'destiny': transfer.analytic_account_destiny.id
        }
        lines.append(line)
        print "************** informacion linea origen ******************** \n ", line
        #~ Registra el ajuste en la bitacora para la transferencia destino
        line = {
            'line_id': line_destiny['line_id'],
            'budget_id': transfer.budget_id.id,
            'analytic_account_id': transfer.analytic_account_destiny.id,
            'amount_approve': line_destiny['amount_approve'],
            'amount_adjusted': line_destiny['amount_adjusted'],
            'amount_available': line_destiny['amount_available'],
            'extension_amount': round(float(transfer.transfer_amount), decimal_precision),
            'state': 'transfer',
            'destiny': transfer.analytic_account_origin.id
        }
        lines.append(line)
        print "************** informacion linea destino ******************** \n ", line

        budget_obj.account_budget_adjusted_amount(cr, uid, lines, context=context)

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account_budget', 'crossovered_budget_view_form')
        res_id = res and res[1] or False

        #~ Redirecciona al formulario de presupuesto
        return {
            'name':_("Budgets"),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'crossovered.budget', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id' : transfer.budget_id.id, # id of the object to which to redirected
        }

    _columns = {
        'budget_id': fields.many2one('crossovered.budget', 'Presupuesto', select=True, required=True),
        'analytic_account_origin': fields.many2one('account.analytic.account', 'Cuenta Analitica Origen', required=True),
        'analytic_account_destiny': fields.many2one('account.analytic.account', 'Cuenta Analitica Destino', required=True),
        'transfer_amount':fields.float('Monto', required=True, digits_compute=dp.get_precision('Account')),
    }

