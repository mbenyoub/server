# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx),
#               Israel Cabrera Juarez(icabrera@saas.com.mx),
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
# ---MODIFICACION 17/04/2015-----
#   Agregacion del campo 'exceeded_limit' en la clase 'purchase.order'

# -----MODIFICACION 19/04/2015-------
#   Agregacion del campo 'state' en 'purchase_order'
#   Agregacion del metodo 'validar_monto'

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc

# ------MODIFICACION 15/04/2015-----------
class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        """
            prepara el movimiento de almacen
        """
        print "******REALIZANDO EL SUPER DEL METODO PREPARE_ORDER_LINE_MOVE*****"
        # Realizando el super del metodo para llamar la funcionalidad original
        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id,
            context=context)
        # Se agrega el valor del campo 'to_weight_product' al diccionario que se recibe de la funcion
        # original
        res['to_weight_product'] = order_line.to_weight_product
        res['analisis'] = order_line.analisis
        res['analisis_type'] = order_line.analisis_type.id
        print "*****RES***: ", res
        return res
    
    
    
    def view_invoice(self, cr, uid, ids, context=None):
        purchase_id = self.browse(cr, uid, ids[0], context=context)['id']
        picking_obj = self.pool.get('stock.picking.in')
        
        # Obteniendo el estado de la orden de entrada del pedido de venta
        picking_srch = picking_obj.search(cr, uid, [('purchase_id', '=', purchase_id)], context=context)
        state = picking_obj.browse(cr, uid, picking_srch[0], context=context)['state']
        
        if state in ['done']:
            return super(purchase_order, self).view_invoice(cr, uid, ids, context=context)
        else:
            raise osv.except_osv(_('Warning'), _("""La recepcion de mercancia no ha sido autorizada"""))
        
    def validar_monto(self, cr, uid, ids, context=None ):
        """
        Compara el monto permitido en una solicitud de compra contra el
        total de la compra, si este total eccede debe de pasar por un autoriacion
        """
        for id in ids:
            cr.execute('SELECT amount_total FROM purchase_order WHERE id=%s',(id,))
            amount_total=cr.fetchone()[0]
        result = {}
        #try:
        cr.execute('SELECT monto_maximo FROM canis_config WHERE ultimo_monto = True')
        monto= cr.fetchone()[0]
        if (amount_total>monto):
            print "****MONTO EXCEDIDO*******"
            self.write(cr, uid, ids, {'state':'verificacion'}, context=context)
        else:
            self.write(cr, uid, ids, {'exceeded_limit': False}, context=context)
            
    
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        # Obteniendo el peso real o esperado del producto
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        picking_srch = picking_obj.search(cr, uid, [('purchase_id', '=', order_line.order_id.id or False)],
            context=context)
        picking_id = picking_obj.browse(cr, uid, picking_srch[0], context=context)['id'] or False
        move_srch = move_obj.search(cr, uid, [('picking_id', '=', picking_id),
            ('product_id', '=', order_line.product_id.id or False)], context=context)
        move = move_obj.browse(cr, uid, move_srch[0], context=context)
        quantity = move.product_qty
        print "*****PURCHASE QUANTITY******: ", quantity
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': quantity,
            # 'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
        }
    
    
    _columns = {
        'exceeded_limit': fields.boolean('limite excedido'),
        'state': fields.selection([('draft', 'OC en borrador'),
                                   ('verificacion', 'Pendiente por autorizar'),
                                   ('sent', 'Peteció de contización enviada'),
                                   ('confirmed', 'Esperando aprobación'),
                                   ('approved', 'Pedido de compra'),
                                   ('except_picking','Excepción de compra'),
                                   ('except_ivoice', 'Excepción de factura'),
                                   ('done', 'Realizado'),
                                   ('cancel', 'Cancelado')],
                                  'Estado', readonly=True),
    }
    
    _defaults = {
        'exceeded_limit': True,
    }

purchase_order()
# --------------------------------


class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        print "*****HACIENDO EL ONCHANGE*******"
        #cambio de variables para escribir en la tabla de order line las propiedades del producto
        res = {}
        product_obj = self.pool.get('product.product')
        
        # Llamando la funcionalidad original del metodo onchange del producto
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id,
            qty, uom_id, partner_id, date_order, fiscal_position_id, date_planned,
            name, price_unit, context=context)
        
        product_srch = product_obj.search(cr, uid, [('id', '=', product_id)], context=context)
        print "****PRODUCT_SRCH****: ", product_srch
        for product in product_obj.browse(cr, uid, product_srch, context=context):
            weight = product.to_weight_product
            analise = product.analisis
            analisis2_type = product.analisis_type.id
            res['value']['to_weight_product'] = weight
            res['value']['analisis'] = analise
            res['value']['analisis_type'] = analisis2_type
        
        
        print "*****RES****: ", res
        
        return res
    
    _columns = {
        # 'to_weight_product': fields.related('product_id', 'to_weight_product',type='boolean',
        #     string='Pesar', store=True),
        'to_weight_product': fields.boolean('Pesar'),
        #'analisis': fields.boolean('A Analizar'),
        #'analisis_type': fields.many2one('catalogo.producto','Analisis'),
    }
    
    # _defaults = {
    #     'to_weight_product': _get_default_weight_bool,
    # }