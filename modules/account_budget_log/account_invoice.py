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
    Herencia sobre facturacion en el modulo de Contablidad(account_invoice) para aplicar momento ejercido
"""

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import datetime

class account_invoice(osv.Model):
    """Inherited account.invoice"""

    def wkf_exercised_move(self, cr, uid, ids, context=None):
        """
            Agrega el momento ejercido si la factura va ligada a una recepcion de mercancia
        """

        print "***************************** Agregar estado ejercido a factura ************************************ "

        order_obj = self.pool.get('purchase.order')
        invoice_line_obj = self.pool.get('account.invoice.line')
        picking_obj = self.pool.get('stock.picking')
        move_lines_obj = self.pool.get('stock.move')

        #~ Recorre la informacion de las facturas
        for invoice in self.browse(cr, uid, ids, context=context):
            #~ Valida que haya una recepcion de mercancia ligada a la factura
            if not invoice.picking_id.id:
                print "***************** valida que haya recepcion de mercancia ligada a la factura **********************"
                raise osv.except_osv('Error!','No se puede ejercer la factura en el presupuesto porque no tiene ligado un albaran de entrada')

            #~ Recorre la informacion del albaran de entrada ligado a la factura
            for picking in picking_obj.browse(cr, uid, [invoice.picking_id.id,], context=context):

                print "************************* Recorre la informacion del albaran de entrada ******************************"

                #~ Valida que el estado del albaran de entrada ya haya sido recibido
                if picking.state != 'done':
                    raise osv.except_osv('Error!','No se puede ejercer la factura en el presupuesto porque los productos del albaran de entrada "' + picking.name +'" no se han recibido')

                date = datetime.datetime.now().strftime("%Y-%m-%d")

                #~ Crea un diccionario con la informacion para generar los movimientos
                inf_doc = {
                    'reference' : invoice.internal_number,
                    'document': 'Factura',
                    'state' : 'exercised',
                    'date' : date,
                    'total' : invoice.amount_total,
                    'partner_id': invoice.partner_id.id,
                }

                print "**** read ***** ", inf_doc

                #~ Valida que haya una compra ligada al albarán de entrada
                if not picking.purchase_id.id:
                    print "************** no compra en albarán de entrada facturado *********************"
                    raise osv.except_osv('Error!','No se puede ejercer la factura en el presupuesto porque el albaran de entrada "' + picking.name +'" no proviene de una orden de compra')
                    continue

                #~ Obtengo la informacion de la compra
                for order in order_obj.browse(cr, uid, [picking.purchase_id.id,], context=context):
                    print "******************** datos de compra ************************ ", order.name

            line_ids = []

            #~ Obtiene los ids de las lineas de la factura
            if not invoice.invoice_line:
                raise osv.except_osv('Error!','La facltura no tiene lineas de pedido.')
            for line in invoice.invoice_line:
                line_ids.append(line.id)

            inf_line = []
            decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

            #~ Obtiene la informacion de las lineas de facturacion
            for line in invoice_line_obj.browse(cr, uid, line_ids, context=context):
                print "*****  line id ***** ", line.id
                print "************  line  ***** ", invoice_line_obj.read(cr, uid, line.id, context=context)

                #~ Obtiene los impuestos por producto y calcula el total en base a la cantidad recibida
                amount_line = invoice_line_obj.get_amount_tax(cr, uid, [line.id, ], context)

                one_line = {
                    'product_id': line.product_id.id,
                    'product_name': line.name,
                    'account_analytic_id' : line.account_analytic_id.id,
                    'product_uom': line.uos_id.id,
                    'price_unit': line.price_unit,
                    'quantity': float(line.quantity),
                    'tax_code_id': line.invoice_line_tax_id[0].id,
                    'amount_tax': round(float(amount_line[line.id]['amount_tax']), decimal_precision),
                    'amount_total': round(float(amount_line[line.id]['amount_total']), decimal_precision),
                }

                inf_line.append(one_line)
                print "********* Inf_line **************************  ", inf_line

            #~ Aplica la informacion dentro de los momentos presupuestales
            budget_log_obj = self.pool.get('account.budget.log.moments')
            budget_log_obj.action_budget_log_movement(cr, uid, inf_doc, inf_line, context=context)

        #~ Pone las facturas como ejercidas
        self.write(cr, uid, ids, {'exercised' : True})

        return True

    def do_partial(self, cr, uid, ids, partial_datas, context=None):


        print "******************** Informacion partidas ************************* ", partial_datas

        #~ Recorre la informacion de los albaranes de entrada
        for picking in self.browse(cr, uid, ids, context=context):

            print "***************** informacion picking *********************************** "

            print "******************** nombre albaran de entrada ************************* ", picking.name, "  id compra  ", picking.purchase_id.id

            #~ Validar que el producto recibido sea menor al producto aprobado en el albaran de entrada
            for move_dic_id in partial_datas:

                #~ Valida que el movimiento sea un move
                if move_dic_id[0:4] != 'move':
                    print "*********************** Diferente de movimiento *************************"
                    continue

                move_id = int(move_dic_id[4:])

                print "******************* tipo id move a validar ********************", type(move_id)
                print "******************* tipo id purchase ********************", type(picking.purchase_id.id)
                print "******************* id move a validar ********************", move_id
                print "******************* id move a validar ********************", move_dic_id
                print "******************* ids movimientos ********************", picking.move_lines
                print "******************* cantidad confirmada movimiento ********************", picking.move_lines[0]['product_qty']

                #~ Obtiene la informacion del detalle de los movimientos
                for stock_move in stock_move_obj.browse(cr, uid, [move_id,], context=context):

                    print "******************** stock move ********************** ", stock_move_obj.read(cr, uid, move_id, context=context)
                    print "******************** partial datas ********************** ", partial_datas[move_dic_id]
                    print "******************** cantidad move ********************* ", stock_move.product_qty

                    #~ Valida que el producto sea el mismo que el confirmado
                    if stock_move.product_id.id != partial_datas[move_dic_id]['product_id']:
                        print "***************** valida producto diferente **********************"
                        raise osv.except_osv('Error!','El producto recibido no coincide con el producto confirmado en el albaran de entrada')

                    #~ Valida que la cantidad no sea mayor a lo confirmado en la recepcion
                    if stock_move.product_qty < partial_datas[move_dic_id]['product_qty']:
                        print "***************** valida cantidad mayor a lo confirmado **********************"
                        raise osv.except_osv('Error!','La cantidad recibida es mayor a la cantidad confirmada en el albaran de entrada. (CONFIRMADO: ' + str(stock_move.product_qty) + ')')

                print "***************** Inicializa monto completado en partial_datas *************************"
                #~ Inicializa parametro para monto completado
                partial_datas[move_dic_id]['complete'] = 0

            print "*************************** Crear diccionario para presupuestos ***************************************"

            #~ Crea un diccionario con la informacion para generar los movimientos
            inf_doc = {
                'reference' : picking.name,
                'state' : 'accrued',
                'date' : partial_datas['delivery_date'] or date,
                'total' : 0.0,
                'partner_id': picking.partner_id.id,
            }

            print "**** read ***** ", inf_doc

            #~ Valida que haya una compra ligada al albarán de entrada
            if not picking.purchase_id.id:
                print "************** no compra en albarán de entrada *********************"
                continue

            #~ Obtengo la informacion de la compra
            for order in order_obj.browse(cr, uid, [picking.purchase_id.id,], context=context):
                print "******************** datos de compra ************************ ", order.name

                print "******************** Indica recibido en compra *************** ", order.shipped

                #~ Valida que la orden de compra no tenga el albarán de entrada como completado
                if order.shipped != 0:
                    print "****************** recibido verdadero *****************************"
                    raise osv.except_osv('Error!','Los productos recibidos de la solicitud de compra ya fueron recibidos')

                line_ids = []

                #~ Obtiene los ids de las lineas de pedido de compra
                if not order.order_line:
                    raise osv.except_osv('Error!','La compra de la que se reciben los productos no tiene lineas de pedido.')
                for line in order.order_line:
                    line_ids.append(line.id)

                inf_line = []
                decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

                print "***************** ORDER *************** ", order_obj.read(cr, uid, order.id, context=context)

                #~ Obtiene la informacion de cada linea de pedido de la compra
                for line in order_line_obj.browse(cr, uid, line_ids, context=context):
                    qty = 0
                    print "*****  line id ***** ", line.id
                    print "************  line  ***** ", order_line_obj.read(cr, uid, line.id, context=context)

                    #~ Agrega la cantidad completada que se va a tomar de las lineas de pedido
                    for move_dic_id in partial_datas:

                        #~ Valida que el movimiento sea un move
                        if move_dic_id[0:4] != 'move':
                            print "*********************** Diferente de movimiento *************************"
                            continue

                        print " ******************* producto id de move ******************* ", partial_datas[move_dic_id]['product_id'], " ++ tipo ", type(partial_datas[move_dic_id]['product_id'])
                        print " ******************* producto id de line ******************* ", line.product_id.id, " ++ tipo ", type(line.product_id.id)

                        #~ Valida que se hayan relacionado todos los productos recibidos con los de la compra
                        if int(partial_datas[move_dic_id]['product_id']) == int(line.product_id.id):
                            if float(partial_datas[move_dic_id]['product_qty']) == float(partial_datas[move_dic_id]['complete']):
                                continue
                            if (line.product_qty - line.product_picking) < partial_datas[move_dic_id]['product_qty']:
                                raise osv.except_osv('Error!','La cantidad recibida es mayor a la cantidad confirmada en el albaran de entrada. (CONFIRMADO: ' + str(stock_move.product_qty) + ')')
                            else:
                                partial_datas[move_dic_id]['complete'] += partial_datas[move_dic_id]['product_qty']
                                qty = float(partial_datas[move_dic_id]['product_qty'])
                                break

                    #~ Valida que se hayan relacionado productos para esta linea de pedido
                    if qty == 0:
                        print "************** linea no relacionada ********************* "
                        continue

                    #~ Obtiene los impuestos por producto y calcula el total en base a la cantidad recibida
                    amount_line = order_line_obj.get_amount_tax(cr, uid, [line.id, ], context)
                    amount_tax = float(amount_line[line.id]['amount_tax']) / float(line.product_qty)
                    amount_total = float(line.price_unit) * qty

                    one_line = {
                        'product_id': line.product_id.id,
                        'product_name': line.name,
                        'account_analytic_id' : line.account_analytic_id.id,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'quantity': qty,
                        'tax_code_id': line.taxes_id[0].id,
                        'amount_tax': round((amount_tax * qty), decimal_precision),
                        'amount_total': round(amount_total, decimal_precision),
                    }

                    inf_line.append(one_line)
                    print "********* Inf_line **************************  ", inf_line

                    #~ Actualiza el total recibido en la linea de pedido
                    product_picking = float(line.product_picking) + qty
                    order_line_obj.write(cr, uid, line.id, {'product_picking': product_picking}, context=context)
                    print "******************** cantidad recibida ********************* ", product_picking, " +++ del producto ", line.name

                #~ Valida que todos los movimientos se hayan relacionado con el producto
                for move_dic_id in partial_datas:
                    #~ Valida que el movimiento sea un move
                    if move_dic_id[0:4] != 'move':
                        print "*********************** Diferente de movimiento *************************"
                        continue
                    #~ Valida se haya relacionado con la linea de pedido de compra
                    if float(partial_datas[move_dic_id]['complete']) != float(partial_datas[move_dic_id]['product_qty']):
                        print " *********** ", float(partial_datas[move_dic_id]['complete']), " != ", float(partial_datas[move_dic_id]['product_qty'])
                        product_obj = self.pool.get('product.product')
                        for product in product_obj.browse(cr, uid, [picking.purchase_id.id,], context=context):
                            raise osv.except_osv('Error!','Ocurrio un error al relacionar el producto "' + product.name + '" con la solicitud de compra al recibir el pedido.')

            #~ Aplica la informacion dentro de los momentos presupuestales
            budget_log_obj = self.pool.get('account.budget.log.moments')
            budget_log_obj.action_budget_log_movement(cr, uid, inf_doc, inf_line, context=context)

        print "************************* pasa al flujo original con un super ********************************************"

        #~ raise osv.except_osv(_('Error!'), _('Detenido para pruebas.'))
        #~ return False
        return super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)

    _inherit = "account.invoice"
    _table = "account_invoice"

    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Recepcion de Mercancia',
            ondelete='set null', select=True, readonly=True, invisible=True),
        'exercised': fields.boolean('Ejercido'),
        'paid': fields.boolean('Pagado'),
    }

    _defaults = {
        'exercised': False,
        'paid': False,
    }

class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"

    def get_amount_tax(self, cr, uid, ids, context=None):
        """
            Obtiene el detalle de los montos por linea de factura
        """

        res = {}
        cur_obj=self.pool.get('res.currency')
        invoice_obj=self.pool.get('account.invoice')

        #~ Recorre las lineas de factura
        for invoice_line in self.browse(cr, uid, ids, context=context):
            res[invoice_line.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }

            amount_tax = amount_untaxed = 0.0
            invoice = invoice_obj.browse(cr, uid, invoice_line.invoice_id.id, context=context)
            cur = invoice.currency_id

            amount_untaxed += invoice_line.price_subtotal
            for c in self.pool.get('account.tax').compute_all(cr, uid, invoice_line.invoice_line_tax_id, invoice_line.price_unit, invoice_line.quantity, invoice_line.product_id, invoice.partner_id)['taxes']:
                amount_tax += c.get('amount', 0.0)

            print "***************** monto impuestos de ", invoice_line.name,  " ******************* ", amount_tax

            #~ Actualiza el monto
            res[invoice_line.id]['amount_tax']=cur_obj.round(cr, uid, cur, amount_tax)
            res[invoice_line.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, amount_untaxed)
            res[invoice_line.id]['amount_total']=res[invoice_line.id]['amount_untaxed'] + res[invoice_line.id]['amount_tax']
        return res

    _columns = {
        'amount_paid': fields.float(string='Monto pagado', readonly=True, digits_compute=dp.get_precision('Account')),
    }

    _defaults = {
        'amount_paid': 0.0,
    }
