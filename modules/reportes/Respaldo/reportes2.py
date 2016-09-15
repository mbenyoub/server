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
        est = []
        balanza = []

        company = self.pool.get('res.company').browse(cr, uid, 1, context=context).name
        logo = self.pool.get('res.company').browse(cr, uid, 1, context=context).logo
        acc_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move.line')
        balanza_obj = self.pool.get('account.annual.balance')

#_________________________________________Busqueda de las variables utilizadas para el reporte_______________________________________________#
        for reporte in self.browse(cr, uid, ids, context=context):
            id = reporte.id              


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

        if reporte.reporte == 'bal':

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
#_________________________________________Consulta para sacar el reporte de Estado de resultados______________________________________________#                
        elif reporte.reporte == 'est':     
            ingresos = 0
            egresos = 0
            
            acc_ids = acc_obj.search(cr, uid, [('type','!=','view')])
            for cuenta in acc_obj.browse(cr, uid, acc_ids):
                balance = 0
                acumuladoi = 0
                acumuladoe = 0

                if int(reporte.mes) < 10:
                    mes = '0' + str(reporte.mes) + '/' + reporte.periodo.name
                else:
                    mes = str(reporte.mes) + '/' + reporte.periodo.name

                period_obj = self.pool.get('account.period')
                #period_ids = period_obj.search(cr, uid, [('fiscalyear_id.name','=',reporte.periodo.name)])
                period_mes = period_obj.search(cr, uid, [('code','=',mes)])
                for m in period_obj.browse(cr, uid, period_mes):
                    month = m.id

                #if reporte.mensual == True:
                #    move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id),('period_id.code','=',mes)])
                #    move_acumulado = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id),('period_id.id','<',month)])
                #else:
                move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id)])
                
                for move in move_obj.browse(cr, uid, move_ids):
                    if reporte.mensual == True:
                        if move.period_id.code == mes:
                            balance += move.debit - move.credit          
                #for move_a in move_obj.browse(cr, uid, move_acumulado):       
                    if str(move.account_id.parent_id.code)[0:1] == '5' or str(move.account_id.parent_id.code)[0:2] == '92':
                        acumuladoi += move.debit - move.credit 

                    if str(move.account_id.parent_id.code)[0:1] == '6' or str(move.account_id.parent_id.code)[0:1] == '7' or str(move.account_id.parent_id.code)[0:1] == '8' or str(move.account_id.parent_id.code)[0:2] == '91':
                        acumuladoe += move.debit - move.credit 

                if round(balance, 2) != 0.0:              
                    if str(move.account_id.parent_id.code)[0:1] == '5' or str(move.account_id.parent_id.code)[0:2] == '92':
                        if len(est) == 0:
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                #3: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: 'Ingresos',
                                1: '',
                                2: '',
                                #3: ''
                            }
                            est.append(saldo)
                        saldo = {
                                0: move.account_id.name,
                                1: balance,
                                #2: acumuladoi,
                                2: 'I'
                            }
                        ingresos += balance
                        est.append(saldo)  
                    if str(move.account_id.parent_id.code)[0:1] == '6' or str(move.account_id.parent_id.code)[0:1] == '7' or str(move.account_id.parent_id.code)[0:1] == '8' or str(move.account_id.parent_id.code)[0:2] == '91':
                        for ad in est:
                            a = ad
                        if 'E' not in str(a[2]):
                            saldo = {
                                0: 'Suma Ingresos',
                                1: ingresos,
                                2: '',
                                #3: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                #3: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: 'Egresos',
                                1: '',
                                2: '',
                                #3: ''
                            }
                            est.append(saldo)
                        saldo = {
                                0: move.account_id.name,
                                1: balance,
                                #2: acumuladoe,
                                2: 'E'
                            }
                        egresos += balance
                        est.append(saldo)   

            saldo = {
                0: 'Suma Egresos',
                1: egresos,
                2: '',
                #3: ''
            }       
            est.append(saldo)
            

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
        elif reporte.reporte == 'est':
            com[0] = {0:report + " " + self._get_mes(cr, uid, reporte.mes, context) + ' ' + reporte.periodo.name, 1:company}
        else:    
            com[0] = {0:report, 1:self._get_mes(cr, uid, reporte.mes, context) , 2:reporte.periodo.name, 3:company}


# #______________________________________________________Creacion del archivo PDF_______________________________________________________________#


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
        
        size = 48
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

        elif reporte.reporte == 'est':
            cabeceras = {0:'Nombre',1:'Balance',2:'Acumulado'}
            for num in range(len(est)):
                row = sheet.row(num)
                fila = est[num]
                for col in range(0, 6):
                    colunm = sheet.col(col)
                    #if col == 2:
                    #    colunm.width = 32 * 30
                    #else:
                    colunm.width = 256 * 30 
                if num == 0:
                    fila = com[num]
                    for index, col in enumerate(fila):
                        comp = com[0]
                        if index == 0:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))#pattern: pattern solid, fore_color white;                             
                            row.height_mismatch = True
                            row.height = 90 * 30
                        elif index == 1:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))
                            row.height_mismatch = True
                            row.height = 90 * 30
                else:
                    for index, col in enumerate(cabeceras):
                        if num == 1:
                            cab = cabeceras[index]
                            #if index == 1:
                            #    cab = cabeceras[index+1]
                            #    row.write(index+2, cab, style=style)
                            #elif index == 0:
                            if index < 2:
                                row.write(index, cab, style=style)
                        elif num > 1:  
                            if index < 2:  
                                fila = est[num-2]
                                celda = fila[index]                
                            #for index, col in enumerate(fila):
                    #raise osv.except_osv(index, fila)
                            if index < 2:
                                if 'Ingreso' in str(celda) or 'Egreso' in str(celda):
                                    row.write(index, celda, style=style)
                                else: 
                                    row.write(index, celda)
                if num+2 == len(est):
                    row = sheet.row(num+2)
                    for index, col in enumerate(fila):
                        fila = est[num]
                        celda = fila[index]
                        if index < 2:
                            row.write(index, celda)

                if num+1 == len(est):
                    row = sheet.row(num+2)
                    for index, col in enumerate(fila):
                        fila = est[num]
                        celda = fila[index]
                        if index < 2:
                            if index == 0:
                                row.write(index, celda, style=style)
                            else:
                                row.write(index, celda)

        elif reporte.reporte == 'com':
            if reporte.mensual == True:
                for num in range(registros):
                    row = sheet.row(num)
                    fila = resultado[num]
                    for col in range(0, 7):
                        colunm = sheet.col(col)
                    #if col == 2:
                    #    colunm.width = 32 * 30
                    #else:
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
                                row.write(index, cab)
                            #row.write(index, cab[0])
                            elif num>1:    
                                fila = resultado[num-2]
                                celda = fila[index]
                                row.write(index, celda)
                    if num+2 == registros:
                        row = sheet.row(num+2)
                        for index, col in enumerate(fila):
                            fila = resultado[num]
                            celda = fila[index]
                            row.write(index, celda)        
                    if num+1 == registros:
                        row = sheet.row(num+2)
                        for index, col in enumerate(fila):
                            fila = resultado[num]
                            celda = fila[index]
                            row.write(index, celda)
            else:
                for num in range(registros):
                    row = libro1.row(num)
                    fila = resultado[num]
                    if num == 0:
                        fila = com[num]
                        for index, col in enumerate(fila):
                            colunm = libro1.col(col)
                            colunm.width = 256 * 30  
                        comp = com[0]
                        row.write(index, comp[col])
                    else:
                        for index, col in enumerate(fila):
                            if num == 1:
                                cab = cabeceras[index]
                                row.write(index, cab)
                        #row.write(index, cab[0])
                            elif num>1:    
                                fila = resultado[num-2]
                                celda = fila[index]
                                row.write(index, celda)
                    if num+2 == registros:
                        row = libro1.row(num+2)
                        for index, col in enumerate(fila):
                            fila = resultado[num]
                            celda = fila[index]
                            row.write(index, celda)        
                    if num+1 == registros:
                        row = libro1.row(num+2)
                        for index, col in enumerate(fila):
                            fila = resultado[num]
                            celda = fila[index]
                            row.write(index, celda)
   

            # for num in range(len(bal1)):
            #     row = sheet.row(num+2)
            #     fila = bal1[num]
            #     for index, col in enumerate(fila):
            #         fila = bal1[num]
            #         celda = fila[index]
            #         if index < 2:
            #             if 'Suma' in str(fila[0]):
            #                 row = sheet.row(32)
            #                 if index == 0:
            #                     row.write(index + 3, celda, style=style)
            #                 else:
            #                     row.write(index + 3, celda)
            #             elif 'Pasivo' in str(celda) or 'Capital' in str(celda):
            #                 row.write(index + 3, celda, style=style)
            #             else: 
            #                 row.write(index+3, celda)

        fp = StringIO.StringIO()
        book.save(fp)
        fp.seek(0)        
        data = fp.read()
        fp.close()
        out = base64.encodestring(data)
        book.save('tmp/Excel.pdf')

        this = self.browse(cr, uid, ids, context=context)[0]

        if 'Balance General' in report:
            filename = report + " " + reporte.periodo.name
        else: 
            filename = report + " " + self._get_mes(cr, uid, reporte.mes, context) + " " + reporte.periodo.name

        extension = "xls"#this.format

        name = "%s.%s" % (filename, extension)
        this.write({'binario': out, 'name': name})

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

