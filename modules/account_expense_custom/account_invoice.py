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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools.translate import _

class account_invoice(osv.Model):
    _inherit = "account.invoice"
    
    _columns = {
        'invoice_expense': fields.boolean('Factura de gasto'),
        'expense_id': fields.many2one('hr.expense.expense', 'Gasto Relacionado', ondelete='cascade')
    }
    
    def onchange_date_invoice_exp(self, cr, uid, ids, date_invoice=False, context=None):
        """
            Cuando cambia la fecha de factura pone el mismo dato sobre la fecha de vencimiento
        """
        res =  {'value': {}}
        if date_invoice:
            res['value']['date_due'] = date_invoice
        return res
    
    def onchange_invoice_expense(self, cr, uid, ids, invoice_expense=False, context=None):
        """
            Actualiza el diario a utilizar si es un gasto
        """
        # Si la factura no es de gasto no modifica nada
        if invoice_expense == False:
            return {}
        res = {
            'value': {}
        }
        journal_obj = self.pool.get('account.journal')
        # Busca el diario de compras relacionado con el gasto
        journal_ids = journal_obj.search(cr, uid, [('type','=','purchase'),'|',('name','like','%Gasto%'),('code','like','%EXP%')], context=context)
        if journal_ids:
            res['value']['journal_id'] = journal_ids[0]
        return res
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
