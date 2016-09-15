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

class account_budget_log_create_inclusion_budget_wizard(osv.TransientModel):
    _name = 'account.budget.log.create.inclusion.budget.wizard'

    def action_add_inclusion_budget(self, cr, uid, ids, context=None):
        """
            Aplica una inclusion a una linea del presupuesto
        """
        print "******************** Inclusion al presupuesto *********************** "

        budget_obj = self.pool.get('crossovered.budget')
        budget_lines_obj = self.pool.get('crossovered.budget.lines')
        inclusion = self.browse(cr, uid, ids[0], context=context)
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

        #~ Valida que haya un monto para aplicar al presupuesto
        if inclusion.inclusion_amount <= 0:
            print "************** no hay monto ******************* ", inclusion.inclusion_amount
            raise osv.except_osv(_('Error!'),_("El monto debe ser mayor a cero"))

        print "****************** presupuesto id **************** ", inclusion.budget_id

        #~ Valida que el presupuesto este validado
        budget = inclusion.budget_id
        print "****************** budget ************** ", budget
        if budget.state != 'validate':
            print "*********** presupuesto ********************* ", budget.state
            raise osv.except_osv(_('Error!'),_("El presupuesto no esta Validado"))

        #~ Valida que el presupuesto contenga la cuenta analitica
        line = budget_obj.get_analytic_account_in_budget(cr, uid, inclusion.budget_id.id, inclusion.analytic_account_id.id, context=context)
        if line:
            raise osv.except_osv(_('Error!'),_("El prespuesto ya tiene dada de alta la cuenta analitica en las lineas del presupuesto"))

        #~ Registra la cuenta analitica en el presupuesto
        line_id = budget_lines_obj.create(cr, uid, {
            'crossovered_budget_id': inclusion.budget_id.id,
            'analytic_account_id': inclusion.analytic_account_id.id,
            'general_budget_id': inclusion.general_budget_id.id,
            'state': 'validate',
        }, context=context)

        print " ********** linea del presupuesto creada ************** ", line_id

        lines = []
        #~ Registra el ajuste en la bitacora
        line = {
            'line_id': line_id,
            'budget_id': inclusion.budget_id.id,
            'analytic_account_id': inclusion.analytic_account_id.id,
            'amount_approve': 0.0,
            'amount_adjusted': 0.0,
            'amount_available': 0.0,
            'extension_amount': round(float(inclusion.inclusion_amount), decimal_precision),
            'state': 'inclusion'
        }
        lines.append(line)

        print "************** informacion line ******************** \n ", line
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
            'res_id' : inclusion.budget_id.id, # id of the object to which to redirected
        }

    _columns = {
        'budget_id': fields.many2one('crossovered.budget', 'Presupuesto', select=True, required=True),
        'general_budget_id': fields.many2one('account.budget.post', 'Posición presupuestaria', required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Cuenta Analitica', required=True),
        'inclusion_amount':fields.float('Monto', required=True, digits_compute=dp.get_precision('Account')),
    }

