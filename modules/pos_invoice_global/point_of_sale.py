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

class pos_session(osv.osv):
    _inherit = "pos.session"
    ################################################################################
    #Israel Cabrera Juarez
    def _get_sesion_actual(self, cr, uid, ids, name, arg, context = {} ):
        "Funcion que guarda la sesion actual actual en la base"
        try:
            result = {}
            result_aux = {}
            mostrar = True
            for id in ids:
                cr.execute("UPDATE pos_session SET session_actual=%s",(id,))
            for record in self.browse( cr, uid, ids, context = context):
                result[record.id] = mostrar
            return	result
        except Exception:
            return result_aux
    #Israel Cabrera Juarez
    def _get_usuario_actual(self, cr, uid, ids, name, arg, context = {} ):
        try:
            "funcion que guarda el usuario actual en la base"
            result = {}
            result_aux = {}
            mostrar = True
            cr.execute("""SELECT rp.name FROM
                       res_users AS ru JOIN
                       res_partner AS rp ON
                       ru.partner_id=rp.id WHERE ru.id=%s""",(uid,))
            usuario = str(cr.fetchone()[0])
            for id in ids:
                cr.execute("UPDATE pos_session SET usuario_logueado=%s",(usuario,))
            for record in self.browse( cr, uid, ids, context = context):
                result[record.id] = mostrar
            return	result
        except Exception:
            return result_aux
  
    #Israel Caberera Juarez
    def onchange_actualizar_cliente( self, cr, uid, ids, usuario_actual) :
      "onchange que guarda el usuario actual en la base"
      try:
        if(usuario_actual == True):
          cr.execute("""SELECT rp.name FROM
                     res_users AS ru JOIN
                     res_partner AS rp ON
                     ru.partner_id=rp.id WHERE ru.id=%s""",(uid,))
          usuario = str(cr.fetchone()[0])
          for id in ids:
              
              cr.execute("UPDATE pos_session SET usuario_logueado=%s",(usuario,))
              
              return	{
                'value' :	{ },
                  
               }
      except Exception:
       return	{
                'value' :	{ },
                  
               }
    #Israel Cabrera Juarez
    def onchange_actualizar( self, cr, uid, ids, sesion_actual) :
      "onchange que guarda el usuario actual en la base"
      try:
        if(session_actual == True):
          for id in ids:
              
              cr.execute("UPDATE pos_session SET session_actual=%s",(id,))
              
              return	{
                'value' :	{ },
                  
               }
      except Exception:
             return	{
                'value' :	{ },
                  
               }
    ###############################################################################  
    
    def _confirm_orders(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        #~ Valida que el objeto pos.order se encuentre en las referencias
        link_obj = self.pool.get('links.get.request')
        link_obj.validate_link(cr, uid, 'pos.order', 'Sale Order (POS)', context=None)
        
        for session in self.browse(cr, uid, ids, context=context):
            # Se elimino para 
            order_ids = [order.id for order in session.order_ids if order.state == 'paid']
            #order_ids = [order.id for order in session.order_ids]

            for order in session.order_ids:
                # Crea una poliza por pedido
                reference = 'pos.order,%s'%(order.id,)
                
                move_id = self.pool.get('account.move').create(cr, uid, {'ref' : '%s (%s)'%(session.name,order.name), 'journal_id' : session.config_id.journal_id.id, 'reference':reference}, context=context)
                self.pool.get('pos.order')._create_account_move_line(cr, uid, [order.id], session, move_id, context=context)
                
                #print "*************** estado ************* ", order.state
                
                if order.state not in ('draft', 'picking', 'to_paid','paid', 'return', 'invoiced', 'done'):
                    raise osv.except_osv(
                        _('Error!'),
                        _("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                else:
                    wf_service.trg_validate(uid, 'pos.order', order.id, 'done', cr)

        return True
    
    def wkf_action_close(self, cr, uid, ids, context=None):
        # Close CashBox
        bsl = self.pool.get('account.bank.statement.line')
        for record in self.browse(cr, uid, ids, context=context):
            for st in record.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.pool.get('ir.model.access').check_groups(cr, uid, "point_of_sale.group_pos_manager"):
                        raise osv.except_osv( _('Error!'),
                            _("Your ending balance is too different from the theorical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))
                if (st.journal_id.type not in ['bank', 'cash']):
                    raise osv.except_osv(_('Error!'), 
                        _("The type of the journal for your payment method should be bank or cash "))
                if st.difference and st.journal_id.cash_control == True:
                    if st.difference > 0.0:
                        name= _('Point of Sale Profit')
                        account_id = st.journal_id.profit_account_id.id
                    else:
                        account_id = st.journal_id.loss_account_id.id
                        name= _('Point of Sale Loss')
                    if not account_id:
                        raise osv.except_osv( _('Error!'),
                        _("Please set your profit and loss accounts on your payment method '%s'. This will allow OpenERP to post the difference of %.2f in your ending balance. To close this session, you can update the 'Closing Cash Control' to avoid any difference.") % (st.journal_id.name,st.difference))
                    bsl.create(cr, uid, {
                        'statement_id': st.id,
                        'amount': st.difference,
                        'ref': record.name,
                        'name': name,
                        'account_id': account_id
                    }, context=context)
                
                #print "************ tipo diario ***************** ", st.journal_id.type
                #print "************ tipo diario ***************** ", st.journal_id.name
                
                if st.journal_id.self_apply_credit != True:
                    if st.journal_id.type == 'bank':
                        st.write({'balance_end_real' : st.balance_end})
                    getattr(st, 'button_confirm_%s' % st.journal_id.type)(context=context)
        self._confirm_orders(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state' : 'closed'}, context=context)

        obj = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'point_of_sale', 'menu_point_root')[1]
        return {
            'type' : 'ir.actions.client',
            'name' : 'Point of Sale Menu',
            'tag' : 'reload',
            'params' : {'menu_id': obj},
        }
    
    def open_frontend_cb(self, cr, uid, ids, context=None):
        """
            Valida el inicio de sesion
        """
        user_id = self.browse(cr, uid, ids[0], context=context).user_id.id or False
        # Valida que tanto el usuario como el responsable del punto de venta sean el mismo
        if uid == user_id:
            return super(pos_session, self).open_frontend_cb(cr, uid, ids, context=context)
        else:
            raise osv.except_osv(
                _('Error!'),
                _("No se puede utilizar otro usuario como responsable"))
        
    def button_paid_show(self, cr, uid, ids, context=None):
        
        session_name = self.browse(cr, uid, ids[0], context=context)['name']
        session_id = self.browse(cr, uid, ids[0], context=context)['id']
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'pos_invoice_global', 'view_pos_order_payment_tree')
        view_id = view_ref and view_ref[1] or False
        
        #dummy, view_id('ir.model.data').get_object_reference(cr, uid, 'pos_order_payment', 'view_pos_order_payment_tree')
        return {
            'name':_("Comision"),
            'view_mode': 'tree',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'pos.order.payment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('session_id', '=', session_id)],
            'context': context,
            'res_id': session_name,
        }
    
    def _get_difference_aux(self, cr, uid, ids, field_name, args, context=None):
        """
            Obtiene la diferencia calculada y para poder colocarla en el reporte
        """
        result =  {}
        
        bank_obj = self.pool.get('account.bank.statement')

        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = 0.0
            # Buscando sobre las conciliacion bancaria el balance final real y el balance final
            bank_srch = bank_obj.search(cr, uid, [('pos_session_id', '=', obj.id)], context=context)
            for bank in bank_obj.browse(cr, uid, bank_srch, context=context):
                # Validando que ambos balances tengan valor para realizar la operación
                if bank.balance_end_real and bank.balance_end:
                    result[obj.id] = bank.balance_end_real - bank.balance_end
                    #print "*****RESULT****: ", result[obj.id]
            
        return result
               
       
    
        
    _columns = {
        'balance_end_real': fields.function(_get_difference_aux, type="float", digits=(2, 2), string="Diferencia",
            store=True, method=True),
        'sesion_actual' : fields.function(_get_sesion_actual, string='',type='boolean', method=True, store=False),
        'usuario_actual' : fields.function(_get_usuario_actual, string='',type='boolean', method=True, store=False),
        'session_actual' : fields.integer("session"),
        'usuario_logueado' : fields.char('Usuario Logueado',size=254),
        'order_paid_ids': fields.one2many('pos.order', 'session_id', 'Ordenes en efectivo',
            domain=[('state', 'in', ['paid']),('state_order', 'in', ['cash'])]),
        'order_return_ids': fields.one2many('pos.order', 'session_id', 'Ordenes en devolucion',
            domain=[('state', 'in', ['return']), ('state_order', 'in', ['cash', 'credit'])]),
        'order_credit_ids': fields.one2many('pos.order', 'session_id', 'Ordenes en credito',
            domain=[('state_order', 'in', ['credit'])]),
        #'order_credit_statement': fields.one2many('pos.order.credit', 'session_id', 'Ordenes en credito'),
        'payments_out_session': fields.one2many('pos.order.payment', 'session_id', 'Cobros',
            domain=[('type', '=', 'session_close')])
    }
    
    
pos_session()

class pos_order(osv.osv):
    _inherit = "pos.order"
    _description = "Point of Sale"
    
    def create_from_ui(self, cr, uid, orders, context=None):
        """
            Genera la recepcion de la mercancia automatica sobre el pedido
            Valida pago por credito desde TPV
        """
        partner_obj = self.pool.get('res.partner')
        order_credit_obj = self.pool.get('pos.order.credit')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        
        if not context:
            context = {}
        
        ctx = context.copy()
        
         
        #_logger.info("orders: %r", orders)
        order_ids = []
        wf_service = netsvc.LocalService("workflow")
        for tmp_order in orders:
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
            # Creando la orden de compra en punto de venta
            order_id = self.create(cr, uid, vals, context)
            wf_service.trg_validate(uid, 'pos.order', order_id, 'picking', cr)
            
            for payments in order['statement_ids']:
                payment = payments[2]
                # Valida que el pago a registrar no venga de un credito
                journal = self.pool.get('account.journal').browse(cr, uid, payment['journal_id'], context=context)
                
                # Valida si el pago es por credito
                if journal.self_apply_credit:
                    #print "*****APLICANDO CREDITO*****"
                    
                    self.write(cr, uid, order_id, {'state_order': 'credit'}, context=context)
                        
                    partner_srch = partner_obj.search(cr, uid, [('id', '=', order['partner_id'])], context=context)
                    # Se reduce el credito al cliente
                    for move in partner_obj.browse(cr, uid, partner_srch, context=context):
                        partner_id = move.id or False
                        credit = move.credit_available
                        credit_available = credit - payment['amount']
                    
                    cr.execute("UPDATE res_partner SET credit_limit = %s WHERE id = %s",(credit_available,
                            partner_id,))
                    continue
                else:
                    #print "*******APLICANDO EFECTIVO*****"
                    self.write(cr, uid, order_id, {'state_order': 'cash'}, context=context)
                # Valida que el pago en efectivo sea mayor a cero
                if payment['amount'] > 0.0:
                    # Agregando el pago en la orden
                    self.add_payment(cr, uid, order_id, {
                        'amount': payment['amount'],
                        'payment_date': payment['name'],
                        'statement_id': payment['statement_id'],
                        'payment_name': payment.get('note', False),
                        'journal': payment['journal_id']
                    }, context=context)
                
            if order['amount_return'] and order['amount_return'] > 0.0:
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
            wf_service.trg_validate(uid, 'pos.order', order_id, 'paid', cr)
        return order_ids
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        """
            Calcula monto pagado despues de cerrar sesion
        """
        res = {}
        
        session_state = self.browse(cr, uid, ids[0], context=context).session_id.state
        
        if session_state == 'closed':
            #print "****CALCULANDO DESPUES DE CERRAR SESION*****"
            tax_obj = self.pool.get('account.tax')
            cur_obj = self.pool.get('res.currency')
            for order in self.browse(cr, uid, ids, context=context):
                res[order.id] = {
                    'amount_paid': 0.0,
                    'amount_return':0.0,
                    'amount_tax':0.0,
                }
                val1 = val2 = 0.0
                cur = order.pricelist_id.currency_id
                #print "****PAYMENT_IDS******: ", order.payment_ids
                for payment in order.payment_ids:
                    print "*****PAYMENT.AMOUNT****: ", payment.amount
                    res[order.id]['amount_paid'] +=  payment.amount
                    res[order.id]['amount_return'] += (payment.amount < 0 and payment.amount or 0)
                for line in order.lines:
                    val1 += line.price_subtotal_incl
                    val2 += line.price_subtotal
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1-val2)
                res[order.id]['amount_total'] = cur_obj.round(cr, uid, cur, val1)
                
                #print "******AMOUNT_PAID CAL****: ", res[order.id]['amount_paid']
                #print "******AMOUNT_TOTAL CAL****: ", res[order.id]['amount_total']
            return res
        else:
            #print "****CALCULANDO ANTES DE CERRAR SESION*****"
            res = super(pos_order, self)._amount_all(cr, uid, ids, name, args, context=context)
            return res
    
    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el subtotal sobre el pedido de venta
        """
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.amount_total - order.amount_tax
        return res
    
    def _amount_to_paid(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el monto a pagar
        """
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = 0.00
            account_move = order.account_move or False
            t_paid = 0.00
            total = 0.00
            paid = 0.00
            
            total = order.amount_total
            paid = order.amount_paid
            
            #print "*****ACCOUNT_MOVE to_paid*****: ", account_move
            # Valida si ya tiene el pedido una poliza
            if account_move:
                # Obtiene el pendiente por conciliar de la cuenta de cuentas por cobrar
                for aml in order.account_move.line_id:
                    #print "*******AML.ACCOUNT_ID.TYPE******: ", aml.account_id.type
                    if aml.account_id.type in ('receivable','payable', 'other'):
                        print "****AML.AMOUNT_RESIDUAL_CURRENCY****: ", aml.amount_residual_currency
                        if aml.amount_residual_currency == 0.0:
                            t_paid = order.amount_total - order.amount_paid
                        else:
                            t_paid += aml.amount_residual_currency
            else:
                t_paid = total - paid
                
            res[order.id] = round(t_paid, 2)
            print "*****T_PAID FINAL*****: ", round(t_paid, 2)
        return res
    
    def _get_amount_returned(self, cr, uid, ids, field_name, args, context=None):
        """
            Funcion que calcula el total del producto devuelto por el cliente
        """
        res = {}
        amount_returned = 0.0
        
        for move in self.browse(cr, uid, ids , context=context):
            for line_returned in move.product_returned_ids:
                amount_returned += line_returned.price_subtotal_incl
                print "***AMOUNT_RETURNED****: ", amount_returned
            res[move.id] = amount_returned
        return res
    
    _columns = {
        'state': fields.selection([('draft', 'Nuevo'),
                                   ('picking', 'Entregado'),
                                   ('to_paid', 'Pendiente de pago'),
                                   ('paid', 'Pagado'),
                                   ('return', 'En devolucion'),
                                   ('done', 'Contabilizado'),
                                   ('global', 'Aplicado Factura Global'),
                                   ('cancel', 'Cancelado'),
                                   ('invoiced', 'Facturado')],
                                  'Estado', readonly=True),
        'state_order': fields.selection([('cash', 'Efectivo'), ('credit', 'Credito')], 'Compra en'),
        'amount_untaxed': fields.function(_amount_untaxed, string='Subtotal', type='float',
            digits_compute=dp.get_precision('Point Of Sale'), method=True),
        'to_paid': fields.function(_amount_to_paid, string='Por pagar', type='float'),
        'global_invoice': fields.boolean('Aplico Factura Global'),
        'global_invoice_id': fields.many2one('account.invoice', 'Factura global'),
        'global_invoice_paid': fields.boolean('Pagado en factura Global'),
        'payment_ids': fields.one2many('pos.order.payment', 'order_id', 'Pagos'),
        'per_paid_id': fields.many2one('account.period', 'Periodo de pago'),
        'amount_tax': fields.function(_amount_all, string='Taxes', type='float',
                multi='all'),
        'amount_total': fields.function(_amount_all, string='Total', multi='all'),
        'amount_paid': fields.function(_amount_all, string='Paid',
                states={'draft': [('readonly', False)]}, readonly=True, type='float', multi='all'),
        'amount_return': fields.function(_amount_all, 'Returned', type='float', multi='all'),
        'product_returned_ids': fields.one2many('returned.product', 'order_id', 'Producto devuelto'),
        'amount_product_return': fields.function(_get_amount_returned, type='float', string="Total"),
        'order_origin_id': fields.many2one('pos.order', 'Referencia'),
    }
    
    _defaults = {
        'global_invoice': False,
        'global_invoice_paid': False,
    }
    
    def test_paid(self, cr, uid, ids, context=None):
        """A Point of Sale is paid when the sum
        @return: True
        """
        for order in self.browse(cr, uid, ids, context=context):
            to_paid = order.to_paid or 0.0
            #print "************** amount_total ************* ", order.amount_total
            #print "**************ORDER.TO_PAID************* ", order.to_paid
            # Valida que no haya monto pendiente
            if to_paid > 0.0:
                #print "****COLOCANDO EN 'PENDIENTE DE PAGO'*********"
                self.write(cr, uid, ids, {'state':'to_paid'}, context=context)
                return False
            else:
                if order.lines or order.amount_total == order.amount_paid:
                    #print "****SIN MONTO PENDIENTE******"
                    return True
            if (not order.lines) or (not order.statement_ids) or \
                (abs(order.amount_total-order.amount_paid) > 0.00001):
                #print "****ENTRANDO A 3ER IF*****"
                return False

    
    def _create_account_move_line(self, cr, uid, ids, session=None, move_id=None, context=None):
        """
            Genera los movimientos de la poliza sobre el pedido de venta con cuentas de orden de nota de venta
        """
        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        account_period_obj = self.pool.get('account.period')
        account_tax_obj = self.pool.get('account.tax')
        user_proxy = self.pool.get('res.users')
        property_obj = self.pool.get('ir.property')
        cur_obj = self.pool.get('res.currency')

        ctx = dict(context or {}, account_period_prefer_normal=True)
        period = account_period_obj.find(cr, uid, context=ctx)[0]

        #session_ids = set(order.session_id for order in self.browse(cr, uid, ids, context=context))

        if session and not all(session.id == order.session_id.id for order in self.browse(cr, uid, ids, context=context)):
            raise osv.except_osv(_('Error!'), _('Selected orders do not have the same session!'))

        current_company = user_proxy.browse(cr, uid, uid, context=context).company_id

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False

        def compute_tax(amount, tax, line):
            if amount > 0:
                tax_code_id = tax['base_code_id']
                tax_amount = line.price_subtotal * tax['base_sign']
            else:
                tax_code_id = tax['ref_base_code_id']
                tax_amount = line.price_subtotal * tax['ref_base_sign']

            return (tax_code_id, tax_amount,)

        for order in self.browse(cr, uid, ids, context=context):
            if order.account_move:
                continue
            if order.state not in ('to_paid','paid'):
                continue

            user_company = user_proxy.browse(cr, order.user_id.id, order.user_id.id).company_id

            group_tax = {}
            account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context).id
            
            # Obtiene la cuenta del cliente
            order_account = order.partner_id and \
                            order.partner_id.property_account_receivable_note and \
                            order.partner_id.property_account_receivable_note.id or account_def or False
            if not order_account:
                order_account = order.partner_id and \
                                order.partner_id.property_account_receivable and \
                                order.partner_id.property_account_receivable.id or account_def or current_company.account_receivable.id

            if move_id is None:
                # Create an entry for the sale
                move_id = account_move_obj.create(cr, uid, {
                    'ref' : order.name,
                    'journal_id': order.sale_journal.id,
                }, context=context)

            def insert_data(data_type, values):
                # if have_to_group_by:

                sale_journal_id = order.sale_journal.id

                # 'quantity': line.qty,
                # 'product_id': line.product_id.id,
                values.update({
                    'date': order.date_order[:10],
                    'ref': order.name,
                    'journal_id' : sale_journal_id,
                    'period_id' : period,
                    'move_id' : move_id,
                    'company_id': user_company and user_company.id or False,
                })

                if data_type == 'product':
                    key = ('product', values['partner_id'], values['product_id'])
                elif data_type == 'tax':
                    key = ('tax', values['partner_id'], values['tax_code_id'],)
                elif data_type == 'counter_part':
                    key = ('counter_part', values['partner_id'], values['account_id'])
                else:
                    return

                grouped_data.setdefault(key, [])

                # if not have_to_group_by or (not grouped_data[key]):
                #     grouped_data[key].append(values)
                # else:
                #     pass

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) +  values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                        current_value['tax_amount'] = current_value.get('tax_amount', 0.0) + values.get('tax_amount', 0.0)
                else:
                    grouped_data[key].append(values)

            #because of the weird way the pos order is written, we need to make sure there is at least one line, 
            #because just after the 'for' loop there are references to 'line' and 'income_account' variables (that 
            #are set inside the for loop)
            #TOFIX: a deep refactoring of this method (and class!) is needed in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line

            cur = order.pricelist_id.currency_id
            for line in order.lines:
                tax_amount = 0
                taxes = [t for t in line.product_id.taxes_id]
                computed_taxes = account_tax_obj.compute_all(cr, uid, taxes, line.price_unit * (100.0-line.discount) / 100.0, line.qty)['taxes']

                for tax in computed_taxes:
                    tax_amount += cur_obj.round(cr, uid, cur, tax['amount'])
                    
                    tx = account_tax_obj.browse(cr, uid, tax['id'], context=context)
                    
                    group_key = (tax['tax_code_id'], tax['base_code_id'], tx.account_collected_note_id.id or tax['account_collected_id'], tax['id'])

                    group_tax.setdefault(group_key, 0)
                    group_tax[group_key] += cur_obj.round(cr, uid, cur, tax['amount'])

                amount = line.price_subtotal

                # Cuenta de nota de venta para producto
                if line.product_id.categ_id.property_account_income_note_categ:
                    income_account = line.product_id.categ_id.property_account_income_note_categ.id
                elif  line.product_id.property_account_income:
                    income_account = line.product_id.property_account_income.id
                elif line.product_id.categ_id.property_account_income_categ:
                    income_account = line.product_id.categ_id.property_account_income_categ.id
                else:
                    raise osv.except_osv(_('Error!'), _('Please define income '\
                        'account for this product: "%s" (id:%d).') \
                        % (line.product_id.name, line.product_id.id, ))

                # Empty the tax list as long as there is no tax code:
                tax_code_id = False
                tax_amount = 0
                while computed_taxes:
                    tax = computed_taxes.pop(0)
                    tax_code_id, tax_amount = compute_tax(amount, tax, line)

                    # If there is one we stop
                    if tax_code_id:
                        break

                # Create a move for the line
                insert_data('product', {
                    'name': line.product_id.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'credit': ((amount>0) and amount) or 0.0,
                    'debit': ((amount<0) and -amount) or 0.0,
                    'tax_code_id': tax_code_id,
                    'tax_amount': tax_amount,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                })
                
                #print "******** impuestos calculados ******** ", computed_taxes
                
                # For each remaining tax with a code, whe create a move line
                for tax in computed_taxes:
                    tax_code_id, tax_amount = compute_tax(amount, tax, line)
                    if not tax_code_id:
                        continue

                    insert_data('tax', {
                        'name': _('Tax'),
                        'product_id':line.product_id.id,
                        'quantity': line.qty,
                        'account_id': income_account,
                        'credit': 0.0,
                        'debit': 0.0,
                        'tax_code_id': tax_code_id,
                        'tax_amount': tax_amount,
                        'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                    })

            # Create a move for each tax group
            (tax_code_pos, base_code_pos, account_pos, tax_id)= (0, 1, 2, 3)

            for key, tax_amount in group_tax.items():
                tax = self.pool.get('account.tax').browse(cr, uid, key[tax_id], context=context)
                insert_data('tax', {
                    'name': _('Tax') + ' ' + tax.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': key[account_pos] or income_account,
                    'credit': ((tax_amount>0) and tax_amount) or 0.0,
                    'debit': ((tax_amount<0) and -tax_amount) or 0.0,
                    'tax_code_id': key[tax_code_pos],
                    'tax_amount': tax_amount,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                })

            # counterpart
            insert_data('counter_part', {
                'name': _("Trade Receivables"), #order.name,
                'account_id': order_account,
                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
            })
            
            if order.state == 'paid':
                order.write({'state':'done', 'account_move': move_id})
            else:
                order.write({'account_move': move_id})

        all_lines = []
        for group_key, group_data in grouped_data.iteritems():
            for value in group_data:
                all_lines.append((0, 0, value),)
        if move_id: #In case no order was changed
            self.pool.get("account.move").write(cr, uid, [move_id], {'line_id':all_lines}, context=context)

        return True
    
    def get_period_on_date(self, cr, uid, date, context=None):
        """
            Obtiene el periodo en base a una fecha
        """
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.find(cr, uid, date, context=context)
        return period_ids and period_ids[0] or False
    
    def add_payment(self, cr, uid, order_id, data, context=None):
        """Create a new payment for the order"""
        #print "*****REGISTRANDO PAGO CONTADO Antes de cerrar sesion*****"
        if not context:
            context = {}        
        
        statement_line_obj = self.pool.get('account.bank.statement.line')
        payment_obj = self.pool.get('pos.order.payment')
        property_obj = self.pool.get('ir.property')
        order = self.browse(cr, uid, order_id, context=context)
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', time.strftime('%Y-%m-%d')),
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
        }
        
        # Valida que el monto sea mayor a cero
        if data['amount'] == 0.0:
            return False
        
        # Obtiene cuenta del cliente
        account_id = False
        account_id = (order.partner_id and order.partner_id.property_account_receivable_note \
                     and order.partner_id.property_account_receivable_note.id) or False
        #print "****ACCOUNT_ID add_payment****: ", account_id
        if account_id:
            args['account_id'] = account_id
        else:
            account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
            args['account_id'] = (order.partner_id and order.partner_id.property_account_receivable \
                                 and order.partner_id.property_account_receivable.id) or (account_def and account_def.id) or False
        args['partner_id'] = order.partner_id and order.partner_id.id or None

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (order.partner_id.name, order.partner_id.id,)
            raise osv.except_osv(_('Configuration Error!'), msg)

        context.pop('pos_session_id', False)
        #print "****CONTEXT.POP*****: ", context.pop('pos_session_id', False)

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        for statement in order.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break

        if not statement_id:
            raise osv.except_osv(_('Error!'), _('You have to open at least one cashbox.'))

        args.update({
            'statement_id' : statement_id,
            'pos_statement_id' : order_id,
            'journal_id' : journal_id,
            'type' : 'customer',
            'ref' : order.session_id.name,
        })

        st_line_id = statement_line_obj.create(cr, uid, args, context=context)
        
        # Crea el registro del pago para el pedido de venta
        vals = {
            'order_id': order_id,
            'session_id': order.session_id.id or False,
            'journal_id': journal_id,
            'type': 'session_open',
            'amount': data['amount'],
            'date': data.get('payment_date', time.strftime('%Y-%m-%d')),
            'statement_id': statement_id,
            'statement_line_id': st_line_id,
            'ref' : order.session_id.name,
            #'move_id': move_id,
        }
        payment_obj.create(cr, uid, vals, context=context)
        
        return statement_id

    def add_payment_credit(self, cr, uid, ids, order_id, data, context=None):
        """
            Registra un nuevo pago sobre pedidos con cerrada
        """
        #print"****REGISTRANDO NUEVO PAGO CREDITO despues del cierre de sesion*******"
        if not context:
            context = {}
        statement_line_obj = self.pool.get('account.bank.statement.line')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        payment_obj = self.pool.get('pos.order.payment')
        journal_obj = self.pool.get('account.journal')
        session_obj = self.pool.get('pos.session')
        property_obj = self.pool.get('ir.property')
        order = self.browse(cr, uid, order_id, context=context)
        
        journal_id = data.get('journal', False)
        date = data.get('payment_date', time.strftime('%Y-%m-%d'))
        period_id = self.get_period_on_date(cr, uid, date, context=context)
        obj_seq = self.pool.get('ir.sequence')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', time.strftime('%Y-%m-%d')),
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
        }
        
        
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'pos.order', 'Pedido Venta (POS)', context=None)
        
        # Valida que el monto sea mayor a cero
        if data['amount'] == 0.0:
            return False
        
        ctx = context.copy()
        # Inicializa las variables para generar el movimiento
        mov_lines = []
        rec_ids = []
        #print "****************** data **************** ", data
        #print "****************** journal **************** ", journal_id
        
        # Obtiene el numero de la secuencia del movimiento
        journal = journal_obj.browse(cr, uid, journal_id, context=context)
        mov_number = '/'
        if journal.sequence_id:
            mov_number = obj_seq.next_by_id(cr, uid, journal.sequence_id.id, context=ctx)
        
        # Obtiene cuenta del cliente
        account_id = False
        account_id = (order.partner_id and order.partner_id.property_account_receivable_note \
                     and order.partner_id.property_account_receivable_note.id) or False
        if account_id:
            args['account_id'] = account_id
        else:
            account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
            args['account_id'] = (order.partner_id and order.partner_id.property_account_receivable \
                                 and order.partner_id.property_account_receivable.id) or (account_def and account_def.id) or False
        partner_id = order.partner_id and order.partner_id.id or None

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (order.partner_id.name, order.partner_id.id,)
            raise osv.except_osv(_('Configuration Error!'), msg)
        
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        session_srch = session_obj.search(cr, uid, [('id', '=', data['session_id'][0])], context=context)
        
        for move in session_obj.browse(cr, uid, session_srch, context=context):
            session_name = move.name
            for statement in move.statement_ids:
                if statement.id == statement_id:
                    journal_id = statement.journal_id.id
                    break
                elif statement.journal_id.id == journal_id:
                    statement_id = statement.id
                    break

        args.update({
            'statement_id' : statement_id,
            'pos_statement_id' : order_id,
            'journal_id' : journal_id,
            'type' : 'customer',
            'ref' : session_name,
        })

        st_line_id = statement_line_obj.create(cr, uid, args, context=context)
        
        # Genera el asiento contable
        mov = {
            'name': mov_number,
            'ref': order.name + ': ' + (data.get('payment_name', '') or ''),
            'journal_id': journal_id,
            'period_id': period_id,
            'date': date,
            'to_check': False,
            'reference': 'pos.order,' + str(order_id)
        }
        move_id = move_obj.create(cr, uid, mov, context=ctx)
        
        
        # Genera las lineas de movimiento sobre el pago
        move_line = {
            'journal_id': journal_id,
            'period_id': period_id,
            'name': mov_number or '/',
            'account_id': journal.default_debit_account_id.id or False,
            'move_id': move_id,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': 0.0,
            'debit': data['amount'],
            'date': date,
            'reference': 'pos.order,' + str(order_id)
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=ctx)
        mov_lines.append(new_id)
        move_line = {
            'journal_id': journal_id,
            'period_id': period_id,
            'name': order.name,
            'account_id': account_id,
            'move_id': move_id,
            'partner_id': partner_id,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': data['amount'],
            'debit': 0.0,
            'date': date,
            'reference': 'pos.order,' + str(order_id)
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=ctx)
        mov_lines.append(new_id)
        rec_ids.append(new_id)
        #print "********* poliza creada ************* ", move_id
        #print "********* lineas creadas ************* ", mov_lines
        
        # Revisa si el pedido ya esta registrado sobre una factura global
        payment_type = 'session_close' if order.session_id.state == 'closed' or order.session_id.state == 'closing_control' else 'session_open'
        if order.global_invoice:
            payment_type = 'invoice_global'
        
        # Crea el registro del pago para el pedido de venta
        vals = {
            'order_id': order_id,
            'session_id': data['session_id'][0],
            'journal_id': journal_id,
            'type': payment_type,
            'amount': data['amount'],
            'date': date,
            'move_id': move_id,
            'ref' : data['session_id'][0],
            'statement_id': statement_id,
            'statement_line_id': st_line_id,
        }
        payment_id = payment_obj.create(cr, uid, vals, context=context)
        
        # Concilia el movimiento pagado con el pedido
        if order.account_move:
            for aml in order.account_move.line_id:
                # Si la linea es la principal donde se carga el monto facturado la pasa a los valores a conciliar
                if account_id == aml.account_id.id:
                    rec_ids.append(aml.id)
            # Concilia los movimientos generados con la factura global
            reconcile = False
            if len(rec_ids) >= 2:
                reconcile = move_line_obj.reconcile_partial(cr, uid, rec_ids,
                                                writeoff_acc_id=account_id,
                                                writeoff_period_id=period_id,
                                                writeoff_journal_id=journal_id)
        return payment_id
    
    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        #print "*****PERIOD_IDS****: ", period_ids
        return period_ids[0]

    def action_picking(self, cr, uid, ids, context=None):
        """
            Realiza la entrega de mercancia
        """
        self.create_picking(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'picking'}, context=context)
        #print "************ action_picking **************** "
        return True

    def action_paid(self, cr, uid, ids, context=None):
        """
            Valida si se realizo la sesion completa
        """
        #self.create_picking(cr, uid, ids, context=context)
        #self.write(cr, uid, ids, {'state': 'paid'}, context=context)
        
        order_ids = []
        
        for order in self.browse(cr, uid, ids, context=context):
            # Valdia si el pago es una factura global
            if order.global_invoice_id:
                order_ids.append(order.id)
        if order_ids:
            self.pool.get('account.invoice').pos_generate_voucher_invoice_global(cr, uid, order_ids, context=context)
        
        #Registra
        period_id = self._get_period(cr, uid, context=context)
        #print "******PERIOD_ID******: ", period_id
        self.write(cr, uid, ids, {'per_paid_id': period_id, 'state': 'paid'}, context=context)
        return True
    
    def return_products(self, cr, uid, ids, context=None):
        pos_line_obj = self.pool.get('pos.order.line')
        
        # Pasando el pedido en devuelto
        self.write(cr, uid, ids, {'state': 'return'}, context)
        return True
    
pos_order()


class pos_order_payment(osv.osv):
    _name = "pos.order.payment"
    _description = "Point of Sale - Payment"
    
    _columns = {
        'order_id': fields.many2one('pos.order', 'Pedido de venta'),
        'session_order': fields.related('order_id', 'session_id', type='many2one', relation='pos.session',
            string='Sesion de la orden', store=True),
        'session_id': fields.many2one('pos.session', 'Sesion'),
        'journal_id': fields.many2one('account.journal', 'Diario'),
        'statement_id': fields.many2one('account.bank.statement', 'Extracto'),
        'statement_line_id': fields.many2one('account.bank.statement.line', 'Linea de Extracto'),
        'amount': fields.float('Extracto', digits_compute=dp.get_precision('Point Of Sale')),
        'move_id': fields.many2one('account.move', 'Poliza pago'),
        'date': fields.date('Fecha'),
        'type': fields.selection([('invoice_global', 'Factura Global'),
                                   ('session_open', 'Sesion abierta'),
                                   ('session_close', 'Sesion cerrada')], 'Referencia pago', readonly=True),
        'ref': fields.char('Referencia', size=128),
    }
    
pos_order_payment()


class returned_product(osv.osv):
    _name = 'returned.product'
    
    def _amount_line_all(self, cr, uid, ids, field_names, arg, context=None):
        res = dict([(i, {}) for i in ids])
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            taxes_ids = [ tax for tax in line.product_id.taxes_id if tax.company_id.id == line.order_id.company_id.id ]
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = account_tax_obj.compute_all(cr, uid, taxes_ids, price, line.quantity, product=line.product_id, partner=line.order_id.partner_id or False)

            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_subtotal_incl'] = cur_obj.round(cr, uid, cur, taxes['total_included'])
        return res
    
    _columns = {
        'name': fields.char('Nombre'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'quantity': fields.float('Cantidad'),
        'price_unit': fields.float('Precio unidad'),
        'discount': fields.float('Descuento'),
        'price_subtotal': fields.function(_amount_line_all, string='Subtotal neto', multi="amount_all"),
        'price_subtotal_incl': fields.function(_amount_line_all, string='Subtotal', multi="amount_all"),
        'order_id': fields.many2one('pos.order', 'Pedido de venta'),
    }

returned_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
