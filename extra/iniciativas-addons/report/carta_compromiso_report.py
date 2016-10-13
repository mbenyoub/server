## -*- coding: utf-8 -*-
from openerp.report import report_sxw
import base64
import binascii
import logging
logging.basicConfig(level=logging.INFO)


class carta_compromiso_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(carta_compromiso_report, self).__init__(cr, uid, name, context=context)

report_sxw.report_sxw('report.carta.compromiso.report','crm.lead','extra/iniciativas-addons/report/carta_compromiso.mako',parser=carta_compromiso_report)
