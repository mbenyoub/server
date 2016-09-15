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
    'name' : "Personalizacion Backoffice",
    'category' : "Customer Management Client",
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
        'hr_expense'
    ],
    'author' : "Akkadian",
    'description' : """\
        Despliega los menus principales en relacion a ventas, compras y almacen en un solo menu
        para optimizar el proceso de trabajo mediante el aplicativo
    """,
    'data' : [
        'security/backoffice_security.xml',
        'security/ir.model.access.csv',
        'backoffice_view.xml',
        'stock_view.xml',
        'data/stock_data.xml',
        'data/res.country.state.csv'
    ],
    'installable': True,
    'auto_install': False,
}
