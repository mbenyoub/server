# -*- encoding: utf-8 -*-
###########################################################################
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
    "name": "Transferencias Bancarias",
    "version": "1.0",
    "description": """
Manage transfers between cash and bank accounts
===============================================

The management of bank and cash transfers, enables you to track your money transfers in easy and secure way.
OpenERP has several methods of tracking the cash account move, like vouchers or bank statements. In this way this module will generate payment vouchers to integrate the cash and bank transfers to OpenERP.

Key Features
------------
* Manage the authorization of money transfers
* Allow transfer money between accounts directly
* Optimize the treasure management

Dashboard / Reports for Money Transfer will include:
----------------------------------------------------
* Transfer Report
    """,
    "author": "Saas ERP",
    "website": "http://saaserp.mx",
    "category": "Financial",
    "depends": [
        "account",
        "account_voucher",
        ],
    "data":[
        "account_transfer_view.xml",
        "security/account_transfer_security.xml",
        "security/ir.model.access.csv",
        "account_transfer_workflow.xml",
        "account_view.xml",
        "account_transfer_sequence.xml",
        "account_transfer_data.xml",
        ],
    "demo_xml": [],
    "update_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
