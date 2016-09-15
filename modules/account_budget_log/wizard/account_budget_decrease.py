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

class account_budget_log_create_decrease_budget_wizard(osv.TransientModel):
    _name = 'account.budget.log.create.decrease.budget.wizard'

    def calculate_amount_decrease(self, cr, uid, ids, context=None):
        """
            Calcula el monto resultante que se dara al disminuir la linea del presupuesto
        """
        print "********************** Calcular Disminucion ************************** "
        #~ account_budget_log_obj = self.pool.get('account.budget.log.moments')
        #~ account_budget_log_obj.create(cr, uid, {
                #~ 'name': 'Prueba',
                #~ 'account_analytic_id': 1401,
                #~ 'amount': 200.00,
                #~ 'reference': 'na',
                #~ 'state': 'adjusted',
                #~ 'move': False,
                #~ 'budget_id': 11,
            #~ }, context=context)

        #~ adjusted = self.browse(cr, uid, ids[0], context=context)
#~
        #~ adjusted.decrease_amount = 500.00

        self.write(cr, uid, ids[0], {'decrease_amount': 500.00}, context=context)

        return {
            'value' : {'decrease_amount' : 500.00,},
            'res_model': 'your.osv.memory',
            'view_type': 'form',
            'view_mode': 'form',
            #~ 'type': 'ir.ui.view',
            #~ 'nodestroy': True,
            'target': 'current',
            'context': {},
        }

    def action_add_decrease_budget(self, cr, uid, ids, context=None):
        """
            Aplica una disminucion a una linea del presupuesto
        """
        print "******************** Disminucion al presupuesto *********************** "

        budget_obj = self.pool.get('crossovered.budget')
        budget_lines_obj = self.pool.get('crossovered.budget.lines')
        decrease = self.browse(cr, uid, ids[0], context=context)

        #~ Valida que haya un monto para aplicar al presupuesto
        if decrease.decrease_amount <= 0:
            print "************** no hay monto ******************* ", decrease.decrease_amount
            raise osv.except_osv(_('Error!'),_("El monto disminuido debe ser mayor a cero"))

        print "****************** presupuesto id **************** ", decrease.budget_id

        #~ Valida que el presupuesto este validado
        budget = decrease.budget_id
        print "****************** budget ************** ", budget
        if budget.state != 'validate':
            print "*********** presupuesto ********************* ", budget.state
            raise osv.except_osv(_('Error!'),_("El presupuesto no esta Validado"))

        #~ Valida que el presupuesto contenga la cuenta analitica
        line = budget_obj.get_analytic_account_in_budget(cr, uid, decrease.budget_id.id, decrease.analytic_account_id.id, context=context)
        if not line:
            raise osv.except_osv(_('Error!'),_("El presupuesto no tiene dada de alta la cuenta analitica en las lineas del presupuesto"))

        #~ Valida que haya monto suficiente para aplicar la disminucion
        if (line['amount_available'] - decrease.decrease_amount) < 0:
            print "*************** Monto a disminuir mayor a monto disponible ******** amou_ava *** ", line['amount_available'], "  ++ dec_amou ++ ", decrease.decrease_amount
            raise osv.except_osv(_('Error!'),_("El monto a disminuir es mayor al monto disponible (DISPONIBLE:" + str(line['amount_available']) + ")"))

        lines = []
        #~ Registra el ajuste en la bitacora
        line['budget_id'] = decrease.budget_id.id
        line['extension_amount'] = float(decrease.decrease_amount) * -1.0
        line['state'] = 'decrease'
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
            'res_id' : decrease.budget_id.id, # id of the object to which to redirected
        }

    _columns = {
        'budget_id': fields.many2one('crossovered.budget', 'Presupuesto', size=32, select=True, required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Cuenta Analitica', size=32, required=True),
        'decrease_amount':fields.float('Monto', required=True, digits_compute=dp.get_precision('Account')),
    }

