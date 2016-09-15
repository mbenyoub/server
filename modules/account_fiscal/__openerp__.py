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

{
    'name' : "Gestion de Contabilidad Fiscal",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : [
        'base',
        'links_get',
        'account',
        'account_fiscal_tax',
        'account_accountant',
        'l10n_mx_custom_fiscal',
        'account_cancel',
        'account_asset',
        'account_asset_trade',
        'l10n_mx_balanza_anual',
        'l10n_mx_regimen_fiscal',
        'l10n_mx_facturae',
        'l10n_mx_facturae_pac_sf',
        'hr_expense',
        'shop_invoice',
        'l10n_mx_facturae_refund',
        'account_expense_custom',
        'l10n_mx_account_move',
        'account_transfer',
        #'account_invoice_global'
    ],
    'author' : "Akkadian",
    'description' : """\
Herramientas para la administracion de la contabilidad fiscal
=======================================================================
Este modulo contiene herramientas que nos permiten administrar de manera optima la contabilidad fiscal.
    """,
    'data' : [
        'data/account_fiscal_data.xml',
        'data/payment_method_data.xml',
        'data/partner_data.xml',
        #'data/journal_data.xml',
        'data/stock_data.xml',
        'security/ir.model.access.csv',
        'security/account_fiscal_security.xml',
        'wizard/account_bank_statement_conciliate_view.xml',
        'wizard/account_fiscal_rate_child_view.xml',
        'wizard/account_fiscal_code_child_view.xml',
        'wizard/account_fiscal_code_chart_view.xml',
        'wizard/account_fiscal_utility_line_new_view.xml',
        'wizard/account_tax_chart_view.xml',
        'wizard/account_fiscal_balance_return_view.xml',
        'wizard/account_fiscal_balance_apply_tax_view.xml',
        'wizard/account_fiscal_balance_apply_code_view.xml',
        'wizard/account_invoice_cancel_view.xml',
        'wizard/account_bank_statement_import_view.xml',
        'wizard/create_account_bank_view.xml',
        'res_config_view.xml',
        'regimen_fiscal_view.xml',
        'account_tax_view.xml',
        'account_fiscal_view.xml',
        'wizard/account_fiscal_utility_validate_view.xml',
        'account_fiscal_rate_view.xml',
        'account_fiscal_balance_view.xml',
        'account_fiscal_utility_view.xml',
        'account_view.xml',
        
        'account_fiscal_statement_view.xml',
        'account_invoice_view.xml',
        'account_bank_statement_view.xml',
        'res_partner_view.xml',
        'account_voucher_view.xml',
        'account_fiscal_menu.xml',
        'company_view.xml',
        'account_asset_view.xml',
        'stock_view.xml',
        'sale_view.xml',
        'product_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
