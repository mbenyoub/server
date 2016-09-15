# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
    'name' : "Lote de produccion",
    'category' : "mrp",
    'version' : "1.0",
    'depends' : [
        'mrp',
    ],
    'author' : "Akkadian",
    'description' : """\
        Modulo para asignar lote de produccion
    """,
    'data' : [
        'res_config_view.xml',
        'mrp_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}