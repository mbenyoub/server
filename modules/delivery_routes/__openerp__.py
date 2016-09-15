# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#    Copyright (C) 2013 Elico Corp (<http://www.elico-corp.com>).
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
    "name": "Delivery Routes",
    "version": "2",
    "description": """
Manage delivery routes.
=======================
Based on Cubic ERP's Delivery Routes Module\n
it add the following features:\n
* Add group Customer Service
* Add dts_id in purchase order, A purchase order with flag is_collected can have a delivery_route_line
* Improve DTS , PTS. 
* Improve Delivery carrier and driver, picker. Add color for delivery driver and picker.
* Add interface functions with other modules sales, purchase, stock
* use 3-seg daily dts/pts to arrange delivery.
""",
    "author": "Akkadian",
    "website": "http://saaserp.mx",
    "category": "Delivery",
    "depends": [
            'product',
            'stock',
            'delivery',
            'hr',
            'procurement',
            'resource',
            'purchase',
            'l10n_mx_partner_address'
        ],
    "data":[
            "security/delivery_security.xml",
            "security/ir.model.access.csv",
            "data/delivery_data.xml",
            "wizard/prepare_move_stock_route_view.xml",
            "wizard/prepare_delivery_stock_route_view.xml",
            "wizard/prepare_unload_stock_route_view.xml",
            "wizard/prepare_departure_route_view.xml",
            "wizard/reception_entry_route_view.xml",
            "wizard/delivery_route_out_view.xml",
            "delivery_view.xml",
            "stock_view.xml",
            "sale_view.xml",
	        "purchase_view.xml",
            "res_partner_view.xml",
            "report/delivery_route_report.xml",
    ],
    "demo_xml": [ ],
    "active": False,
    "installable": True,
    "certificate" : "",
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
