# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
#try:
#    import json
#except ImportError:
#    import simplejson as json

#from openerp.addons.web import http as openerpweb
#from openerp.addons.web.controllers.main import ExcelExport
try:
    import json
except ImportError:
    import simplejson as json

from datetime import date
from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from django.http import HttpResponse
from lxml import etree
from web.controllers.main import ExcelExport
from web.controllers.main import Export
from lxml  import etree
from PIL import Image
#from xhtml2pdf import pisa
#from fpdf import FPDF

import time
import openerp.addons.decimal_precision as dp
import openerp.exceptions
import csv
import os
import xlwt
import getpass
import pwd
import StringIO
import cStringIO
import base64
#import zip
#import streaming
#import response
import tempfile
import web.http as openerpweb
import re
import reportes
import time, os
import locale
import openerp.tools as tools
import xmlrpclib

class reportes(osv.osv_memory):
    _name = "reportes"
    _description = "Exportar a excel"
    
    def exportar(self, cr, uid, ids, directory=".", context=None):
        #ExcelExportView.index()
        _cp_path = '/web/export/zb_excel_export'
        result = {}
        bal = []
        activo = 0
        pasivocapital = 0
        saldo = {}
        bal1 = []

        company = self.pool.get('res.company').browse(cr, uid, 1, context=context).name
        logo = self.pool.get('res.company').browse(cr, uid, 1, context=context).logo
        acc_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move.line')

#_________________________________________Busqueda de las variables utilizadas para el reporte_______________________________________________#
        for reporte in self.browse(cr, uid, ids, context=context):
            id = reporte.id              

        acc_ids = acc_obj.search(cr, uid, [('type','!=','view')])
        for cuenta in acc_obj.browse(cr, uid, acc_ids):
            balance = 0
            if reporte.movimiento == 1:
                move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id)])
            else:
                move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id),('state','!=','draft')])
            for move in move_obj.browse(cr, uid, move_ids):
                balance += move.debit - move.credit
            if round(balance, 2) != 0.0:
                if str(move.account_id.parent_id.code)[0:2] == '11':
                    if len(bal) == 0:
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                        saldo = {
                            0: 'Activo Circulante',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance,
                        2: 'AC'
                    }
                elif str(move.account_id.parent_id.code)[0:2] == '12':
                    for af in bal:
                        a = af
                    if 'AF' not in str(a[2]):
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                        saldo = {
                            0: 'Activo Fijo',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance,
                        2: 'AF'
                    }
                #     bal.append(saldo) 
                elif str(move.account_id.parent_id.code)[0:2] == '13':
                    for ad in bal:
                        a = ad
                    if 'AD' not in str(a[2]):
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                        saldo = {
                            0: 'Activo Fijo',
                            1: '',
                            2: ''
                        }
                        bal.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance,
                        2: 'AD'
                    }
                #     bal.append(saldo)  
                elif str(move.account_id.parent_id.code)[0:2] == '21':
                    if len(bal1) == 0:
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                        saldo = {
                            0: 'Pasivo Corto Plazo',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance * -1,
                        2: 'PC'
                    }
                elif str(move.account_id.parent_id.code)[0:2] == '22':
                    for ad in bal1:
                        a = ad
                    if 'PO' not in str(a[2]):
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                        saldo = {
                            0: 'Pasivo Corto Plazo(Otros)',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance * -1,
                        2: 'PO'
                    }
                elif str(move.account_id.parent_id.code)[0:2] == '25':
                    for ad in bal1:
                        a = ad
                    if 'PL' not in str(a[2]):
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                        saldo = {
                            0: 'Pasivo Largo Plazo',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance * -1,
                        2: 'PL'
                    }
                elif str(move.account_id.parent_id.code)[0:1] == '3':
                    for ad in bal1:
                        a = ad
                    if 'CT' not in str(a[2]):
                        saldo = {
                            0: '',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                        saldo = {
                            0: 'Capital',
                            1: '',
                            2: ''
                        }
                        bal1.append(saldo)
                    saldo = {
                        0: move.account_id.name,
                        1: balance * -1,
                        2: 'CT'
                    }
                # else:
                #     saldo = {
                #         0: move.account_id.name,
                #         1: str(balance * -1),
                #         2: 'N/A'
                #     }
                #else:
                #    saldo = {
                #        0: move.account_id.name,
                #        1: balance,
                #        2: 'N/A'
                #    }
                if 'AC' in str(saldo[2]) or 'AF' in str(saldo[2]) or 'AD' in str(saldo[2]):
                    activo += saldo[1]
                    bal.append(saldo)

                elif 'PC' in str(saldo[2]) or 'PO' in str(saldo[2]) or 'PL' in str(saldo[2]) or 'CT' in str(saldo[2]):
                    pasivocapital += saldo[1]
                    bal1.append(saldo)
        saldo = {
            0: 'Suma Activo',
            1: activo,
            2: ''

        }
        bal.append(saldo)
        saldo = {
            0: 'Suma Pasivo + Capital',
            1: pasivocapital,
            2: ''

        }
        bal1.append(saldo)

        #raise osv.except_osv('res', bal)

#_________________________________________Declaracion de variables para realizar la consulta_________________________________________________#        
        debit = 'debit'+reporte.mes
        credit = 'credit'+reporte.mes
        balance = 'balance'+reporte.mes 

#_________________________________________Consulta para sacar el reporte de Balance de comprobacion___________________________________________#
        if reporte.cero == True:
            if reporte.reporte == 'com':
                if reporte.mensual == True:  #  fiscalyear,           
                    query = ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(debit, credit, balance, reporte.periodo.name,(int(reporte.nivel))))               
                    cr.execute("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(debit, credit, balance, reporte.periodo.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = {0:'Codigo', 1:'Cuenta',2:'Nivel',3:'Saldo inicial',4:'Cargo',5:'Abono',6:'Saldo Final'}#cr.description
                elif reporte.mensual == False:  
                    query = ("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(reporte.periodo.name,(int(reporte.nivel))))                                   
                    cr.execute("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(reporte.periodo.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = cr.description
        elif reporte.cero == False:
            if reporte.reporte == 'com':
                if reporte.mensual == True:
                    query = ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (%s) != 0"%(debit, credit, balance, reporte.periodo.name,(int(reporte.nivel)), balance))                    
                    cr.execute ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (%s) != 0"%(debit, credit, balance, reporte.periodo.name,(int(reporte.nivel)), balance))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = {0:'Codigo', 1:'Cuenta',2:'Nivel',3:'Saldo inicial',4:'Cargo',5:'Abono',6:'Saldo Final'}#cr.description
                elif reporte.mensual == False:    
                    query = ("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (balance1 + balance2 + balance3 + balance4 + balance5 + balance6 + balance7 + balance8 + balance9 + balance10 + balance11 + balance12) != 0"%(reporte.periodo.name,(int(reporte.nivel))))
                    cr.execute("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (balance1 + balance2 + balance3 + balance4 + balance5 + balance6 + balance7 + balance8 + balance9 + balance10 + balance11 + balance12) != 0"%(reporte.periodo.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = cr.description

#_________________________________________Consulta para sacar el reporte de Balance General_________________________________________________#                    

            # elif reporte.reporte == 'bal':
            #     res = []
            #     query = ("""select a.cuenta, a.nombre, a.saldo from (select 'A' as f, 'Activo' as cuenta, null as nombre, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'B', code, account_account.name, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1153003000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'B1', 'Total Circulante', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1153003000 and account_move.state != 'draft'
            #     union
            #     select 'C', code, account_account.name, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1211001000 and cast(code as bigint) <= 1212015000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'C1', 'Total Fijo', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1211001000 and cast(code as bigint) <= 1212015000 and account_move.state != 'draft'
            #     union
            #     select 'D', code, account_account.name, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1221001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'D1', 'Total Diferido', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1221001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft'
            #     union 
            #     select 'E', 'Suma Activo', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft'
            #     union
            #     select 'F', 'Pasivo', null, null from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'G' as f, code as cod, account_account.name as nom, sum(debit-credit) as bal from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2202123000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'G1', 'Total Corto Plazo', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2202123000 and account_move.state != 'draft'
            #     union
            #     select 'H' as f, code as cod, account_account.name as nom, sum(debit-credit) as bal from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2511001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'H1', 'Total Largo Plazo', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2511001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft'
            #     union
            #     select 'I', 'Suma Pasivo', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft'
            #     union
            #     select 'J', 'Capital', null, null from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'K' as f, code as cod, account_account.name as nom, sum(debit-credit) as bal from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 3111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'K1', 'Suma Capital', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 3111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft'
            #     union
            #     select 'L', 'Suma Pasivo+Capital', null, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft'
            #     ) as a order by f""".format(reporte.periodo.name))
            #     cr.execute("""select a.cuenta, a.saldo from (select 'A' as f, 'Activo Circulante' as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'B' as f, account_account.name as cuenta, sum(debit-credit) as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1153003000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'B1', 'Total Circulante', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1153003000 and account_move.state != 'draft'
            #     union
            #     select 'B2' as f, null as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'C' as f, 'Activo Fijo' as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'C1', account_account.name, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1211001000 and cast(code as bigint) <= 1212015000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'C2', 'Total Fijo', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1211001000 and cast(code as bigint) <= 1212015000 and account_move.state != 'draft'
            #     union
            #     select 'C3' as f, null as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'D' as f, 'Activo Diferido' as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'D1', account_account.name, sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1221001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'D2', 'Total Diferido', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1221001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft'
            #     union 
            #     select 'E', 'Suma Activo', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 1111001000 and cast(code as bigint) <= 1291004000 and account_move.state != 'draft'
            #     ) as a order by f""".format(reporte.periodo.name))
            #     resultado = cr.fetchall()
            #     registros = cr.rowcount
            #     cr.execute("""select a.cuenta, a.saldo from (select 'G' as f, 'Pasivo Circulante' as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'G1' as f, account_account.name as cuenta, sum(debit-credit) as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2202123000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'G2', 'Total Corto Plazo', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2202123000 and account_move.state != 'draft'
            #     union
            #     select 'G3' as f, null as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'H' as f, account_account.name as nom, sum(debit-credit) as bal from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2511001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'H1', 'Total Largo Plazo', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2511001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft'
            #     union
            #     select 'H2' as f, null as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'I', 'Suma Pasivo', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 2591001000 and account_move.state != 'draft'
            #     union
            #     select 'I1' as f, null as cuenta, null as saldo from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'J', 'Capital', null from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id
            #     union
            #     select 'K' as f, account_account.name as nom, sum(debit-credit) as bal from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 3111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft' group by code, account_account.name
            #     union
            #     select 'K1', 'Suma Capital', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 3111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft'
            #     union
            #     select 'L', 'Suma Pasivo+Capital', sum(debit-credit) from account_move_line inner join account_account on account_move_line.account_id = account_account.id inner join account_move on account_move_line.move_id = account_move.id where extract(year from account_move.date)=cast({0} as int) and cast(code as bigint) >= 2111001000 and cast(code as bigint) <= 3911003000 and account_move.state != 'draft'
            #     ) as a order by f""".format(reporte.periodo.name))
            #     resultado1 = cr.fetchall()
            #     registros1 = cr.rowcount
                #raise osv.except_osv('res', res)
                #cr.description

#_________________________________________Consulta para sacar el reporte de Estado de resultados______________________________________________#                
            elif reporte.reporte == 'est':     
                query = ("""select a.cuenta, a.nombre, a.periodo, a.acumulado from (select 'A' as f, 'Ingresos' as cuenta, null as nombre, null as periodo, null as acumulado from account_account
                union
                select 'B', code, name, (select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)={1} and extract(year from date)={0}),(select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)<={1} and extract(year from date)={0}) from account_account where cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000 group by id, code, name
                union
                select 'B1', 'Total Ingresos', null, (select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000), (select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000)
                union
                select 'C' as f, 'Egresos' as cuenta, null as nombre, null as periodo, null as acumulado from account_account
                union
                select 'D', code, name, (select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)={1} and extract(year from date)={0}),(select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)<={1} and extract(year from date)={0}) from account_account where cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000 group by id, code, name
                union
                select 'D1', 'Total Egresos', null, (select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)={1} and extract(year from date)={0} and cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000),(select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000)
                union
                select 'E', 'Utilidad o Perdida', null, (select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 9212008000), (select (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 9212008000)
                ) as a where a.acumulado is not null order by f""".format(reporte.periodo.name, reporte.mes))

#, null, (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000
#, null, (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000

                cr.execute(query)#"""select a.cuenta, a.nombre, a.periodo, a.acumulado from (select 'A' as f, 'Ingresos' as cuenta, null as nombre, null as periodo, null as acumulado from account_account
                #union
                #select 'B', code, name, (select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)={1} and extract(year from date)={0}),(select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)<={1} and extract(year from date)={0}) from account_account where cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000 group by id, code, name
                #union
                #select 'B1', 'Total Ingresos', null, null, (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 5114001000 or cast(code as bigint) >= 9211001000 and cast(code as bigint) <= 9212008000
                #union
                #select 'C' as f, 'Egresos' as cuenta, null as nombre, null as periodo, null as acumulado from account_account
                #union
                #select 'D', code, name, (select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)={1} and extract(year from date)={0}),(select (sum(debit-credit)*-1) from account_move_line where account_id=account_account.id and extract(month from date)<={1} and extract(year from date)={0}) from account_account where cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000 group by id, code, name
                #union
                #select 'D1', 'Total Egresos', null, null, (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 6111001000 and cast(code as bigint) <= 9113099000
                #union
                #select 'E', 'Utilidad o Perdida', null, null, (sum(debit-credit)*-1) from account_move_line inner join account_account on account_move_line.account_id = account_account.id where extract(month from date)<={1} and extract(year from date)={0} and cast(code as bigint) >= 5111001000 and cast(code as bigint) <= 9113099000
                #) as a where a.acumulado is not null order by f""".format(reporte.periodo.name, reporte.mes))
                resultado = cr.fetchall()
                registros = cr.rowcount
                cabeceras = {0:'Cuenta', 1:'Nombre',2:'Periodo',3:'Acumulado'}#cr.description
#__________________________________________________Variable de formato de consulta____________________________________________________________#
        com = {}
        if reporte.reporte == 'est':
            report = 'Estado de resultados'
        elif reporte.reporte == 'bal':
            report = 'Balance General'
        elif reporte.reporte == 'com':
            report = 'Balanza de comprobacion'

        if reporte.reporte == 'bal':
            com[0] = {0:report + " " + reporte.periodo.name, 1: reporte.periodo.name, 2:company}
        else:    
            com[0] = {0:report, 1:self._get_mes(cr, uid, reporte.mes, context) , 2:reporte.periodo.name, 3:company}

#         outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)
#         with open('tmp/excel.txt', 'w')  as f:
#             writer = csv.writer(f, delimiter=',')
#             cr.copy_expert(outputquery, f)
#         with open('tmp/excel.txt', 'r') as l:
#             data = l.read()
#         fil = data.split('\n')
# #______________________________________________________Creacion del archivo PDF_______________________________________________________________#
   #      pdf = FPDF('L', 'mm', 'Letter')
   #      fila = fil[0].split(',')     
   #      pdf.add_page()
   #      pdf.set_font('Arial', 'B', 12)

   #      for num in range(registros):
   #          fila = resultado[num]
   #          for index, col in enumerate(fila):
   #              if num == 0:
   #                  if index>0 and index%9==0:
   #                      pdf.add_page()
   #                      pdf.set_font('Arial', 'B', 12)  
   #                  cab = cabeceras[index]
   #                  pdf.cell(30, 0, str(cab[0]), 0, 0, 'C')
   #              else:   
   #                  pdf.set_font('Arial','',10)
   #                  fila = resultado[num-1]
   #                  celda = fila[index]
   #                  pdf.cell(30, 0, str(celda), 0, 0, 'C')
   #          if num+1 == registros:
   #              pdf.cell(50, 5, "", 0, 1)
   #              for index, col in enumerate(fila):  
   #                  pdf.set_font('Arial','',10)
   #                  fila = resultado[num]
   #                  celda = fila[index]
   #                  pdf.cell(30, 0, str(celda), 0, 0, 'C')
   #          pdf.cell(50, 5, "", 0, 1) 
   #      pdf.close()
   #      pdf.output("tmp/pdf.pdf","F")
   # # Se agrega otra celda próxima a la anterior pero con texto centrado
   #      #pdf.cell(80, 10, "Muy cerca de ti!", 1, 1, "C")
   #      with open("tmp/pdf.pdf", "rb") as f:
   #          data = f.read()
   #      pdf = data.encode("base64")  
   #      #return libro
   #      thispdf = self.browse(cr, uid, ids, context=context)[0]
   #      # mods = sorted(map(lambda m: m.name, this.modules)) or ['all']
   #      # lang = this.lang if this.lang != NEW_LANG_KEY else False
   #      filenamepdf = 'new'
   #      # if lang:
   #      #     filename = get_iso_codes(lang)
   #      # elif len(mods) == 1:
   #      # filename = mods[0]
   #      extensionpdf = "pdf"#this.format
   #      # if not lang and extension == 'po':
   #      #     extension = 'pot'
   #      namepdf = "%s.%s" % (filenamepdf, extensionpdf)
   #      thispdf.write({'bpdf': pdf, 'namepdf': namepdf})
    # Se cierra el documento y se escribe
        #pdf.output("tmp/pdf.pdf","F")
        #with open('tmp/excel.csv', 'w')  as f:
        #    writer = csv.writer(f, delimiter=',')
        #    cr.copy_expert(outputquery, f)

        #filepdf = open('tmp/excel.csv', 'r')
        #outfile = open('tmp/pdf.pdf', 'w+b')
        #pisaStatus = pisa.CreatePDF(filepdf, dest=outfile)
         #pdf = base64.encodestring(pisaStatus)

#______________________________________________________Creacion del archivo XLS_______________________________________________________________#        
        libro = xlwt.Workbook()
        libro1 = libro.add_sheet("Consulta")
        book = xlwt.Workbook()
        sheet = book.add_sheet("Reporte")
        txt = "Fila %s, Columna %s"
        style = xlwt.XFStyle()

    # font
        font = xlwt.Font()
        font.bold = True
        style.font = font

# borders
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.DASHED
        style.borders = borders
        
        size = 48, 48
        im = Image.open(StringIO.StringIO(base64.b64decode(logo)))
        im.thumbnail(size, Image.ANTIALIAS)
        im.convert("RGB").save('tmp/logo.bmp')
        sheet.insert_bitmap('tmp/logo.bmp', 0, 0, 0, 0)# )

        if reporte.reporte == 'bal':
            cabeceras = {0:'Activo', 1:'-', 2:'Pasivo'}
            for num in range(len(bal)):
                row = sheet.row(num)
                fila = bal[num]
                for col in range(0, 6):
                    colunm = sheet.col(col)
                    if col == 2:
                        colunm.width = 32 * 30
                    else:
                        colunm.width = 256 * 30 
                if num == 0:
                    fila = com[num]
                    for index, col in enumerate(fila):
                        comp = com[0]
                        if index == 0:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))#pattern: pattern solid, fore_color white;                             
                            row.height_mismatch = True
                            row.height = 90 * 30
                        elif index == 2:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))
                            row.height_mismatch = True
                            row.height = 90 * 30
                else:
                    for index, col in enumerate(fila):
                        if num == 1:
                            cab = cabeceras[index]
                            if index == 1:
                                cab = cabeceras[index+1]
                                row.write(index+2, cab, style=style)
                            elif index == 0:
                                row.write(index, cab, style=style)
                        elif num > 1:    
                            fila = bal[num-2]
                            celda = fila[index]                
                            #for index, col in enumerate(fila):
                    #raise osv.except_osv(index, fila)
                            if index < 2:
                                if 'Activo' in str(celda):
                                    row.write(index, celda, style=style)
                                else: 
                                    row.write(index, celda)
                if num+2 == len(bal):
                    row = sheet.row(num+2)
                    for index, col in enumerate(fila):
                        fila = bal[num]
                        celda = fila[index]
                        if index < 2:
                            row.write(index, celda)

                if num+1 == len(bal):
                    row = sheet.row(num+2)
                    for index, col in enumerate(fila):
                        fila = bal[num]
                        celda = fila[index]
                        row = sheet.row(32)
                        if index < 2:
                            if index == 0:
                                row.write(index, celda, style=style)
                            else:
                                row.write(index, celda)

            for num in range(len(bal1)):
                row = sheet.row(num+2)
                fila = bal1[num]
                for index, col in enumerate(fila):
                    fila = bal1[num]
                    celda = fila[index]
                    if index < 2:
                        if 'Suma' in str(fila[0]):
                            row = sheet.row(32)
                            if index == 0:
                                row.write(index + 3, celda, style=style)
                            else:
                                row.write(index + 3, celda)
                        elif 'Pasivo' in str(celda) or 'Capital' in str(celda):
                            row.write(index + 3, celda, style=style)
                        else: 
                            row.write(index+3, celda)

        # if reporte.reporte == 'bal':
        #     for num in range(registros):
        #         row = libro1.row(num)
        #         fila = resultado[num]
        #         for col in range(0, 6):
        #             colunm = libro1.col(col)
        #             if col == 2:
        #                 colunm.width = 64 * 30
        #             else:
        #                 colunm.width = 256 * 30 
        #         if num == 0:
        #             fila = com[num]
        #             for index, col in enumerate(fila):
        #                 comp = com[0]
        #                 if index == 0:
        #                     row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))#pattern: pattern solid, fore_color white;                             
        #                     row.height_mismatch = True
        #                     row.height = 90 * 30
        #                 elif index == 2:
        #                     row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))
        #                     row.height_mismatch = True
        #                     row.height = 90 * 30
        #         else:
        #             for index, col in enumerate(fila):
        #                 if num == 1:
        #                     cab = cabeceras[index]
        #                     if index == 1:
        #                         cab = cabeceras[index+1]
        #                         row.write(index+2, cab, style=style)
        #                     else:
        #                         row.write(index, cab, style=style)
        #                 #row.write(index, cab[0])
        #                 elif num>1:    
        #                     fila = resultado[num-2]
        #                     celda = fila[index]
        #                     if 'Activo Circulante' in str(celda) or 'Total Circulante' in str(celda):
        #                         row.write(index, celda, style=style) 
        #                     elif 'Activo Fijo' in str(celda) or 'Total Fijo' in str(celda):
        #                         row.write(index, celda, style=style)
        #                     elif 'Activo Diferido' in str(celda):
        #                         row.write(index, celda, style=style)
        #                     else:
        #                         row.write(index, celda)  
        #         if num+2 == registros:
        #             row = libro1.row(num+2)
        #             for index, col in enumerate(fila):
        #                 fila = resultado[num]
        #                 celda = fila[index]
        #                 if index == 0:
        #                     row.write(index, celda, style=style)
        #                 else:      
        #                     row.write(index, celda)
        #         if num+1 == registros:
        #             row = libro1.row(num+2)
        #             for index, col in enumerate(fila):
        #                 fila = resultado[num]
        #                 celda = fila[index]
        #                 if index == 0:
        #                     row = libro1.row(36)
        #                     row.write(index, celda, style=style)
        #                 else:
        #                     row = libro1.row(36)
        #                     row.write(index, celda)
        #                 #else:
        #                 #    row.write(index, celda)

        #     for num in range(registros1):
        #         row = libro1.row(num+2)
        #         fila = resultado1[num]
        #         for index, col in enumerate(fila):
        #             fila = resultado1[num]
        #             celda = fila[index]
        #             #raise osv.except_osv(fila, num)
        #             if 'Pasivo+Capital' in str(celda):
        #                 row = libro1.row(36)
        #                 row.write(index+3, celda, style=style)
        #             elif 'Pasivo' in str(celda) and 'Circulante' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             elif 'Total Corto Plazo' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             elif 'Total Largo Plazo' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             elif 'Suma' in str(celda) and 'Pasivo' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             elif 'Capital' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             elif 'Suma' in str(celda) and 'Capital' in str(celda):
        #                 row.write(index+3, celda, style=style)
        #             else:
        #                 row.write(index+3, celda)


        #         # if num+1 == registros1:
        #         #     row = libro1.row(num+2)
        #         #     for index, col in enumerate(fila):                    
        #         #         fila = resultado1[num]
        #         #         celda = fila[index]
        #         #         row.write(index+3, celda)

        # else:
        #     for num in range(registros):
        #         row = libro1.row(num)
        #         fila = resultado[num]
        #         if num == 0:
        #             fila = com[num]
        #             for index, col in enumerate(fila):
        #                 colunm = libro1.col(col)
        #                 colunm.width = 256 * 30  
        #                 comp = com[0]
        #                 row.write(index, comp[col])
        #         else:
        #             for index, col in enumerate(fila):
        #                 if num == 1:
        #                     cab = cabeceras[index]
        #                     row.write(index, cab)
        #                 #row.write(index, cab[0])
        #                 elif num>1:    
        #                     fila = resultado[num-2]
        #                     celda = fila[index]
        #                     row.write(index, celda)
        #         if num+2 == registros:
        #             row = libro1.row(num+2)
        #             for index, col in enumerate(fila):
        #                 fila = resultado[num]
        #                 celda = fila[index]
        #                 row.write(index, celda)        
        #         if num+1 == registros:
        #             row = libro1.row(num+2)
        #             for index, col in enumerate(fila):
        #                 fila = resultado[num]
        #                 celda = fila[index]
        #                 row.write(index, celda)

        fp = StringIO.StringIO()
        #libro.save(fp)
        book.save(fp)
        fp.seek(0)        
        data = fp.read()
        fp.close()
        out = base64.encodestring(data)
        #libro.save('tmp/Excel.pdf')
        book.save('tmp/Excel.pdf')
  
        #return libro
        this = self.browse(cr, uid, ids, context=context)[0]
        # mods = sorted(map(lambda m: m.name, this.modules)) or ['all']
        # lang = this.lang if this.lang != NEW_LANG_KEY else False

        if 'Balance General' in report:
            filename = report + " " + reporte.periodo.name
        else: 
            filename = report + " " + self._get_mes(cr, uid, reporte.mes, context) + " " + reporte.periodo.name
        # if lang:
        #     filename = get_iso_codes(lang)
        # elif len(mods) == 1:
        # filename = mods[0]
        extension = "xls"#this.format
        # if not lang and extension == 'po':
        #     extension = 'pot'

        name = "%s.%s" % (filename, extension)
        this.write({'binario': out, 'name': name})
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'exportar',
        #     'view_mode': 'form',
        #     'view_type': 'form',
        #     'res_id': this.id,
        #     'views': [(False, 'form')],
        #     'target': 'new',
        # }

    def _get_mes(self, cr, uid, mes, context=None):

        meses = [
            'Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
        ]

        mes_act = meses[int(mes)-1]

        return mes_act


    _columns = {
        'reporte': fields.selection([('bal','Balance General'),('com','Balanza de comprobacion'),('est','Estados de resultados')], 'Reporte', required=True, help="Escoger el informe a exportar"),
        'nivel': fields.selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6')], 'Nivel', help="Escoger el nivel", size=30), 
        'periodo':fields.many2one('account.fiscalyear', 'Periodo'),
        'movimiento': fields.selection([('1','Todos los movimientos'),('2','Todos los movimientos asentados')], 'Movimientos'),
        'cero': fields.boolean('Cuentas cero', help="Marcar si se desea visualizar cuentas con saldo cero"),
        'mensual': fields.boolean('Mensual', help="Marcar si se desea visualizar un mes en especifico"),
        'mes': fields.selection([('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')], 'Mes', help="Escoger el mes"),
        'todos': fields.boolean('Asientos', help="Marcar si se desea visualizar todos los asientos"),
        'deb_cre': fields.boolean('Debito/Credito', help="Marcar si se desea visualizar la columna debito y credito"),
        #'archivo': fields.text('Archivo', size=30,help="Marcar si se desea visualizar un mes en especifico"),
        'binario': fields.binary('Label',filters='*.xml', filename='Excel'),
        'name': fields.char('File Name', readonly=True),
        #'bpdf': fields.binary('Label',filters='*.xml', filename='PDF'),
        #'namepdf': fields.char('File Name', readonly=True),
    }
    
    _defaults = {
        'nivel':'1',
        'periodo': '2',
        'cero': False,
        'mensual': True,
        'mes':'1',
        'todos': False,
        'deb_cre': False,
        'movimiento': '1',
        #'archivo': 'Excel.csv',
        #'binario': '/tmp/excel.csv',
    }

reportes()

class catalogo(osv.osv_memory):
     _name = "catalogo"
     _description = "Catalogos para importar la informacion"
    
     _columns = {
         'Productos': fields.binary('Catalogo',filters='*.csv', filename='productos'),
         'pname': fields.char('File Name', readonly=True),
     }
    
# #    _defaults = {

# #    }
    
catalogo()

