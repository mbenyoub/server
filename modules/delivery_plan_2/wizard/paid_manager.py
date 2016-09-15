#-*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
from osv import osv, fields
from openerp import netsvc
import openerp.addons.decimal_precision as dp


class paid_manager_wizard(osv.osv_memory):
    _name = 'paid.manager.wizard'
    
    _description = 'Gestion de pagos'
    
    def _get_period(self, cr, uid, context=None):
        """
            Obtencion de periodo contable
        """
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    
    def _make_journal_search(self, cr, uid, ttype, context=None):
        journal_pool = self.pool.get('account.journal')
        return journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
    
    def _get_journal(self, cr, uid, context=None):
        """
            Obtención del metodo de pago
        """
        if context is None: context = {}
        invoice_pool = self.pool.get('account.invoice')
        journal_pool = self.pool.get('account.journal')
        if context.get('invoice_id', False):
            currency_id = invoice_pool.browse(cr, uid, context['invoice_id'], context=context).currency_id.id
            journal_id = journal_pool.search(cr, uid, [('currency', '=', currency_id)], limit=1)
            return journal_id and journal_id[0] or False
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')
        
        ttype = context.get('type', 'cash')
        if ttype in ('payment', 'receipt'):
            ttype = 'cash'
        res = self._make_journal_search(cr, uid, ttype, context=context)
        return res and res[0] or False
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Cliente', required=True, readonly=True),
        'amount': fields.float('Importe a pagar', digits_compute=dp.get_precision('Delivery'), readonly=True,
            required=True),
        'journal_id': fields.many2one('account.journal', 'Metodo de pago', required=True),
        'date': fields.date('Fecha', readonly=True),
        'period_id': fields.many2one('account.period', 'Periodo', readonly=True, required=True),
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True),
        'reference': fields.char('Ref. pago'),
        'name': fields.char('Memoria'),
        'route_id': fields.many2one('delivery.route', 'Ruta'),
    }
    
    _defaults = {
        'journal_id': _get_journal,
        'period_id': _get_period,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
    
    def _generate_paid(self, cr, uid, invoice_id, amount, period_id, date, context=None):
        """
            Genera el cobro automatico de una factura sobre una nota de credito
        """
        v_obj = self.pool.get('account.voucher')
        v_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        account_type = 'receivable'
        type_line = 'receipt'
        
        # Obtiene la informacion de la factura
        inv = inv_obj.browse(cr, uid, invoice_id, context=context)
        
        if inv.type in ['in_invoice','in_refund']:
            account_type = 'payable'
            type_line = 'payment'
        else:
            account_type = 'receivable'
            type_line = 'receipt'
        
        reconcile = 0
        to_reconcile_ids = []
        # Recorre las lineas de la factura y obtiene los movimientos a pagar de la factura
        movelines = inv.move_id.line_id
        for line in movelines:
            # Si la factura origen ya esta pagada en su totalidad se omite el proceso
            if (line.account_id.id == inv.account_id.id) and (type(line.reconcile_id) == osv.orm.browse_null):
                to_reconcile_ids.append(line.id)
                reconcile += 1
        # Si no se encontraron lineas para conciliar termina el proceso
        if reconcile == 0:
            raise osv.except_osv(_('Error!'), _('No hay pagos por conciliar'))
        
        # Obtiene la cuenta que se va a aplicar para el voucher
        account_id = inv.partner_id.property_account_receivable.id
        
        amount_to_paid = amount
        line_cr_ids = []
        line_dr_ids = []
        voucher_line = []
        # Recorre las lineas de movimiento y crea las lineas del voucher
        for line in move_line_obj.browse(cr, uid, to_reconcile_ids, context=context):
            to_paid = 0
            amount_unreconciled = abs(line.amount_residual_currency)
            reconcile = False
            line_type = line.credit and 'dr' or 'cr'
            
            # Revisa si se esta conciliando el movimiento completo
            if amount_unreconciled <= amount_to_paid:
                to_paid = amount_unreconciled
                amount_to_paid = amount_to_paid - to_paid
                reconcile = True
            else:
                to_paid = amount_to_paid
                amount_to_paid = 0.0
            # Genera un arreglo con la informacion de la linea a generar
            rs = {
                'name':line.move_id.name,
                'type': line_type,
                'move_line_id': line.id,
                'account_id': line.account_id.id,
                'amount_original': abs(line.amount_currency),
                'amount': to_paid,
                'date_original': line.date,
                'date_due': line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': inv.currency_id.id,
                'reconcile': reconcile
            }
            
            # Agrega la informacion a los cargos o abonos
            if rs['type'] == 'cr':
                line_cr_ids.append(rs)
            else:
                line_dr_ids.append(rs)
            voucher_line.append(rs)
        
        writeoff_amount = v_obj._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, 0.0, type_line)
        
        vals = {
            'invoice_id': inv.id,
            'partner_id': inv.partner_id.id,
            'currency_id': inv.currency_id.id,
            'type': type_line,
            'pre_line': 1,
            'writeoff_amount': writeoff_amount,
            'account_id': account_id,
            'amount': amount,
            'period_id': period_id,
            'date': date
        }
        
        # Crea el nuevo voucher para la factura
        v_id = v_obj.create(cr, uid, vals)
        
        # Crea las lineas del voucher
        for line in voucher_line:
            line['voucher_id'] = v_id
            v_line_obj.create(cr, uid, line, context=context)
        
        # Aplica el pago sobre los movimientos
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.voucher', v_id, 'proforma_voucher', cr)
        return v_id
    
    def _write_log(self, cr, uid, invoice_id, amount, date, route_id, journal_id, context=None):
        """
            Registra el pago realizado en la ruta
        """
        print "*******REGISTRANDO EL REGISTRO DEL PAGO******"
        
        dr_paid_log_obj = self.pool.get('delivery.route.paid.log')
        
        # Se introducen los datos del pago de la ruta
        vals = {
            'invoice_id': invoice_id,
            'amount': amount,
            'date': date,
            'route_id': route_id,
            'journal_id': journal_id,
        }
        
        print "***********VALS IN LOG PAID**********: ", vals
        paid_log_id = dr_paid_log_obj.create(cr, uid, vals, context=context)
        print "*******PAID_LOG_ID*****: ", paid_log_id
        
        return True
    
    
    def action_paid(self, cr, uid, ids, context=None):
        """
            Boton que realiza el pago de la factura
        """
        drl_obj = self.pool.get('delivery.route.line')
        
        
        # Se obtienen los datos del wizard
        move = self.browse(cr, uid, ids[0], context=context)
        invoice_id = move.invoice_id.id or False
        partner_id = move.partner_id.id or False
        amount = move.amount or 0.0
        period_id = move.period_id.id or False
        date = move.date
        route_id = move.route_id.id or False
        journal_id = move.journal_id.id or False
        
        # Pasando la entrega a estado 'arribado'
        drl_srch = drl_obj.search(cr, uid, [('route_id', '=', route_id)], context=context)
        state = drl_obj.browse(cr, uid, drl_srch[0], context=context).state
        print "*****STATE****: ", state
        #print "******PASANDO DE ESTADO ARRIBADO PM******"
        
        #drl_obj.write(cr, uid, drl_srch, {'state': 'arrived', 'visit_date': date}, context=context)
        ## Registra el log sobre la actualizacion sobre la transicion de estado
        #self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, drl_srch, state='arrived', context=context)
        
        self._generate_paid(cr, uid, invoice_id, amount, period_id, date, context=context)
        
        self._write_log(cr, uid, invoice_id, amount, date, route_id, journal_id, context=context)
        
        #drl_obj.action_delivered(cr, uid, ids, context=context)
        return True
    
