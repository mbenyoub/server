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
    "name" : "Hotel Management",
    "version" : "0.04",
    "author": ["Serpent Consulting Services", "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Management",
    "description": """
    Module for Hotel/Resort/Property management. You can manage:
    * Configure Property
    * Hotel Configuration
    * Check In, Check out
    * Manage Folio
    * Payment

    Different reports are also provided, mainly for hotel statistics.
    """,
    "website": ["http://www.serpentcs.com", "http://www.openerp.com"],
    "depends" : ["sale", "stock"],
    "demo" : [
    ],
    "data": [
        "security/hotel_security.xml",
        "security/ir.model.access.csv",
        "hotel_sequence.xml",
        "hotel_folio_workflow.xml",
#        "hotel_scheduler.xml",
        "report/hotel_report.xml",
        "hotel_view.xml",
        "hotel_data.xml",
        "wizard/hotel_wizard.xml",
    ],
    "auto_install": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: