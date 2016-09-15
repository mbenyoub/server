# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    All Rights Reserved
###############Credits######################################################
#    Coded by: Roberto Ivan Serrano Saldaña riss_600@hotmail.com,
#    Planified by: Roberto Ivan Serrano Saldaña
#    Finance by: Akkadian.
#    Audited by: Roberto Ivan Serrano Saldaña
#############################################################################
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    "name" : "Mexico - GRP Accounting",
    "version" : "1.0",
    "author" : "Akkadian",
    "category" : "Localization/Account Charts",
    "description": """
Minimal accounting configuration for Mexico GRP, don't add account.
============================================

With this module you will have:

 - Minimal chart of taxes, to comply with SAT_ requirements.

    """,
    "depends" : ["account",
                 "base_vat",
                 "account_chart",
                 ],
    "demo_xml" : [],
    "update_xml" : ["data/account_tax_code.xml",
                    "data/account_chart.xml",
                    "data/account_tax.xml",
                    "data/l10n_chart_mx_wizard.xml"],
    "active": False,
    "installable": True,
    "certificate": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

