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
    'name' : "Generar notas de credito y su timbrado",
    'category' : "Localization/Mexico",
    'version' : "1.0",
    'depends' : [
        'l10n_mx_ir_attachment_facturae',
        'l10n_mx_facturae',
        'l10n_mx_facturae_pac_sf',
        'shop_invoice',
    ],
    'author' : "Akkadian",
    'description' : """\
        Generacion de timbrados sobre notas de credito, cuando se valida la nota de credito genera el
        timbre para aplicar sobre el sistema,
        
        Aplicacion de pagos mediante notas de credito
    """,
    'data' : [
        'data/journal_data.xml',
        #'data/account_minimal.xml',
        'account_invoice_view.xml',
        'account_view.xml',
        'account_journal_view.xml',
        'product_view.xml',
        'wizard/account_invoice_create_line_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
