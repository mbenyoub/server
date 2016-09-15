# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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

"""
    Herencia sobre modulo de account_voucher, para el registro de los pagos parciales de la factura en los momentos presupuestales
"""

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import datetime

class account_voucher(osv.Model):
    """Inherited account.voucher"""

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        print "*********************** pago de factura desde budget log ************************* "
        print "*********************** Valida el monto de la factura ************************** "
        print "********************** informacion context **************** ", context

        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(cr, uid, context['invoice_id'])

        print "*********** Saldo pendiente factura ****************** ", invoice.residual

        #~ Recorre los voucher a pagar en la factura
        for voucher in self.browse(cr, uid, ids, context=context):
            print "************ voucher ***************** ", voucher.id
            #~ Valida que el monto a pagar no sea mayor al saldo pendiente en la factura
            if voucher.amount > invoice.residual:
                print "************ cantidad invalida ************* Monto ***** ", voucher.amount, "  ** pendiente **  ", invoice.residual
                raise osv.except_osv('Error!','El monto a pagar es mayor al saldo pendiente en la factura (PENDIENTE: ' + str(invoice.residual) + ').')

        return super(account_voucher, self).button_proforma_voucher(cr, uid, ids, context=context)

    def wkf_add_move_paid(self, cr, uid, ids, context=None):
        print "************************ Proceso para afectar pagos parciales en las facturas ************************************************ "

        invoice_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        move_line_obj = self.pool.get('account.move.line')
        voucher_line_obj = self.pool.get('account.voucher.line')
        budget_log_obj = self.pool.get('account.budget.log.moments')
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

        #~ Recorre la informacion del voucher
        for voucher in self.browse(cr, uid, ids, context=context):
            print "*************** voucher ********************* ", voucher.id, " ** name ** ", voucher.name
            print "*************** voucher line ********************* ", voucher.line_ids
            print "*************** voucher line cr ********************* ", voucher.line_cr_ids
            print "*************** voucher line dr ********************* ", voucher.line_dr_ids
            print "*************** proveedor del vouceher *************** ", voucher.partner_id

            #~ Obtiene las facturas que ya se hayan ejercido para el proveedor
            args = [('exercised', '=' , True), ('partner_id', '=', voucher.partner_id.id), ('company_id', '=', voucher.company_id.id), ('paid', '=', False)]

            print "******************* args ************************* ", args

            inv_ids = invoice_obj.search(cr, uid, args, context=context)
            if not inv_ids:
                partner_obj = self.pool.get('res.partner')
                partner = partner_obj.browse(cr, user, voucher.partner_id.id, context=context)
                raise osv.except_osv(_('Error!'), _('No hay facturas por pagar para el proveedor "' + partner.name + '".'))

            print "******************* Facturas del proveedor ************************ ", inv_ids

            #~ Recorre las facturas del proveedor para obtienes los movimientos de los pagos
            for invoice in invoice_obj.browse(cr, uid, inv_ids, context=context):
                print "*********************** factura ********************* ", invoice.name

                #~ Crea un diccionario con la informacion para generar los movimientos
                inf_doc = {
                    'reference' : invoice.internal_number,
                    'document': 'Pago',
                    'state' : 'paid',
                    'date' : date,
                    'total' : 0.0,
                    'partner_id': invoice.partner_id.id,
                }

                print "**** read ***** ", inf_doc

                #~ Obtiene las lineas de pedido de la factura
                src = []
                move_lines = []
                if invoice.move_id:
                    for m in invoice.move_id.line_id:
                        temp_lines = []
                        if m.reconcile_id:
                            temp_lines = map(lambda x: x.id, m.reconcile_id.line_id)
                        elif m.reconcile_partial_id:
                            temp_lines = map(lambda x: x.id, m.reconcile_partial_id.line_partial_ids)
                        move_lines += [x for x in temp_lines if x not in move_lines]
                        src.append(m.id)

                move_lines = filter(lambda x: x not in src, move_lines)

                print "**************** ids de lineas de movimiento en la factura ", invoice.id, " ************* ", move_lines

                #~ Valida que haya movimientos en la factura
                if len(move_lines) == 0:
                    continue

                inv_line_ids = []
                #~ Obtiene los ids de las lineas de la factura
                if not invoice.invoice_line:
                    raise osv.except_osv('Error!','La facltura no tiene lineas de pedido.')
                for line in invoice.invoice_line:
                    inv_line_ids.append(line.id)

                num_lines = 0
                amount_total = 0.0
                inf_line = []
                #~ Recorre las lineas de pedido de la factura y guarda la informacion principal en un arreglo
                for line in inv_line_obj.browse(cr, uid, inv_line_ids, context=context):
                    print "*****  line id ***** ", line.id
                    print "************  line  ***** ", inv_line_obj.read(cr, uid, line.id, context=context)

                    #~ Obtiene los impuestos por producto y calcula el total en base a la cantidad recibida
                    amount_line = inv_line_obj.get_amount_tax(cr, uid, [line.id, ], context)

                    one_line = {
                        'line_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.name,
                        'account_analytic_id' : line.account_analytic_id.id,
                        'product_uom': line.uos_id.id,
                        'price_unit': line.price_unit,
                        'quantity': float(line.quantity),
                        'tax_code_id': line.invoice_line_tax_id[0].id,
                        'amount_original': round(float(amount_line[line.id]['amount_total']), decimal_precision),
                        'amount_total': 0.0,
                        'amount_paid': round(float(line.amount_paid), decimal_precision)
                    }
                    num_lines += 1
                    amount_total += one_line['amount_original']
                    inf_line.append(one_line)
                    print "********* Inf_line ********super******************  ", inf_line

                #~ Recorre las lineas de movimiento que aplican a la factura y se revisa cuales ya fueron aplicados al presupuesto
                for move_line in move_line_obj.browse(cr, uid, move_lines, context=context):
                    print "************** movimiento ", move_line.name, " ********************** ", move_line.invoice_paid
                    print "************** movimiento debe ********************** ", move_line.debit
                    print "************** movimiento haber ********************** ", move_line.credit

                    #~ Valida que el pago no se haya aplicado en el presupuesto
                    if move_line.invoice_paid:
                        print "*************** pago aplicado *******************"
                        continue

                    #~ Valida que el movimiento tenga un monto en el debe
                    if move_line.debit == 0.0:
                        print "***************** no hay monto en el debe *******************"
                        continue

                    mismatch = 0.0
                    amount_paid = 0.0
                    amount_pay = 0.0

                    #~ Recorre las lineas de movimiento para aplicar los pagos
                    for inv_line in inf_line:
                        #~ Calcula el monto a aplicar por linea de factura en el pago
                        porcent = (inv_line['amount_original'] * 100) / amount_total
                        amount_pay = round(float((porcent * move_line.debit) / 100), decimal_precision)
                        print "*********************** porcentaje ********************* ", porcent
                        print "*********************** monto aplicar ************************ ", amount_pay
                        #~ Si el pago es menor al monto original
                        if (inv_line['amount_paid'] + amount_pay) <= inv_line['amount_original']:
                            print "************ pago menor **************** ", inv_line['amount_paid'], " + ", amount_pay, " <= ", inv_line['amount_original']
                            inv_line['amount_paid'] += amount_pay
                            inv_line['amount_total'] += amount_pay
                            amount_paid += amount_pay
                            #~ Si hay monto por ajustar lo agrega en el pago
                            if mismatch > 0.0:
                                #~ Si el ajuste es menor al monto original
                                if (inv_line['amount_paid'] + mismatch) <= inv_line['amount_original']:
                                    print "************ agregar ajuste **************** ", inv_line['amount_paid'], " + ", mismatch, " <= ", inv_line['amount_original']
                                    inv_line['amount_paid'] += mismatch
                                    inv_line['amount_total'] += mismatch
                                    amount_paid += mismatch
                                    mismatch = 0.0
                                #~ Si el ajuste es mayor al monto original
                                else:
                                    print "************ ajuste mayor **************** ", inv_line['amount_paid'], " + ", mismatch, " > ", inv_line['amount_original']
                                    dif = round(float((inv_line['amount_paid'] + mismatch) - inv_line['amount_original']), decimal_precision)
                                    inv_line['amount_paid'] += mismatch - dif
                                    inv_line['amount_total'] += mismatch - dif
                                    amount_paid += mismatch - dif
                                    mismatch = dif
                        #~ Si el pago es mayor al original
                        elif (inv_line['amount_paid'] + amount_pay) > inv_line['amount_original']:
                            print "************ pago mayor **************** ", inv_line['amount_paid'], " + ", amount_pay, " > ", inv_line['amount_original']
                            dif = round(float((inv_line['amount_paid'] + amount_pay) - inv_line['amount_original']), decimal_precision)
                            mismatch += dif
                            inv_line['amount_paid'] += amount_pay - dif
                            inv_line['amount_total'] += amount_pay - dif
                            amount_paid += amount_pay - dif
                            print "************ diferencia ********** ", dif
                        print "************** mismatch *********** ", mismatch, "   paid ", amount_paid, "  pagado en linea  ", inv_line['amount_paid']

                    #~ Valida que el monto pagado sea igual al monto por pagar
                    if amount_paid + mismatch <> move_line.debit:
                        print "*************** actualiza mismatch por diferencia pagos ", amount_paid, " <> ", move_line.debit
                        mismatch += round(float(move_line.debit- (amount_paid + mismatch)), decimal_precision)
                        #~ Valida que no haya centavos fuera
                        if amount_paid + mismatch <> move_line.debit:
                            mismatch = round(float(move_line.debit - amount_paid), decimal_precision)
                        print "************* valor mismatch ***************** ", mismatch

                    #~ Si hay monto pendiente, recorre las lineas de pedido para aplicar el pago
                    if mismatch > 0.0:
                        print "***************** monto pendiente ********************* "
                        for inv_line in inf_line:
                            print "********** amount paid   ", type(inv_line['amount_paid']), "  amount original   ", type(inv_line['amount_original']), "   mismatch   ", type(mismatch)

                            #~ Si el ajuste es menor al monto original
                            if (inv_line['amount_paid'] + mismatch) <= inv_line['amount_original']:
                                print "************ agregar ajuste **************** ", inv_line['amount_paid'], " + ", mismatch, " <= ", inv_line['amount_original']
                                inv_line['amount_paid'] += mismatch
                                inv_line['amount_total'] += mismatch
                                amount_paid += mismatch
                                mismatch = 0.0
                            #~ Si el ajuste es mayor al monto original
                            elif (inv_line['amount_paid'] + mismatch) > inv_line['amount_original']:
                                print "************ ajuste mayor **************** ", inv_line['amount_paid'], " + ", mismatch, " > ", inv_line['amount_original']
                                dif = round(float((inv_line['amount_paid'] + mismatch) - inv_line['amount_original']), decimal_precision)
                                inv_line['amount_paid'] += mismatch - dif
                                inv_line['amount_total'] += mismatch - dif
                                amount_paid += mismatch - dif
                                mismatch = dif
                                print " ********** diferencia *********** ", dif
                            print " **************** mismatch *************** ", mismatch, "  paid   ", amount_paid, " pay for line ", inv_line['amount_paid'], " to pay ", inv_line['amount_total']

                    #~ Valida que el monto pagado no sea mayor al monto a pagar
                    if mismatch > 0.0:
                        print "***************** monto pagado es mayor al monto a pagar ********************** ", mismatch
                        raise osv.except_osv('Error!','El monto pagado es mayor al monto a pagar en la factura "' + invoice.internal_number + '".')

                    #~ Valida que el monto pagado sea igual al monto por pagar
                    if amount_paid <> move_line.debit:
                        print "***************** monto pagado es diferente a monto por pagar ********************** ", amount_paid, " <> ", move_line.debit
                        raise osv.except_osv('Error!','Ocurrio un error al aplicar los pagos del presupuesto en la factura "' + invoice.internal_number + '".')

                    #~ Agrega el id de la factura que utiliza el movimiento
                    move_line_obj.write(cr, uid, move_line.id, {'invoice_paid': invoice.id}, context=context)

                print " *********** resultado de array *************** \n ", inf_line

                #~ Aplica la informacion dentro de los momentos presupuestales
                budget_log_obj.action_budget_log_movement(cr, uid, inf_doc, inf_line, context=context)

                #~ Actualiza en la base de datos el monto pagado por linea de factura
                for inv_line in inf_line:
                     inv_line_obj.write(cr, uid, inv_line['line_id'], {'amount_paid' : inv_line['amount_paid']}, context=context)

                #~ Si el estado de la factura esta pagado actualiza el campo de pagado
                if invoice.state == 'paid':
                    invoice_obj.write(cr, uid, invoice.id, {'paid': True}, context=context)

            voucher_lines = []

            print "************************ detalle del voucher *********************************** "

            #~ Obtiene los ids de las lineas del voucher
            for line in voucher.line_cr_ids:
                voucher_lines.append(line.id)

            #~ Recorre las lineas del voucher
            for voucher_line in voucher_line_obj.browse(cr, uid, voucher_lines, context=context):
                print "************************** informacion voucher line **************************** ", voucher_line.name
                print "************************** informacion voucher line monto **************************** ", voucher_line.amount
                print "************************** informacion voucher line monto original **************************** ", voucher_line.amount_original

        return True

    _inherit = "account.voucher"
    _description = "Account Voucher"

    _columns = {
        #~ No hay columnas heredadas al objeto
    }
