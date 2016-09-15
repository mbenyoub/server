# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class hr_expense_expense(osv.osv):
    _inherit = "hr.expense.expense"
    
    def onchange_currency_id(self, cr, uid, ids, currency_id=False, company_id=False, context=None):
        """
            Cuando cambia la moneda valida si hay un diario que ya maneje la moneda
        """
        res =  {'value': {}}
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('type','=','purchase'), ('currency','=',currency_id), ('company_id', '=', company_id)], context=context)
        if journal_ids:
            res['value']['journal_id'] = journal_ids[0]
        return res
    
    def get_period_on_date(self, cr, uid, date, context=None):
        """
            Obtiene el periodo en base a una fecha
        """
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.find(cr, uid, date, context=context)
        return period_ids and period_ids[0] or False
        
    def onchange_date(self, cr, uid, ids, date, context=None):
        """
            Actualiza el periodo del registro al cambiar la fecha
        """
        res = {}
        # Si hay una fecha actualiza el periodo
        if date:
            res['period_id'] = self.get_period_on_date(cr, uid, date, context=context)
        return {'value': res}
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el monto total sobre lo gastado, aplicando un desgloce sobre impuestos
        """
        res = {}
        for expense in self.browse(cr, uid, ids, context=context):
            res[expense.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            # Obtiene el total sobre lo no facturado
            for line in expense.line_ids:
                res[expense.id]['amount_untaxed'] += line.total_amount
            # Obtiene el total sobre lo facturado
            for line in expense.invoice_ids:
                res[expense.id]['amount_tax'] += line.amount_tax
                res[expense.id]['amount_untaxed'] += line.amount_untaxed
            res[expense.id]['amount_total'] = res[expense.id]['amount_tax'] + res[expense.id]['amount_untaxed']
        return res
    
    def button_reset_taxes(self, cr, uid, ids, context=None):
        """
            Actualiza los totales del documento
        """
        if context is None:
            context = {}
        invoice_obj = self.pool.get('account.invoice')
        ctx = context.copy()
        invoice_ids = []
        # Actualiza las facturas para que se refresquen los totales
        invoice_ids = invoice_obj.search(cr, uid, [('expense_id','in',ids)], context=ctx)
        invoice_obj.write(cr, uid, invoice_ids, {}, context=ctx)
        
        # Actualiza el registro de gasto
        self.write(cr, uid, ids, {}, context=ctx)
        return True
    
    def action_validate(self, cr, uid, ids, context=None):
        """
            Validacion sobre la
        """
        inv_obj = self.pool.get('account.invoice')
        link_obj = self.pool.get('links.get.request')
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        
        #~ Valida que el objeto hr.expense.expense se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'hr.expense.expense', 'Gastos', context=None)
        
        # Recorre los registros de gasto
        for exp in self.browse(cr, uid, ids, context=context):
            # Valida que el empleado tenga un contacto para poder generar la poliza
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error Validacion!'),_("El empleado %s no tiene registrada una direccion particular para continuar con el proceso")%(exp.employee_id.name,))
            # Valida que el gasto tenga al menos un registro para aplicar
            if exp.invoice_ids or exp.line_ids:
                if exp.invoice_ids:
                    # Referencia para agregar a facturas donde apunta al gasto
                    ref = 'hr.expense.expense,%s'%(exp.id,)
                    # Valida que si hay gastos facturados esten todos en borrador
                    for inv in exp.invoice_ids:
                        if inv.state != 'draft':
                            raise osv.except_osv(_('Error Validacion!'),_("No puede validar el gasto con facturas abiertas o pagadas, revise que la factura %s del proveedor %s se ecuentre en estado borrador")%(inv.number,inv.partner_id.name,))
                        # Actualiza el total facturado sobre la factura
                        inv_obj.write(cr, uid, [inv.id], {}, context=context)
                        invoice = inv_obj.browse(cr, uid, inv.id, context=context)
                        check_total = invoice.amount_total
                        # Actualiza el total validado de la factura y la referencia sobre el gasto
                        inv_obj.write(cr, uid, [inv.id], {'check_total': check_total, 'ref': ref}, context=context)
                        
                        # Pasa la factura a abierto (Valida factura)
                        wf_service.trg_validate(uid, 'account.invoice', \
                                                     inv.id, 'invoice_open', cr)
            else:
                raise osv.except_osv(_('Error Validacion!'),_("Revise que haya al menos un detalle agregado sobre el gasto"))
        # Actualiza los totales del gasto
        self.button_reset_taxes(cr, uid, ids, context=context)
        return True
    
    def action_move_create(self, cr, uid, ids, context=None):
        """
            Crea la poliza del gasto
        """
        # Valores iniciales
        move_obj = self.pool.get('account.move')
        mline_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        cur_date = time.strftime('%Y-%m-%d')
        date = cur_date
        period_id = False
        to_reconcile_ids = []
        # Recorre los registros
        for exp in self.browse(cr, uid, ids, context=context):
            # Valida que haya una fecha de factura
            if exp.date:
                date = exp.date
            else:
                # Fecha actual
                date = cur_date
            # Valida si hay un periodo seleccionado en el gasto
            if exp.period_id:
                period_id = exp.period_id.id or False
            else:
                # Obtiene el periodo sobre la fecha registrada
                period_id = self.get_period_on_date(cr, uid, date, context=context)
            
            # Inicializa las variables para generar el movimiento
            mov_lines = []
            
            # Obtiene el numero de la secuencia del movimiento
            exp_number = obj_seq.next_by_code(cr, uid, 'hr.expense.expense.sequence', context=context)
            mov_number = '/'
            if exp.journal_id.sequence_id:
                mov_number = obj_seq.next_by_id(cr, uid, exp.journal_id.sequence_id.id, context=context)
            
            # Referencia para agregar a facturas donde apunta al gasto
            ref = 'hr.expense.expense,%s'%(exp.id,)
            
            # Genera el asiento contable
            mov = {
                'name': mov_number,
                'ref': exp_number,
                'journal_id': exp.journal_id.id or False,
                'period_id': period_id,
                'date': date,
                'narration': exp.note,
                'company_id': exp.company_id.id or False,
                'to_check': False,
                'reference': ref
            }
            print "********** gasto movimiento *********** ", mov
            move_id = move_obj.create(cr, uid, mov, context=context)
            
            # Genera el apunte sobre el monto principal cargado al gasto
            move_line = {
                'journal_id': exp.journal_id.id or False,
                'period_id': period_id,
                'name': mov_number or '/',
                'account_id': exp.account_id.id or False,
                'move_id': move_id,
                'partner_id': exp.employee_id.address_home_id.id or False,
                'credit': exp.amount_total,
                'debit': 0.0,
                'date': exp.date,
                'ref': exp_number,
                'reference': ref
            }
            new_id = mline_obj.create(cr, uid, move_line, context=context)
            mov_lines.append(new_id)
            
            # Genera los apuntes sobre lo no facturado
            for line in exp.line_ids:
                move_line = {
                    'journal_id': exp.journal_id.id,
                    'period_id': period_id,
                    'name': line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': exp.employee_id.address_home_id.id or False,
                    'credit': 0.0,
                    'debit': line.total_amount,
                    'date': line.date_value,
                    'ref': exp_number,
                    'reference': ref
                }
                new_id = mline_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
            
            inv_ids = []
            # Recorre las facturas para generar los apuntes sobre lo facturado
            for inv in exp.invoice_ids:
                inv_ids.append(inv.id)
                reconcile_ids = []
                # Movimiento para aplicacion de lo pagado sobre cuentas por cobrar al proveedor
                move_line = {
                    'journal_id': exp.journal_id.id or False,
                    'period_id': period_id,
                    'name': inv.number or '/',
                    'account_id': inv.account_id.id or False,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id or False,
                    'credit': 0.0,
                    'debit': inv.amount_total,
                    'date': inv.date_invoice,
                    'ref': exp_number,
                    'reference': ref
                }
                new_id = mline_obj.create(cr, uid, move_line, context=context)
                mov_lines.append(new_id)
                reconcile_ids.append(new_id)
                
                #print "****************** partner employee ******************** ", exp.employee_id.address_home_id.id
                
                # Concilia el movimiento de la factura con el movimiento generado para dejarla como pagada
                for line in inv.move_id.line_id:
                    # Valida si la linea de movimiento es la del movimiento por pagar
                    if (inv.account_id.id == line.account_id.id):
                        # Concilia con el movimiento creado en la factura
                        # Si la linea es la principal donde se carga el monto facturado la pasa a los valores a conciliar
                        if line.account_id.id == inv.account_id.id:
                            reconcile_ids.append(line.id)
                            #print "************** line partner id ************** ", line.partner_id.id
                            # Si ya hay conciliaciones sobre el movimiento las rompe
                            if type(line.reconcile_id) != osv.orm.browse_null:
                                reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
                #print "************ reconcile_ids ************** ", reconcile_ids
                to_reconcile_ids.append(reconcile_ids)
                # Crea los movimientos del iva por acreditar al iva acreditado
                for tax_line in inv.tax_line:
                    # Valida que tenga valor en la base del monto
                    if tax_line.base:
                        tax_apply_account_id = False
                        # Actualiza el valor de la cuenta a aplicar para los impuestos
                        if inv.type in ('out_invoice','in_invoice'):
                            tax_apply_account_id = tax_line.account_tax_id.account_collected_id_apply.id or False
                        else:
                            tax_apply_account_id = tax_line.account_tax_id.account_paid_id_apply.id or False
                        # Valida si la factura no hay un registro por acreditar
                        if not tax_apply_account_id:
                            # Continua con el siguiente impuesto
                                continue
                        
                        # Movimiento para aplicacion de impuestos 
                        move_line = {
                            'journal_id': exp.journal_id.id or False,
                            'period_id': period_id,
                            'name': inv.number or '/',
                            'account_id': tax_line.account_id.id or False,
                            'move_id': move_id,
                            'partner_id': inv.partner_id.id or False,
                            'credit': tax_line.amount,
                            'debit': 0.0,
                            'date': inv.date_invoice,
                            'ref': exp_number,
                            'reference': ref
                        }
                        # Valida que el monto aplicado no sea negativo
                        if move_line['credit'] < 0.0:
                            move_line['debit'] = move_line['credit'] * -1
                            move_line['credit'] = 0.0
                        # Crea el registro del impuesto por acreditar
                        new_id = mline_obj.create(cr, uid, move_line, context=context)
                        mov_lines.append(new_id)
                        move_line = {
                            'journal_id': exp.journal_id.id or False,
                            'period_id': period_id,
                            'name': inv.number or '/',
                            'account_id': tax_apply_account_id,
                            'move_id': move_id,
                            'partner_id': inv.partner_id.id or False,
                            'credit': 0.0,
                            'debit': tax_line.amount,
                            'date': inv.date_invoice,
                            'ref': exp_number,
                            'reference': ref,
                            'base': tax_line.base,
                            'tax_code_id': tax_line.tax_code_id.id or False,
                            'tax_amount': tax_line.amount
                        }
                        # Valida que el monto aplicado no sea negativo
                        if move_line['credit'] < 0.0:
                            move_line['debit'] = move_line['credit'] * -1
                            move_line['credit'] = 0.0
                        # Crea el registro del impuesto acreditado
                        new_id = mline_obj.create(cr, uid, move_line, context=context)
                        mov_lines.append(new_id)
            
            # Asienta la poliza generada
            move_obj.button_validate(cr, uid, [move_id], context=context)
            
            # Conciliacion sobre los apuntes seleccionados
            for reconcile in to_reconcile_ids:
                #print "*************** reconcile ************* ", reconcile
                mline_obj.reconcile(cr, uid, reconcile,
                        writeoff_period_id=exp.period_id.id,
                        writeoff_journal_id = exp.journal_id.id,
                        writeoff_acc_id=exp.account_id.id
                    )
            
            # Agrega el origen sobre los datos de la factura
            inv_obj.write(cr, uid, inv_ids, {'origin': exp_number}, context=context)
            
            # Actualiza la informacion del gasto
            self.write(cr, uid, [exp.id], {'date': date, 'period_id': period_id, 'account_move_id': move_id, 'name': exp_number, 'state': 'done'}, context=context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Proceso para cancelacion de movimientos sobre la factura
        """
        move_obj = self.pool.get('account.move')
        reconcile_obj = self.pool.get('account.move.reconcile')
        inv_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        
        # Recorre los registros para la cancelacion de la factura
        for exp in self.browse(cr, uid, ids, context=context):
            # Cancela las conciliaciones y el movimiento del gasto
            if exp.account_move_id:
                # Concilia los movimientos y elimina la relacion con los voucher generados
                movelines = exp.account_move_id.line_id
                recs = []
                for line in movelines:
                    if line.reconcile_id:
                        recs += [line.reconcile_id.id]
                    if line.reconcile_partial_id:
                        recs += [line.reconcile_partial_id.id]
                    # Si ya hay conciliaciones sobre el movimiento las rompe
                    #if type(line.reconcile_id) != osv.orm.browse_null:
                    #    reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
                
                # Elimina el movimiento 
                reconcile_obj.unlink(cr, uid, recs)
                
                # Elimina la poliza de movimiento del gasto
                move_obj.button_cancel(cr, uid, [exp.account_move_id.id], context=context)
                move_obj.unlink(cr, uid, [exp.account_move_id.id], context=context)
                
                inv_ids = []
                # Elimina los movimientos de las facturas
                for inv in exp.invoice_ids:
                    if inv.move_id:
                        move_id = inv.move_id.id
                        print "************ cancela factura *************** "
                        
                        # Cambia la factura a estado borrador y elimina los movimientos
                        inv_obj.write(cr, uid, [inv.id], {'state':'cancel', 'move_id':False})
                        
                        # Elimina la poliza de la factura
                        move_obj.button_cancel(cr, uid, [move_id], context=context)
                        move_obj.unlink(cr, uid, [move_id], context=context)
                        
                        # Cancela la factura
                        wf_service.trg_delete(uid, 'account.invoice', inv.id, cr)
                        wf_service.trg_create(uid, 'account.invoice', inv.id, cr)
                        
                    inv_ids.append(inv.id)
        print "*************** cancela gasto ************ ", ids
        # Pasa el gasto a cancelado
        self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
        print "************* cancelado *********** "
        return True
    
    def _reconciled(self, cr, uid, ids, name, args, context=None):
        """
            Valida si ya esta pagado el gasto
        """
        res = {}
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = self.test_paid(cr, uid, [inv.id])
            if not res[inv.id] and inv.state == 'paid':
                wf_service.trg_validate(uid, 'hr.expense.expense', inv.id, 'open_test', cr)
        return res
    
    def draft_invoice(self, cr, uid, ids, context=None):
        """
            Pasa las facturas a borrador
        """
        if context is None:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        
        for exp in self.browse(cr, uid, ids, context=context):
            inv_ids = []
            # Valida que haya facturas sobre el gasto
            if exp.invoice_ids:
                # Recorre las facturas de gasto y genera una lista con los ids
                for inv in exp.invoice_ids:
                    inv_ids.append(inv.id)
            # Pasa las facturas de gasto a borrador
            inv_obj.write(cr, uid, inv_ids, {'state': 'draft'})
        return True
    
    def confirm_paid(self, cr, uid, ids, context=None):
        """
            Confirma que se haya aplicado el pago sobre el gasto
        """
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state':'paid'}, context=context)
        return True
    
    def move_line_id_payment_get(self, cr, uid, ids, *args):
        """
            Obtiene el total de los pagos
        """
        if not ids: return []
        result = self.move_line_id_payment_gets(cr, uid, ids, *args)
        return result.get(ids[0], [])
    
    def move_line_id_payment_gets(self, cr, uid, ids, *args):
        res = {}
        if not ids: return res
        cr.execute('SELECT e.id, l.id '\
                   'FROM account_move_line l '\
                   'LEFT JOIN hr_expense_expense e ON (e.account_move_id=l.move_id) '\
                   'WHERE e.id IN %s '\
                   'AND l.account_id=e.account_id',
                   (tuple(ids),))
        for r in cr.fetchall():
            res.setdefault(r[0], [])
            res[r[0]].append( r[1] )
        return res
    
    def test_paid(self, cr, uid, ids, *args):
        res = self.move_line_id_payment_get(cr, uid, ids)
        if not res:
            return False
        ok = True
        for id in res:
            cr.execute('select reconcile_id from account_move_line where id=%s', (id,))
            ok = ok and  bool(cr.fetchone()[0])
        return ok
    
    def _get_expense_from_line(self, cr, uid, ids, context=None):
        """
            Busca las lineas conciliadas y las compara con los movimientos del gasto
        """
        move = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        expense_ids = []
        if move:
            expense_ids = self.pool.get('hr.expense.expense').search(cr, uid, [('account_move_id','in',move.keys())], context=context)
        return expense_ids
    
    def _get_expense_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True
        expense_ids = []
        if move:
            expense_ids = self.pool.get('hr.expense.expense').search(cr, uid, [('account_move_id','in',move.keys())], context=context)
        return expense_ids
    
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene el valor residual del gasto
        """
        if context is None:
            context = {}
        ctx = context.copy()
        result = {}
        currency_obj = self.pool.get('res.currency')
        for exp in self.browse(cr, uid, ids, context=context):
            nb_exp_in_partial_rec = max_exp_id = 0
            result[exp.id] = 0.0
            if exp.account_move_id:
                for aml in exp.account_move_id.line_id:
                    
                    if aml.account_id.type in ('receivable','payable'):
                        #print "************* account_id **************** ",aml.account_id.name, "  - ", aml.account_id
                        if aml.currency_id and aml.currency_id.id == exp.currency_id.id:
                            #print "***************** amount_residual **************** ", aml.amount_residual_currency
                            result[exp.id] += aml.amount_residual_currency
                        else:
                            ctx['date'] = aml.date
                            new_value = currency_obj.compute(cr, uid, aml.company_id.currency_id.id, exp.currency_id.id, aml.amount_residual, context=ctx)
                            result[exp.id] += new_value
                            #print "***************** amount moneda diferente **************** ", new_value
                        #print "************ result ***************** ", result[exp.id]
                        #if aml.reconcile_partial_id.line_partial_ids:
                        #    for line in aml.reconcile_partial_id.line_partial_ids:
                        #        #print "************** line partial DATA **************** ", line._name, " -  ", line.id 
                        #        #print "************** line partial name **************** ", line.reconcile_partial_id.name
                        #        #print "************** line partial **************** ", nb_exp_in_partial_rec
                        #        nb_exp_in_partial_rec += 1
                        #        #store the max expense id as for this expense we will make a balance instead of a simple division
                        #        max_exp_id = max(max_exp_id, exp.id)
                        #        #print "************ exp.id ********** ", exp.id
            #print "******************* result ************* ", result
            #print "*************** exp_partial ************ ", nb_exp_in_partial_rec
            #print "*************** max exp_id ************ ", max_exp_id
            #if nb_exp_in_partial_rec:
            #    new_value = currency_obj.round(cr, uid, exp.currency_id, result[exp.id] / nb_exp_in_partial_rec)
            #    if exp.id == max_exp_id:
            #        #print "************ result resta ************** ", result[exp.id], ' - ((', nb_exp_in_partial_rec, ' - 1) * ', new_value
            #        #balance to avoid rounding errors
            #        result[exp.id] = result[exp.id] - ((nb_exp_in_partial_rec - 1) * new_value)
            #    else:
            #        #print "************* result new value ************* ", new_value
            #        result[exp.id] = new_value
            
            #prevent the residual amount on the expense to be less than 0
            result[exp.id] = max(result[exp.id], 0.0)            
        return result
    
    def _compute_lines(self, cr, uid, ids, name, args, context=None):
        """
            Obtiene los apuntes relacionados con los pagos
        """
        result = {}
        for expense in self.browse(cr, uid, ids, context=context):
            src = []
            lines = []
            if expense.account_move_id:
                for m in expense.account_move_id.line_id:
                    temp_lines = []
                    # Valida que sea la cuentra principal sobre el gasto
                    if m.account_id.id == expense.account_id.id:
                        if m.reconcile_id:
                            temp_lines = map(lambda x: x.id, m.reconcile_id.line_id)
                            
                        elif m.reconcile_partial_id:
                            temp_lines = map(lambda x: x.id, m.reconcile_partial_id.line_partial_ids)
                        lines += [x for x in temp_lines if x not in lines]
                        src.append(m.id)

            lines = filter(lambda x: x not in src, lines)
            result[expense.id] = lines
        return result
    
    _columns = {
        'name': fields.char('Numero', size=64),
        'journal_id': fields.many2one('account.journal', 'Journal', help = "The journal used when the expense is done."),
        'state': fields.selection([
                ('draft', 'Nuevo'),
                ('cancelled', 'Cancelado'),
                ('confirm', 'Esperando aprobacion'),
                ('accepted', 'Aprobado'),
                ('done', 'Abierto'),
                ('paid', 'Pagado'),
            ], 'Estado', readonly=True, track_visibility='onchange'),
        'period_id': fields.many2one('account.period', 'Forzar Periodo', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]}),
        'account_id': fields.many2one('account.account', 'Cuenta', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'invoice_ids': fields.one2many('account.invoice', 'expense_id', 'Gasto Facturado'),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always', store=True, multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Impuestos', store=True, multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total', store=True, multi='all'),
        
        # A partir de aqui es para gestion de pagos sobre el gasto
        'reconciled': fields.function(_reconciled, string='Paid/Reconciled', type='boolean',
            store={
                'hr.expense.expense': (lambda self, cr, uid, ids, c={}: ids, None, 50), # Check if we can remove ?
                'account.move.line': (_get_expense_from_line, None, 50),
                'account.move.reconcile': (_get_expense_from_reconcile, None, 50),
            }, help="It indicates that the invoice has been paid and the journal entry of the invoice has been reconciled with one or several journal entries of payment."),
        'residual': fields.function(_amount_residual, digits_compute=dp.get_precision('Account'), string='Saldo pendiente',
            #store={
            #    'hr.expense.expense': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','move_id'], 50),
            #    'account.invoice.tax': (_get_invoice_tax, None, 50),
            #    'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
            #    'account.move.line': (_get_invoice_from_line, None, 50),
            #    'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
            #},
            help="Monto pendiente por pagar sobre el gasto."),
        'payment_ids': fields.function(_compute_lines, relation='account.move.line', type="many2many", string='Payments'),
    }
    
    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        """
            Obtiene la informacion relacionada al empleado
        """
        emp_obj = self.pool.get('hr.employee')
        account_obj = self.pool.get('account.account')
        department_id = False
        company_id = False
        account_id = False
        # Si hay un empleado seleccionado obtiene la informacion relacionada
        if employee_id:
            employee = emp_obj.browse(cr, uid, employee_id, context=context)
            department_id = employee.department_id.id
            company_id = employee.company_id.id
            if employee.address_home_id:
                account_id = employee.address_home_id.property_account_payable.id
        
        # Si no hay una cuenta seleccionada pone la cuenta por default
        if not account_id:
            account_ids = account_obj.search(cr, uid, [('code','=','2141001000')], context=context)
            if account_ids:
                account_id = account_ids[0]
        return {'value': {'department_id': department_id, 'company_id': company_id, 'account_id': account_id}}
    
    def _default_get_journal(self, cr, uid, context=None):
        """
            Obtiene el diario del gasto
        """
        res = False
        # Valida que el id no este registrado
        try:
            register_model, res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_expense_custom', 'account_expense_account_journal_01')
        except:
            pass
        return res
    
    _defaults = {
        'journal_id': _default_get_journal
    }
    
    def expense_pay_employee(self, cr, uid, ids, context=None):
        """
            Pago sobre el gasto en efectivo
        """
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')

        exp = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Registrar Pago"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': exp.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(exp.employee_id.address_home_id).id,
                'default_amount': exp.residual,
                'default_reference': exp.name,
                'close_after_process': True,
                'reference': 'hr.expense.expense,%s'%(exp.id,),
                'default_type': 'payment',
                'type': 'payment'
            }
        }
    
hr_expense_expense()

class hr_expense_line(osv.osv):
    _inherit = "hr.expense.line"
    
    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """
            Actualiza la informacion del producto seleccionado sobre la linea del gasto
        """
        res = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['name'] = product.name
            amount_unit = product.price_get('standard_price')[product.id]
            res['unit_amount'] = amount_unit
            res['uom_id'] = product.uom_id.id
            # Obtiene la cuenta del producto
            if product.property_account_expense:
                res['account_id'] = product.property_account_expense.id or False
            else:
                res['account_id'] = product.categ_id.property_account_expense_categ.id or False
        return {'value': res}
    
    _columns = {
        'account_id': fields.many2one('account.account', 'Cuenta', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="Cuenta relacionada al producto seleccionado."),
    }
    
hr_expense_line()

#class account_move_line(osv.osv):
#    _inherit = "account.move.line"
#
#    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
#        res = super(account_move_line, self).reconcile(cr, uid, ids, type=type, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id, context=context)
#        #when making a full reconciliation of account move lines 'ids', we may need to recompute the state of some hr.expense
#        account_move_ids = [aml.move_id.id for aml in self.browse(cr, uid, ids, context=context)]
#        expense_obj = self.pool.get('hr.expense.expense')
#        currency_obj = self.pool.get('res.currency')
#        if account_move_ids:
#            expense_ids = expense_obj.search(cr, uid, [('account_move_id', 'in', account_move_ids)], context=context)
#            for expense in expense_obj.browse(cr, uid, expense_ids, context=context):
#                if expense.state == 'done':
#                    #making the postulate it has to be set paid, then trying to invalidate it
#                    new_status_is_paid = True
#                    for aml in expense.account_move_id.line_id:
#                        if aml.account_id.type == 'payable' and not currency_obj.is_zero(cr, uid, expense.company_id.currency_id, aml.amount_residual):
#                            new_status_is_paid = False
#                    if new_status_is_paid:
#                        expense_obj.write(cr, uid, [expense.id], {'state': 'paid'}, context=context)
#        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
