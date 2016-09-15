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

from openerp.osv import fields, osv

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'
    
    def balance_check(self, cr, uid, st_id, journal_type='bank', context=None):
        """
            Valida que el balance del asiento sea correcto
        """
        session_obj = self.pool.get('pos.session')
        ## Se manda llamar la funcionalidad original
        #super(account_bank_statement, self).balance_check(cr, uid, st_id, journal_type='bank', context=context)
        
        st = self.browse(cr, uid, st_id, context=context)
        
        # Se obtiene el saldo final de la sesion
        session_srch = session_obj.search(cr, uid, [('user_id', '=', st.user_id.id or False)], context=context)
        balance_end_real = session_obj.browse(cr, uid, session_srch[0], context).balance_end_real
        print "*****BALANCE_END_REAL****: ", balance_end_real
        
        # Se valida que el balance final sea menor al esperado
        if not ((abs((st.balance_end or 0.0) - balance_end_real) < 0.0001) or (abs((st.balance_end or 0.0) - balance_end_real) < 0.0001)):
            print "****ERROR BALANCE******"
            raise osv.except_osv(_('Error!'),
                    _('The statement balance is incorrect !\nThe expected balance (%.2f) is different than the computed one. (%.2f)') % (balance_end_real, st.balance_end))
        return True
    
    #def button_confirm_bank(self, cr, uid, ids, context=None):
    #    super(account_bank_statement, self).button_confirm_bank(cr, uid, ids, context=context)
    #    obj_seq = self.pool.get('ir.sequence')
    #    if context is None:
    #        context = {}
    #
    #    for st in self.browse(cr, uid, ids, context=context):
    #        j_type = st.journal_id.type
    #        company_currency_id = st.journal_id.company_id.currency_id.id
    #        if not self.check_status_condition(cr, uid, st.state, journal_type=j_type):
    #            continue
    #
    #        self.balance_check2(cr, uid, st.id, journal_type=j_type, context=context)
    #        if (not st.journal_id.default_credit_account_id) \
    #                or (not st.journal_id.default_debit_account_id):
    #            raise osv.except_osv(_('Configuration Error!'),
    #                    _('Please verify that an account is defined in the journal.'))
    #
    #        if not st.name == '/':
    #            st_number = st.name
    #        else:
    #            c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
    #            if st.journal_id.sequence_id:
    #                st_number = obj_seq.next_by_id(cr, uid, st.journal_id.sequence_id.id, context=c)
    #            else:
    #                st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement', context=c)
    #
    #        for line in st.move_line_ids:
    #            if line.state <> 'valid':
    #                raise osv.except_osv(_('Error!'),
    #                        _('The account entries lines are not in valid state.'))
    #        for st_line in st.line_ids:
    #            if st_line.analytic_account_id:
    #                if not st.journal_id.analytic_journal_id:
    #                    raise osv.except_osv(_('No Analytic Journal!'),_("You have to assign an analytic journal on the '%s' journal!") % (st.journal_id.name,))
    #            if not st_line.amount:
    #                continue
    #            st_line_number = self.get_next_st_line_number(cr, uid, st_number, st_line, context)
    #            self.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)
    #
    #        self.write(cr, uid, [st.id], {
    #                'name': st_number,
    #                'balance_end_real': st.balance_end
    #        }, context=context)
    #        self.message_post(cr, uid, [st.id], body=_('Statement %s confirmed, journal items were created.') % (st_number,), context=context)
    #    return self.write(cr, uid, ids, {'state':'confirm'}, context=context)


class account_cash_statement(osv.osv):
    _inherit = 'account.bank.statement'
    
    #def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, st_line_number, context=None):
    #    """Create the account move from the statement line.
    #
    #       :param int/long st_line_id: ID of the account.bank.statement.line to create the move from.
    #       :param int/long company_currency_id: ID of the res.currency of the company
    #       :param char st_line_number: will be used as the name of the generated account move
    #       :return: ID of the account.move created
    #    """
    #    print "****MODIFICANDO****"
    #    if context is None:
    #        context = {}
    #    res_currency_obj = self.pool.get('res.currency')
    #    account_move_obj = self.pool.get('account.move')
    #    account_move_line_obj = self.pool.get('account.move.line')
    #    account_bank_statement_line_obj = self.pool.get('account.bank.statement.line')
    #    payment_obj = self.pool.get('pos.order.payment')
    #    st_line = account_bank_statement_line_obj.browse(cr, uid, st_line_id, context=context)
    #    st = st_line.statement_id
    #    
    #    # Busca el pago que aplica sobre la linea de conciliacion bancaria
    #    payment_ids = payment_obj.search(cr, uid, [('statement_line_id','=',st_line_id)], context=context)
    #    
    #    context.update({'date': st_line.date})
    #    
    #    # Si tiene creditos no genera el proceso 
    #    if st_line.statement_id.journal_id.self_apply_credit == True:
    #        return False
    #
    #    move_vals = self._prepare_move(cr, uid, st_line, st_line_number, context=context)
    #    move_id = account_move_obj.create(cr, uid, move_vals, context=context)
    #    account_bank_statement_line_obj.write(cr, uid, [st_line.id], {
    #        'move_ids': [(4, move_id, False)]
    #    })
    #    torec = []
    #    acc_cur = ((st_line.amount<=0) and st.journal_id.default_debit_account_id) or st_line.account_id
    #
    #    # Actualiza el apunte contable sobre el pago
    #    if payment_ids:
    #        payment_obj.write(cr, uid, payment_ids, {'move_id':move_id}, context=context)
    #
    #    context.update({
    #            'res.currency.compute.account': acc_cur,
    #        })
    #    amount = res_currency_obj.compute(cr, uid, st.currency.id,
    #            company_currency_id, st_line.amount, context=context)
    #
    #    bank_move_vals = self._prepare_bank_move_line(cr, uid, st_line, move_id, amount,
    #        company_currency_id, context=context)
    #    move_line_id = account_move_line_obj.create(cr, uid, bank_move_vals, context=context)
    #    torec.append(move_line_id)
    #
    #    counterpart_move_vals = self._prepare_counterpart_move_line(cr, uid, st_line, move_id,
    #        amount, company_currency_id, context=context)
    #    account_move_line_obj.create(cr, uid, counterpart_move_vals, context=context)
    #
    #    for line in account_move_line_obj.browse(cr, uid, [x.id for x in
    #            account_move_obj.browse(cr, uid, move_id,
    #                context=context).line_id],
    #            context=context):
    #        if line.state <> 'valid':
    #            raise osv.except_osv(_('Error!'),
    #                    _('Journal item "%s" is not valid.') % line.name)
    #
    #    # Bank statements will not consider boolean on journal entry_posted
    #    account_move_obj.post(cr, uid, [move_id], context=context)
    #    return move_id
    
    def _compute_difference(self, cr, uid, ids, fieldnames, args, context=None):
        """
            Realiza la diferencia entre el saldo final y la diferencia para indicar
            la cantidad de dinero entregado al momento del corte de caja en el
            punto de venta
        """
        balance_end_real = 0.0
        difference_return = 0.0
        difference = 0.0
        result =  dict.fromkeys(ids, 0.0)        
        session_obj = self.pool.get('pos.session')
        
        # Se manda llamar la funcionalidad original del metodo
        difference_return = super(account_cash_statement, self)._compute_difference(cr, uid, ids, fieldnames, args,
                context=context)
        
        # Se obtiene la la diferencia para realizar la resta entre el saldo final
        for obj in self.browse(cr, uid, ids, context=context):
            user_id = obj.user_id.id or False
            #print "********USER_ID******: ", user_id
            # Se obtiene la cantidad entregada al momento del corte de caja (saldo final)
            session_srch = session_obj.search(cr, uid, [('user_id', '=', user_id)], context=context)
            balance_end_real = session_obj.browse(cr, uid, session_srch[0], context).balance_end_real
            #print "*****BALANCE_END_REAL******: ", balance_end_real
            
            difference = balance_end_real - obj.balance_end
            #difference += difference_return
            result[obj.id] = difference
        
        return result
    
    def button_confirm_cash(self, cr, uid, ids, context=None):
        super(account_cash_statement, self). button_confirm_cash(cr, uid, ids, context=context)
        
        super(account_cash_statement, self).button_confirm_bank(cr, uid, ids, context=context)
        absl_proxy = self.pool.get('account.bank.statement.line')

        TABLES = ((_('Profit'), 'profit_account_id'), (_('Loss'), 'loss_account_id'),)

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.difference == 0.0:
                continue

            for item_label, item_account in TABLES:
                if getattr(obj.journal_id, item_account):
                    raise osv.except_osv(_('Error!'),
                                         _('There is no %s Account on the journal %s.') % (item_label, obj.journal_id.name,))

            is_profit = obj.difference < 0.0

            account = getattr(obj.journal_id, TABLES[is_profit][1])

            values = {
                'statement_id' : obj.id,
                'journal_id' : obj.journal_id.id,
                'account_id' : account.id,
                'amount' : obj.difference,
                'name' : 'Exceptional %s' % TABLES[is_profit][0],
            }

            absl_proxy.create(cr, uid, values, context=context)

        return self.write(cr, uid, ids, {'closing_date': time.strftime("%Y-%m-%d %H:%M:%S")}, context=context)

    
    _columns = {
        'difference' : fields.function(_compute_difference, method=True, string="Difference", type="float"),
    }
    
account_cash_statement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
