## -*- coding: utf-8 -*-
from openerp.report import report_sxw
import base64
import binascii
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)


class carta_compromiso_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(carta_compromiso_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
	    'getYear': self.getYear,
	    'getMonth': self.getMonth,
            'getDay': self.getDay,
        })

    def getDay(self):
	d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%d'
	day = d.strftime(n_format)
	return day

    def getYear(self):
        d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%Y'
        year = d.strftime(n_format)
	return year

    def getMonth(self):
        d=datetime.now()-timedelta(hours=6) #Se quitan 6 horas para que sea la hora de Mexico
        n_format = '%B'
        m = d.strftime(n_format)
	months = {'January':'Enero',
	'February':'Febrero',
        'March':'Marzo',
        'April':'Abril',
        'May':'May',
        'June':'Junio',
        'July':'Julio',
        'August':'Agosto',
        'September':'Septiembre',
        'October':'Octubre',
	'November':'Noviembre',
        'December':'Diciembre',
	}
	mes = months[m]
        return mes


report_sxw.report_sxw('report.carta.compromiso.report','crm.lead','extra/iniciativas-addons/report/carta_compromiso.mako',parser=carta_compromiso_report)
