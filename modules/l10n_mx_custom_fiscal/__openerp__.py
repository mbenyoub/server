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
    "name" : "Mexico - Contabilidad Fiscal",
    "version" : "2.2",
    "author" : "Akkadian",
    "category" : "Localization/Account Charts",
    "description": """
Minimal accounting configuration for Mexico.
============================================

This Chart of account is a minimal proposal to be able to use OoB the 
accounting feature of Openerp.

This doesn't pretend be all the localization for MX it is just the minimal 
data required to start from 0 in mexican localization.

This modules and its content is updated frequently by openerp-mexico team.

With this module you will have:

 - Minimal chart of account tested in production eviroments.
 - Minimal chart of taxes, to comply with SAT_ requirements.

.. SAT: http://www.sat.gob.mx/
    """,
    "depends" : [
        "account",
        "account_fiscal_tax",
        "base_vat",
        "account_chart",
        "account_voucher",
    ],
    'demo_xml' : [],
    'update_xml' : [
        "data/account_tax_code.xml",
        "data/account_chart.xml",
        "data/account_tax.xml",
        "data/l10n_chart_mx_wizard.xml",
        "account_voucher_view.xml",
        "account_bank_statement_view.xml",
    ],
    "active": False,
    "installable": True,
    "certificate": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

