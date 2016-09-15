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
    'name' : "Gestion de Contabilidad Electronica (SAT)",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : [
        'base',
        'links_get',
        'account'
    ],
    'author' : "Saas",
    'description' : """\
Herramientas para la administracion de la contabilidad Electronica
=======================================================================
Este modulo contiene herramientas que nos permiten administrar de manera optima la 
contabilidad electronica en base a las disposiciones presentadas por el SAT.
    """,
    'data' : [
        'security/account_sat_security.xml',
        'security/ir.model.access.csv',
        'data/account_sat_data.xml',
        'account_view.xml',
        'account_sat_view.xml',
        'wizard/account_sat_related_view.xml',
        'wizard/account_sat_create_xml_report_view.xml',
        'wizard/account_sat_chart_view.xml',
    ],
    'init_xml': [
        #'data/account.account.sat.csv',
    ],
    'installable': True,
    'auto_install': False,
}
