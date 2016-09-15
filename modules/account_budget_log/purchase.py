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
    Herencia sobre modulo de compras en el area de solicitud para aplicar momento comprometido
"""

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
import datetime

class purchase_order(osv.Model):
    """Inherited purchase.order"""

    def copy(self, cr, uid, id, default=None, context=None):
        """
            Duplicar la informacion de la compra
        """
        order_line_obj = self.pool.get('purchase.order.line')

        #~ Campos del documento a limpiar
        default['date_approve'] = None

        print "******************* recorre las lineas de pedido ******************* "

        #~ Recorre las ordenes de compra
        order = self.browse(cr, uid, id, context=context)

        print "************** Actualiza lineas por presupuesto *******************"
        #~ Obtiene los ids de las lineas de pedido
        order_line_ids = []
        for line in order.order_line:
            order_line_ids.append(line.id)

        print "******************** cambia linea de pedido *********************"

        #~ Recorre las lineas de pedido
        for order_line in order_line_obj.browse(cr, uid, order_line_ids, context=context):
            order_line_obj.write(cr, uid, order_line.id, {
                    'product_picking': 0.0,
                })

        print "******************* copy original ************************* "

        # en el copy hace un retorno con toda la informacion en base al id marcado
        return super(purchase_order, self).copy(cr, uid, id, default, context=context)

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        res = False

        print "**************************** Metodo heredado compra *******************************"

        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv('Error!','No se puede seleccionar la compra porque no hay pedidos de compra.')
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)

        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})

        return True

    def wkf_add_move_confirm(self, cr, uid, ids, context=None):
        print "**************************** Metodo agregado a workflow confirm compra *******************************"

        order_line_obj = self.pool.get('purchase.order.line')

        #~ Recorre las ordenes de compra activas o seleccionadas
        for order in self.browse(cr, uid, ids, context=context):
            print "****************************** Informacion orden **************************************"

            date = datetime.datetime.now().strftime("%Y-%m-%d")

            #~ Crea un diccionario con la informacion para generar los movimientos
            inf_doc = {
                'reference' : order.name,
                'document': 'Compra',
                'state' : 'committed',
                'date' : date,
                'total' : order.amount_total,
                'partner_id': order.partner_id.id,
            }

            print "**** read ***** ", inf_doc
            print "****************************** Informacion lineas de pedido **************************************"

            line_ids = []

            #~ Obtiene los ids de las lineas de pedido de compra
            if not order.order_line:
                raise osv.except_osv('Error!','No se puede seleccionar la compra porque no hay pedidos de compra.')
            for line in order.order_line:
                line_ids.append(line.id)

            inf_line = []
            decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

            print "***************** ORDER *************** ", self.read(cr, uid, order.id, context=context)

            #~ Obtiene la informacion de cada linea de pedido de la compra
            for line in order_line_obj.browse(cr, uid, line_ids, context=context):
                print "*****  line id ***** ", line.id

                amount_line = order_line_obj.get_amount_tax(cr, uid, [line.id, ], context)

                one_line = {
                    'product_id': line.product_id.id,
                    'product_name': line.name,
                    'account_analytic_id' : line.account_analytic_id.id,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'quantity': line.product_qty,
                    'tax_code_id': line.taxes_id[0].id,
                    'amount_tax': round(float(amount_line[line.id]['amount_tax']), decimal_precision),
                    'amount_total': round(float(amount_line[line.id]['amount_total']), decimal_precision),
                }

                inf_line.append(one_line)
                print "********* Inf_line **************************  ", inf_line

                """
                print "***************** line *************** ", order_line_obj.read(cr, uid, line.id, context=context)

                #~ Genera listado con las afectaciones a las cuentas del movimiento del presupuesto, agrupados por cuenta analitica
                amount_line = order_line_obj.get_amount_tax(cr, uid, [line.id, ], context)
                print "+++++++++++++++  ", amount_line
                print "+++++++++++++  ", line.account_analytic_id.id

                #~ Inicializa el monto si no esta activo
                if line.account_analytic_id.id not in inf_line:
                    inf_line[line.account_analytic_id.id] = 0.0

                inf_line[line.account_analytic_id.id] += round(float(amount_line[line.id]['amount_total']), 2)
                print inf_line
                """

            print "************************************** Fin de metodo ************************************************"

            #~ Aplica la informacion dentro de los momentos presupuestales
            budget_log_obj = self.pool.get('account.budget.log.moments')
            budget_log_obj.action_budget_log_movement(cr, uid, inf_doc, inf_line, context=context)

        return True

    _inherit = 'purchase.order'
    _columns = {
        # We just add a new column in res.partner model
        'invoice_method': fields.selection([('manual','Based on Purchase Order lines'),('order','Based on generated draft invoice'),('picking','Based on incoming shipments')], 'Invoicing Control', required=True,
            readonly=True, help="Metodo de facturacion tiene que ser por recepciones de mercancia para afectar los momentos del presupuesto."
        ),
    }

    def _check_product_repeat(self, cr, uid, ids, context=None):
        order = self.browse(cr, uid, ids[0], context=context)
        #~ Valida que no haya productos repetidos en la solicitud de compra
        cr.execute("select count(id) as cantidad from purchase_order_line where order_id='" + str(order.id) + "' group by product_id having count(id) > 1")
        if cr.fetchone():
            return False
        return True

    _constraints = [
        (_check_product_repeat, 'No puede haber productos repetidos en las lineas de pedido de la misma solicitud de compra.', ['order_line']),
    ]

    _defaults = {
        'invoice_method': 'picking',
    }

class purchase_order_line(osv.Model):
    """Inherited purchase.order.line"""

    def get_amount_tax(self, cr, uid, ids, context=None):
        """
            Obtiene el detalle de los montos por linea de pedido de compra
        """

        res = {}
        cur_obj=self.pool.get('res.currency')
        order_obj=self.pool.get('purchase.order')

        #~ Recorre las lineas de pedido de compra
        for order_line in self.browse(cr, uid, ids, context=context):
            res[order_line.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }

            amount_tax = amount_untaxed = 0.0
            order = order_obj.browse(cr, uid, order_line.order_id.id, context=context)
            cur = order.pricelist_id.currency_id

            amount_untaxed += order_line.price_subtotal
            for c in self.pool.get('account.tax').compute_all(cr, uid, order_line.taxes_id, order_line.price_unit, order_line.product_qty, order_line.product_id, order.partner_id)['taxes']:
                amount_tax += c.get('amount', 0.0)

            #~ Actualiza el monto
            res[order_line.id]['amount_tax']=cur_obj.round(cr, uid, cur, amount_tax)
            res[order_line.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, amount_untaxed)
            res[order_line.id]['amount_total']=res[order_line.id]['amount_untaxed'] + res[order_line.id]['amount_tax']
        return res

    _inherit = 'purchase.order.line'
    _columns = {
        # We just add a new column in res.partner model
        'product_id': fields.many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True, required=True),
        'account_analytic_id':fields.many2one('account.analytic.account', 'Analytic Account', required=True),
        'product_picking' : fields.float('Cantidad recibida', digits_compute=dp.get_precision('Product Unit of Measure')),
    }
    _defaults = {
        # By default, no partner is an instructor
        'product_picking': 0,
    }
