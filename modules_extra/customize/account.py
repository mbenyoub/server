# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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


class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    _columns = {
            'parent_id' : fields.many2one('account.invoice',string="Related Invoice", 
                                            help="This field must be used to register the related invoice from a refound invoice"),
            'purchase_ids': fields.many2many('purchase.order', 'purchase_invoice_rel', 'invoice_id', 'purchase_id', 'Purchases', help="Invoices generated from a purchase order"),
        }

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        res = super(account_invoice,self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        res['parent_id'] = invoice.id
        return res