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
#              Juan Manuel Oropeza ()
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
    'name': 'Sale commission',
   ' version': '1.0',
    'category': 'Customization',
    'description': 'Calculo de comisiones',
    'depends': [
        'sale',
        'account',
        'product',
        'stock',
        'crm',
        'sale_crm',
        'sale_report',
    ],
    'author': 'Akkadian',
    'update_xml': [],
    'data': [
        'data/sale_commission_data.xml',
        'wizard/sale_commission_compute_view.xml',
        'res_users_view.xml',
        'filtro_personal.xml',
        'sale_commission_view.xml',
        'sale_commission_menu.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_installable': False,
    'application': False,
}