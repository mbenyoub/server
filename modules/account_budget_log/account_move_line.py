# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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

"""
    Herencia sobre modulo de lineas de movimiento para marcar las lineas de movimiento que han sido pagadas y aplicadas al presupuesto
"""

import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Entries
# ---------------------------------------------------------

class account_move_line(osv.Model):
    """Inherited account.move.line"""

    _inherit = 'account.move.line'

    _columns = {
        'invoice_paid': fields.many2one('account.invoice', 'Invoice paid'),
    }

account_move_line()
