# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
import pdb
import time

import openerp
from openerp import netsvc, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product

_logger = logging.getLogger(__name__)

class pos_config(osv.osv):
    _inherit = 'pos.config'

    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Cliente default'),
    }

class pos_order(osv.osv):
    _inherit = "pos.order"
    _description = "Point of Sale"
    
    def create_from_ui(self, cr, uid, orders, context=None):
        #_logger.info("orders: %r", orders)
        order_ids = []
        for tmp_order in orders:
            print "********* archivo temporal data orden ************ ", tmp_order['data']
            
            order = tmp_order['data']
            vals = {
                'name': order['name'],
                'user_id': order['user_id'] or False,
                'session_id': order['pos_session_id'],
                'lines': order['lines'],
                'pos_reference':order['name'],
            }
            if order.get('partner_id',False):
                vals['partner_id'] = order['partner_id'] or False
            
            order_id = self.create(cr, uid, vals, context)
            
            for payments in order['statement_ids']:
                payment = payments[2]
                
                # Valida que el pago a registrar no venga de un credito
                journal = self.pool.get('account.journal').browse(cr, uid, payment['journal_id'], context=context)
                if journal.self_apply_credit:
                    continue
                
                self.add_payment(cr, uid, order_id, {
                    'amount': payment['amount'] or 0.0,
                    'payment_date': payment['name'],
                    'statement_id': payment['statement_id'],
                    'payment_name': payment.get('note', False),
                    'journal': payment['journal_id']
                }, context=context)
                
            if order['amount_return']:
                session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)
                cash_journal = session.cash_journal_id
                cash_statement = False
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type=='cash', session.statement_ids)
                    if not len(cash_journal_ids):
                        raise osv.except_osv( _('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                self.add_payment(cr, uid, order_id, {
                    'amount': -order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                }, context=context)
            order_ids.append(order_id)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'pos.order', order_id, 'paid', cr)
        return order_ids
    
    def _default_partner(self, cr, uid, context=None):
        so = self.pool.get('pos.session')
        partner_id = False
        session_ids = so.search(cr, uid, [('state','=', 'opened'), ('user_id','=',uid)], context=context)
        if session_ids:
            # Obtiene el partner relacionado a la sesion
            session = so.browse(cr, uid, session_ids[0], context=context)
            partner_id = session.config_id.partner_id.id or False
        return partner_id

    _defaults = {
        'partner_id': _default_partner,
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
