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
    'name' : "Modelo basico facturacion electronica",
    'category' : "Akkadian backoffice",
    'version' : "1.0",
    'depends' : [
        'sale',
        'purchase',
        'account',
        'document',
        'stock',
        'hr',
        'board',
        'account_voucher',
        'purchase_requisition',
        'account_fiscal',
        'l10n_mx_facturae',
        'l10n_mx_facturae_pac_sf',
        'backoffice',
        'shop_invoice',
        'stock_invoice_directly',
        'stock_location',
        'account_report_company'
    ],
    'author' : "Akkadian",
    'description' : """\
        Modulo basico para la implementacion de facturacion electronica. contenido:
            - Productos
            - Clientes
            - Facturas
            - Cuentas
            - Pagos
    """,
    'data' : [
        'security/backoffice_security.xml',
        'security/ir.model.access.csv',
        'data/country_data.xml',
        'akk_back_view.xml',
        'dashboard/board_backoffice_view.xml',
        'account_invoice_view.xml',
        'account_fiscal_statement_view.xml',
        'res_partner_view.xml',
        'backoffice_view.xml',
        'product_view.xml',
        'stock_view.xml',
        'account_view.xml',
        'sale_view.xml',
        'crm_meeting_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
