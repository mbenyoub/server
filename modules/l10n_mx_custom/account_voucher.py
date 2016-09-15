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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account voucher - Modifica los metodos de pago
# ---------------------------------------------------------

class account_journal(osv.Model):
    _inherit='account.journal'
    
    def _have_bank(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa verdadero si tiene una cuenta de banco configurada
        """
        res = {}
        for journal in self.browse(cr, uid, ids, context=context):
            res[journal.id] = False
            if journal.type == 'bank':
                res[journal.id] = True
                # Valida que tenga una cuenta de banco registrada
                bank_ids = self.pool.get('res.partner.bank').search(cr, uid, [('journal_id', '=', journal.id),])
                if not bank_ids:
                    res[journal.id] = False
        return res

    _columns = {
        'have_bank': fields.function(_have_bank, method=True, store=True, string='Tiene cuenta de banco', readonly=True, type='boolean'),
        'partner_bank_ids': fields.one2many('res.partner.bank', 'journal_id', 'Cuentas Bancarias'), 
    }

account_journal()

class account_voucher(osv.Model):
    _inherit='account.voucher'

    _columns = {
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}, domain=['|',('type','in',['cash']),('partner_bank_ids','!=',None)],),
    }

account_voucher()

class res_partner_bank(osv.Model):
    _inherit='res.partner.bank'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Account Journal', domain=[('type','in',['bank'])], context={'type': 'bank'}, help="Este diario sera creado automaticamente para esta cuenta bancaria cuando grabe el registro", required=True),
    }

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
