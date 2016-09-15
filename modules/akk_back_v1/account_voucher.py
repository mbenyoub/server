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
from openerp.tools import float_compare
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account generation from template wizards
# ---------------------------------------------------------

class account_voucher(osv.Model):
    _inherit='account.voucher'
    _description = 'Accounting Voucher'
    
    def _get_journal_default(self, cr, uid, context=None):
        """
            Busca si hay un diario con el nombre bancos y lo pone por default
        """
        journal_id = False
        journal_obj = self.pool.get('account.journal')
        
        # Busca el Diario de bancos
        journal_ids = journal_obj.search(cr, uid, [('name','ilike','Bancos%')], context=context)
        #print "**************** bancos journal_ids ************ ", journal_ids
        if journal_ids:
            journal_id = journal_ids[0]
        
        # Recorre los registros
        return journal_id
    
    _defaults = {
        'journal_id': _get_journal_default
    }
    
account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
