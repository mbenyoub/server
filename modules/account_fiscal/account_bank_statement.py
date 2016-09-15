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
# Account generation from template wizards
# ---------------------------------------------------------

class account_bank_statement(osv.Model):
    _inherit='account.bank.statement'
    
    def action_import_data_wizard(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con la ventana para la importacion de registros de bancos en el sistema
        """
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_bank_statement_import_view')
        
        return {
            'name':_("Importar movimientos de banco"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement.import',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_statement_id': ids[0]
            }
        }
    
    def action_clean_data_bank(self, cr, uid, ids, context=None):
        """
            Limpia los movimientos de banco
        """
        bank_obj = self.pool.get('account.bank.statement.bank')
        
        # Actualiza documento
        self.write(cr, uid, ids, {}, context=context)
        
        # Elimina registros
        bank_ids = bank_obj.search(cr, uid, [('statement_id','in',ids)],context=context)
        bank_obj.unlink(cr, uid, bank_ids, context=context)
        return True
    
    def onchange_journal_id(self, cr, uid, statement_id, journal_id, context=None):
        """
            Actualiza registros cuando se cambia el diario
        """
        if not journal_id:
            return {}
        # balance_start = self._compute_balance_end_real(cr, uid, journal_id, context=context)

        journal_data = self.pool.get('account.journal').read(cr, uid, journal_id, ['company_id', 'currency'], context=context)
        company_id = journal_data['company_id']
        currency_id = journal_data['currency'] or self.pool.get('res.company').browse(cr, uid, company_id[0], context=context).currency_id.id
        return {'value': {'company_id': company_id, 'currency': currency_id}}
    
    def button_cancel(self, cr, uid, ids, context=None):
        """
            Cancelar conciliacion bancaria
        """
        done = []
        #account_move_obj = self.pool.get('account.move')
        line_obj = self.pool.get('account.move.line')
        income_obj = self.pool.get('account.fiscal.statement')
        balance_obj = self.pool.get('account.bank.statement.balance')
        
        for st in self.browse(cr, uid, ids, context=context):
            if st.state=='draft':
                continue
            # Busca los registros relacionados con el documento y elimina la relacion
            line_ids = line_obj.search(cr, uid, [('statement_id','=',st.id)])
            if line_ids:
                line_obj.write(cr, uid, line_ids, {'statement_id':False}, context=context)
            
            # Elimina los registros de banco aplicados el el saldo bancario
            balance_ids = balance_obj.search(cr, uid, [('statement_id','=',st.id)])
            if balance_ids:
                balance_obj.unlink(cr, uid, balance_ids, context=context)
            
        return self.write(cr, uid, ids, {'state':'cancel'}, context=context)
    
    def button_reopen(self, cr, uid, ids, context=None):
        """
            Vuelve a abrir la conciliacion bancaria para su edicion
        """
        return self.write(cr, uid, ids, {'state':'open'}, context=context)
    
    def button_confirm_bank(self, cr, uid, ids, context=None):
        """
            Confirma los movimientos de conciliacion bancaria
        """
        bank_obj = self.pool.get('account.bank.statement.bank')
        balance_obj = self.pool.get('account.bank.statement.balance')
        move_obj = self.pool.get('account.move.line')
        journal_obj = self.pool.get('account.journal')
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}
        
        # Recorre los documentos de conciliacion
        for st in self.browse(cr, uid, ids, context=context):
            j_type = st.journal_id.type
            company_currency_id = st.journal_id.company_id.currency_id.id
            # Valida si el estado del documento se encuentra en borrador o abierto
            if not self.check_status_condition(cr, uid, st.state, journal_type=j_type):
                continue
            
            # self.balance_check(cr, uid, st.id, journal_type=j_type, context=context)
            #if (not st.journal_id.default_credit_account_id) \
            #        or (not st.journal_id.default_debit_account_id):
            #    raise osv.except_osv(_('Configuration Error!'),
            #            _('Please verify that an account is defined in the journal.'))
            
            # Si no se a definido un nombre para el documento agrega un numero por la serie
            if not st.name == '/':
                st_number = st.name
            else:
                # Obtiene la secuencia de la conciliacion
                c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
                st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement.con', context=c)
            
            #for line in st.move_line_ids:
            #    if line.state <> 'valid':
            #        raise osv.except_osv(_('Error!'),
            #                _('The account entries lines are not in valid state.'))
            #for st_line in st.line_ids:
            #    if st_line.analytic_account_id:
            #        if not st.journal_id.analytic_journal_id:
            #            raise osv.except_osv(_('No Analytic Journal!'),_("You have to assign an analytic journal on the '%s' journal!") % (st.journal_id.name,))
            #    if not st_line.amount:
            #        continue
            #    st_line_number = self.get_next_st_line_number(cr, uid, st_number, st_line, context)
            #    self.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)
            
            # Valida que tenga movimientos de banco y movimientos para conciliar
            if not st.move_ids:
                raise osv.except_osv(_('Warning!'),_("No hay transacciones pendientes, Seleccione la opcion de calcular o de obtener transacciones pendientes!"))
            if not st.bank_ids:
                raise osv.except_osv(_('Warning!'),_("No hay movimientos de banco registrados, debe registrar los movimientos de banco del periodo para implementar la conciliacion!"))
            # Valida que todos los movimientos de banco esten conciliados para poder confirmar
            bank_ids = bank_obj.search(cr, uid, [('statement_id','=',st.id),('state','in',['PREV','NCON'])])
            if bank_ids:
                raise osv.except_osv(_('Warning!'),_("No se puede confirmar la conciliacion si hay movimientos de banco sin conciliar!"))
            
            amount_con = 0.0
            con = 0
            # Recorre los movmientos de las transacciones
            for st_line in st.move_ids:
                if not st_line.amount:
                    continue
                # Valida que el movimiento no este conciliado sobre la parte de conciliaciones
                if st_line.concilie_bank and st_line.bank_id:
                    raise osv.except_osv(_('Transaccion conciliada!'),_("El movimiento '%s' ya fue conciliado, actualice las transacciones pendientes, vuelva a calcular los movimientos o rompa la conciliacion con el banco!") % (st_line.name,))
                
                # Valida que el apunte contable no se haya aplicado en otra conciliacion bancaria
                if st_line.move_id.statement_id:
                    raise osv.except_osv(_('Transaccion conciliada!'),_("El movimiento '%s' ya fue conciliado, actualice las transacciones pendientes, vuelva a calcular los movimientos o rompa la conciliacion con el banco!. (Conciliacion Bancaria: %s)") % (st_line.name,st_line.move_id.statement_id.name))
                
                # Relaciona el pago con los movimientos conciliados con la poliza
                if st_line.bank_id:
                    move_obj.write(cr, uid, [st_line.move_id.id], {'statement_id': st.id}, context=context)
                    con +=1
                    # Actualiza el total conciliado
                    amount_con += st_line.amount
            
            # Valida que haya conciliaciones en el movimiento
            if con < 1:
                raise osv.except_osv(_('Warning!'),_("No hay movimientos conciliados!"))
            
            # Obtiene el saldo real del banco registrado por conciliaciones
            amount_bal = journal_obj.action_get_balance(cr, uid, st.journal_id.id, st.date, context=context)
            # Actualiza la informacion de la conciliacion
            self.write(cr, uid, [st.id], {
                    'name': st_number,
                    'state': 'confirm',
                    'balance_start': amount_bal,
                    'balance_end_real': amount_bal + amount_con
            }, context=context)
            
            # Actualiza el saldo bancario
            bal_id = balance_obj.create(cr, uid, {
                    'statement_id': st.id,
                    'name': st_number,
                    'date': st.date,
                    'amount': amount_con
            }, context=context)
            self.message_post(cr, uid, [st.id], body=_('Statement %s confirmed, journal items were created.') % (st_number,), context=context)
        return True
    
    def button_dummy(self, cr, uid, ids, context=None):
        """
            Compara lo que tengo en la parte de movimientos con la parte de los registros bancarios
        """
        bankv_obj = self.pool.get('account.bank.statement.move')
        bankb_obj = self.pool.get('account.bank.statement.bank')
        
        # Actualiza los movimientos disponibles
        self.action_update_moves(cr, uid, ids, context=context)
        
        # Recorre los registros
        for statement in self.browse(cr, uid, ids, context=context):
            # Valida que haya transacciones disponibles
            if not statement.move_ids:
                raise osv.except_osv(_('Warning!'), _('No hay transacciones disponibles para calcular la conciliacion!'))
            # Valida que haya Registros de Banco
            if not statement.bank_ids:
                raise osv.except_osv(_('Warning!'), _('No hay registros de banco disponibles para calcular la conciliacion!'))
            
            bank_ids = []
            # Recorre los registros de los movimientos registrados en openerp
            for move in statement.move_ids:
                # Valida que todavia este disponible el movimiento
                if move.move_id.concilie_bank:
                    # Elimina el registro conciliado de la lista
                    bankv_obj.unlink(cr, uid, [move.id])
                # Busca el campo que coincida con el movimiento
                bankb_ids = bankb_obj.search(cr, uid, [('statement_id','=',statement.id),('date','=',move.date),('amount','=',move.amount),('id','not in', bank_ids)])
                # Si hay un registro que coincida lo relaciona
                if len(bankb_ids):
                    #Actualiza el detalle del movimento
                    bank_ids.append(bankb_ids[0])
                    bankv_obj.write(cr, uid, [move.id], {'bank_ids': [[6, False, [bankb_ids[0]]]]}, context=context)
            
            print "************** statement bank_ids ***************** ",statement.bank_ids
            print "************** bank_ids ***************** ",bank_ids
            
            bankf_ids = []
            # Valida que no haya movimientos de banco no conciliados
            if len(bank_ids) == len(statement.bank_ids):
                # Recorre los movimientos de banco que no se han conciliado
                bankb_ids = bankb_obj.search(cr, uid, [('statement_id','=',statement.id),('id','not in', bank_ids)])
                for bank in bankb_obj.browse(cr, uid, bankb_ids, context=context):
                    # Busca si hay un registro que coincida con el monto
                    bankv_ids = bankv_obj.search(cr, uid, [('statement_id','=',statement.id),('bank_id','=', False),('amount','=',bank.amount)])
                    if len(bankv_ids):
                        #Actualiza el detalle del voucher
                        bank_ids.append(bank.id)
                        bankv_obj.write(cr, uid, [bankv_ids[-1]], {'bank_ids': [[6, False, [bank.id]]]}, context=context)
                    else:
                        # Pone el movimiento de banco como no conciliado
                        bankf_ids.append(bank.id)
                
            print "************** bank_ids ***************** ",bank_ids
            
            # Actualiza los registros del banco identificados y no identificados
            bankb_obj.write(cr, uid, bank_ids, {'state': 'CON'}, context=context)
            bankb_obj.write(cr, uid, bankf_ids, {'state': 'NCON'}, context=context)
            
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)
    
    def action_update_moves(self, cr, uid, ids, context=None):
        """
            Actualiza la lista de movimientos pendientes
        """
        vals = {}
        vline_ids = []
        acc_obj = self.pool.get('account.account')
        mline_obj = self.pool.get('account.move.line')
        bankv_obj = self.pool.get('account.bank.statement.move')
        bankb_obj = self.pool.get('account.bank.statement.bank')
        journal_obj = self.pool.get('account.journal')
        
        # Recorre los registros
        for statement in self.browse(cr, uid, ids, context=context):
            # Valida que tenga un diario asignado en el documento de conciliacion
            if not statement.journal_id:
                raise osv.except_osv(_('Warning!'), _('El documento de concialiacion debe tener un diario asignado!'))
            
            # Elimina las transacciones actuales
            bankv_ids = bankv_obj.search(cr, uid, [('statement_id','in',ids)])
            if bankv_ids:
                bankv_obj.unlink(cr, uid, bankv_ids)
            
            # Pone los movimientos de los registros del banco como pendientes por revisar
            bankb_ids = bankb_obj.search(cr, uid, [('statement_id','in',ids)])
            if bankb_ids:
                bankb_obj.write(cr, uid, bankb_ids, {'state': 'PREV'})
            
            # Obtiene las cuentas de liquidez
            acc_ids = acc_obj.search(cr, uid, [('type','=','liquidity')])
            
            # Obtiene el saldo real del banco registrado por conciliaciones
            amount_bal = journal_obj.action_get_balance(cr, uid, statement.journal_id.id, statement.date, context=context)
            
            # Obtiene los apuntes que se registraron y no estan conciliados (ANTERIORES AL PERIODO DEL REGISTRO)
            line_ids = mline_obj.search(cr, uid, [('journal_id','=',statement.journal_id.id),('account_id','in',acc_ids),('statement_id','=',None),('date','<=',statement.date)], context=context)
            if line_ids:
                # Recorre los movmientos obtenidos
                for line in mline_obj.browse(cr, uid, line_ids, context=context):
                    # Obtiene el monto y el tipo de movimiento
                    if line.credit == 0.0:
                        amount = line.debit
                        mtype = 'debit'
                    else:
                        amount = line.credit * -1
                        mtype = 'credit'
                    
                    reference = ''
                    #print "*************** referencia ************************** ", line.reference
                    # Referencia sobre apunte
                    if line.move_id.reference:
                        reference = "%s,%s"%(line.move_id.reference._name,line.move_id.reference.id)
                    else:
                        reference = "account.move,%s"%(line.move_id.id,)
                    
                    vals = {
                        'statement_id': statement.id,
                        'name': "%s -%s($ %s)"%(line.move_id.name,line.name,amount), 
                        'date': line.date,
                        'move_id': line.id,
                        'partner_id': line.partner_id.id,
                        'reference': reference,
                        'type': mtype,
                        'amount': amount
                    }
                    #print "********** Vals  ******* ", vals
                    vline_id = bankv_obj.create(cr, uid, vals, context=context)
                    vline_ids.append(vline_id)
            
            # Actualiza el saldo inicial en la conciliacion
            self.write(cr, uid, [statement.id], {'balance_start': amount_bal, 'state': 'open'})
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no pueda eliminar la conciliacion si esta cerrada
        """
        stat = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in stat:
            # Valida que el movimiento no este conciliado
            if t['state'] in ('draft','open'):
                unlink_ids.append(t['id'])
            else:
                raise osv.except_osv(_('Documento Conciliado!'),_('No puedes eliminar documentos de conciliacion que ya fueron cerrados, primero debes cancelar la conciliacion'))
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    _columns = {
        'state': fields.selection([('draft', 'Nuevo'),
                                   ('open','Abierto'), # used by cash statements
                                   ('confirm', 'Cerrado'),
                                   ('cancel', 'Cancelado'),],
                                   'Estado', required=True, readonly="1",
                                   help='Cuando una nueva conciliacion es creada la pone en \'Nuevo\'.\n'
                                        'Despues de obtener la informacion del banco pasa a estado \'Abierto\'. \n'
                                        'Se agrega una doble confirmacion para dejar la conciliacion como cerrada una vez validado el proceso.'),
        'bank_ids': fields.one2many('account.bank.statement.bank', 'statement_id', 'Movimientos Banco', states={'confirm':[('readonly', True)]}),
        'move_ids': fields.one2many('account.bank.statement.move', 'statement_id', 'Transacciones', states={'confirm':[('readonly', True)]}),
    }
    
account_bank_statement()

class account_bank_statement_bank(osv.Model):
    """
        Detalle en conciliacion bancaria sobre movimientos del banco
    """
    _name='account.bank.statement.bank'
    _order= 'date asc'
    
    def action_conciliate_line(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con los movimientos posibles a relacionar
        """
        # Obtiene el objeto a cargar
        bank = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_bank_statement_conciliate_bank_view')
        
        return {
            'name':_("Conciliacion Movimientos"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement.conciliate.bank',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_statement_id': bank.statement_id.id,
                'default_amount': bank.amount,
                'default_name': bank.move,
                'default_bank_id': bank.id
            }
        }
    
    def action_break_conciliate_line(self, cr, uid, ids, context=None):
        """
            Rompe la conciliacion del movimiento
        """
        voucher_obj = self.pool.get('account.bank.statement.move')
        
        # Modifica los registros conciliados
        self.write(cr, uid, ids, {'state': 'PREV'}, context=context)
        
        if type(ids) != list:
            ids = [ids]
        
        break_ids = [] # Ids por romper conciliacion
        statement_id = 0
        # Recorre los registros
        for bank in self.browse(cr, uid, ids, context=context):
            statement_id = bank.statement_id.id
            voucher_ids = voucher_obj.search(cr, uid, [('bank_ids','in',[bank.id])], context=context)
            if voucher_ids:
                # Recorre los registros
                for voucher in voucher_obj.browse(cr, uid, voucher_ids, context=context):
                    if len(voucher.bank_ids) > 1:
                        # Agrega los movimientos relacionados al que se le esta rompiendo la conciliacion
                        for bnk in voucher.bank_ids:
                            if bnk.id != bank.id:
                                break_ids.append(bnk.id)
                # Elimina los registros relacionados
                voucher_obj.write(cr, uid, voucher_ids, {'bank_ids': [[6, False, []]]}, context=context)
                #print "************** rompe conciliacion voucher_ids ************ ", voucher_ids
                # Revisa si hay mas registros por romper conciliacion
                if len(break_ids):
                    self.action_break_conciliate_line(cr, uid, break_ids, context=context)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_bank_statement_form')
        return {
            'name':_("Conciliacion Bancaria"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : statement_id, # id of the object to which to redirected
        }
        
    def _get_name(self, cr, uid, ids, field_name, arg, context=None):
        """
            Combina el nombre del movimiento con el monto
        """
        res = {}
        for bank in self.browse(cr, uid, ids, context=context):
            res[bank.id] = bank.move + ' (' + str(bank.amount) + ')'
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no pueda eliminar los detalles si ya esta conciliado
        """
        #print "************* unlink bank ************* "
        if context is None:
            context = {}
        # Recorre los registros
        for bank in self.browse(cr, uid, ids, context=context):
            # Valida que el movimiento no este conciliado
            if bank.state == 'CON':
                raise osv.except_osv(_('Movimiento Conciliado Eliminado!'),_('No puedes eliminar movimientos conciliados, primero debes romper la conciliacion'))
        # Elimina los registros
        return super(account_bank_statement_bank, self).unlink(cr, uid, ids, context=context)
    
    _columns = {
        'statement_id': fields.many2one('account.bank.statement', 'Statement', select=True, required=True, ondelete='cascade'),
        'name':fields.function(_get_name, type='char', size=128, string="Nombre", store=True, readonly=True),
        'move': fields.char('Movimiento', size=128, required=True),
        'date': fields.date('Fecha'),
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account')),
        'state': fields.selection([
                                    ('PREV', 'Por Revisar'),
                                    ('CON', 'Conciliado'),
                                    ('NCON', 'No conciliado'),], 'Estatus', readonly=True),
        'st_bank': fields.related('statement_id','state', type='char', readonly=True, store=False, string='Estado conciliacion'),
    }
    
    _defaults = {
        'name': '/',
        'move': '/',
        'amount': 0.0,
        'date': fields.datetime.now,
        'state': 'PREV'
    }

account_bank_statement_bank()

class account_bank_statement_move(osv.Model):
    """
        Detalle en conciliacion bancaria sobre cobros, pagos, ingresos y egresos basado en movimientos
    """
    _name = 'account.bank.statement.move'
    _order = 'date desc'
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    def _concilie_bank(self, cr, uid, ids, field_name, arg, context=None):
        """
            Valida si se concilio el movimiento con el banco
        """
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            res[statement.id] = False
            amount = 0.0
            id = False
            for bank in statement.bank_ids:
                amount += bank.amount
                id = bank.id
            if amount >= statement.amount:
                res[statement.id] = id
        return res
    
    def action_conciliate_line(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con los movimientos posibles a relacionar
        """
        # Obtiene el objeto a cargar
        move = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_bank_statement_conciliate_move_view')
        
        return {
            'name':_("Conciliacion Transacciones"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement.conciliate.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_statement_id': move.statement_id.id,
                'default_amount': move.amount,
                'default_name': move.name,
                'default_move_id': move.id
            }
        }
    
    def action_break_conciliate_line(self, cr, uid, ids, context=None):
        """
            Rompe la conciliacion del movimiento
        """
        bank_obj = self.pool.get('account.bank.statement.bank')
        if type(ids) != list:
            ids = [ids]
        
        bank_ids = []
        v_ids = []
        statement_id = 0
        # Recorre los registros
        for voucher in self.browse(cr, uid, ids, context=context):
            statement_id = voucher.statement_id.id
            v_ids.append(voucher.id)
            # Registra todos los movimientos de banco que se utilizan
            for bank in voucher.bank_ids:
                bank_ids.append(bank.id)
                # Valida si hay otras transacciones involucradas con el movimiento
                voucher_ids = self.search(cr, uid, [('bank_ids','in',[bank.id])], context=context)
                if voucher_ids:
                    for v in voucher_ids:
                        v_ids.append(v)
        # Elimina la relacion con los movimientos
        bank_obj.write(cr, uid, bank_ids, {'state': 'PREV'}, context=context)
        self.write(cr, uid, v_ids, {'bank_ids': [[6, False, []]]}, context=context)
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_bank_statement_form')
        return {
            'name':_("Conciliacion Bancaria"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : statement_id, # id of the object to which to redirected
        }
    
    _columns = {
        'statement_id': fields.many2one('account.bank.statement', 'Conciliacion bancaria', select=True, required=True, ondelete='cascade'),
        'name': fields.char('Nombre', size=64, required=True),
        'date': fields.date('Fecha'),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
        'move_id': fields.many2one('account.move.line', 'Registro Banco', ondelete='cascade', required=True, domain=[('type','=','liquidity')]),
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account')),
        'bank_id':fields.function(_concilie_bank, type='many2one', relation="account.bank.statement.bank", string="Movimiento de banco", store=True, readonly=True),
        'bank_ids': fields.many2many('account.bank.statement.bank', 'account_bank_statement_move_concilie', 'bank_id', 'moves_id', 'Movimientos de Banco'),
        'concilie_bank': fields.related('move_id','concilie_bank', type='boolean', readonly=True, store=False, string='Conciliado'),
        'st_bank': fields.related('statement_id','state', type='char', readonly=True, store=False, string='Estado conciliacion'),
        'type': fields.selection([('debit', 'Abono'),('credit', 'Cargo'),], 'Tipo', readonly=True),
    }
    
    _defaults = {
        'name': '/',
        'date': fields.datetime.now,
        'amount': 0.0,
        'type': 'debit'
    }

account_bank_statement_move()

class account_bank_statement_balance(osv.Model):
    """
        Registro de saldos obtenidos por periodo
    """
    _name = 'account.bank.statement.balance'
    
    _columns = {
        'statement_id': fields.many2one('account.bank.statement', 'Conciliacion Bancaria', select=True, required=True, ondelete='cascade'),
        'journal_id': fields.related('statement_id', 'journal_id', type="many2one", relation="account.journal", store=True, string="Diario Banco", readonly=True),
        'period_id': fields.related('statement_id', 'period_id', type="many2one", relation="account.period", store=True, string="Periodo", readonly=True),
        'name': fields.char('Referencia', size=128, required=True),
        'date': fields.date('Fecha'),
        'amount': fields.float('Monto', digits_compute=dp.get_precision('Account')),
    }
    
    _defaults = {
        'name': '/',
        'date': fields.datetime.now,
        'amount': 0.0,
    }

account_bank_statement_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
