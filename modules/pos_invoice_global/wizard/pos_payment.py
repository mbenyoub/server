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

from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

class account_journal(osv.osv):
    _inherit = 'account.journal'

class pos_make_payment(osv.osv_memory):
    _inherit = 'pos.make.payment'
    _description = 'Point of Sale Payment'
    
    def check(self, cr, uid, ids, context=None):
        """
            Registra el pago sobre el pedido de venta (POS)
        """
        print "****REGISTRANDO EL PAGO SOBRE PEDIDO DE VENTA****"
        amount = 0.0
        context = context or {}
        order_obj = self.pool.get('pos.order')
        obj_partner = self.pool.get('res.partner')
        active_id = context and context.get('active_id', False)
        #print "******ACTIVE_ID*****: ", active_id
        
        # Obtiene la orden donde se va a registrar el pago
        order = order_obj.browse(cr, uid, active_id, context=context)
        account = order.account_move        
        
        #amount = round(order.amount_total, 2) - round(order.amount_paid, 2)
        data = self.read(cr, uid, ids, context=context)[0]
        print "*****DATA****: ", data
        # this is probably a problem of osv_memory as it's not compatible with normal OSV's
        data['journal'] = data['journal_id'][0]
        #print "******AMOUNT WIZARD*****: ", amount
        if data['amount'] <> 0.0:
            #print "******ACCOUNT****: ", account
            # Valida si el pago va por un pedido que no tiene sesion abierta
            if not account:
                order_obj.add_payment(cr, uid, active_id, data, context=context)
            else:
                print "*****REALIZANDO PAGO CREDITO*****"
                payment_id = order_obj.add_payment_credit(cr, uid, ids, active_id, data, context=context)
                #print "*****PAYMENT_ID*****: ", payment_id
        paid_release = order_obj.test_paid(cr, uid, [active_id])
        print "*****PAID_RELEASE****: ", paid_release
        if paid_release:
            print "*****PEDIDO PAGADO*****"
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'pos.order', active_id, 'paid', cr)
            return {'type' : 'ir.actions.act_window_close' }
        else:
            return {'type': 'ir.actions.act_window_close'}
         ##self.print_report(cr, uid, ids, context=context)

        return self.launch_payment(cr, uid, ids, context=context)

    def _default_journal(self, cr, uid, context=None):
        if not context:
            context = {}
        session = False
        order_obj = self.pool.get('pos.order')
        active_id = context and context.get('active_id', False)
        if active_id:
            order = order_obj.browse(cr, uid, active_id, context=context)
            session = order.session_id
        if session:
            for journal in session.config_id.journal_ids:
                if journal.self_apply_credit == False:
                    return journal.id
        return False
    
    def _default_session(self, cr, uid, context=None):
        """
            Obtiene la sesion donde se efectuara el pago
        """
        try:
            # Ejecucion de query para obtener el id de la sesion
            cr.execute("SELECT id FROM pos_session WHERE state = 'opened' and user_id=%s",(uid,))
            session_id = cr.fetchone()[0]
            return session_id
        except Exception:
            raise osv.except_osv(_('¡Alerta!'),
                    _('No es Posible procesar su pago por que no hay ninguna sesion en proceso, Espere por favor a que una sesion sea abierta y este en proceso '))
                
    
    def _default_order(self, cr, uid, context=None):
        if not context:
            context = {}
        order_id = False
        order_obj = self.pool.get('pos.order')
        active_id = context and context.get('active_id', False)
        if active_id:
            order = order_obj.browse(cr, uid, active_id, context=context)
            order_id = order.id or False
            if order_id:
                return order_id
        else: 
            return False

    def _default_amount(self, cr, uid, context=None):
        order_obj = self.pool.get('pos.order')
        active_id = context and context.get('active_id', False)
        if active_id:
            order = order_obj.browse(cr, uid, active_id, context=context)
            return order.amount_total - order.amount_paid
        return False
    
    _columns = {
        'session_id': fields.many2one('pos.session', 'Sesion'),
        'order_id': fields.many2one('pos.order', 'Pedido de venta'),
        'amount': fields.float('Amount', digits=(16,2), required= True),
    }

    _defaults = {
        'journal_id' : _default_journal,
        'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'amount': _default_amount,
        'order_id': _default_order,
        'session_id': _default_session,
    }

pos_make_payment()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
