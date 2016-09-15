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

from openerp.osv import fields, osv

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'property_account_income_refund_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta categoria nota de credito de gastos",
            view_load=True,
            help="Esta cuenta se utiliza para cuando se aplican notas de credito de cliente."),
        'property_account_expense_refund_categ': fields.property(
            'account.account',  
            type='many2one',
            relation='account.account',
            string="Cuenta de la categoria notas de creditos de ingresos",
            view_load=True,
            help="Esta cuenta se utiliza cuando se generan notas de credito de proveedor."),
    }
product_category()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
