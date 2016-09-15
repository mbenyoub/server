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
    'name' : "Adaptacion para empresa CANIS",
    'category' : "customize",
    'version' : "1.0",
    'depends' : [
            'base',
            'account',
            'purchase',
            'account_voucher',
            'sale',
            'requisition_credit',
            'product',
            'message_alert',
            'crm_custom',
            'l10n_mx_facturae_refund',
            'account_fiscal',
            'point_of_sale',
            'pos_second_header',
            'pos_invoice_global',
            'delivery_routes',
            'delivery_plan',
            'sale_report',
            'sale_commission',
    ],
    'author' : "Akkadian",
    'description' : """\
        -Generacion de proceso para tarifas por categoria y en cada tarifa poder adaptar descuentos
    """,
    'data' : [
        'security/canis_security.xml',
        'security/ir.model.access.csv',
        'data/res.partner.type.csv',
        'data/pricelist_data.xml',
        'pricelist_view.xml',
        'res_partner_view.xml',
        'sale_view.xml',
        'sale_report_view.xml',
        'account_invoice_view.xml',
        'account_voucher_view.xml',
        'account_journal_view.xml',
        'product_view.xml',
        'access_branch_view.xml',
        'res_users_view.xml',
        'crm_meeting_view.xml',
        'crm_phonecall_view.xml',
        #'point_of_sale_view.xml',
    ],
    'qweb': [
        'static/src/xml/psc.xml',
    ],
    'js': [
        'static/src/js/psc.js',
    ],
    'css': [
        'static/src/css/psc.css',
    ],
    'installable': True,
    'auto_install': False,
}
