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
    'name' : "Comercializacion de Activos",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : [
        'base',
        'account',
        'purchase',
        'account_asset'
    ],
    'author' : "Akkadian",
    'description' : """\
Herramientas para automatizacion de activos y venta
=======================================================================

Este modulo contiene herramientas que nos permiten automatizar la creacion de activos fijos a
travez de la compra y la facturacion de los mismos para su venta.
    """,
    'data' : [
        'security/project_evaluation_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_asset_drop_view.xml',
        'account_view.xml',
        'product_view.xml',
        'account_invoice_view.xml',
        'account_asset_view.xml',
        'account_fiscal_view.xml',
        'res_partner_view.xml',
        #'data/product_data.xml',
        'data/account_asset_data.xml',
        'data/account_fiscal_inpc_data.xml'
    ],
    'installable': True,
    'auto_install': False,
}
