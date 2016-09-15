# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "Hotel Housekeeping Management",
    "version" : "0.02",
    "author": ["Serpent Consulting Services", "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Housekeeping",
    "description": """
    Module for Hotel/Hotel Housekeeping. You can manage:
    * Housekeeping process
    * Housekeeping history room wise

      Different reports are also provided, mainly for hotel statistics.
    """,
    "website": ["http://www.serpentcs.com", "http://www.openerp.com"],
    "depends" : ["hotel"],
    "demo" : ["hotel_housekeeping_data.xml",
    ],
    "data" : [
        "security/ir.model.access.csv",
        "report/hotel_housekeeping_report.xml",
        "wizard/hotel_housekeeping_wizard.xml",
        "hotel_housekeeping_workflow.xml",
        "hotel_housekeeping_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: