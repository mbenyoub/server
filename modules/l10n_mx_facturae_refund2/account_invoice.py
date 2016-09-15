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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import pytz

class account_invoice(osv.osv):
    _inherit='account.invoice'
    
    _columns = {
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ('repaid','Saldado'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.'),
        'invoice_id': fields.many2one('account.invoice', 'Factura origen', readonly=True, select=1, ondelete='restrict', help="Referencia sobre factura"),
        'invoice_id2': fields.many2one('account.invoice', 'Factura origen', readonly=True, select=1, ondelete='restrict', help="Referencia sobre factura"),
        'refund_ids': fields.one2many('account.invoice', 'invoice_id', 'Notas de credito', domain=[('type','in',['out_refund','in_refund'])]),
        'note_ids': fields.one2many('account.invoice', 'invoice_id2', 'Notas de cargo', domain=[('type','in',['out_invoice','in_invoice'])]),
        'filter_refund': fields.selection([
                ('none', 'No aplica'),
                ('desc', 'Bonificacion por descuento'),
                ('dev', 'Devolucion parcial'),
                ('dev_desc', 'Bonificacion con devolucion parcial')], "Metodo Nota de Creditdo"),
        'debit_note': fields.boolean("Es nota de cargo"),
    }
    _defaults = {
        'filter_refund': 'none',
        'debit_note': False
    }
    
    def action_create_line(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard para agregar detalles de factura
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_mx_facturae_refund', 'wizard_account_invoice_create_line_view')
        
        type = ''
        # Valida si el registro debe aplicar por año
        inv = self.browse(cr, uid, ids[0], context=context)
        type = inv.type
        
        return {
            'name':_("Linea de Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice.create.line',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_invoice_id': ids[0],
                'type': type,
                'default_type': inv.type,
                'default_company_id': inv.company_id.id or False,
                'default_partner_id': inv.partner_id.id or False,
                'default_journal_id': inv.journal_id.id or False,
                'default_fiscal_position': inv.fiscal_position.id or False,
                'default_currency_id': inv.currency_id.id or False
            }
        }
    
    #def action_date_assign(self, cr, uid, ids, *args):
    #    #print "************ action_date_assign **************** "
    #    res = super(account_invoice, self).action_date_assign(cr, uid, ids, args)
    #    for inv in self.browse(cr, uid, ids):
    #        if inv.invoice_id:
    #            #print "********* estado ndc ****************** ", inv.state
    #            #print "*************** estado factura ", inv.invoice_id.id, " ********** ", inv.invoice_id.state
    #    return res
    #
    #def action_move_create(self, cr, uid, ids, context=None):
    #    #print "************ action_move_create **************** "
    #    res = super(account_invoice, self).action_move_create(cr, uid, ids)
    #    for inv in self.browse(cr, uid, ids):
    #        if inv.invoice_id:
    #            #print "********* estado ndc ****************** ", inv.state
    #            #print "*************** estado factura ", inv.invoice_id.id, " ********** ", inv.invoice_id.state
    #    return res
    #
    #def action_number(self, cr, uid, ids, context=None):
    #    #print "************ action_number **************** "
    #    res = super(account_invoice, self).action_number(cr, uid, ids)
    #    for inv in self.browse(cr, uid, ids):
    #        if inv.invoice_id:
    #            #print "********* estado ndc ****************** ", inv.state
    #            #print "*************** estado factura ", inv.invoice_id.id, " ********** ", inv.invoice_id.state
    #    return res
    
    def generate_voucher_invoice(self, cr, uid, invoice_id, refund_id, context=None):
        """
            Genera el cobro automatico de una factura sobre una nota de credito
        """
        v_obj = self.pool.get('account.voucher')
        v_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        type_line = 'receipt'
        
        # Obtiene la informacion de la factura
        inv = self.browse(cr, uid, invoice_id, context=context)
        
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
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
        # Si no se encontraron lineas para conciliar termina el proceso
        if reconcile == 0:
            return True
        
        # Obtiene la informacion de la nota de credito
        refund = self.browse(cr, uid, refund_id, context=context)
        reconcile = 0
        # Recorre las lineas de la nota de credito y obtiene los movimientos a pagar de la factura
        movelines = refund.move_id.line_id
        for line in movelines:
            # Si la factura origen ya esta pagada en su totalidad se omite el proceso
            if (line.account_id.id == refund.account_id.id) and (type(line.reconcile_id) == osv.orm.browse_null):
                to_reconcile_ids.append(line.id)
                reconcile += 1
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
        # Si no se encontraron lineas para conciliar termina el proceso
        if reconcile == 0:
            return True
        
        # Obtiene la cuenta que se va a aplicar para el voucher
        account_id = inv.partner_id.property_account_receivable.id
        
        line_cr_ids = []
        line_dr_ids = []
        voucher_line = []
        concilie = 0
        # Recorre las lineas de movimiento y crea las lineas del voucher
        for line in move_line_obj.browse(cr, uid, to_reconcile_ids, context=context):
            amount_unreconciled = abs(line.amount_residual_currency)
            reconcile = False
            if line.credit:
                amount = min(amount_unreconciled, abs(total_debit))
                total_debit -= amount
            else:
                amount = min(amount_unreconciled, abs(total_credit))
                total_credit -= amount
            line_type = line.credit and 'dr' or 'cr'
            
            # Revisa si se esta conciliando el movimiento completo
            if amount_unreconciled == amount and concilie == 0:
                reconcile = True
                #print "****************** total_credit ******************* ", total_credit
                #print "****************** total_debit ******************* ", total_debit
                if total_credit == 0 or total_debit == 0:
                    concilie = 1
            # Genera un arreglo con la informacion de la linea a generar
            rs = {
                'name':line.move_id.name,
                'type': line_type,
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': abs(line.amount_currency),
                'amount': amount,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': inv.currency_id.id,
                'reconcile': reconcile
            }
            #print "********************** rs ************************ ", rs
            
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
            'account_id': account_id
        }
        
        #print "*********************** vals ******************* ", vals
        
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
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Valida que al cancelar la factura no haya notas de credito relacionadas
        """
        #print "***************** cancel invoice refund ******************* "
        line_obj = self.pool.get('account.invoice.line')
        # Recorre los registros
        for inv in self.browse(cr, uid, ids, context=context):
            # Si es una nota de credito del cliente regresa a como estaba la cantidad de origen y
            if inv.type in ['out_refund','in_refund']:
                # Cancela las notas de cargo si esta relacionada
                if inv.invoice_id2:
                    self.action_cancel(cr, uid, [inv.invoice_id2.id], context=context)
                # Regresa los valores de las lineas de factura a antes de generar la nota de credito
                for line in inv.invoice_line:
                    if line.line_id_ref:
                        if line.edit_refund == 'desc':
                            line_obj.write(cr, uid, [line.line_id_ref.id], {'discount_refund': line.line_id_ref.discount_refund - line.quantity} ,context=context)
                        elif line.edit_refund == 'dev':
                            line_obj.write(cr, uid, [line.line_id_ref.id], {'quantity_refund': line.line_id_ref.quantity_refund - line.quantity} ,context=context)
            elif inv.type in ['out_invoice','in_invoice']:
                # Valida que no tenga notas de credito relacionadas para cancelar la factura
                cr.execute("""
                    select (CASE WHEN sum(amount_total) > 0 THEN sum(amount_total) ELSE 0 END) AS suma
                    from account_invoice
                    where state in ('open','paid') and invoice_id=%s
                    """%(inv.id,))
                for value in cr.fetchall():
                    amount += value[0]
                    break;
                if amount > 0.0:
                    raise osv.except_osv(_('Error!'),_("No se puede cancelar la Factura '%s' si tiene notas de credito aplicadas!")%(inv.number))
        return super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({'filter_refund' : 'none', 'invoice_id':False, 'invoice_id2':False})
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def date_to_datetime(self, cr, uid, userdate, context=None):
        """ Convert date values expressed in user's timezone to
        server-side UTC timestamp, assuming a default arbitrary
        time of 12:00 AM - because a time is needed.
    
        :param str userdate: date string in in user time zone
        :return: UTC datetime string for server-side use
        """
        # TODO: move to fields.datetime in server after 7.0
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    
    def _prepare_order_picking_refund(self, cr, uid, order, context=None):
        """
            Obtiene el detalle de la nota de credito
        """
        if context is None:
            context = {}
        type = context.get('type','in')
        
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
        return {
            'name': pick_name,
            'origin': 'Nota de Credito %s'%(order.number,),
            'date': self.date_to_datetime(cr, uid, order.date_invoice, context),
            'type': type,
            'state': 'auto',
            'move_type': 'one',
            'partner_id': order.partner_id.id,
            'note': '',
            'invoice_state': 'none',
            'company_id': order.company_id.id,
        }
    
    def _prepare_order_line_move_refund(self, cr, uid, order, line, picking_id, date_planned, type='in', context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.quantity,
            'product_uom': line.uos_id.id,
            'product_uos_qty': line.quantity,
            'product_uos': line.uos_id.id,
            'partner_id': order.partner_id.id,
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': location_id,
            'tracking_id': False,
            'state': 'draft',
            'type': type,
            'company_id': order.company_id.id,
            'price_unit': line.price_unit or 0.0
        }
    
    def _prepare_refund_debit_line(self, cr, uid, invoice_id, line, mode='none', context=None):
        """
            Retorna el detalle para generar una nueva linea sobre una nota de cargo
        """
        tax_list = []
        for tax in line['invoice_line_tax_id']:
            tax_list.append(tax.id)
        if mode == 'dev':
            quantity = line.quantity
            discount = line.line_id_ref.discount_refund
        elif mode == 'desc':
            quantity = line.line_id_ref.quantity_refund
            discount = line.discount
        else:
            quantity = line.quantity
            discount = line.discount
        
        #print "********* nota name ************ ", line.name
        #print "********* nota cargo mode ************ ", mode
        #print "********* nota cargo quantity ************ ", quantity
        #print "********* nota cargo discount ************ ", discount
        
        res = {
            'name': line.name,
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'uos_id': line.uos_id.id,
            'account_id': line.account_id.id,
            'price_unit': line.price_unit,
            'quantity': quantity,
            'discount': discount,
            'invoice_line_tax_id': [(6,0, tax_list)],
            'account_analytic_id': line.account_analytic_id.id or False
        }
        return res
    
    def _create_refund_debit_note(self, cr, uid, invoice, mode='none', context=None):
        """
            Crea un nuevo documento para nota de cargo sin los detalles
        """
        obj_journal = self.pool.get('account.journal')
        if context is None:
            context = {}
        type_dict = {
            'out_invoice': 'out_refund', # Customer Invoice
            'in_invoice': 'in_refund',   # Supplier Invoice
            'out_refund': 'out_invoice', # Customer Refund
            'in_refund': 'in_invoice',   # Supplier Refund
        }
        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False
        
        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        # Obtiene el diario para generar el documento de nota de debito
        if invoice['type'] in ['in_invoice','in_refund']:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_debit')], context=context)
        if invoice['type'] in ['out_invoice','out_refund']:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_debit')], context=context)
        else:
            refund_journal_ids = [invoice.invoice_id.journal_id.id]
        
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': invoice.date_invoice,
            'state': 'draft',
            'period_id': invoice.period_id.id,
            'number': False,
            'tax_line': tax_lines,
            'name': invoice.comment,
            'check_total': invoice.check_total,
            'invoice_id': invoice.id,
            'invoice_id2': invoice.invoice_id.id or False,
            'debit_note': True,
            'filter_refund': mode,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
        })
        
        invoice_id = self.create(cr, uid, invoice_data, context=context)
        return invoice_id
        
    def invoice_validate(self, cr, uid, ids, context=None):
        """
            Valida el estado al que debe transicionar la factura, si es una nota de credito para el cliente pone a la factura relacionada como transicionada
        """
        #print "************ invoice_validate **************** "
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        inv_line_obj = self.pool.get('account.invoice.line')
        picking_m_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')
        delete_lines = []
        
        # Revisa si alguna factura es de nota de credito y ve si tiene que aplicar una modificacion sobre la factura origen
        for inv in self.browse(cr, uid, ids, context=context):
            # No puedes validar notas de credito en ceros
            if inv.amount_total == 0.0 and inv.type in ['out_refund','in_refund']:
                raise osv.except_osv(_('Error!'),_("No puede validar notas de credito en cero: '%s'!")%(inv.number,))
            
            # Valida que sea una nota de credito generada para el cliente
            if inv.type in ['out_refund','in_refund']:
                # Valida si tiene una factura origen
                if inv.invoice_id:
                    type = 'in'
                    if inv.type == 'in_refund':
                        type = 'out'
                    amount = 0.0
                    note_id = False
                    picking_id = False
                    date_planned = inv.date_invoice
                    if context is None:
                        context = {}
                    
                    #print "********* estado ndc ****************** ", inv.state
                    #print "*************** estado factura ", inv.invoice_id.id, " ********** ", inv.invoice_id.state
                    # Valida que la factura se encuentre en estado abierto
                    if inv.invoice_id.state != 'open' and inv.invoice_id.state != 'paid':
                        raise osv.except_osv(_('Error!'),_("La factura origen '%s' no se encuentra en estado abierto!")%(inv.invoice_id.number,))
                    #    self.write(cr, uid, [inv.invoice_id.id], {'state': 'open'}, context=context)
                    #print "*************** estado factura ", inv.invoice_id.id, " ********** ", inv.invoice_id.state
                    
                    # Obtiene el total aplicado sobre notas de credito relacionadas a la factura
                    cr.execute("""
                        select (CASE WHEN sum(amount_total) > 0 THEN sum(amount_total) ELSE 0 END) AS suma
                        from account_invoice
                        where type='out_refund' and state in ('open','paid') and invoice_id=%s
                        """%(inv.invoice_id.id,))
                    for value in cr.fetchall():
                        amount += value[0]
                        break;
                    # Obtiene el total aplicado sobre notas de cargo relacionadas a la factura y las resta de las notas de credito
                    cr.execute("""
                        select (CASE WHEN sum(amount_total) > 0 THEN sum(amount_total) ELSE 0 END) AS suma
                        from account_invoice
                        where type='out_invoice' and state in ('open','paid') and invoice_id2=%s
                        """%(inv.invoice_id.id,))
                    for value in cr.fetchall():
                        amount -= value[0]
                        break;
                    amount += inv.amount_total
                    
                    # Valida que el monto por aplicar en la nota de credito no sea mayor o igual al monto disponible
                    if amount >= inv.invoice_id.amount_total:
                        raise osv.except_osv(_('Error!'),_("La factura origen '%s' ya rebaso el monto posible por aplicar!")%(inv.invoice_id.number,))
                    
                    # Valida que en los conceptos de la factura no se aplique un descuento o una devolucion mayor a lo que debe aplicar
                    for line in inv.invoice_line:
                        # Valida que el concepto no sea igual a cero de ser asi lo guarda para eliminarlo
                        if line.edit_refund in ['desc','dev','dev_desc'] and line.price_subtotal == 0.0:
                            delete_lines.append(line.id)
                            continue
                        
                        # Valida que el descuento no llegue al 100%
                        if line.edit_refund == 'desc':
                            if float(line.discount or 0.0) + float(line.discount_refund or 0.0) >= 100:
                                raise osv.except_osv(_('Error!'),_("El descuento sobre el producto '%s' no puede dar al 100 porciento aplicado aplicado!")%(line.name,))
                            # Actualiza el descuento aplicado por notas de credito
                            if line.line_id_ref and line.discount:
                                inv_line_obj.write(cr, uid, [line.line_id_ref.id], {'discount_refund': line.line_id_ref.discount_refund + line.discount}, context=context)
                            # Revisa si hay un monto sobre las notas de credito anteriores, de ser asi prepara una nota de cargo
                            if line.line_id_ref.quantity_refund:
                                if not note_id:
                                    note_id = self._create_refund_debit_note(cr, uid, inv, mode='desc', context=context)
                                # Crea la linea sobre la nota de credito
                                vals = self._prepare_refund_debit_line(cr, uid, note_id, line, mode='desc', context=context)
                                #print "********************** vals debit note *************** ", vals
                                line_id = inv_line_obj.create(cr, uid, vals, context=context)
                        elif line.edit_refund == 'dev':
                            if (line.quantity or 0.0) > (line.quantity_refund or 0.0):
                                raise osv.except_osv(_('Error!'),_("La cantidad del producto '%s' no puede ser mayor a %s!, compruebe la cantidad para generar la devolucion.")%(line.name,line.quantity_refund))
                            # Actualiza la cantidad devuelta sobre notas de credito
                            if line.line_id_ref and line.quantity:
                                inv_line_obj.write(cr, uid, [line.line_id_ref.id], {'quantity_refund': line.line_id_ref.quantity_refund + line.quantity}, context=context)
                            # Revisa si hay un monto sobre las notas de credito anteriores, de ser asi prepara una nota de cargo
                            if line.line_id_ref.discount_refund:
                                if not note_id:
                                    note_id = self._create_refund_debit_note(cr, uid, inv, mode='desc', context=context)
                                # Crea la linea sobre la nota de credito
                                vals = self._prepare_refund_debit_line(cr, uid, note_id, line, mode='dev', context=context)
                                #print "********************** vals debit note *************** ", vals
                                line_id = inv_line_obj.create(cr, uid, vals, context=context)
                            # Agrega a la entrada del almacen la informacion del producto a devolver
                            if not picking_id:
                                context['type'] = type
                                picking_id = picking_obj.create(cr, uid, self._prepare_order_picking_refund(cr, uid, inv, context=context))
                            # Crea la nueva linea sobre la entrada de almacen
                            if line.product_id:
                                if line.product_id.type in ('product', 'consu'):
                                    # Genera la linea del movimiento
                                    move_id = picking_m_obj.create(cr, uid, self._prepare_order_line_move_refund(cr, uid, inv, line, picking_id, date_planned, type=type, context=context))
                                    
                    # Si se genero una nota de cargo la valida y la concilia con la nota de credito
                    if note_id:
                        # Actualiza el total de la nota de cargo
                        self.write(cr, uid, [note_id], {}, context=context)
                        note = self.browse(cr, uid, note_id, context=context)
                        check_total = note.amount_total
                        #print "**************** check_total ************** ", check_total
                        self.write(cr, uid, [note_id], {'check_total': check_total}, context=context)
                        
                        # Pasa la factura a abierto
                        wf_service.trg_validate(uid, 'account.invoice', \
                                                     note_id, 'invoice_open', cr)
                        # Salda la nota de credito con la factura
                        self.generate_voucher_invoice(cr, uid, note_id, inv.id, context=context)
                        
                        # Actualiza la informacion de la factura
                        self.write(cr, uid, [inv.id], {'invoice_id2': note_id}, context=context)
                    
                    ## Valida si el monto aplicado en notas de credito es igual al monto facturado
                    #if amount == inv.invoice_id.amount_total:
                    #    # Concilia los movimientos y elimina la relacion con los voucher generados
                    #    movelines = inv.invoice_id.move_id.line_id
                    #    to_reconcile_ids = {}
                    #    for line in movelines:
                    #        if line.account_id.id == inv.invoice_id.account_id.id:
                    #            to_reconcile_ids[line.account_id.id] = [line.id]
                    #        
                    #        if type(line.reconcile_id) != osv.orm.browse_null:
                    #            reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
                    #    
                    #    for refund in inv.invoice_id.refund_ids:
                    #        for tmpline in refund.move_id.line_id:
                    #            if tmpline.account_id.id == inv.account_id.id:
                    #                to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    #    
                    #    for account in to_reconcile_ids:
                    #        account_m_line_obj.reconcile(cr, uid, to_reconcile_ids[account],
                    #                    writeoff_period_id=inv.period_id.id,
                    #                    writeoff_journal_id = inv.invoice_id.journal_id.id,
                    #                    writeoff_acc_id=inv.invoice_id.account_id.id
                    #                    )
                    #    
                    #    # Cambia el estado a saldado (Solo aplica si la factura se salda con notas de credito)
                    #    self.write(cr, uid, [inv.invoice_id.id], {'state':'repaid'}, context=context)
                    # Aplica cuando solo debe conciliar una parte del monto
                    #elif amount < inv.invoice_id.amount_total:
                    #    # Valida que no se rebase el monto por pagar
                    #    if inv.invoice_id.residual < inv.amount_total:
                    #        raise osv.except_osv(_('Error!'),_("La factura origen '%s' ya rebaso el monto posible por aplicar!")%(inv.invoice_id.number,))
                    #    
                    #    # Concilia los movimientos y elimina la relacion con los voucher generados
                    #    movelines = inv.invoice_id.move_id.line_id
                    #    to_reconcile_ids = {}
                    #    for line in movelines:
                    #        if line.account_id.id == inv.invoice_id.account_id.id:
                    #            to_reconcile_ids[line.account_id.id] = [line.id]
                    #       
                    #        if type(line.reconcile_id) != osv.orm.browse_null:
                    #            raise osv.except_osv(_('Error!'),_("La factura origen '%s' ya esta conciliada en su totalidad, verifique que los pagos parciales no rebasen el monto de la factura!")%(inv.invoice_id.number,))
                    #           
                    #        if type(line.reconcile_partial_id) != osv.orm.browse_null:
                    #            # Agrega los ids de las lineas para aplicar la conciliacion parcial
                    #            for aml in line.reconcile_partial_id.line_partial_ids:
                    #                to_reconcile_ids[aml.account_id.id] = [aml.id]
                    #            # Elimina la conciliacion del movimiento
                    #            reconcile_obj.unlink(cr, uid, line.reconcile_partial_id.id)
                    #        
                    #    # Agrega el movimiento de la nota de credito
                    #    for tmpline in inv.move_id.line_id:
                    #        if tmpline.account_id.id == inv.invoice_id.account_id.id:
                    #            to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    #    
                    #    for account in to_reconcile_ids:
                    #        account_m_line_obj.reconcile_partial(cr, uid, to_reconcile_ids[account],
                    #                    writeoff_period_id=inv.period_id.id,
                    #                    writeoff_journal_id = inv.invoice_id.journal_id.id,
                    #                    writeoff_acc_id=inv.invoice_id.account_id.id
                    #                    )
                    ## Valida que no se pueda conciliar un monto mayor al de la factura
                    #elif amount > inv.invoice_id.amount_total:
                    #    raise osv.except_osv(_('Error!'),_("La factura origen '%s' ya rebaso el monto posible por aplicar!")%(inv.invoice_id.number,))
        # Si hay lineas por eliminar las elimina
        if delete_lines:
            inv_line_obj.unlink(cr, uid, delete_lines, context=context)
        return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
    
    def action_invoice_open_and_concile(self, cr, uid, ids, context=None):
        """
            Valida la factura y la concilia con el faltante a pagar
        """
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        wf_service = netsvc.LocalService('workflow')
        
        # Revisa si alguna factura es de nota de credito y ve si tiene que aplicar una modificacion sobre la factura origen
        for inv in self.browse(cr, uid, ids, context=context):
            #print "**************** valida factura ************* ", inv.id
            # Pasa la factura a abierto
            wf_service.trg_validate(uid, 'account.invoice', \
                                         inv.id, 'invoice_open', cr)
            #print "************** factura tipo ************ ", inv.type
            # Valida que sea una nota de credito generada para el cliente
            if inv.type in ['out_refund','in_refund']:
                # Valida si tiene una factura origen
                if inv.invoice_id:
                    # Salda la nota de credito con la factura
                    vid = self.generate_voucher_invoice(cr, uid, inv.invoice_id.id, inv.id, context=context)
                    
                    ## Concilia los movimientos y elimina la relacion con los voucher generados
                    #movelines = inv.invoice_id.move_id.line_id
                    #to_reconcile_ids = {}
                    #for line in movelines:
                    #    if line.account_id.id == inv.invoice_id.account_id.id:
                    #        to_reconcile_ids[line.account_id.id] = [line.id]
                    #    # Si la factura origen ya esta pagada en su totalidad se omite el proceso
                    #    if type(line.reconcile_id) != osv.orm.browse_null:
                    #        continue
                    #    if type(line.reconcile_partial_id) != osv.orm.browse_null:
                    #        # Agrega los ids de las lineas para aplicar la conciliacion parcial
                    #        for aml in line.reconcile_partial_id.line_partial_ids:
                    #            to_reconcile_ids[aml.account_id.id] = [aml.id]
                    #        # Elimina la conciliacion del movimiento
                    #        reconcile_obj.unlink(cr, uid, line.reconcile_partial_id.id)
                    #    
                    ## Agrega el movimiento de la nota de credito
                    #for tmpline in inv.move_id.line_id:
                    #    if tmpline.account_id.id == inv.invoice_id.account_id.id:
                    #        to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    #
                    #for account in to_reconcile_ids:
                    #    account_m_line_obj.reconcile_partial(cr, uid, to_reconcile_ids[account],
                    #                writeoff_period_id=inv.period_id.id,
                    #                writeoff_journal_id = inv.invoice_id.journal_id.id,
                    #                writeoff_acc_id=inv.invoice_id.account_id.id
                    #                )
        return True
    
    def action_invoice_concile(self, cr, uid, ids, context=None):
        """
            Concilia con el faltante a pagar de la factura origen
        """
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        wf_service = netsvc.LocalService('workflow')
        
        #print "**************** concilia factura ********************* "
        
        # Revisa si alguna factura es de nota de credito y ve si tiene que aplicar una modificacion sobre la factura origen
        for inv in self.browse(cr, uid, ids, context=context):
            #print "**************** salda factura ************* ", inv.id
            # Valida que la factura este en estado abierto
            if inv.state != 'open':
                raise osv.except_osv(_('Error!'),_("Para saldar la factura tiene que estar en estado abierto!"))
            
            #print "************** factura tipo ************ ", inv.type
            # Valida que sea una nota de credito generada para el cliente
            if inv.type in ['out_refund','in_refund']:
                # Valida si tiene una factura origen
                if inv.invoice_id:
                    #print "***************** genera voucher ***************** "
                    # Salda la nota de credito con la factura
                    vid = self.generate_voucher_invoice(cr, uid, inv.invoice_id.id, inv.id, context=context)
                    #print "**************+ voucher generado **************** ", vid
        return True
    
    def get_account_line_refund(self, cr, uid, line_id, context=None):
        """
            Obtiene la cuenta de la linea para nota de credito
        """
        line = self.pool.get('account.invoice.line').browse(cr, uid, line_id, context=context)
        account_id = False
        # Obtiene el tipo de factura
        inv_type = line.invoice_id.type
        
        # Revisa si la linea tiene un producto relacionado y de ser asi obtiene el producto de la categoria
        if line.product_id:
            if line.product_id.categ_id:
                if inv_type == 'in_invoice':
                    if line.product_id.categ_id.property_account_expense_refund_categ:
                        account_id = line.product_id.categ_id.property_account_expense_refund_categ.id
                elif inv_type == 'out_invoice':
                    if line.product_id.categ_id.property_account_income_refund_categ:
                        account_id = line.product_id.categ_id.property_account_income_refund_categ.id
        
        
        
        return account_id

    def _refund_cleanup_invoice_lines(self, cr, uid, lines, context=None):
        """Convert records to dict of values suitable for one2many line creation

            :param list(browse_record) lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        if context is None:
            context = {}
        mode = context.get('mode','none')
        #print "****************** mode **************** ", mode
        clean_lines = []
        for line in lines:
            clean_line = {}
            for field in line._all_columns.keys():
                #print "************* field ", field, " *********** ", line[field]
                if field == 'line_id_ref':
                    #print "****************A**************"
                    clean_line[field] = line.id
                elif field == 'invoice_line_tax_id':
                    #print "****************D**************"
                    tax_list = []
                    for tax in line[field]:
                        tax_list.append(tax.id)
                    clean_line[field] = [(6,0, tax_list)]
                elif field == 'quantity_refund':
                    #print "****************E**************"
                    continue
                elif field == 'quantity':
                    #print "****************F**************"
                    quantity = float(line[field] or 0.0) - float(line['quantity_refund'] or 0.0)
                    #print "********** quantity *********** ", quantity
                    if mode == 'dev':
                        clean_line[field] = 0.0
                    else:
                        clean_line[field] = line[field]
                    clean_line['quantity_refund'] = quantity
                elif field == 'discount':
                    #print "****************G**************"
                    clean_line[field] = 0.0
                elif field == 'account_id':
                    account = self.get_account_line_refund(cr, uid, line.id, context=context)
                    clean_line['account_id'] = account
                elif field == 'discount_refund':
                    clean_line[field] = float(line[field] or 0.0) + float(line['discount'] or 0.0)
                elif line._all_columns[field].column._type == 'many2one':
                    #print "****************B**************"
                    clean_line[field] = line[field].id
                elif line._all_columns[field].column._type not in ['many2many','one2many']:
                    #print "****************C**************"
                    clean_line[field] = line[field]
                else:
                    cliean_line[field] = line[field]
            clean_lines.append(clean_line)
        return map(lambda x: (0,0,x), clean_lines)

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        """Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param integer invoice_id: id of the invoice to refund
            :param dict invoice: read of the invoice to refund
            :param string date: refund creation date from the wizard
            :param integer period_id: force account.period from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """
        obj_journal = self.pool.get('account.journal')
        if context is None:
            context = {}
        type_dict = {
            'out_invoice': 'out_refund', # Customer Invoice
            'in_invoice': 'in_refund',   # Supplier Invoice
            'out_refund': 'out_invoice', # Customer Refund
            'in_refund': 'in_invoice',   # Supplier Refund
        }
        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = self._refund_cleanup_invoice_lines(cr, uid, invoice.invoice_line, context=context)

        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        if journal_id:
            refund_journal_ids = [journal_id]
        elif invoice['type'] == 'in_invoice':
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')], context=context)
        else:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')], context=context)

        if not date:
            date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            'invoice_line': invoice_lines,
            'tax_line': tax_lines,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
        })
        if period_id:
            invoice_data['period_id'] = period_id
        if description:
            invoice_data['name'] = description
        # Agrega el campo de tipo de nota de credito si lo trae entre los parametros
        if context.get('default_filter_refund',False):
            invoice_data['filter_refund'] = context.get('default_filter_refund',False)
        return invoice_data
    
    def action_invoice_refund_partial(self, cr, uid, ids, context=None):
        """
            Valida que no haya facturas en borrador,
            si las hay abre la factura actual sino manda una ventana para generar una nueva
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        
        # Busca que no haya notas de credito en borrador
        refund_ids = self.search(cr, uid, [('type', 'in', ['out_refund','in_refund']),('state','=','draft'),('invoice_id','=',ids[0])], context=context)
        inv = self.browse(cr, uid, ids[0], context=context)
        if not refund_ids or inv.type not in ['out_invoice','in_invoice']:
            # Muestra la ventana para generar una nueva nota de credito
            xml_id = 'action_account_invoice_refund'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            result['tarjet'] = 'new'
        else:
            xml_id = (inv.type == 'out_refund') and 'action_invoice_tree1' or \
                     (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                     (inv.type == 'out_invoice') and 'action_invoice_tree3' or \
                     (inv.type == 'in_invoice') and 'action_invoice_tree4'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', [refund_ids[0]]))
            result['domain'] = invoice_domain
            
            ## Obtiene la vista a cargar
            #dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_mx_facturae_refund', 'invoice_refund_form')
            #
            #return {
            #    'name':_("Notas de Credito"),
            #    'view_mode': 'form',
            #    'view_id': view_id,
            #    'view_type': 'form',
            #    'res_model': 'account.invoice',
            #    'type': 'ir.actions.act_window',
            #    'nodestroy': True,
            #    'target': 'current',
            #    'domain': '[]',
            #    'context': {},
            #    'res_id': refund_ids[0]
            #}
        return result
    
account_invoice()

class account_invoice_line(osv.Model):
    _inherit='account.invoice.line'
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({'discount_refund':0.0, 'quantity_refund':0.0, 'line_id_ref':False})
        return super(account_invoice_line, self).copy(cr, uid, id, default, context)
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            type_inv = 'out_invoice'
            if line.invoice_id:
                type_inv = line.invoice_id.type
            #print "********* type inv amount line *************** ", type_inv
            if type_inv in ['out_refund','in_refund'] or line.invoice_id.debit_note == True:
                if line.edit_refund == 'desc':
                    if float(line.discount or 0.0) + float(line.discount_refund or 0.0) >= 100:
                        raise osv.except_osv(_('Error!'),_("El descuento sobre el producto '%s' no puede dar al 100 porciento de descuento aplicado!")%(line.name,))
                    price = line.price_unit * ((line.discount or 0.0)/100.0)
                    taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                    #print "************** taxes desc *********** ", taxes
                    res[line.id] = taxes['total']
                elif line.edit_refund == 'dev':
                    #print "*************** valida cantidad ************* ", line.quantity, " ** ", line.quantity_refund
                    if line.quantity > line.quantity_refund:
                        raise osv.except_osv(_('Error!'),_("La cantidad del producto '%s' no puede ser mayor a %s!")%(line.name,line.quantity_refund))
                    discount = (line.discount or 0.0)# + line.discount_refund
                    price = line.price_unit * (1-discount/100.0)
                    taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                    #print "************** taxes dev *********** ", taxes
                    res[line.id] = taxes['total']
                elif line.edit_refund == 'dev_desc':
                    res[line.id] = 0.0
                    #print "**************** dev_desc *************************** "
                else:
                    price = line.price_unit * (1-(line.discount or 0.0)/100.0)
                    taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                    res[line.id] = taxes['total']
                    #print "************************ else *********************** ", taxes
            else:
                price = line.price_unit * (1-(line.discount or 0.0)/100.0)
                taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                res[line.id] = taxes['total']
                #print "*************** taxes price ******************* ", taxes
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
                #print "************************* currency invoice ***************** ",
        return res
    
    def _get_refund(self, cr, uid, ids, name, args, context=None):
        """
            Revisa que tipo de accion aplica para cada concepto de la nota de credito
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            val = 'all'
            if line.filter_refund == 'desc':
                val = 'desc'
            elif line.filter_refund == 'dev':
                val = 'dev'
            elif line.filter_refund == 'dev_desc':
                val = 'dev_desc'
                if line.quantity != line.quantity_refund:
                    val = 'dev'
                elif line.discount:
                    val = 'desc'
            res[line.id] = val
        return res
    
    _columns = {
        # Campos para notas de credito
        'filter_refund': fields.related('invoice_id', 'filter_refund', type='selection', selection=[
                ('none', 'No aplica'),
                ('desc', 'Bonificacion por descuento'),
                ('dev', 'Devolucion parcial'),
                ('dev_desc', 'Bonificacion con devolucion parcial')], string="Metodo Nota de Creditdo", readonly=True),
        'line_id_ref': fields.many2one('account.invoice.line', 'Linea referencia', readonly="1"),
        # Campos para indicar cuanto se aplico en notas de credito
        'discount_refund': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
        'quantity_refund': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'edit_refund': fields.function(_get_refund, string='Edicion', type='char', size=64),
        'inv_state': fields.related('invoice_id', 'state', type='char', string="Estado factura", readonly=True),
        'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
    }
    
    _defaults = {
        'filter_refund': 'none',
        'discount_refund': 0.0,
        'quantity_refund': 0.0,
        'edit_refund': 'all'
    }
    
    def action_delete_line(self, cr, uid, ids, context=None):
        """
            Elimina la linea de la factura seleccionada
        """
        self.unlink(cr, uid, ids, context=context)
        return True
    
    def onchange_edit_refund(self, cr, uid, ids, filter_refund, quantity, quantity_refund, discount, context=None):
        """
            Revisa que tipo de accion aplica para cada concepto de la nota de credito
        """
        val = 'all'
        if filter_refund == 'desc':
            val = 'desc'
        elif filter_refund == 'dev':
            val = 'dev'
        elif filter_refund == 'dev_desc':
            val = 'dev_desc'
            if quantity != quantity_refund:
                val = 'dev'
            elif discount:
                val = 'desc'
        return {'value': {'edit_refund': val}}
    
account_invoice_line()

class account_invoice_tax(osv.Model):
    _inherit = "account.invoice.tax"
    
    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        
        type_inv = inv.type
        #print " ************* calcula impuestos ***** ", type_inv, "   **  ", inv.debit_note
        if type_inv in ['out_refund','in_refund'] or inv.debit_note == True:
            for line in inv.invoice_line:
                for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_subtotal), 1, line.product_id, inv.partner_id)['taxes']:
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['account_analytic_id'] = tax['account_analytic_collected_id']
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['account_analytic_id'] = tax['account_analytic_paid_id']
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']
    
            for t in tax_grouped.values():
                t['base'] = cur_obj.round(cr, uid, cur, t['base'])
                t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
                t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
                t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
            return tax_grouped
        return super(account_invoice_tax, self).compute(cr, uid, invoice_id, context=context)

account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
