# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: julio (julio@vauxoo.com)
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
    "name" : "Decimal Precision to Rate Tax",
    "version" : "0.1",
    "depends" : ["base","decimal_precision","account"],
    "author" : "Vauxoo",
    "description" : """
                    This module, add decimal  precision format to Rate Tax.
                    """,
    "website" : "http://vauxoo.com",
    "category" : "Administracion/Personalizacion/Estructura de la base de datos/Precision Decimal",
    "init_xml" : [
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
        "data/decimal_precision_tax.xml",
    ],
    "active": False,
    "installable": True,
}
