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
    'name' : "Facturacion Global",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : [
        'base',
        'links_get',
        'account',
        'account_fiscal_tax',
        'l10n_mx_balanza_anual',
        'l10n_mx_regimen_fiscal',
        'l10n_mx_facturae',
        'l10n_mx_facturae_pac_sf'
    ],
    'author' : "Saas",
    'description' : """\
Herramientas para la creacion de Facturas globales
=======================================================================
Este modulo contiene herramientas que nos permiten crear una factura global en base a facturas de nota de venta.
    """,
    'data' : [
        'data/journal_data.xml',
        'security/account_invoice_global_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_invoice_global_view.xml',
        'account_tax_view.xml',
        'account_view.xml',
        'account_invoice_view.xml',
        'res_partner_view.xml',
        'product_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
