# -*- coding: utf-8 -*-
##############################################################################
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
    'name': 'Delivery Time Plan',
    'version': '2',
    'category': 'Delivery',
    'sequence': 19,
    'summary': 'Plan delivery time for sale order',
    'description': """
Delivery Time Plan
=================================
* Plan delivery time for sale order
* Add delivery return reason,
* Calculate sale order dts, pts based on order start_date, enddate,
* Compute dts,pts of delivery order based on start_date and end date of sale order, delivery zone of partner.
    """,
    'author': 'Akkadian',
    'website': 'http://saaserp.mx',
    'images' : [],
    'depends': ['sale_stock', 'delivery_routes',
            'mrp',
            "report_webkit",
            'stock_extra',
            'crm_custom'
            ],
    'data': [
        #'security/security.xml',
        'security/ir.model.access.csv',
        'data/delivery_data.xml',
        'stock_view.xml',
        'delivery_report.xml',
        'wizard/prepare_delivery_route_view.xml',
        
        #'sequence.xml',
        'res_config_view.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
