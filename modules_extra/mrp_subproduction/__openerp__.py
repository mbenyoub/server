# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: fernandoL (fernando_ld@vauxoo.com)
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
    "name": "MRP Subproduction",
    "version": "1.0",
    "author" : "Vauxoo",
    "category": "Generic Modules",
    "website" : "http://www.vauxoo.com/",
    "description": """This module allows to assign production orders to another parent production
    order, showing how many of the parent product was consumed in each of its children production orders.
    """,
    'depends': ['mrp'],
    'init_xml': [],
    'update_xml': [
        'mrp_view.xml',
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    
}