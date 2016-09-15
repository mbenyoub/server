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
        pasivo = 0
        capital = 0
        pasivocapital = 0
        activo_end = 0
        pasivo_end = 0
        capital_end = 0
        pasivocapital_end = 0
        saldo = {}
        bal1 = []
        est = []
        balanza = []

        company = self.pool.get('res.company')
        acc_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move.line')
        balanza_obj = self.pool.get('account.annual.balance')
        budget_obj = self.pool.get('account_budget_post')
        cross_obj = self.pool.get('crossovered_budget_lines')

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
                    query = ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(debit, credit, balance, reporte.periodo_init.name,(int(reporte.nivel))))               
                    cr.execute("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(debit, credit, balance, reporte.periodo_init.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = {0:'Codigo', 1:'Cuenta',2:'Nivel',3:'Saldo inicial',4:'Cargo',5:'Abono',6:'Saldo Final'}#cr.description
                elif reporte.mensual == False:  
                    query = ("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(reporte.periodo_init.name,(int(reporte.nivel))))                                   
                    cr.execute("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s"%(reporte.periodo_init.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = cr.description
        elif reporte.cero == False:
            if reporte.reporte == 'com':
                if reporte.mensual == True:
                    query = ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (%s) != 0"%(debit, credit, balance, reporte.periodo_init.name,(int(reporte.nivel)), balance))                    
                    cr.execute ("select account_code, account_name, account_level, initial_balance, %s, %s, %s from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (%s) != 0"%(debit, credit, balance, reporte.periodo_init.name,(int(reporte.nivel)), balance))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = {0:'Codigo', 1:'Cuenta',2:'Nivel',3:'Saldo inicial',4:'Cargo',5:'Abono',6:'Saldo Final'}#cr.description
                elif reporte.mensual == False:    
                    query = ("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (balance1 + balance2 + balance3 + balance4 + balance5 + balance6 + balance7 + balance8 + balance9 + balance10 + balance11 + balance12) != 0"%(reporte.periodo_init.name,(int(reporte.nivel))))
                    cr.execute("select account_code, account_name, account_level, initial_balance, debit1, credit1, balance1, debit2, credit2, balance2, debit3, credit3, balance3, debit4, credit4, balance4, debit5, credit5, balance5, debit6, credit6, balance6, debit7, credit7, balance7, debit8, credit8, balance8, debit9, credit9, balance9, debit10, credit10, balance10, debit11, credit11, balance11, debit12, credit12, balance12 from account_annual_balance where fiscalyear = cast(%s as text) and account_level <= %s and (balance1 + balance2 + balance3 + balance4 + balance5 + balance6 + balance7 + balance8 + balance9 + balance10 + balance11 + balance12) != 0"%(reporte.periodo_init.name,(int(reporte.nivel))))
                    resultado = cr.fetchall()
                    registros = cr.rowcount
                    cabeceras = cr.description

        #raise osv.except_osv(resultado, registros)

#_________________________________________Consulta para sacar el reporte de Balance General_________________________________________________#                    

        if reporte.reporte == 'bal':

            acc_ids = acc_obj.search(cr, uid, [('type','!=','view')])
            for cuenta in acc_obj.browse(cr, uid, acc_ids):

                balance = 0
                balance_end = 0
                if reporte.movimiento == 1:
                    move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_init.name),('account_id.id','=',cuenta.id)])
                else:
                    move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_init.name),('account_id.id','=',cuenta.id),('state','!=','draft')])
                for move in move_obj.browse(cr, uid, move_ids):
                    balance += move.debit - move.credit

                if reporte.movimiento == 1:
                    move1_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_end.name),('account_id.id','=',cuenta.id)])
                else:
                    move1_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_end.name),('account_id.id','=',cuenta.id),('state','!=','draft')])
                for move1 in move_obj.browse(cr, uid, move1_ids):
                    balance_end += move1.debit - move1.credit

                if round(balance, 2) != 0.0 or round(balance_end, 2) != 0.0:
                    if str(move.account_id.parent_id.code)[0:2] == '11': 
                        if len(bal) == 0:
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Activo Circulante',
                                1: reporte.periodo_init.name,
                                2: reporte.periodo_end.name,
                                3:''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2),
                            2: 'AC',
                            3: round(balance_end, 2),
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '11':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2),
                            2: 'AC',
                            3: round(balance_end, 2),
                        }
                    elif str(move.account_id.parent_id.code)[0:2] == '12':
                        for af in bal:
                            a = af
                        if 'AF' not in str(a[2]):
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Activo Fijo',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2),
                            2: 'AF',
                            3: round(balance_end, 2),
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '12':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2),
                            2: 'AF',
                            3: round(balance_end, 2),
                        }
                #     bal.append(saldo) 
                    elif str(move.account_id.parent_id.code)[0:2] == '13':
                        for ad in bal:
                            a = ad
                        if 'AD' not in str(a[2]):
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Activo Diferido',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2),
                            2: 'AD',
                            3: round(balance_end, 2),
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '13':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2),
                            2: 'AD',
                            3: round(balance_end, 2),
                        }
                #     bal.append(saldo)  
                    elif str(move.account_id.parent_id.code)[0:2] == '21':
                        for ad in bal:
                            a = ad
                        if 'PC' not in str(a[2]):
                            saldo = {
                                0: '    Total Activo',
                                1: activo,
                                2: '',
                                3: activo_end
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: 'Pasivo',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Pasivo Corto Plazo',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PC',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '21':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PC',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move.account_id.parent_id.code)[0:2] == '22':
                        for ad in bal:
                            a = ad
                        if 'PO' not in str(a[2]):
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Pasivo Corto Plazo(Otros)',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PO',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '22':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PO',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move.account_id.parent_id.code)[0:2] == '25':
                        for ad in bal:
                            a = ad
                        if 'PL' not in str(a[2]):
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '    Pasivo Largo Plazo',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PL',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move1.account_id.parent_id.code)[0:2] == '25':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'PL',
                            3: round(balance_end, 2) * -1,
                        }
                    elif str(move.account_id.parent_id.code)[0:1] == '3':
                        for ad in bal:
                            a = ad
                        if 'CT' not in str(a[2]):
                            saldo = {
                                0: '    Total Pasivo',
                                1: pasivo,
                                2: '',
                                3: pasivo_end
                            }
                            bal.append(saldo)
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                            saldo = {
                                0: 'Patrimonio',
                                1: '',
                                2: '',
                                3: ''
                            }
                            bal.append(saldo)
                        saldo = {
                            0: move.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'CT',
                            3: round(balance_end, 2) * -1,
                        }
                    
                    elif str(move1.account_id.parent_id.code)[0:2] == '3':
                        saldo = {
                            0: move1.account_id.name,
                            1: round(balance, 2) * -1,
                            2: 'CT',
                            3: round(balance_end, 2) * -1,
                        }

       
                    if 'AC' in str(saldo[2]) or 'AF' in str(saldo[2]) or 'AD' in str(saldo[2]):
                        activo += saldo[1]
                        activo_end += saldo[3]
                        bal.append(saldo)

                    elif 'PC' in str(saldo[2]) or 'PO' in str(saldo[2]) or 'PL' in str(saldo[2]) or 'CT' in str(saldo[2]):
                        if 'PC' in str(saldo[2]) or 'PO' in str(saldo[2]) or 'PL' in str(saldo[2]):
                            pasivo += saldo[1]
                            pasivo_end += saldo[3]
                        elif 'CT' in str(saldo[2]):
                            for a in bal:
                                aa = a
                            if  'UTILIDADES DE EJERCICIOS ANTERIORES' not in str(aa[0]):
                                capital += saldo[1]
                                capital_end += saldo[3]
                        for a in bal:
                            aa = a
                        if  'UTILIDADES DE EJERCICIOS ANTERIORES' not in str(aa[0]):
                            pasivocapital += saldo[1]
                            pasivocapital_end += saldo[3]
                            bal.append(saldo)

            saldo = {
                0: '    Total Patrimonio',
                1: capital,
                2: '',
                3: capital_end
            }
            bal.append(saldo)
            saldo = {
                0: 'Suma Pasivo mas Capital',
                1: pasivocapital,
                2: '',
                3: pasivocapital_end
            }
            bal.append(saldo)

            #raise osv.except_osv('bal', bal)
#_________________________________________Consulta para sacar el reporte de Estado de resultados______________________________________________#                
        elif reporte.reporte == 'est':     
            ingresos = 0
            egresos = 0
            ingresos_end = 0
            egresos_end = 0
            acum_i = 0
            acum_i_end = 0
            acum_e = 0
            acum_e_end = 0
            presupuesto_i = 0
            presupuesto_e = 0
            presi = 0
            prese = 0
            vari = 0
            vare = 0

            acc_ids = acc_obj.search(cr, uid, [('type','!=','view')])
            for cuenta in acc_obj.browse(cr, uid, acc_ids):
                balance = 0
                balance_end = 0
                acumuladoi = 0
                acumuladoe = 0
                acumuladoi_end = 0
                acumuladoe_end = 0
                p = 0

                if int(reporte.mes) < 10:
                    mes = '0' + str(reporte.mes) + '/' + reporte.periodo_init.name
                    mes_end = '0' + str(reporte.mes) + '/' + reporte.periodo_end.name
                else:
                    mes = str(reporte.mes) + '/' + reporte.periodo_init.name
                    mes_end = str(reporte.mes) + '/' + reporte.periodo_init.name

                period_obj = self.pool.get('account.period')
                #period_ids = period_obj.search(cr, uid, [('fiscalyear_id.name','=',reporte.periodo.name)])
                period_mes = period_obj.search(cr, uid, [('code','=',mes)])
                for m in period_obj.browse(cr, uid, period_mes):
                    month = m.id

                #if reporte.mensual == True:
                #    move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id),('period_id.code','=',mes)])
                #    move_acumulado = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo.name),('account_id.id','=',cuenta.id),('period_id.id','<',month)])
                #else:
                #budget_ids = budget_obj.search(cr, uid, [('account_id.id','=',cuenta.id)])
                cr.execute("""select planned_amount from account_budget_rel t0 inner join account_budget_post t1 on t0.budget_id = t1.id inner join crossovered_budget_lines t2 on t2.general_budget_id = t1.id where t0.account_id = %s""" % (cuenta.id))
                presupuesto  = cr.fetchall()

                move_ids = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_init.name),('account_id.id','=',cuenta.id)])
                move_ids1 = move_obj.search(cr, uid, [('period_id.fiscalyear_id.name','=',reporte.periodo_end.name),('account_id.id','=',cuenta.id)])

                for pres in presupuesto:
                    p = float(pres[0])

                for move in move_obj.browse(cr, uid, move_ids):
                    if reporte.mensual == True:
                        if move.period_id.code == mes:
                            balance += move.debit - move.credit          
                #for move_a in move_obj.browse(cr, uid, move_acumulado):       
                    if str(move.account_id.parent_id.code)[0:1] == '5' or str(move.account_id.parent_id.code)[0:2] == '92':
                        if int(str(move.period_id.code)[0:2]) >= int(reporte.mes):
                            acumuladoi += move.debit - move.credit 

                    if str(move.account_id.parent_id.code)[0:1] == '6' or str(move.account_id.parent_id.code)[0:1] == '7' or str(move.account_id.parent_id.code)[0:1] == '8' or str(move.account_id.parent_id.code)[0:2] == '91':
                        if int(str(move.period_id.code)[0:2]) >= int(reporte.mes):
                            acumuladoe += move.debit - move.credit 

                for move1 in move_obj.browse(cr, uid, move_ids1):
                    if reporte.mensual == True:
                        if move1.period_id.code == mes_end:
                            balance_end += move1.debit - move1.credit          
                #for move_a in move_obj.browse(cr, uid, move_acumulado):       
                    if str(move1.account_id.parent_id.code)[0:1] == '5' or str(move1.account_id.parent_id.code)[0:2] == '92':
                        if int(str(move1.period_id.code)[0:2]) <= int(reporte.mes):
                            acumuladoi_end += move1.debit - move1.credit 

                    if str(move1.account_id.parent_id.code)[0:1] == '6' or str(move1.account_id.parent_id.code)[0:1] == '7' or str(move1.account_id.parent_id.code)[0:1] == '8' or str(move1.account_id.parent_id.code)[0:2] == '91':
                        if int(str(move1.period_id.code)[0:2]) <= int(reporte.mes):
                            acumuladoe_end += move1.debit - move1.credit 

                if round(acumuladoi_end, 2) != 0.0 or round(acumuladoe_end, 2) != 0.0:              
                    if str(move.account_id.parent_id.code)[0:1] == '5' or str(move.account_id.parent_id.code)[0:2] == '92':
                        if len(est) == 0:
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: '',
                                4: '',
                                5: '',
                                6: '',
                                7:'',
                                8:'',
                                9:'',
                                10:'',
                                11:'',
                                12:'',
                                13: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: 'Ingresos',
                                1: '',
                                2: '',
                                3: '',
                                4: '',
                                5: '',
                                6: '',
                                7:'',
                                8:'',
                                9:'',
                                10:'',
                                11:'',
                                12:'',
                                13: ''
                            }
                            est.append(saldo)
                        if p > 0:
                            presi += balance_end
                        saldo = {
                                0: move.account_id.name,
                                1: balance_end * -1,
                                2: '',#acumuladoi,
                                6: '',
                                3: p,#balance,
                                4: '',
                                5: (balance_end * -1) - p,
                                7: acum_i + acum_i_end,
                                8:'',
                                9: p,
                                10:'',
                                11: (acum_i + acum_i_end) - p,
                                12:'',
                                13: 'I'
                            }

                        vari += (balance_end * -1) - p
                        presupuesto_i += p    
                        ingresos += balance_end
                        acum_i += acumuladoi
                        acum_i_end += acumuladoi_end
                        ingresos_end += balance_end
                        est.append(saldo)  
                    if str(move.account_id.parent_id.code)[0:1] == '6' or str(move.account_id.parent_id.code)[0:1] == '7' or str(move.account_id.parent_id.code)[0:1] == '8' or str(move.account_id.parent_id.code)[0:2] == '91':
                        for ad in est:
                            a = ad
                        if 'E' not in str(a[13]):
                            saldo = {
                                0: 'Total',
                                1: ingresos*-1,
                                2: '100.00%',#acum_i
                                4: '100.00%',#str(round(100/(presupuesto_i/presi),2)*-1)+'%',#acum_i_end,
                                3: presupuesto_i,#ingresos_end,
                                5: vari,
                                6: str(round(100/(presupuesto_i/presi),2)*-1)+'%',
                                7: ingresos_end,
                                8: '100.00%',
                                9:'',
                                10:'',
                                11:'',
                                12:'',
                                13: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: '',
                                1: '',
                                2: '',
                                3: '',
                                4: '',
                                5: '',
                                6: '',
                                7:'',
                                8:'',
                                9:'',
                                10:'',
                                11:'',
                                12:'',
                                13: ''
                            }
                            est.append(saldo)
                            saldo = {
                                0: 'Egresos',
                                1: '',
                                2: '',
                                3: '',
                                4: '',
                                5: '',
                                6: '',
                                7:'',
                                8:'',
                                9:'',
                                10:'',
                                11:'',
                                12:'',
                                13: ''
                            }
                            est.append(saldo)
                        if '-' in str(p):
                            saldo = {
                                    0: move.account_id.name,
                                    1: balance_end,
                                    2: '',#acumuladoe,
                                    6: '',
                                    3: p * -1,#balance,
                                    4: '',
                                    5: balance_end + p,
                                    7: acum_e + acum_e_end,
                                    8:'',
                                    9: p,
                                    10:'',
                                    11: (acum_e  + acum_e_end) - p,
                                    12:'',
                                    13: 'E'
                                }
                            vare += balance_end + p
                            presupuesto_e += (p * -1)
                        else:    
                            saldo = {
                                    0: move.account_id.name,
                                    1: balance_end,
                                    2: '',#acumuladoe,
                                    6: '',
                                    3: p,#balance,
                                    4: '',
                                    5: balance_end - p,
                                    7: acum_e + acum_e_end,
                                    8:'',
                                    9: p,
                                    10:'',
                                    11: (acum_e  + acum_e_end) - p,
                                    12:'',
                                    13: 'E'
                                }
                            vare += balance_end - p
                            presupuesto_e += p
                        if p > 0:
                            prese += balance_end
                        egresos += balance_end
                        acum_e += acumuladoe
                        acum_e_end += acumuladoe_end
                        egresos_end += balance_end + balance
                        est.append(saldo)   

            saldo = {
                0: 'Total',
                1: egresos,
                2: str(round(100/(ingresos/egresos),2)*-1)+'%',#acum_e,
                4: '100%',#str(round(100/(presupuesto_e+presupuesto_i/prese+presi),2)*-1)+'%',#acum_e_end,
                3: presupuesto_e,#egresos_end,
                5: vare,
                6: str(round(100/(presupuesto_e/prese),2)*-1)+'%',
                7: egresos_end,
                8: str(round(100/(ingresos_end/egresos_end),2)*-1)+'%',
                9:'',
                10:'',
                11:'',
                12:'',
                13: ''
            }       
            est.append(saldo)
            saldo = {
                0: '',
                1: '',
                2: '',
                3: '',
                4: '',
                5: '',
                6: '',
                7:'',
                8:'',
                9:'',
                10:'',
                11:'',
                12:'',
                13: ''
                            }
            est.append(saldo)
            saldo = {
                0: 'Utilidad o Perdida',
                1: ingresos + egresos,
                2: str(round(100/(ingresos/(ingresos+egresos)),2))+'%',#acum_i + acum_e,
                4: '',#acum_i_end + acum_e_end,
                3: '',#ingresos_end + egresos_end,
                5: '',
                6: '',
                7: ingresos_end + egresos_end,
                8: str(round(100/(ingresos_end/(ingresos_end+egresos_end)),2))+'%',
                9:'',
                10:'',
                11:'',
                12:'',
                13: ''
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
        elif reporte.reporte == 'flujo':
            report = 'Flujo de Efectivo'

        if reporte.reporte == 'bal':
            com[0] = {0:report + " " + reporte.periodo_init.name, 1: reporte.periodo_init.name + ' - '+ reporte.periodo_end.name, 2:company.browse(cr, uid, 1, context=context).name}
        elif reporte.reporte == 'est':
            com[0] = {0:report + " " + self._get_mes(cr, uid, reporte.mes, context) + ' ' + reporte.periodo_init.name, 1:company.browse(cr, uid, 1, context=context).name}
        elif reporte.reporte == 'com' and reporte.mensual == True:
            com[0] = {0:report + " " + self._get_mes(cr, uid, reporte.mes, context) + ' ' + reporte.periodo_init.name, 3:company.browse(cr, uid, 1, context=context).name}
        else:    
            com[0] = {0:report, 1:self._get_mes(cr, uid, reporte.mes, context) , 2:reporte.periodo_init.name, 3:company.browse(cr, uid, 1, context=context).name}


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

        #pattern
        pattern = xlwt.Pattern()
        pattern.solid = True
        pattern.fore_color = 'white'
        style.pattern = pattern
        
        size = 64,64
        im = Image.open(StringIO.StringIO(base64.b64decode(company.browse(cr, uid, 1, context=context).logo)))
        im.thumbnail(size, Image.ANTIALIAS)
        im.convert("RGB").save('tmp/logo.bmp')
        #sheet.insert_bitmap('tmp/logo.bmp', 0, 0, 0, 0)# )

######################################## Balance General ###############################################
        if reporte.reporte == 'bal':
            com[0] = {0:'Balance General'}
            cabeceras = {0:'Activo'}
            row = sheet.row(0)
            row.write(0,'')
            row = sheet.row(1)
            row.write(0,'')
            for num in range(len(bal)):
                row = sheet.row(num+1)
                fila = bal[num]
                for col in range(0, 6):
                    colunm = sheet.col(col)
                    if col == 1 or col == 2:
                        colunm.width = 256 * 30
                    elif col == 4:
                        colunm.width = 512 * 30
                    else:
                        colunm.width = 128 * 30 
                if num == 0:
                    fila = com[num]
                    for index, col in enumerate(fila):
                        comp = com[0]
                        if index == 0:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; pattern: pattern solid, fore_color white; align: wrap on, vert bottom, horiz left"))#pattern: pattern solid, fore_color white;                             
                            row.height_mismatch = True
                            row.height = 15 * 30
                        elif index == 2:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; pattern: pattern solid, fore_color white; align: wrap on, vert bottom, horiz left"))
                            row.height_mismatch = True
                            row.height = 15 * 30
                    row = sheet.row(num+2) 
                    row.write(index+1, company.browse(cr, uid, 1, context=context).partner_id.name, xlwt.easyxf("pattern: pattern solid, fore_color white;"))   
                    row = sheet.row(num+3) 
                    row.write(index+1, str(company.browse(cr, uid, 1, context=context).partner_id.street)+' '+str(company.browse(cr, uid, 1, context=context).partner_id.l10n_mx_street3), xlwt.easyxf("pattern: pattern solid, fore_color white;"))
                    row = sheet.row(num+4) 
                    row.write(index+1, company.browse(cr, uid, 1, context=context).partner_id.street2, xlwt.easyxf("pattern: pattern solid, fore_color white;"))                       
                    row = sheet.row(num+5) 
                    row.write(index+1, str(company.browse(cr, uid, 1, context=context).partner_id.zip)+' - '+str(company.browse(cr, uid, 1, context=context).partner_id.l10n_mx_city2), xlwt.easyxf("pattern: pattern solid, fore_color white;"))
                else:
                    row = sheet.row(num+6)
                    for index, col in enumerate(fila):
                        if num == 1:
                            if index == 0:
                                cab = cabeceras[index]
                                row.write(index+1, cab, xlwt.easyxf("font: name Arial, height 200, bold on;"))#, style=style)
                        elif num > 1:    
                            fila = bal[num-2]
                            celda = fila[index]         
            #                 #for index, col in enumerate(fila):
            #         #raise osv.except_osv(index, fila)
                            if index < 4:
                                if 'Activo' in str(celda) or 'Pasivo' in str(celda) or 'Patrimonio' in str(celda):
                                    row.write(index+1, celda, xlwt.easyxf("font: name Arial, height 200, bold on;"))#, style=style)
                                    if 'Circulante' in str(celda):
                                        row.write(index+5, fila[2])
                                else:
                                    if index == 1:
                                        row.write(index+3, celda)#, xlwt.easyxf("pattern: pattern solid, fore_color white;")
                                    elif index == 3 and len(str(celda)) != 0:
                                        row.write(index+2, celda)
                                    elif index == 0:
                                        row.write(index+2, celda)

                if num+2 == len(bal):
                    row = sheet.row(num+8)
                    for index, col in enumerate(fila):
                        fila = bal[num]
                        celda = fila[index]
                        if index < 4:
                            if index == 0:
                                row.write(index+1, celda, xlwt.easyxf("font: name Arial, height 200, bold on;"))#, style=style)
                            elif index == 3 and len(str(celda)) != 0:
                                row.write(index+2, celda)
                            elif index == 1:
                                row.write(index+3, celda)

                if num+1 == len(bal):
                    row = sheet.row(num+8)
                    for index, col in enumerate(fila):
                        fila = bal[num]
                        celda = fila[index]
                        row = sheet.row(num+9)
                        if index < 4:
                            if index == 0:
                                row.write(index+1, celda, xlwt.easyxf("font: name Arial, height 200, bold on;"))#, style=style)
                            elif index == 3 and len(str(celda)) != 0:
                                row.write(index+2, celda)
                            elif index == 1:
                                row.write(index+3, celda)

            # for num in range(len(bal1)):
            #     row = sheet.row(num+4)
            #     fila = bal1[num]
            #     for index, col in enumerate(fila):
            #         fila = bal1[num]
            #         celda = fila[index]
            #         if index < 2:
            #             if 'Suma' in str(fila[0]):
            #                 row = sheet.row(num+5)
            #                 if index == 0:
            #                     row.write(index + 3, celda, style=style)
            #                 else:
            #                     row.write(index + 3, celda)
            #             elif 'Pasivo' in str(celda) or 'Capital' in str(celda):
            #                 row.write(index + 3, celda, style=style)
            #             else: 
            #                 row.write(index+3, celda)

        elif reporte.reporte == 'est':
            row = sheet.row(0)
            row.write(0,'')
            row = sheet.row(1)
            row.write(0,'')
            cabeceras = {0:'Cambios en el patrimonio no restringido:',1:'Real',2:'%',3:'Presup',4:'%',5:'Variacion',6:'%',7:'Real',8:'%',9:'Presup',10:'%',11:'Variacion',12:'%'}
            conceptos = {0:'CONCEPTO',1:'',2:'',3:'MES',4:'',5:'',6:'',7:'',8:'',9:'ACUMULADO'}
            com[0] = {0:'Estado de Resultados',1:'Periodo',2:self._get_mes(cr, uid, reporte.mes, context) + ' de ' + reporte.periodo_init.name,3:' a ',4:self._get_mes(cr, uid, reporte.mes, context) + ' de ' + reporte.periodo_end.name,5:'',6:''}
            for num in range(len(est)):
                row = sheet.row(num+2)
                fila = est[num]
                for col in range(0, 10):
                    colunm = sheet.col(col)
                    #if col == 2:
                    #    colunm.width = 32 * 30
                    #else:
                    if col == 0:
                        colunm.width = 256 * 30 
                    else:
                        colunm.width = 128 * 30 
                if num == 0:
                    fila = com[num]
                    for index, col in enumerate(fila):
                        comp = com[0]
                        #if index == 0:
                        row.write(index, comp[col], xlwt.easyxf("font: name Arial, height 200, color blue, bold on; align: wrap on, vert centre, horiz center"))#pattern: pattern solid, fore_color white;                             
                        row.height_mismatch = True
                        row.height = 20 * 30
                        #elif index == 1:
                        #    row.write(index, comp[col], xlwt.easyxf("font: name Arial, height 200, color blue, bold on; align: wrap on, vert centre, horiz center"))
                        #    row.height_mismatch = True
                        #    row.height = 30 * 30
                else:
                    for index, col in enumerate(conceptos):
                        if num == 1:
                            row = sheet.row(num+3)
                            row.write(index, conceptos[index], xlwt.easyxf("font: name Arial, height 200, color black, bold on; align: wrap on, vert centre, horiz center"))
                    for index, col in enumerate(est):
                        row = sheet.row(num+4)
                        if num == 1:
                            row.height_mismatch = True
                            row.height = 20 * 30
                            #if index == 1:
                            #    cab = cabeceras[index+1]
                            #    row.write(index+2, cab, style=style)
                            #elif index == 0:
                            if index < 13:
                                cab = cabeceras[index]
                                row.write(index, cab, xlwt.easyxf("font: name Arial, height 140, color black, bold on; align: wrap on, vert centre, horiz center"))#style=style)
                        elif num > 1:  
                            row = sheet.row(num+5)
                            if index < 13:  
                                fila = est[num-2]
                                celda = fila[index]                
                            #for index, col in enumerate(fila):
                    #raise osv.except_osv(index, fila)
                            if index < 13:
                                if 'Ingreso' in str(celda) or 'Egreso' in str(celda):
                                    row.write(index, celda, style=style)
                                else: 
                                    row.write(index, celda)
                if num+2 == len(est):
                    row = sheet.row(num+7)
                    for index, col in enumerate(fila):
                        fila = est[num]
                        celda = fila[index]
                        if index < 13:
                            row.write(index, celda)

                if num+1 == len(est):
                    row = sheet.row(num+7)
                    for index, col in enumerate(fila):
                        fila = est[num]
                        celda = fila[index]
                        if index < 13:
                            if index == 0:
                                row.write(index, celda, style=style)
                            else:
                                row.write(index, celda)

        elif reporte.reporte == 'com' and reporte.mensual == True:
            row = sheet.row(0)
            row.write(0,'')
            row = sheet.row(1)
            row.write(0,'')
            for num in range(registros):
                row = sheet.row(num+2)
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
                            row.height = 30 * 30
                        elif index == 2:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))
                            row.height_mismatch = True
                            row.height = 30 * 30
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
                    row = sheet.row(num+4)
                    for index, col in enumerate(fila):
                        fila = resultado[num]
                        celda = fila[index]
                        row.write(index, celda)        
                if num+1 == registros:
                    row = sheet.row(num+4)
                    for index, col in enumerate(fila):
                        fila = resultado[num]
                        celda = fila[index]
                        row.write(index, celda)

        elif reporte.reporte == 'com' and reporte.mensual == False:
            cabeceras = {
                0:'Codigo', 1:'Cuenta', 2:'Nivel', 3:'Saldo inicial', 
                4:'Cargo Enero', 5:'Abono Enero', 6:'Saldo Enero', 
                7:'Cargo Febrero', 8:'Abono Febrero', 9:'Saldo Febrero', 
                10:'Cargo Marzo', 11:'Abono Marzo', 12:'Saldo Marzo', 
                13:'Cargo Abril', 14:'Abono Abril', 15:'Saldo Abril', 
                16:'Cargo Mayo', 17:'Abono Mayo', 18:'Saldo Mayo', 
                19:'Cargo Junio', 20:'Abono Junio', 21:'Saldo Junio', 
                22:'Cargo Julio', 23:'Abono Julio', 24:'Saldo Julio', 
                25:'Cargo Agosto', 26:'Abono Agosto', 27:'Saldo Agosto', 
                28:'Cargo Septiembre', 29:'Abono Septiembre', 30:'Saldo Septiembre', 
                31:'Cargo Octubre', 32:'Abono Octubre', 33:'Saldo Octubre', 
                34:'Cargo Noviembre', 35:'Abono Noviembre', 36:'Saldo Noviembre', 
                37:'Cargo Diciembre', 38:'Abono Diciembre', 39:'Saldo Diciembre'}
            row = sheet.row(0)
            row.write(0,'')
            row = sheet.row(1)
            row.write(0,'')
            for num in range(registros):
                row = sheet.row(num+2)
                fila = resultado[num]
                for col in range(0, 40):
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
                            row.height = 30 * 30
                        elif index == 2:
                            row.write(index+1, comp[col], xlwt.easyxf("font: name Arial, height 280, color blue, bold on; align: wrap on, vert centre, horiz center"))
                            row.height_mismatch = True
                            row.height = 30 * 30
                    #for index, col in enumerate(fila):
                    #    colunm = sheet.col(col)
                    #    colunm.width = 256 * 30  
                    #    comp = com[0]
                    #    row.write(index, comp[col])
                else:
                    for index, col in enumerate(fila):
                        if num == 1:
                            cab = cabeceras[index]
                            row.write(index, cab)
                        elif num>1:    
                            fila = resultado[num-2]
                            celda = fila[index]
                            row.write(index, celda)
                if num+2 == registros:
                    row = sheet.row(num+4)
                    for index, col in enumerate(fila):
                        fila = resultado[num]
                        celda = fila[index]
                        row.write(index, celda)        
                if num+1 == registros:
                    row = sheet.row(num+4)
                    for index, col in enumerate(fila):
                        fila = resultado[num]
                        celda = fila[index]
                        row.write(index, celda)
   
            #f.read()
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
        if reporte.reporte == 'flujo':
            f = open('tmp/flujo_efectivo.xls', 'r')
            data = f.read()
        fp.close()
        out = base64.encodestring(data)
        book.save('tmp/Excel.pdf')

        this = self.browse(cr, uid, ids, context=context)[0]

        if 'Balance General' in report or (reporte.reporte == 'com' and reporte.mensual == False):
            filename = report + " " + reporte.periodo_init.name + " - " + reporte.periodo_end.name
        else: 
            filename = report + " " + self._get_mes(cr, uid, reporte.mes, context) + " " + reporte.periodo_init.name + " - " + reporte.periodo_end.name

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
        'reporte': fields.selection([('bal','Balance General'),('com','Balanza de comprobacion'),('est','Estados de resultados'),('flujo','Flujo Efectivo')], 'Reporte', required=True, help="Escoger el informe a exportar"),
        'nivel': fields.selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6')], 'Nivel', help="Escoger el nivel", size=30), 
        'periodo_init':fields.many2one('account.fiscalyear', 'Periodo Inicial'),
        'periodo_end':fields.many2one('account.fiscalyear', 'Periodo Final'),
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
        'periodo_init': '2',
        'periodo_end': '4',
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

