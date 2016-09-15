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

{
    'name' : "Registro de momentos presupuestales",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : ['account', 'account_budget', 'account_voucher', 'purchase'],
    'author' : "Riss - Intecpro",
    'description' : """
This module allows accountants manage the budgets moments
=======================================================================

The budgets moments are defined for the moments Presupuesto Autorizado,
Por Ejercer, Comprometido, Devengado, Ejercido y Pagado.

The accountant has the posibility to see the total of amount planned for
each budget moment, in order to ensure the total planned is not
greater/lower than what he planned for this Budget.
""",
    'data' : [
        'security/account_budget_log_security.xml',
        'security/ir.model.access.csv',
        'account_budget_log_view.xml',
        'account_budget_view.xml',
        'account_budget_workflow .xml',
        'purchase_workflow.xml',
        'stock_view.xml',
        'account_invoice_workflow.xml',
        'account_voucher_workflow.xml',
        'wizard/stock_invoice_onshipping_view.xml',
        'wizard/account_budget_decrease_view.xml',
        'wizard/account_budget_extension_view.xml',
        'wizard/account_budget_inclusion_view.xml',
        'wizard/account_budget_transfer_view.xml',
        'voucher_payment_receipt_view.xml',
        'res_config_view.xml',
        #~ 'stock_workflow.xml',  Pendiente de revisar, al parecer no se necesita
        #~ 'purchase_view.xml'  Queda pendiente, por el momento no necesario
    ],
    'installable': True,
    'auto_install': False,
}
