# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 HESATEC - http://www.hesatecnica.com
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@hesatecnica.com)
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
    'name': 'Balanza de Comprobacion Anual',
    'version': '1',
    "author" : "HESATEC",
    "category" : "Accounting",
    'description': """
        Balanza de comprobación conforme a los requerimientos de México, basados en 12 periodos al año (12 meses naturales), 
        donde el mes 1 y 12 son de apertura/cierre respectivamente.
        Permite ver la balanza en vista de lista con el fin de que el contador pueda exportar la balanza a hoja de cálculo para
        realizar todo lo relacionado a reportes fiscales, así como análisis particulares
    """,
    "website" : "http://www.hesatecnica.com/",
    "license" : "AGPL-3",
    "depends" : ["account","account_type_sign"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["account_annual_balance_view.xml"],
    "installable" : True,
    "active" : False,
}
