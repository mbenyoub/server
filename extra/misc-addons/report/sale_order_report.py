## -*- coding: utf-8 -*-
from openerp.report import report_sxw
import base64
import binascii
import logging
logging.basicConfig(level=logging.INFO)


class sale_order_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(sale_order_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            #'get_data':self._get_data,
            #'addComa': self.addComa,
        })



report_sxw.report_sxw('report.sale.order.report','sale.order','extra/misc-addons/report/sale_order.mako',parser=sale_order_report)
