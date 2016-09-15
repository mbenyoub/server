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
    'name' : "Personalizacion CRM",
    'category' : "Customer Relationship Management",
    'version' : "1.0",
    'depends' : ['base', 'board', 'sale', 'crm', 'sale_crm', 'sale_stock'],
    'author' : "Akkadian",
    'description' : """\
     Personalizacion del modulo de CRM y Ventas
     Agregar relaciones entre documentos
    """,
    'data' : [
        'security/crm_custom_security.xml',
        'security/ir.model.access.csv',
        'sale_view.xml',
        'crm_meeting_view.xml',
        'crm_lead_view.xml',
        'account_invoice_view.xml',
        'wizard/crm_make_sale_view.xml',
        'wizard/update_section_user_view.xml',
        'stock_view.xml',
        'crm_custom_view.xml',
        'crm_phonecall_view.xml',
        'res_partner_view.xml',
        'crm_view.xml',
        'crm_custom_data.xml',
        'data/res.country.state.csv'
    ],
    'installable': True,
    'auto_install': False,
}
