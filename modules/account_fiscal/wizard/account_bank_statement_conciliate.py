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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_bank_statement_conciliate_bank(osv.osv_memory):
    """ Conciliacion manual de movimientos de banco """
    _name = 'account.bank.statement.conciliate.bank'
    _description = 'Conciliacion manual de Movimientos de Banco'
    
    def onchange_statement_id(self, cr, uid, ids, statement_id, context=None):
        """
            Actualiza la informacion de los movimientos pendientes de relacionar
        """
        move_obj = self.pool.get('account.bank.statement.move')
        lines = []
        
        if statement_id:
            # Busca los movimientos pendientes de conciliar
            move_ids = move_obj.search(cr, uid, [('statement_id','=',statement_id),('bank_id','=',False)])
            if move_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for line in move_obj.browse(cr, uid, move_ids, context=context):
                    val = {
                        'move_id': line.id,
                        'partner_id': line.partner_id.id or False,
                        'amount': line.amount,
                        'type': line.type,
                        'date': line.date,
                        'apply': False
                    }
                    lines.append(val)
        # Actualiza los valores de retorno
        return {'value': {'move_ids': lines}}
    
    def action_validate_conciliation(self, cr, uid, ids, context=None):
        """
            Valida que la conciliacion con los registros seleccionados sea correcta
        """
        id = 0
        # Recorre los registros a validar
        for con in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            move_ids = []
            # Obtiene el total a cargar en las transacciones
            for line in con.move_ids:
                # Valida que este seleccionado el movimiento
                if line.apply == False:
                    continue
                amount += line.move_id.amount
                # Valida que el id del move no se encuentre en la lista
                if len(move_ids):
                    if line.move_id.id in move_ids:
                        raise osv.except_osv(_('Warning!'), _('La transaccion ' + line.move_id.name + ' esta repetida!'))
                # Agrega el registro al arreglo
                move_ids.append(line.move_id.id)
            id = con.statement_id.id
            # Valida que el total conciliado de la transaccion sea igual al movimiento
            if amount != con.amount:
                raise osv.except_osv(_('Warning!'), _('El total del monto de las transacciones debe ser igual al del movimiento de banco!'))
            
            # Actualiza la informacion de los move_ids
            self.pool.get('account.bank.statement.move').write(cr, uid, move_ids, {'bank_ids': [[6, False, [con.bank_id.id]]]}, context=context)
            self.pool.get('account.bank.statement.bank').write(cr, uid, [con.bank_id.id], {'state': 'CON'}, context=context)
            
        if not id:
            return True
        
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
            'res_id' : id, # id of the object to which to redirected
        }
    
    def button_dummy(self, cr, uid, ids, context=None):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        
        self.write(cr, uid, ids, {}, context=context)
        # Obtiene el objeto a cargar
        if not ids: return True
        res_id = ids[0]
        
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
            'context': context,
            'res_id' : res_id, # id of the object to which to redirected
        }
    
    def _get_amount_apply(self, cr, uid, ids, name, args, context=None):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        res = {}
        for wizard in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            for line in wizard.move_ids:
                if line.apply:
                    amount += line.amount
            res[wizard.id] = amount
        return res
    
    _columns = {
        'name': fields.char('Movimiento', size=128, readonly=True),
        'bank_id': fields.many2one('account.bank.statement.bank','Movimiento de Banco', select="1", readonly=True),
        'move_ids': fields.one2many('account.bank.statement.conciliate.bank.line', 'wizard_id', 'Transacciones'),
        'amount':fields.float('Monto a conciliar', readonly=True),
        'amount_apply': fields.function(_get_amount_apply, string="Monto conciliado", type='float'),
        #'amount_apply':fields.float('Monto conciliado', readonly=True),
        'statement_id': fields.many2one('account.bank.statement', 'Documento conciliacion', readonly=True)
    }

account_bank_statement_conciliate_bank()

class account_bank_statement_conciliate_bank_line(osv.osv_memory):
    """ Relacion transacciones Conciliacion manual de movimientos de banco """
    _name = 'account.bank.statement.conciliate.bank.line'
    
    def onchange_statement_move(self, cr, uid, ids, move_id, context=None):
        """
            Actualiza la informacion de la transaccion seleccionada
        """
        move = self.pool.get('account.bank.statement.move').browse(cr, uid, move_id, context=context)
        values = {}
        
        # Actualiza los valores de retorno
        if move:
            values = {
                'partner_id': move.partner_id.id,
                'amount': move.amount,
                'type': move.type,
                'date': move.date
            }
        return {'value': values}
    
    _columns = {
        'wizard_id': fields.many2one('account.bank.statement.conciliate.bank', 'Wizard conciliacion'),
        'move_id' : fields.many2one('account.bank.statement.move','Transaccion', select="1"),
        'partner_id' : fields.many2one('res.partner','Empresa', readonly=True),
        'amount':fields.float('Monto', readonly=True),
        'type': fields.selection([('debit', 'Abono'),('credit', 'Cargo'),], 'Tipo', readonly=True),
        'date': fields.date('Fecha', readonly=True),
        'apply': fields.boolean('Aplicar')
    }

account_bank_statement_conciliate_bank_line()

###########################
#     Conciliacion manual para transacciones
##########################

class account_bank_statement_conciliate_move(osv.osv_memory):
    """ Conciliacion manual de Transacciones """
    _name = 'account.bank.statement.conciliate.move'
    _description = 'Conciliacion manual de Transacciones'
    
    def onchange_statement_id(self, cr, uid, ids, statement_id, context=None):
        """
            Actualiza la informacion de los bancos pendientes de relacionar
        """
        bank_obj = self.pool.get('account.bank.statement.bank')
        lines = []
        
        if statement_id:
            # Busca los movimientos de banco pendientes de conciliar
            bank_ids = bank_obj.search(cr, uid, [('statement_id','=',statement_id),('state','!=','CON')])
            if bank_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for line in bank_obj.browse(cr, uid, bank_ids, context=context):
                    val = {
                        'bank_id': line.id,
                        'amount': line.amount,
                        'date': line.date,
                        'apply': False
                    }
                    lines.append(val)
        # Actualiza los valores de retorno
        return {'value': {'bank_ids': lines}}
    
    def action_validate_conciliation(self, cr, uid, ids, context=None):
        """
            Valida que la conciliacion con los registros seleccionados sea correcta
        """
        id = 0
        # Recorre los registros a validar
        for con in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            bank_ids = []
            # Obtiene el total a cargar en los movimientos
            for b_line in con.bank_ids:
                # Valida que este seleccionado el movimiento
                if b_line.apply == False:
                    continue
                amount += b_line.bank_id.amount
                # Valida que el id del movimiento no se encuentre en la lista
                if len(bank_ids):
                    if b_line.bank_id.id in bank_ids:
                        raise osv.except_osv(_('Warning!'), _('El movimiento de banco ' + b_line.bank_id.name + ' esta repetido!'))
                # Agrega el registro al arreglo
                bank_ids.append(b_line.bank_id.id)
            id = con.statement_id.id
            # Valida que el total conciliado de la transaccion sea igual al movimiento
            if amount != con.amount:
                raise osv.except_osv(_('Warning!'), _('El total del monto de las transacciones debe ser igual al del movimiento de banco!'))
            
            # Actualiza la informacion de los move_ids
            self.pool.get('account.bank.statement.move').write(cr, uid, [con.move_id.id], {'bank_ids': [[6, False, bank_ids]]}, context=context)
            self.pool.get('account.bank.statement.bank').write(cr, uid, bank_ids, {'state': 'CON'}, context=context)
            
        if not id:
            return True
        
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
            'res_id' : id, # id of the object to which to redirected
        }
    
    def button_dummy(self, cr, uid, ids, context=None):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        
        self.write(cr, uid, ids, {}, context=context)
        # Obtiene el objeto a cargar
        if not ids: return True
        res_id = ids[0]
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'wizard_account_bank_statement_conciliate_move_view')
        
        return {
            'name':_("Conciliacion Movimientos"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.bank.statement.conciliate.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
            'res_id' : res_id, # id of the object to which to redirected
        }
    
    
    def _get_amount_apply(self, cr, uid, ids, name, args, context):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        res = {}
        for wizard in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            for line in wizard.bank_ids:
                if line.apply:
                    amount += line.amount
            res[wizard.id] = amount
        return res
    
    _columns = {
        'name': fields.char('Movimiento', size=128, readonly=True),
        'move_id': fields.many2one('account.bank.statement.move','Transaccion', select="1", readonly=True),
        'bank_ids': fields.one2many('account.bank.statement.conciliate.move.line', 'wizard_id', 'Movimientos de Banco'),
        'amount':fields.float('Monto a conciliar', readonly=True),
        'amount_apply': fields.function(_get_amount_apply, string="Monto conciliado", type='float'),
        #'amount_apply':fields.float('Monto conciliado', readonly=True),
        'statement_id': fields.many2one('account.bank.statement', 'Documento conciliacion', readonly=True)
    }

account_bank_statement_conciliate_move()

class account_bank_statement_conciliate_move_line(osv.osv_memory):
    """ Relacion transacciones Conciliacion manual de Transacciones """
    _name = 'account.bank.statement.conciliate.move.line'
    
    def onchange_statement_bank(self, cr, uid, ids, bank_id, context=None):
        """
            Actualiza la informacion del movimiento de banco seleccionado
        """
        bank = self.pool.get('account.bank.statement.bank').browse(cr, uid, bank_id, context=context)
        values = {}
        
        # Actualiza los valores de retorno
        if bank:
            values = {
                'amount': bank.amount,
                'date': bank.date
            }
        return {'value': values}
    
    _columns = {
        'wizard_id': fields.many2one('account.bank.statement.conciliate.move', 'Wizard conciliacion'),
        'bank_id' : fields.many2one('account.bank.statement.bank','Movimiento', select="1"),
        'amount':fields.float('Monto', readonly=True),
        'date': fields.date('Fecha', readonly=True),
        'apply': fields.boolean('Aplicar')
    }

account_bank_statement_conciliate_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
