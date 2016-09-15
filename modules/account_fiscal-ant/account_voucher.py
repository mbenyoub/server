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
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
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
from openerp.tools import float_compare
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Account generation from template wizards
# ---------------------------------------------------------

class account_voucher(osv.Model):
    _inherit='account.voucher'
    _description = 'Accounting Voucher'
    
    def _check_statement(self, cr, uid, ids, field, arg, context=None):
        """
            Indica True si ya fue conciliado con los movimientos del banco
        """
        result = {}
        # Recorre los registros
        for voucher in self.browse(cr, uid, ids, context=context):
            # Obtiene la base del impuesto
            result[voucher.id] = True if voucher.statement_id else False
        return result
    
    def get_account_balance(self, cr, uid, journal_id, type='receipt', context=None):
        """
            Obtiene el saldo de la cuenta en base al diario y al tipo de registro (cobro y pago)
        """
        # Inicializa variables
        journal_obj = self.pool.get('account.journal')
        res = 0.0
        
        # Obtengo el diario seleccionado
        journal = journal_obj.browse(cr, uid, journal_id, context=context)
        # Si es un cobro obtengo la cuenta del diario sobre el debe
        if type == 'receipt' and journal.default_debit_account_id:
            res = journal.default_debit_account_id.balance
        # Si es un pago obtengo la cuenta del diario sobre el haber
        elif type == 'payment' and journal.default_credit_account_id:
            res = journal.default_credit_account_id.balance
        return res
    
    def _get_account_balance(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el saldo de la cuenta en base al diario para cada registro del voucher
        """
        # Inicializa variables
        res = {}
        
        # Obtengo el diario seleccionado
        for voucher in self.browse(cr, uid, ids, context=context):
            res[voucher.id] = self.get_account_balance(cr, uid, voucher.journal_id.id, voucher.type, context=None)
        return res
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        """
            agrega la columna account_balance por medio de herencia a la funcion onchange_journal_id del
            padre account
        """
        # Inicializa variables
        if context is None:
            context = {}
        
        #ejecuta funcion de onchange original
        res = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if journal_id:
            # Obtiene el saldo del banco sobre el diario seleccionado 
            res['value']['account_balance'] = self.get_account_balance(cr, uid, journal_id, context.get('type','receipt'), context=context)
        return res
    
    _columns = {
        'statement_id': fields.many2one('account.bank.statement', 'Statement', select=True, ondelete='restrict', help="conciliacion sobre el pago"),
        'invoice_id': fields.many2one('account.invoice', 'Factura', readonly=False, select=True, ondelete='restrict', help="Referencia sobre el pago de la factura"),
        'concilie_bank': fields.function(_check_statement, type="boolean", store=True, string="Conciliado"),
        'tax_ids': fields.one2many('account.voucher.apply.tax', 'voucher_id', 'Impuestos aplicados'),
        'account_balance': fields.function(_get_account_balance, string='Balance cuenta', type='float', store=False),
    }
    
    _defaults = {
        'concilie_bank': False
    }
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de los impuestos sobre los pagos del voucher,
            Si hay deducciones elimina el valor aplicado
        """
        move_tax_obj = self.pool.get('account.move.tax')
        vapply_tax_obj = self.pool.get('account.voucher.apply.tax')
        deduction_obj = self.pool.get('account.fiscal.deduction')
        #print "*************** cancelar voucher ************** "
        
        # Recorre los registros
        for voucher in self.browse(cr, uid, ids, context=context):
            tax_ids = []
            #print "**************** voucher ****************** ", voucher.tax_ids
            if voucher.tax_ids:
                for tax in voucher.tax_ids:
                    # Actualiza la tabla de impuesto con el total pagado y su base pagada
                    move_tax_obj.write(cr, uid, [tax.move_tax_id.id], {'amount_tax': tax.move_tax_id.amount_tax - tax.amount_apply, 'amount': tax.move_tax_id.amount - tax.base_apply})
                    tax_ids.append(tax.move_tax_id.id)
                # Elimina los registros
                vapply_tax_obj.unlink(cr, uid, tax_ids, context=context)
        
        # Busca en los registros de deducciones si haya algo relacionado al pago
        deduction_ids = deduction_obj.search(cr, uid, [('voucher_id','in',ids)],context=context)
        if deduction_ids:
            # Elimina las deducciones relacionadas a los pagos
            deduction_obj.unlink(cr, uid, deduction_ids, context=context)
        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)
    
    def create_move_lines_payment(self, cr, uid, move, move_line, type='receipt', context=None):
        """
            Aplica el monto a pagar
        """
        if context is None:
            context = {}
        # Inicializa variables
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        move_tax_obj = self.pool.get('account.move.tax')
        inv_obj = self.pool.get('account.invoice')
        vapply_tax_obj = self.pool.get('account.voucher.apply.tax')
        rec_ids = []
        rec_tax_ids = []
        apply_ids = []
        
        payment_total = 0.0
        amount_apply = 0.0
        deduction = 0.0
        invoice = False
        model = 'account.invoice'
        #print "*************** Movimiento ********** ", move
        #print "*************** Id referencia factura ********** ", move.reference
        #print "*************** Id referencia factura ********** ", move.reference.id
        #print "*************** movimiento ********** ", move.move_id
        
        # Valida que contenga la factura sino va y la busca
        if not move.reference:
            print "************** busca la factura ******************* "
            if move.move_id:
                inv_ids = inv_obj.search(cr, uid, [('move_id','=',move.move_id.id)], context=context)
                #print "*************** movimiento_encontrado *** mov ", move.move_id.id,  " ************ ", inv_ids
                if inv_ids:
                    invoice = inv_obj.browse(cr, uid, inv_ids[0], context=context)
        else:
            print "**************** asigna referencia *************** ", move.reference
            invoice = move.reference
        
        if invoice:
            print "*************** factura ********* ", invoice
            model = invoice._name
            print "***************** asigna referencia a movimiento ************* ", invoice
            # Agrega al movimiento del pago la referencia de la factura
            move_line['reference'] = '%s,%s'%(model,invoice.id)
        
        # Obtiene el monto a pagar
        amount = move_line[move_line['type']]
        print "******************* monto a pagar ****************** ", amount
        
        # Aplica el pago a bancos
        voucher_line = move_line_obj.create(cr, uid, move_line)
        rec_ids.append(voucher_line)
        
        print "****************** move.tax_ids *************** ", move.tax_ids
        
        # Si tiene impuestos los recorre y reparte el monto
        if move.tax_ids:
            # Recorre las lineas de impuesto del movimiento
            for tax in move.tax_ids:
                # Valida si tiene la cuenta configurada en los impuestos
                if not tax.account_id:
                    continue
                
                # Obtiene el total a pagar y el total por pagar del impuesto
                payment = 0
                if tax.invoice_total > 0:
                    payment = (amount/tax.invoice_total) * tax.base_tax
                to_payment = tax.base_tax - tax.amount_tax
                # Obtiene el total a pagar y el total por pagar sobre la base del impuesto
                base_payment = 0
                if tax.invoice_total > 0:
                    base_payment = (amount/tax.invoice_total) * tax.base
                base_to_payment = tax.base - tax.amount
                print "********************* payment tax **************** (", amount, "/", tax.invoice_total, ") * ", tax.base_tax, " = ", to_payment
                print "********************* payment base *************** (", amount, "/", tax.invoice_total, ") * ", tax.base, " = ", base_to_payment
                
                # Si el pago es cero pasa con el siguiente impuesto
                if to_payment == 0.0 and base_to_payment == 0.0:
                    continue
                
                # Agrega el id del contacto a los movimientos
                if invoice:
                    move_line['partner_id'] = invoice.partner_id.id
                else:
                    voucher = self.read(cr, uid, context.get('voucher_id', False), ['partner_id'], context=context)
                    #print "******************* contacto voucher ************** ", voucher
                    move_line['partner_id'] = voucher['partner_id']
                
                # Genera una copia del diccionario y la adapta para hacer apuntes sobre los impuestos
                move_new = move_line.copy()
                move_new['account_id'] = tax.account_id.id
                
                move_new['tax_code_id'] = tax.tax_code_id.id
                move_new['name'] = tax.name
                print "*************** payment ************** ", payment
                print "*************** porcentaje ************** ", tax.percent
                print "*************** to payment ************** ", to_payment
                # Valida si la base es negativo
                if tax.base_tax >= 0: 
                    # Valida que el pago no sobrepase los impuestos a pagar
                    if to_payment >= payment:
                        move_new[move_line['type']] = payment
                        move_new['tax_amount'] = payment
                        amount_apply = payment + tax.amount_tax
                    else:
                        amount_apply = to_payment + tax.amount_tax
                        move_new[move_line['type']] = to_payment
                        move_new['tax_amount'] = to_payment
                else:
                    # Valida que el pago no sobrepase los impuestos a pagar
                    if to_payment <= payment:
                        move_new[move_line['type']] = payment
                        move_new['tax_amount'] = payment
                        amount_apply = payment + tax.amount_tax
                    else:
                        amount_apply = to_payment + tax.amount_tax
                        move_new[move_line['type']] = to_payment
                        move_new['tax_amount'] = to_payment
                    
                # Valida que el pago no sobrepase los impuestos a pagar
                if base_to_payment >= base_payment:
                    move_new['base'] = base_payment
                    base_apply = base_payment + tax.amount
                else:
                    base_apply = base_to_payment + tax.amount
                    move_new['base'] = base_to_payment
                
                print "**************** base ******************* ", move_new['base']
                print "**************** tax amount ************* ", move_new['tax_amount']
                
                # Valida importes negativos sobre impuestos 
                if move_new['tax_amount'] < 0:
                    if move_new['type'] == 'credit':
                        move_new['debit'] = move_new['credit'] * -1
                        move_new['credit'] = 0.0
                        move_new['type'] = 'debit'
                    else:
                        move_new['credit'] = move_new['debit'] * -1
                        move_new['debit'] = 0.0
                        move_new['type'] = 'credit'
                
                # Actualiza la tabla de impuesto con el total pagado y su base pagada
                move_tax_obj.write(cr, uid, [tax.id], {'amount_tax': amount_apply, 'amount': base_apply})
                
                print "***************** aplica deducciones ****************** ", base_apply, " - ", move_new['base']
                
                # Actualiza el monto de la deducion sobre los impuestos
                deduction += move_new['base']
                
                # Genera la contraparte del movimiento sobre los impuestos por trasladar
                move_contra = move_new.copy()
                if model == 'account.invoice':
                    if invoice.type in ('out_invoice','in_invoice'):
                        move_contra['account_id'] = tax.tax_id.account_collected_id.id
                    else:
                        move_contra['account_id'] = tax.tax_id.account_paid_id.id
                else:
                    move_contra['account_id'] = tax.tax_id.account_collected_id.id
                if move_contra['type'] == 'debit':
                    move_contra['credit'] = move_contra['debit']
                    move_contra['debit'] = 0.0
                else:
                    move_contra['debit'] = move_contra['credit']
                    move_contra['credit'] = 0.0
                # Quita la aplicacion a los codigos de impuestos de la contraparte
                move_contra['tax_code_id'] = False
                move_contra['tax_amount'] = 0.0
                print "*************** move_new ****************** ", move_new
                print "*************** move_contra ****************** ", move_contra
                
                # Crea el movimiento por trasladar
                voucher_line = move_line_obj.create(cr, uid, move_contra)
                rec_tax_ids.append(voucher_line)
                print "************ id movimiento por trasladar *************** ", voucher_line
                # Crea el movimiento de los impuestos trasladados
                voucher_line = move_line_obj.create(cr, uid, move_new)
                rec_tax_ids.append(voucher_line)
                print "************* id movimiento de impuestos trasladados *** ", voucher_line
                
                # Crea un registro con el total pagado del impuesto
                val_apply_tax = {
                    'voucher_id': context.get('voucher_id',False),
                    'amount_apply': move_new['tax_amount'],
                    'base_apply': move_new['base'],
                    'move_line_id': tax.move_line_id.id if tax.move_line_id else False,
                    'move_tax_id': tax.id
                }
                print "*********** registro creado ************* ", val_apply_tax
                apply_id = vapply_tax_obj.create(cr, uid, val_apply_tax)
                print "************ registro voucher apply tax *********** ", apply_id
        
        print "************** invoice ************** ", invoice
        if invoice and model == 'account.invoice':
            # Valida que sea una factura de proveedor
            if invoice.type == 'in_invoice':
                
                # Valida si aplican deducciones sobre la factura o si el tipo de empresa es de titulo 4 (En titulo 4 aplica siempre deduccion)
                if invoice.apply_deduction and invoice.title == 'title_2':
                    # Crea la deduccion sobre la factura
                    #print "*************** crea deduccion titulo 2*************** "
                    self.pool.get('account.fiscal.deduction').create(cr, uid, {
                        'name': 'Deduccion de factura %s'%(invoice.number),
                        'amount': deduction,
                        'category_id': invoice.partner_id.regimen_fiscal_id.category_id.id,
                        'period_id': context.get('period_id',move.period_id.id),
                        'invoice_id': invoice.id,
                        'voucher_id': context.get('voucher_id',False),
                        'date': context.get('date',time.strftime('%Y-%m-%d')),
                        'type': 'purchase'
                        }, context=context)
                elif invoice.title == 'title_4':
                    # Crea la deduccion sobre la factura
                    #print "*************** crea deduccion titulo 4 *************** "
                    self.pool.get('account.fiscal.deduction').create(cr, uid, {
                        'name': 'Deduccion de factura %s'%(invoice.number),
                        'amount': deduction,
                        'category_id': invoice.company_id.partner_id.regimen_fiscal_id.category_id.id,
                        'period_id': context.get('period_id',move.period_id.id),
                        'invoice_id': invoice.id,
                        'voucher_id': context.get('voucher_id',False),
                        'date': context.get('date',time.strftime('%Y-%m-%d')),
                        'type': 'purchase'
                        }, context=context)
            # Valida si es una factura de cliente
            if invoice.type == 'out_invoice' and invoice.invoice_asset == False:
                
                if invoice.apply_deduction_sale:
                    # Crea la deduccion sobre la factura para ventas
                    self.pool.get('account.fiscal.deduction').create(cr, uid, {
                        'name': 'Ingreso Acumulable de factura %s'%(invoice.number),
                        'amount': deduction,
                        'category_id': invoice.company_id.partner_id.regimen_fiscal_id.category_id_sale.id,
                        'period_id': context.get('period_id',move.period_id.id),
                        'invoice_id': invoice.id,
                        'voucher_id': context.get('voucher_id',False),
                        'date': context.get('date',time.strftime('%Y-%m-%d')),
                        'type': 'sale'
                        }, context=context)
        # Agrega el id del movimiento de cuentas por cobrar al monto
        rec_ids.append(move.id)
        return rec_ids, rec_tax_ids
    
    #def create_move_lines_payment_res(self, cr, uid, move, move_line):
    #    """
    #        Aplica el monto a pagar
    #    """
    #    move_line_obj = self.pool.get('account.move.line')
    #    move_tax_obj = self.pool.get('account.move.tax')
    #    rec_ids = []
    #    payment_total = 0.0
    #    # Obtiene el monto a pagar
    #    amount = move_line[move_line['type']]
    #    #print "******************* amount ****************** ", amount
    #    # Aplica el pago a bancos
    #    voucher_line = move_line_obj.create(cr, uid, move_line)
    #    rec_ids.append(voucher_line)
    #    # Si tiene impuestos los recorre y reparte el monto
    #    if move.percent != 1:
    #        move_lines = []
    #        amount_pen = 0.0
    #        amount_apply = 0.0
    #        # Recorre las lineas de impuesto del movimiento
    #        for tax in move.tax_ids:
    #            payment = amount * tax.percent
    #            to_payment = tax.base - tax.amount
    #            # Si el pago es cero deja el monto como pendiente
    #            if to_payment == 0.0:
    #                amount_pen += payment
    #            else:
    #                # Genera una copia del diccionario
    #                move_new = move_line.copy()
    #                move_new['line_tax_id'] = tax.id # Extra
    #                move_new['account_tax_contra'] = tax.tax_id.account_collected_id.id # Extra Contrapartida
    #                move_new['to_payment'] = to_payment # Extra
    #                #move_new['account_tax_id'] = tax.tax_id.id # Esto genera un cargo sobre el iva
    #                move_new['account_id'] = tax.account_id.id
    #                move_new['tax_code_id'] = tax.tax_id.tax_code_id.id
    #                move_new['name'] = tax.name
    #                #print "*************** move_new ****************** ", move_new
    #                #print "*************** payment ************** ", payment
    #                #print "*************** porcentaje ************** ", tax.percent
    #                #print "*************** to payment ************** ", to_payment
    #                # Valida que el pago no sobrepase los impuestos a pagar
    #                if to_payment >= payment:
    #                    move_new[move_line['type']] = payment
    #                    move_new['tax_amount'] = payment
    #                else:
    #                    amount_pen += (payment - to_payment)
    #                    move_new[move_line['type']] = to_payment
    #                    move_new['tax_amount'] = to_payment
    #                # Agrega el movimiento del impuesto a la lista
    #                move_lines.append(move_new)
    #        # Recorre las lineas de pedido para generar los registros de impuestos a pagar
    #        for line in move_lines:
    #            #print "**************** monto pendiente ***************** ", amount_pen
    #            # Valida si hay monto pendiente
    #            if amount_pen > 0.0 and line[line['type']] < line['to_payment']:
    #                payment = line[line['type']] + amount_pen
    #                # Valida que el pago no sobrepase los impuestos a pagar
    #                if line['to_payment'] >= payment:
    #                    line[line['type']] = payment
    #                    line['tax_amount'] = payment
    #                else:
    #                    amount_pen = payment - line['to_payment']
    #                    line[line['type']] = line['to_payment']
    #                    line['tax_amount'] = line['to_payment']
    #            #print "********************** movimiento creado tax ********************* ", line
    #            # Genera la contraparte del movimiento sobre los impuestos por trasladar
    #            move_contra = line.copy()
    #            move_contra['account_id'] = move_contra['account_tax_contra']
    #            if move_contra['type'] == 'debit':
    #                move_contra['credit'] = move_contra['debit']
    #                move_contra['debit'] = 0.0
    #            else:
    #                move_contra['debit'] = move_contra['credit']
    #                move_contra['credit'] = 0.0
    #            # Quita la aplicacion a los codigos de impuestos de la contraparte
    #            move_contra['tax_code_id'] = False
    #            move_contra['tax_amount'] = 0.0
    #            # Crea el movimiento
    #            voucher_line = move_line_obj.create(cr, uid, move_contra)
    #            rec_ids.append(voucher_line)
    #            # Crea el movimiento de los impuestos trasladados
    #            voucher_line = move_line_obj.create(cr, uid, line)
    #            amount_apply += line[line['type']]
    #            #print "********************** amount_apply tax ********************* ", amount_apply
    #            rec_ids.append(voucher_line)
    #            
    #        ## Agrega el movimiento con el total a pagar a bancos
    #        #payment = (amount * move.percent) + amount_pen
    #        #
    #        #print "**************** payment ***************** (", amount," * ",move.percent,") + ",amount_pen, " = ", payment
    #        #amount_apply += payment
    #        #print "********************* amount_apply **************** ", amount_apply
    #        #dif = amount - amount_apply
    #        #print "******************** dif total *************** ", amount, " - ", amount_apply, " = ", dif
    #        #payment += dif
    #        #move_line[move_line['type']] = payment
    #        #print "**************** movimiento creado ban ************* ", move_line
    #        ## Crea el movimiento
    #        #voucher_line = move_line_obj.create(cr, uid, move_line)
    #        #rec_ids.append(voucher_line)
    #        
    #    # Agrega el id del movimiento de cuentas por cobrar al monto
    #    rec_ids.append(move.id)
    #    return rec_ids
    
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []
        #print "************** tot_line **************** ", tot_line
        
        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        #print "************ context lineas de mov ************ ", ctx
        
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            #print "************** linea de mov **************** ", line.id, " ** ", line.move_line_id, " ** ", line.name, " ** ", line.amount
            
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = voucher.type in ('payment', 'purchase') and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['type'] = 'debit'
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['type'] = 'credit'
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })
            #print "************** linea de movimiento ************* ", move_line
            
            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
            
            #print "*************************** id linea ********************** ", line.move_line_id
            
            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    sign = voucher.type in ('payment', 'purchase') and -1 or 1
                    foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency
            
            move_line['amount_currency'] = amount_currency
            # Obtiene el iva total del movimiento para impuestos
            ctx_move = ctx.copy()
            ctx_move['voucher_id'] = voucher_id
            
            #voucher_line = move_line_obj.create(cr, uid, move_line)
            #print "*************************** voucher_line **************** ", voucher_line
            rec_ids, rec_tax_ids = self.create_move_lines_payment(cr, uid, line.move_line_id, move_line, type=line.voucher_id.type, context=ctx_move)
            
            #print "**************************** rec_ids  ***************** ", rec_ids
            #print "**************************** rec_tax_ids impuestos ***************** ", rec_tax_ids
            
            #print "************ crea la linea de movimiento ****************** ", move_line
            #voucher_line = move_line_obj.create(cr, uid, move_line)
            #rec_ids = [voucher_line, line.move_line_id.id]
            #print "***************** rec ids ************* ", rec_ids
            #print "************* valida si el monto es cero *********** ", currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference)
            
            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                
                #print "******************** exchange lines **************** ", exch_lines
                
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)
            
            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                #print "************** diferencia moneda movimiento ************* ", move_line_foreign_currency
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                #print "*************** nuevo id de dif mov ************* ", new_id
                rec_ids.append(new_id)
            
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
                if len(rec_tax_ids) > 0:
                    rec_lst_ids.append(rec_tax_ids)
        return (tot_line, rec_lst_ids)

    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account_id = False
            write_off_name = ''
            if voucher.payment_option == 'with_writeoff':
                account_id = voucher.writeoff_acc_id.id
                write_off_name = voucher.comment
            elif voucher.type in ('sale', 'receipt'):
                # Revisar si tiene configurada la cuenta de anticipos para cliente
                if voucher.partner_id.property_account_advance_customer:
                    account_id = voucher.partner_id.property_account_advance_customer.id
                else:
                    # Si no hay cuenta configurada toma la cuenta de los cobros
                    account_id = voucher.partner_id.property_account_receivable.id
            else:
                # Revisar si tiene configurada la cuenta de anticipos para proveedor
                if voucher.partner_id.property_account_advance_supplier:
                    account_id = voucher.partner_id.property_account_advance_supplier.id
                else:
                    # Si no esta configurada toma la cuenta de pagos
                    account_id = voucher.partner_id.property_account_payable.id
            sign = voucher.type == 'payment' and -1 or 1
            move_line = {
                'name': write_off_name or name,
                'account_id': account_id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'date': voucher.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or False,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
            }

        return move_line

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
            Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        #print "****************** crea linea de movimiento para pago (func reemplazo) ************************ ", ids
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        link_obj = self.pool.get('links.get.request')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.voucher', 'Voucher', context=None)
        
        for voucher in self.browse(cr, uid, ids, context=context):
            #print "********************** Voucher predefinido ***********************"
            
            if voucher.move_id:
                #print "************** Existe movimiento ********************* ", voucher.move_id
                if voucher.type == 'transfer':
                    move_pool.write(cr, uid, [voucher.move_id.id], {'journal_id_transfer': voucher.journal_id_transfer.id}, context=context)
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_new = self.account_move_get(cr, uid, voucher.id, context=context)
            move_new['reference'] = 'account.voucher,' + str(voucher.id)
            # Actualiza el tipo de movimiento sobre la poliza
            move_new['type'] = voucher.type
            
            #print "*********************** move new *********************** ", move_new
            move_id = move_pool.create(cr, uid, move_new, context=context)
            
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            #print "********************** nombre del movimiento creado **************** ", name
            
            vals_line = self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context)
            
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, vals_line, context)
            #print "************** first move line ****************** ", move_line_id
            
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            #print "************** linea total ******** ", move_line_brw.debit, " - ", move_line_brw.credit, " = ", line_total
            
            # Elimina la linea si va en cero
            if line_total == 0:
                move_line_pool.unlink(cr, uid, [move_line_id], context=context)
            
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            
            #print "********************* linea total con tipo de cambio de moneda *************** ", line_total
            
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
            
            #print "**************** line total moves ******** ", line_total
            #print "**************** rec_list_ids ******** ", rec_list_ids
            
            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            
            #print "*************** move line writeoff ************** ",ml_writeoff
            
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    #raise osv.except_osv(_('xxx'),_("Detenido test."))
                    #print "*************** reconciliacion parcial ***************** ", rec_ids
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
            
            # Actualiza el tipo de movimiento sobre la poliza
            #move_pool.write(cr, uid, [voucher.move_id.id], {'type':voucher.type}, context=context)
            
            #print "******************* voucher move_id ********** ", move_id
            #print "******************* voucher type ********** ", voucher.type
            #print "******************* voucher journal transfer ********** ", voucher.journal_id_transfer
            
            # Valida que reciba un movimiento
            #if not move_id:
            #    continue
            # Valida que el tipo de voucher sea una transferencia
            if voucher.type != 'transfer':
                continue
            
            # Actualiza el diario de transferencia sobre el movimiento creado
            move_pool.write(cr, uid, [move_id], {'journal_id_transfer': voucher.journal_id_transfer.id}, context=context)
            line_ids = move_line_pool.search(cr, uid, [('move_id','=',move_id)])
            move_line_pool.write(cr, uid, line_ids, {}, context=context)
        
        return True
        
account_voucher()

class account_voucher_apply_tax(osv.Model):
    _name='account.voucher.apply.tax'
    _description = 'Accounting Voucher - Impuestos aplicados'
    
    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Pago', select=True, ondelete='cascade'),
        'move_line_id': fields.many2one('account.move.line', 'Apunte', readonly=False, select=True, ondelete='set null'),
        'amount_apply': fields.float('Monto aplicado', digits_compute=dp.get_precision('Account')),
        'base_apply': fields.float('Base aplicada', digits_compute=dp.get_precision('Account')),
        'move_tax_id': fields.many2one('account.move.tax', 'Movimiento impuesto', select=True, ondelete='cascade'),
    }

account_voucher_apply_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
