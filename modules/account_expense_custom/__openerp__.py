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
    'name' : "Gestion de Gastos Facturados y no Facturados",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : ['base', 'hr', 'account','purchase', 'account_payment','account_voucher','links_get'],
    'author' : "Akkadian",
    'description' : """\
         Generacion procesos para identificar los gastos facturados y los no facturados, 
         modificacion de documento de gastos de recursos humandos para simplificacion del proceso y 
         completar la funcionalidad
    """,
    'data' : [
        'data/expense_data.xml',
        'account_invoice_view.xml',
        'hr_expense_view.xml',
        'hr_expense_workflow.xml',
        'account_expense_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
