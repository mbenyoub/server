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

from osv import osv, fields
from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _document_type = {
        'sale': 'Sales Receipt',
        'purchase': 'Purchase Receipt',
        'payment': 'Supplier Payment',
        'receipt': 'Customer Payment',
        'transfer': 'Money Transfer',
        False: 'Payment',
    }
    
    _columns = {
        'transfer_id': fields.many2one('account.transfer','Transferencia', readonly=True,
                                       states={'draft':[('readonly',False)]}, ondelete="cascade"),
        'journal_id_transfer': fields.many2one('account.journal','Diario Transferencia', readonly=True, domain=[('type','in',['cash','bank'])], ondelete="restrict"),
        'type':fields.selection([
                             ('sale','Venta'),
                             ('purchase','Compra'),
                             ('payment','Pago'),
                             ('receipt','Cobro'),
                             ('transfer','Transferencia'),
                             ],'Tipo', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def action_view_move(self, cr, uid, ids, context=None):
        """
            Muestra la poliza generada sobre los pagos
        """
        # Obtiene el objeto a cargar
        voucher = self.browse(cr, uid, ids[0], context=context)
        res_id = voucher.move_id.id or False
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_form')
        
        return {
            'name':_("Poliza"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            'res_id': res_id
        }

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        """
            Agregar funcionalidad sobre transferencias al momento del pago
        """
        if context is None:
            context = {}
        res = super(account_voucher,self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context=context)
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        # Obtiene la informacion de la linea del movimiento para cuando aplican transferencias
        if voucher.type == 'transfer':
            #import pdb; pdb.set_trace()
            if voucher.transfer_id.src_journal_id.id == voucher.journal_id.id:
                res['credit'] = voucher.paid_amount_in_company_currency
            else:
                res['debit'] = voucher.paid_amount_in_company_currency
            if res['debit'] < 0: res['credit'] = -res['debit']; res['debit'] = 0.0
            if res['credit'] < 0: res['debit'] = -res['credit']; res['credit'] = 0.0
            sign = res['debit'] - res['credit'] < 0 and -1 or 1
            res['currency_id'] = company_currency <> current_currency and current_currency or False
            res['amount_currency'] = company_currency <> current_currency and sign * voucher.amount or 0.0
        return res
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
            Modifica el diario que se aplica sobre la poliza
        '''
        if context is None:
            context = {}
        move_obj = self.pool.get('account.move')
        mline_obj = self.pool.get('account.move.line')
        
        print "********************* Crea poliza de banco *****************"
        
        res = super(account_voucher, self).action_move_line_create(self, cr, uid, ids, context=context)
        
        # Recorre los registros
        for voucher in self.browse(cr, uid, ids, context=context):
            # Actualiza el tipo de movimiento sobre la poliza
            move_obj.write(cr, uid, [voucher.move_id.id], {'type':voucher.type}, context=context)
            
            # Valida que reciba un movimiento
            if not voucher.move_id:
                continue
            # Valida que el tipo de voucher sea una transferencia
            if voucher.type != 'transfer':
                continue
            
            # Actualiza el diario de transferencia sobre el movimiento creado
            move_obj.write(cr, uid, [voucher.move_id.id], {'journal_id_transfer': voucher.journal_id_transfer.id}, context=context)
        return True
    
account_voucher()
