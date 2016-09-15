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
    'name' : "Manejar Diario de Facturacion por tienda",
    'category' : "Akkadian",
    'version' : "1.0",
    'depends' : [
        'base',
        'sale',
        'stock',
        'l10n_mx_facturae_pac_sf',
        'l10n_mx_facturae_seq',
        'l10n_mx_facturae_report',
    ],
    'author' : "Akkadian",
    'description' : """\
        Modulo para la aplicacion de series distintas por tienda,
        se relaciona especificando de que tienda proviene cada factura.
    """,
    'data' : [
        'sale_view.xml',
        'account_invoice_view.xml',
        'data/shop_data.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
}
