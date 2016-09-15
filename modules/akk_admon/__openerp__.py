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
    'name' : "Gestion y Administracion de bases de datos",
    'category' : "Akkadian",
    'version' : "1.0",
    'depends' : [
        'base',
        'mail',
        'contacts',
        'l10n_mx_regimen_fiscal',
        'l10n_mx_facturae_lib',
        'report_webkit',
        'base_headers_webkit',
        'warning',
        'account',
        'sale',
        'purchase',
        'account_fiscal_tax',
        'account_voucher',
        'report_webkit',
        'account_followup',
        'message_alert'
    ],
    'author' : "Akkadian",
    'description' : """\
        Modulo para la gestion y administracion de bases de datos. con el fin de controlar y generar bases de datos de
        forma rapida y sencilla
    """,
    'data' : [
        'security/admon_security.xml',
        'security/ir.model.access.csv',
        'wizard/admon_active_user_view.xml',
        'wizard/admon_update_product_data_view.xml',
        'wizard/admon_update_account_data_view.xml',
        'wizard/admon_update_tax_data_view.xml',
        'wizard/admon_update_journal_data_view.xml',
        'admon_view.xml',
        'res_config_view.xml',
        'module_view.xml',
        'admon_menu.xml',
        'data/admon_data.xml',
        'data/res.country.state.csv',
        'report/manifesto_webkit.xml',
        'admon_cron.xml'
    ],
    'installable': True,
    'auto_install': False,
}
