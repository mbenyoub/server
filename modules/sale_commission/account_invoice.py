#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (riss_600@hotmail.com)
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

from osv import osv, fields
import openerp.addons.decimal_precision as dp

class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'type': fields.related('invoice_id', 'type', type='char', string='Tipo', store=True),
        'period_id': fields.related('invoice_id', 'period_id',
            type='many2one', relation='account.period', string="Periodo",
            store=True),
        'user_id': fields.related('invoice_id', 'user_id', type='many2one',
            relation="res.users", string="Vendedor", store=True),
    }

account_invoice_line()