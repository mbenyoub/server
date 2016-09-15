# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP s.a. (<http://www.openerp.com>)
#    Copyright (C) 2013-TODAY Mentis d.o.o. (<http://www.mentis.si/openerp>)
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
    'name': 'Product Cost Recalculation',
    'version': '1.3',
    'category': 'Accounting',
    'description': """

Module adds several options and methods for product cost recalculation:\n

Options:\n
- change values on supplier shipments (incoming and returns) manually (date of delivery, quantity, unit price)\n
- change values on customer shipments (outgoing and returns) manually (date of delivery, quantity)\n
- change values on supplier shipments (incoming and returns) shipment automatically via supplier invoice or refund (unit price)\n

Methods:\n
- cost price recalculation for period\n

TODO:\n
- change values option on inventory stock moves (date, quantity, unit price)\n
 
    """,
    'author': 'Mentis d.o.o.',
    'depends': ['account','stock'],
    'data': [
             'stock_picking_form_view.xml',
             'wizard/stock_picking_update_view.xml',
             'wizard/account_product_cost_recalculation_view.xml',
             'wizard/account_product_cost_set_view.xml'
    ],
    'installable': True,
    'active': False,
}
