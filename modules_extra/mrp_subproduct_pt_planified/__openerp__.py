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
    "name": "MRP Subproducts Planified",
    "version": "1.1",
    "author" : "Vauxoo",
    "category": "Generic Modules/MRP",
    "website" : "http://www.vauxoo.com/",
    "description": """ Add o2m to subproducts produced.
        This module required apply the merge of the branch: lp:~vauxoo/openobject-addons/6.1-bug-1051367-moylop260_vauxoo 
        to the addons of original openobject.
    """,
    'depends': ['mrp_byproduct','mrp_pt_planified'],
    'init_xml': [],
    'update_xml': [
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
