# -*- coding: utf-8 -*-
from osv import osv, fields


class product_pricelist(osv.Model):

    _inherit = 'product.pricelist'

    _columns = {
        'account_invoice_line_ids': fields.one2many('account.invoice.line',
            'pricelist_id', 'Lineas de factura'),
    }