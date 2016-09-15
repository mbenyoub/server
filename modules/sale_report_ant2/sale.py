# -*- coding: utf-8 -*-
from osv import osv
import logging
_logger = logging.getLogger(__name__)


class sale_order_line(osv.Model):

    _inherit = 'sale.order.line'

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False,
        context=None):
        """
            Agrega la informacion de la tarifa sobre la linea de la factura
        """
        pricelist_id = 0
        res = {}

        # Funcion original para obtener la linea de la factura
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)

        # Obtención de la tarifa
        pricelist_id = line.order_id.pricelist_id.id or False

        # Introduciendo la tarifa dentro del diccionario con los demás datos de la que estarán en la linea de factura
        res['pricelist_id'] = pricelist_id

        # Obtiene el precio original sobre la tarifa
        if pricelist_id:
            res['price_original'] = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                line.product_id.id or False, self._get_line_qty(cr, uid, line, context=context), line.order_id.partner_id.id or False, {
                    'uom': self._get_line_uom(cr, uid, line, context=context),
                    'date': line.order_id.date_order,
                    })[pricelist_id]

        # Introduciendo la ciudad del cliente dentro del diccionario con los demás datos que estarán en la línea de factura
        res['city'] = line.order_id.partner_id.city or False

        return res

sale_order_line()