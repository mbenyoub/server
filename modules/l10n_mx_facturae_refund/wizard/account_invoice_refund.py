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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class account_invoice_refund(osv.osv_memory):
    """Refunds invoice"""
    
    _inherit = "account.invoice.refund"
    _description = "Invoice Refund"
    _columns = {
         'filter_refund': fields.selection([
               ('desc', 'Bonificacion por descuento'),
               ('dev', 'Devolucion parcial'),
               ('dev_desc', 'Bonificacion con devolucion parcial')], "Refund Method", required=True, help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled'),
    }
    _defaults = {
        'filter_refund': 'desc'
    }
   
    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice refund’s ID or list of IDs
        """
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        if context is None:
            context = {}
     
        for form in self.browse(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.journal_id.id
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error!'), _('Cannot %s draft/proforma/cancel invoice.') % (mode))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise osv.except_osv(_('Error!'), _('Cannot %s invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.') % (mode))
                if form.period.id:
                    period = form.period.id
                else:
                    period = inv.period_id and inv.period_id.id or False
       
                if not journal_id:
                    journal_id = inv.journal_id.id
      
                if form.date:
                    date = form.date
                    if not form.period.id:
                        cr.execute("select name from ir_model_fields \
                                      where model = 'account.period' \
                                      and name = 'company_id'")
                        result_query = cr.fetchone()
                        if result_query:
                            cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                               and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                        else:
                            cr.execute("""SELECT id
                                   from account_period where date(%s)
                                   between date_start AND  date_stop  \
                                   limit 1 """, (date,))
                        res = cr.fetchone()
                        if res:
                            period = res[0]
                else:
                    date = inv.date_invoice
                if form.description:
                    description = form.description
                else:
                    description = inv.name
      
                if not period:
                    raise osv.except_osv(_('Insufficient Data!'), \
                                            _('No period found on the invoice.'))
                ctx = context.copy()
                ctx['mode'] = mode
                ctx['default_filter_refund'] = mode
                #print "*************** mode **************** ", mode
                refund_id = inv_obj.refund(cr, uid, [inv.id], date, period, description, journal_id, context=ctx)
                refund = inv_obj.browse(cr, uid, refund_id[0], context=ctx)
                # Agrega a la factura relacion sobre la nota de credito generada
                inv_obj.write(cr, uid, [refund.id], {'date_due': date,
                                                'check_total': inv.check_total, 'invoice_id': inv.id, 'filter_refund': mode})
                inv_obj.button_compute(cr, uid, refund_id)
                #print "*********************************** "
                #print "************* inv state ********** ", inv.state
                created_inv.append(refund_id[0])
                if mode in ('cancel', 'modify'):
                    wf_service.trg_validate(uid, 'account.invoice', \
                                         refund.id, 'invoice_open', cr)
                    if mode == 'modify':
                        invoice = inv_obj.read(cr, uid, [inv.id],
                                    ['name', 'type', 'number', 'reference',
                                    'comment', 'date_due', 'partner_id',
                                    'partner_insite', 'partner_contact',
                                    'partner_ref', 'payment_term', 'account_id',
                                    'currency_id', 'invoice_line', 'tax_line',
                                    'journal_id', 'period_id', 'shop_id'], context=context)
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(cr, uid, invoice['invoice_line'], context=context)
                        invoice_lines = inv_obj._refund_cleanup_lines(cr, uid, invoice_lines, context=context)
                        tax_lines = inv_tax_obj.browse(cr, uid, invoice['tax_line'], context=context)
                        tax_lines = inv_obj._refund_cleanup_lines(cr, uid, tax_lines, context=context)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': date,
                            'state': 'draft',
                            'number': False,
                            'invoice_line': invoice_lines,
                            'tax_line': tax_lines,
                            'period_id': period,
                            'name': description
                        })
                        for field in ('partner_id', 'account_id', 'currency_id',
                                          'payment_term', 'journal_id'):
                            invoice[field] = invoice[field] and invoice[field][0]
                        inv_id = inv_obj.create(cr, uid, invoice, {})
                        if inv.payment_term.id:
                            data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv.payment_term.id, date)
                            if 'value' in data and data['value']:
                                inv_obj.write(cr, uid, [inv_id], data['value'])
                        created_inv.append(inv_id)
            xml_id = (inv.type == 'out_refund') and 'action_invoice_tree1' or \
                     (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                     (inv.type == 'out_invoice') and 'action_invoice_tree3' or \
                     (inv.type == 'in_invoice') and 'action_invoice_tree4'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result

account_invoice_refund()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
