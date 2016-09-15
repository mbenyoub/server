#!/usr/bin/python
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
    "name": "Facturacion Global sobre punto de venta",
    "version": "1.0",
    "depends": [
        'point_of_sale',
        'account_invoice_global',
        'links_get',
        'stock_extra',
    ],
    "author": "Akkadian",
    "description" : """
        Herramientas para facturacion global sobre punto de venta
    """,
    "website": "http://saaserp.mx",
    "category": "Point Of Sale",
    "test": [],
    "data": [
        'security/ir.model.access.csv',
        'wizard/pos_account_invoice_global_view.xml',
        'wizard/pos_payment_view.xml',
        'wizard/pos_order_return_view.xml',
        'point_of_sale_workflow.xml',
        'account_invoice_view.xml',
        'point_of_sale_view.xml'
    ],
    "active": False,
    "installable": True,
}
