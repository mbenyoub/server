# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Saldaña (riss_600@hotmail.com)
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

from openerp.osv import osv, fields
from tools.translate import _
from string import upper
from string import join
import datetime
from dateutil.relativedelta import *
from openerp import pooler, tools
from openerp import netsvc
from openerp import release

import time
import doc_xml as xml

class account_sat_create_xml_report(osv.osv_memory):
    _name = 'account.sat.create.xml.report'
    _description = 'Account - XML REPORT'

    _columns = {
        'name': fields.char('Nombre del archivo', readonly=True),
        'company_id': fields.many2one('res.company', 'Compañia', required=True),
        'period_id': fields.many2one('account.period', 'Periodo', help='Seleccionar periodo'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio', help='Seleccionar ejercicio fiscal'),
        'account': fields.many2one('account.account.sat', 'Cuentas', help='Seleccionar cuenta'),
        'filename': fields.char('Nombre del archivo', size=128, readonly=True, help='Este es el nombre del archivo'),
        'file': fields.binary('Archivo', readonly=True),
        'state': fields.selection([
            ('choose', 'Escojer'), 
            ('get', 'Obtener'), 
            ('not_file', 'Sin archivo')]),
        'type': fields.selection([
            ('account', 'Plan de Cuentas'),
            ('balance_month', 'Balanza Mensual'),
            ('balance_year', 'Balanza Anual'),
            ('move', 'Polizas'),
            ('folios', 'Folios Fiscales'),
            ('mayor', 'Auxiliar cuentas de mayor')], string='Tipo Reporte', required=True),
        'date_ref': fields.date('Ultima modificacion', help="Fecha de la última modificación contable de la balanza de comprobación. Es requerido cuando el atributo TipoEnvio = C. Se convierte en requerido cuando se cuente con la información."),
        'send': fields.selection([('N', 'Normal'), ('C', 'Complementaria')], string='Tipo Envio', help="Atributo requerido para expresar el tipo de envío de la balanza (N-Normal; C-Complementaria)"),
        'solicitud': fields.selection([
            ('AF', 'Acto de Fiscalización'), 
            ('FC', 'Fiscalización Compulsa'), 
            ('DE', 'Devolución'),
            ('CO', 'Compensación')], string='Tipo de Solicitud', required=False),
        'orden': fields.char('Numero de Orden/Tramite', size=128, readonly=False, required=False, help='Este es el numero de la orden'),
    }

    _defaults = {
        'state': 'choose',
        'type': 'account',
        'send': 'N',
        'date_ref': fields.datetime.now,
        'solicitud': 'CO',
    }

    def default_get(self, cr, uid, fields, context=None):
        """
            Obtiene la compañia del usuario y el periodo anterior al actual
        """
        period_obj = self.pool.get('account.period')
        
        # Funcionalidad original
        data = super(account_sat_create_xml_report, self).default_get(cr, uid,
            fields, context=context)
        
        # Obtiene el id de la compañia por default
        company_id = self.pool.get('res.company')._company_default_get(cr, uid,
            'account.sat.create.xml.report', context=context)
        data.update({'company_id': company_id})
        
        # Busca el periodo sobre un mes anterior a la fecha actual
        time_now = datetime.date.today()+relativedelta(months=-1)
        period_ids = period_obj.search(cr, uid,
            [('date_start', '<=', time_now),
            ('date_stop', '>=', time_now),
            ('company_id', '=', company_id)])
        if period_ids:
            # Actualiza el periodo y el ejercicio
            period = period_obj.browse(cr, uid, period_ids[0], context=context)
            data.update({'period_id': period.id, 'fiscalyear_id': period.fiscalyear_id.id or False})
        return data
    
    def _get_fname_xml(self, cr, uid, id, context={}):
        """
            Obtiene el nombre del xml generado en base a los parametros establecidos
        """
        if not context:
            context = {}
        data = self.browse(cr, uid, id, context=context)
        fname_xml = 'Reporte-SAT '
        code = ''
        # Nombre para identificar el tipo de reporte XML generado
        if data.type == 'account':
            fname_xml = 'Plan-contable-SAT '
            code = 'CT'
        elif data.type == 'balance_month':
            fname_xml = 'Balanza-mensual-SAT '
            code = 'BN'
            if data.send == 'C':
                code = 'BC'
        elif data.type == 'balance_year':
            fname_xml = 'Balanza-anual-SAT '
            code = 'BN'
            if data.send == 'C':
                code = 'BC'
        elif data.type == 'move':
            fname_xml = 'Reporte-Polizas-SAT '
            code = 'PL'
        elif data.type == 'folios':
            fname_xml = 'Reporte-Folios Fiscales-SAT '
            code = 'XF'
        elif data.type == 'mayor':
            fname_xml = 'Reporte-Auxiliar cuentas de mayor-SAT '
            code = 'XC'

        # Agrega la referencia del RFC de la compañia
        fname_xml = "%s"%(xml.clearspace(data.company_id.partner_id.rfc))
        
        # Fecha por default
        dt = datetime.datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')

        # Obtiene fecha para referencia 
        if data.type == 'balance_year':
            dt = datetime.datetime.strptime(data.period_id.date_start, '%Y-%m-%d')
            # Agrega al nombre del xml el ejercicio y periodo
            fname_xml = "%s%s13"%(fname_xml,dt.strftime('%Y'))#, dt.strftime('%m'))#Correccion para mes del periodo
        elif data.type == 'balance_month' or data.type == 'move':
            dt = datetime.datetime.strptime(data.period_id.date_start, '%Y-%m-%d')
            # Agrega al nombre del xml el ejercicio y periodo
            fname_xml = "%s%s%s"%(fname_xml,dt.strftime('%Y'), dt.strftime('%m'))#Correccion para mes del periodo
        else:            
            dt = datetime.datetime.strptime(data.period_id.date_start, '%Y-%m-%d')
            # Agrega al nombre del xml el ejercicio y periodo en base a la fecha predefinida
            fname_xml = "%s%s%s"%(fname_xml,dt.strftime('%Y'), dt.strftime('%m'))#Correccion para mes del periodo

        # Agrega el codigo y la extension para el nombre del archivo
        fname_xml = "%s%s.xml"%(fname_xml,code)
        return fname_xml
    
    def _get_info_account_xml(self, cr, uid, period, company, context=None):
        """
            Crea Diccionario con la informacion general dle reporte XML para el plan de cuentas
        """
        dt = datetime.datetime.strptime(period.date_start, '%Y-%m-%d')
        
        # Genera diccionario con informacion principal de XML
        xml_data = {
            'Catalogo': {
                'xmlns:catalogocuentas': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/CatalogoCuentas',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/CatalogoCuentas http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/CatalogoCuentas/CatalogoCuentas_1_1.xsd',
                'Version': '1.1',
                'RFC': xml.clearspace(company.partner_id.rfc),
                'Mes': dt.strftime('%m'),
                'Anio': dt.strftime('%Y'),
                'Ctas': []
            }
        }
        return xml_data
    
    def _get_info_account_data(self, cr, uid, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        acc_obj = self.pool.get('account.account.sat')
        res = []
        # Obtiene la lista de cuentas del SAT
        acc_ids = acc_obj.search(cr, uid, [('active','=',True), ('parent_id','!=',1)], context=context)
        # Recorre las cuentas obtenidas
        for acc in acc_obj.browse(cr, uid, acc_ids, context=context):
            # Obtiene el numero de cuenta de la cuenta padre y el nivel
            code_parent = acc.parent_id.number if acc.parent_id else 'NA'
            level = '1' if acc.type == 'view' else '2'
            # Genera diccionario con informacion de la cuenta
            data = {
                'NumCta': acc.number,
                'Desc': acc.name,
                'SubCtaDe': code_parent,
                'Nivel': level,
                'Natur': acc.nature,
                'CodAgrup': acc.code
            }
            res.append(data)
        return res
    
    def generate_xml_account(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre plan de cuentas
        """
        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_account_xml(cr, uid, wizard.period_id, wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['Catalogo']['Ctas'] = self._get_info_account_data(cr, uid, context=context)
        
        print "************************** data dict ************** ", data_dict
        
        # Genera archivo XML
        xml_data = xml.dict2xml(data_dict, reference='catalogocuentas')
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data
    
    
    
    
    def _get_info_balance_xml(self, cr, uid, period=False, fiscalyear=False, company=False, context=None):
        """
            Crea Diccionario con la informacion general dle reporte XML para la balanza
        """
        if context is None:
            context = {}

        # Genera diccionario con informacion principal de XML
        xml_data = {
            'Balanza': {
                'xmlns:BCE': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/BalanzaComprobacion',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/BalanzaComprobacion http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/BalanzaComprobacion/BalanzaComprobacion_1_1.xsd',
                'Version': '1.1',
                'RFC': xml.clearspace(company.partner_id.rfc)
            }
        }
        
        # Valida si es el calculo de la balanza por periodo o anual segun los parametros y agrega los datos q le corresponden
        if period:
            dt = datetime.datetime.strptime(period.date_start, '%Y-%m-%d')
            dt2 = datetime.datetime.strptime(period.date_stop, '%Y-%m-%d')
            # Carga los datos que aplican sobre la balanza por periodo
            xml_data['Balanza']['Mes'] = dt.strftime('%m')
            xml_data['Balanza']['Anio'] = dt.strftime('%Y')
            xml_data['Balanza']['TipoEnvio'] = "N"
        elif fiscalyear:
            dt = datetime.datetime.strptime(fiscalyear.date_start, '%Y-%m-%d')
            xml_data['Balanza']['Anio'] = dt.strftime('%Y')
            xml_data['Balanza']['Mes'] = '13'#dt.strftime('%Y')
            xml_data['Balanza']['TipoEnvio'] = "N"

        # Revisa si viene en los parametros del context el parametro de TipoEnvio
        if context.get('TipoEnvio',False):
            xml_data['Balanza']['TipoEnvio'] = context.get('TipoEnvio','N')
            # Valida si trae la fecha de la ultima modificacion
            if context.get('FechaModBal',False):
                xml_data['Balanza']['FechaModBal'] = context.get('FechaModBal', dt.strftime('%Y-%m-%d'))

        # Agrega al diccionario el arreglo donde se estaran cargando las cuentas
        xml_data['Balanza']['Ctas'] = []
        return xml_data
    
    def _get_info_account_balance_data(self, cr, uid, period_id=False, fiscalyear_id=False, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        acc_obj = self.pool.get('account.account.sat')
        res = []
        # Obtiene la lista de cuentas del SAT
        acc_ids = acc_obj.search(cr, uid, [('active','=',True), ('parent_id','!=',1)], context=context)
        
        # Agrega a la referencia del context la informacion de los periodos y el ejercicio fiscal segun sea el caso
        ctx = context.copy()
        ctx['state'] = 'posted'
        if period_id:
            ctx['periods'] = [period_id]
        elif fiscalyear_id:
            ctx['fiscalyear'] = fiscalyear_id
        
        print "************* ctx ********* ", ctx

        # Recorre las cuentas obtenidas
        for acc in acc_obj.browse(cr, uid, acc_ids, context=ctx):
            print "************** acc *********** ", acc
            print "************** acc credit *********** ", acc.credit
            print "************** acc debit *********** ", acc.debit
            print "************** acc balance *********** ", acc.balance

            # Genera diccionario con informacion de la cuenta
            data = {
                'NumCta': acc.number,
                'SaldoIni': acc.balance_init,
                'Debe': acc.debit,
                'Haber': acc.credit,
                'SaldoFin': acc.balance_end
            }
            res.append(data)
        return res
    
    def generate_xml_balance_month(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre balanza mensual
        """
        if context is None:
            context = {}

        # Agrega en el context la referencia del Tipo de envio y la fecha de ultima modificacion en caso de ser complementaria
        if wizard.send == 'C':
            context.update({
                'TipoEnvio': wizard.send,
                'FechaModBal': wizard.date_ref
            })

        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_balance_xml(cr, uid, period=wizard.period_id, company=wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['Balanza']['Ctas'] = self._get_info_account_balance_data(cr, uid, period_id=wizard.period_id.id, context=context)
        print "************************** data dict ************** ", data_dict
        
        # Genera archivo XML
        xml_data = xml.dict2xml(data_dict, reference='BCE')
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data
    

    def generate_xml_balance_year(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre balanza anual
        """
        if context is None:
            context = {}

        # Agrega en el context la referencia del Tipo de envio y la fecha de ultima modificacion en caso de ser complementaria
        if wizard.send == 'C':
            context.update({
                'TipoEnvio': wizard.send,
                'FechaModBal': wizard.date_ref
            })

        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_balance_xml(cr, uid, fiscalyear=wizard.fiscalyear_id, company=wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['Balanza']['Ctas'] = self._get_info_account_balance_data(cr, uid, fiscalyear_id=wizard.fiscalyear_id.id, context=context)
        print "************************** data dict ************** ", data_dict
        
        # Genera archivo XML
        xml_data = xml.dict2xml(data_dict, reference='BCE')
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data
    
    ########################################################## Creacion de Polizas ###################################################
    def _get_info_move(self, cr, uid, wizard=False, period=False, fiscalyear=False, company=False, context=None):
        """
            Crea Diccionario con la informacion general del reporte XML para las polizas
        """
        if context is None:
            context = {}

            #Informacion del certificado de la empresa
        # cert_obj = self.pool.get('res.company.facturae.certificate')
        # cert_ids = cert_obj.search(cr, uid, [('active','=',True)], context=context)

        # for cert in cert_obj.browse(cr, uid, cert_ids, context=context):
        #     xml_data = {
        #         'noCertificado': cert.serial_number,
        #         'Certificado': cert.certificate_file,
        #     } 
        # Genera diccionario con informacion principal de XML
        xml_data = {
            'Polizas': {
                'xmlns:PLZ': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/PolizasPeriodo',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/PolizasPeriodo http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/PolizasPeriodo/PolizasPeriodo_1_1.xsd',
                'Version': '1.1',
                'RFC': xml.clearspace(company.partner_id.rfc)
            }
        }

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            xml_data['Polizas']['NumOrden'] = wizard.orden
        else:
            xml_data['Polizas']['NumTramite'] = wizard.orden

            # Valida si es el calculo de la balanza por periodo o anual segun los parametros y agrega los datos q le corresponden

        if period:
            dt = datetime.datetime.strptime(period.date_start, '%Y-%m-%d')
            dt2 = datetime.datetime.strptime(period.date_stop, '%Y-%m-%d')
            # Carga los datos que aplican sobre la balanza por periodo
            xml_data['Polizas']['Mes'] = dt.strftime('%m')
            xml_data['Polizas']['Anio'] = dt.strftime('%Y')
            xml_data['Polizas']['TipoSolicitud'] = wizard.solicitud
        elif fiscalyear:
            dt = datetime.datetime.strptime(fiscalyear.date_start, '%Y-%m-%d')
            xml_data['Polizas']['Anio'] = dt.strftime('%Y')
            xml_data['Polizas']['Mes'] = dt.strftime('%m')#'13'
            xml_data['Polizas']['TipoSolicitud'] = wizard.solicitud

        # Revisa si viene en los parametros del context el parametro de TipoEnvio
        if context.get('TipoSolicitud',False):
            xml_data['Polizas']['TipoSolicitud'] = wizard.solicitud
            # Valida si trae la fecha de la ultima modificacion
            if context.get('FechaModBal',False):
                xml_data['Polizas']['FechaModBal'] = context.get('FechaModBal', dt.strftime('%Y-%m-%d'))

        # Agrega al diccionario el arreglo donde se estaran cargando las cuentas
        xml_data['Polizas']['Poliza'] = []

        return xml_data

    def _get_info_account_move(self, cr, uid, period_id=False, fiscalyear_id=False, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        
        move_obj = self.pool.get('account.move')
        move_ln_obj = self.pool.get('account.move.line')

        res = []
        # Obtiene la lista de cuentas del SAT
        #raise osv.except_osv('res', period_id)
        move_ids = move_obj.search(cr, uid, [('period_id','=',period_id),('state','!=','draft')], context=context)
        # Agrega a la referencia del context la informacion de los periodos y el ejercicio fiscal segun sea el caso

        ctx = context.copy()
        ctx['state'] = 'posted'
        if period_id:
            ctx['periods'] = [period_id]
        elif fiscalyear_id:
            ctx['fiscalyear'] = fiscalyear_id
        
        print "************* ctx ********* ", ctx


        # Recorre las cuentas obtenidas
        #for acc in acc_obj.browse(cr, uid, acc_ids, context=ctx):
        #     print "************** acc *********** ", acc
        #     print "************** acc credit *********** ", acc.credit
        #     print "************** acc debit *********** ", acc.debit
        #     print "************** acc balance *********** ", acc.balance

        for move in move_obj.browse(cr, uid, move_ids, context=ctx):
            print "************** acc *********** ", move
            
            if move.narration == False:
                data = {
                    'NumUnIdenPol': move.id,
                    'Fecha': move.date,
                    'Concepto': move.name,
                    }
            else:
                data = {
                    'NumUnIdenPol': move.id,
                    'Fecha': move.date,
                    'Concepto': move.narration,
                    }

            res.append(data)
            move_ln_ids = move_ln_obj.search(cr, uid, [('move_id','=',move.id)], context=context)
            
            data['Transaccion'] = self._get_info_account_move_ln(cr, uid, move.id, move.reference, context)
            res.append(data['Transaccion'])#if len(data['Transaccion']) > 0:
            # for line in move_ln_obj.browse(cr, uid, move_ln_ids, context=ctx):
            #     print "************** acc *********** ", "************** acc *********** ", line
            #     print "************** acc credit *********** ", "************** acc *********** ", line.credit
            #     print "************** acc debit *********** ", "************** acc *********** ", line.debit
            #     # Genera diccionario con informacion de la cuenta
            #     data['Transaccion'] = {
            #         #'NumUnIdenPol':,
            #         #'Fecha':,
            #         #'Concepto':,
            #         #'DesCta':,
            #         #'DesCta': acc_name,
            #         'Concepto': line.name,
            #         #'NumCta': acc_number,
            #         #'NumCta': line.account_id,
            #         #'SaldoIni': line.balance_init,
            #         'Debe': line.debit,
            #         'Haber': line.credit,
            #         #'SaldoFin': acc.balance_end,
            #         }
            #     res.append(data['Transaccion'])
            #     #if type == 'Cheque'
                # lnsplit = str(line.account_id).split(',')[1]
                # lnid = str(lnsplit).split(')')[0]

                # acc_id = acc_obj.search(cr, uid, [('parent_right','=',lnid)],context=context)

                # acc = acc_obj.browse(cr, uid, acc_id, context=ctx)
                # if len(acc) > 0: 
                #     acc_name = acc[0].name
                #     acc_number = acc[0].number 
            
            #raise osv.except_osv(data['Transaccion'], res)
        return res

    def _get_info_account_move_ln(self, cr, uid, move_id, reference, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        move_ln_obj = self.pool.get('account.move.line')
        acc_obj = self.pool.get('account.account.sat')
        act_obj = self.pool.get('account.account')
        vou_obj = self.pool.get('account.voucher')
        inv_obj = self.pool.get('account.invoice')
        resln = []
        move_ln_ids = move_ln_obj.search(cr, uid, [('move_id','=',move_id)], context=context)
        acc_ids = acc_obj.search(cr, uid, [('active','=',True), ('parent_id','!=',1)], context=context)

        ctx = context.copy()
        ctx['state'] = 'posted'
        
        print "************* ctx ********* ", ctx
  
        #raise osv.except_osv(move_ln_ids, move_id)
        for line in move_ln_obj.browse(cr, uid, move_ln_ids, context=context):
            print "************** acc *********** ", line
            print "************** acc credit *********** ",line.credit
            print "************** acc debit *********** ",line.debit
            print "************** acc debit *********** ",line.ref
                # Genera diccionario con informacion de la cuenta
                #if type == 'Cheque'    
            #lnsplit = str(line.account_id).split(',')[1]
            lnid = line.account_id.id#str(lnsplit).split(')')[0]

            act_id = act_obj.search(cr, uid, [('id','=',lnid)], context=context)
            actln = act_obj.browse(cr, uid, act_id, context=ctx)
            #raise osv.except_osv(range(actln[0].account_sat_id), actln)
            if range(actln[0].account_sat_id) != []:
                #raise osv.except_osv(actln[0].account_sat_id, lnid)
                #actsplit = str(actln[0].account_sat_id).split(',')[1]
                act_sat = actln[0].account_sat_id.id#str(actsplit).split(')')[0]

                acc_id = acc_obj.search(cr, uid, [('id','=',act_sat)],context=context)
                acc = acc_obj.browse(cr, uid, acc_id, context=ctx)

            #raise osv.except_osv(acc, act_sat)
                if len(acc) > 0: 
                    acc_name = acc[0].name
                    acc_number = acc[0].number
            else:
                acc_name = 'Estandar'
                acc_number = '000-000-000'

            data = {
                #'NumUnIdenPol':,
                #'Fecha':,
                #'Concepto':,
                'DesCta': acc_name,
                'Concepto': line.name,
                'NumCta': acc_number,
                #'SaldoIni': line.balance_init,
                'Debe': line.debit,
                'Haber': line.credit,
                    #'SaldoFin': acc.balance_end,
                    }
            resln.append(data)
            #raise osv.except_osv(enumerareference),reference.id)
            #try:
                #raise osv.except_osv('res', str(reference))
            if 'invoice' in str(reference) and line.debit > 0:
                #inv_split = reference.split(',')[1]
                inv_id = reference.id#str(inv_split).split(')')[0]
                data['CompNal'] = self._get_info_move_compnal(cr, uid, inv_id, context)
                resln.append(data['CompNal'])
            elif 'voucher' in str(reference) and line.debit > 0: #and 'COMPRA/' in line.name or 'VENT/' in line.name or '/' in line.name:
                #vou_split = reference.split(',')[1] 
                vou_id = reference.id#str(vou_split).split(')')[0]

                vou_ids = vou_obj.search(cr, uid, [('id','=',vou_id)])

                for voucher in vou_obj.browse(cr, uid, vou_ids, context=context):
                    vou_id = voucher.id
                    if voucher.invoice_id.id != False:
                        inv_ids = inv_obj.search(cr, uid, [('id','=',voucher.invoice_id.id)])
                        #for invoice in inv_obj.browse(cr, uid, inv_ids, context=context): 
                    #-no-elif 'Efectivo' in str(invoice.pay_method_id.name):
                        #-no-data['CompNal'] = self._get_info_move_pago(cr, uid, inv_id, context)
                        #-no-resln.append(data['CompNal']) 
                            #if voucher.pay_method_id.id == 2:
                            #    data['Transferencia'] = self._get_info_move_pago(cr, uid, invoice, voucher, context)
                            #    resln.append(data['Transferencia']) 
                            #elif voucher.pay_method_id.id == 3:#'Cheque' in str(invoice.pay_method_id.name):#'Transferencia' in str(invoice.pay_method_id.name):                            
                            #    data['Cheque'] = self._get_info_move_pago(cr, uid, invoice, voucher, context)
                            #    resln.append(data['Cheque'])
                            #else:
                            #    data['OtrMetodoPago'] = self._get_info_move_pago(cr, uid, invoice, voucher, context)
                            #    resln.append(data['OtrMetodoPago'])
            #except UnicodeEncodeError:
            #    pass
                    #raise osv.except_osv(invoice.amount_total, invoice.pay_method_id.name)

        return resln

    def _get_info_move_compnal(self, cr, uid, inv_id, context=None):
        inv_obj = self.pool.get('account.invoice')
        inv_ids = inv_obj.search(cr,uid, [('id','=',inv_id)],context=context)
        partner_obj = self.pool.get('res.partner')
        res = []

        for inv in inv_obj.browse(cr, uid, inv_ids, context=context):
            part_ids = partner_obj.search(cr, uid, [('id','=',inv.partner_id.id)])
            for partner in partner_obj.browse(cr, uid, part_ids, context=context):
                rfc = partner.rfc
            if inv.cfdi_folio_fiscal != False:
                data = {
                    'UUID_CFDI': inv.cfdi_folio_fiscal,
                    'RFC': partner.rfc,
                    'MontoTotal': inv.amount_total,
                        }
                res.append(data)

        return res

    def _get_info_move_pago(self, cr, uid, invoice, voucher, context=None):
        #inv_obj = self.pool.get('account.invoice')
        #inv_ids = inv_obj.search(cr,uid, [('id','=',inv_id)],context=context)
        #partner_obj = self.pool.get('res.partner')
        act_obj = self.pool.get('account.account')
        act_ids = act_obj.search(cr, uid, [('id','=',voucher.journal_id.account_transit.id)], context=context)
        res = []
        #for vou in voucher:
        #    pago = vou

        #for inv in invoice:#inv_obj.browse(cr, uid, inv.id, context=context):
            #part_ids = partner_obj.search(cr, uid, [('id','=',inv.partner_id.id)])
            #for partner in partner_obj.browse(cr, uid, part_ids, context=context):
            #    rfc = partner.rfc
        if int(invoice.pay_method_id.id) < 10:
            pay = '0'+str(invoice.pay_method_id.id)

        if voucher.pay_method_id.id == 2:
            for act in act_obj.browse(cr,uid, act_ids, context=context):
                id = act.id
            data = {
                'CtaOri': voucher.cta_orig,#pay,
                'BancoOriNal': voucher.bnk_orig,
                'CtaDest': voucher.cta_des,
                'BancoDestNal': voucher.bnk_des,#voucher.account_id.code,
                'Fecha': voucher.date,
                'Benef': voucher.partner_id.name[0:20],
                'RFC': voucher.partner_id.rfc,
                'Monto':voucher.amount,
                    }
            res.append(data)
        elif voucher.pay_method_id.id == 3:
            for act in act_obj.browse(cr,uid, act_ids, context=context):
                id = act.id
            data = {
                'CtaOri': voucher.cta_orig,#pay,
                'Num': voucher.num_cqe,
                'BanEmisNal': voucher.ban_emi,#voucher.account_id.code,
                'Fecha': voucher.date,
                'Benef': voucher.partner_id.name[0:20],
                'RFC': voucher.partner_id.rfc,
                'Monto':voucher.amount,
                    }
            res.append(data)
        else:
            data = {
                'MetPagoPol': pay,
                'Fecha': voucher.date,
                'Benef': voucher.partner_id.name[0:20],
                'RFC': voucher.partner_id.rfc,
                'Monto':voucher.amount,
                    }
            res.append(data)

        return res

    def generate_xml_move(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre balanza anual
        """
        if context is None:
            context = {}
                    
        # Agrega en el context la referencia del Tipo de envio y la fecha de ultima modificacion en caso de ser complementaria
        if wizard.send == 'C':
            context.update({
                'TipoEnvio': wizard.send,
                'FechaModBal': wizard.date_ref,
                'TipoSolicitud': wizard.solicitud,
            })

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            context.update({
                'NumOrden': wizard.orden,
            })
        else:
            context.update({
                'NumTramite': wizard.orden,
            })
        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_move(cr, uid, wizard=wizard, period=wizard.period_id, company=wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['Polizas']['Poliza'] = self._get_info_account_move(cr, uid, period_id=wizard.period_id.id, context=context)
        print "************************** data dict ************** ", data_dict

        # Genera archivo XML
         
        #try:
        xml_data = xml.dict2xml(data_dict, reference='PLZ')
        
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data
        #except UnicodeEncodeError:
        #    pass

    def _get_info_folios(self, cr, uid, wizard=False, period=False, fiscalyear=False, company=False, context=None):
        """
            Crea Diccionario con la informacion general del reporte XML para las polizas
        """
        if context is None:
            context = {}

            #Informacion del certificado de la empresa
        # cert_obj = self.pool.get('res.company.facturae.certificate')
        # cert_ids = cert_obj.search(cr, uid, [('active','=',True)], context=context)

        # for cert in cert_obj.browse(cr, uid, cert_ids, context=context):
        #     xml_data = {
        #         'noCertificado': cert.serial_number,
        #         'Certificado': cert.certificate_file,
        #     } 
        # Genera diccionario con informacion principal de XML
        xml_data = {
            'RepAuxFol': {
                'xmlns:RepAux': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarFolios',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarFolios http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarFolios/AuxiliarFolios_1_2.xsd',
                'Version': '1.2',
                'RFC': xml.clearspace(company.partner_id.rfc)
            }
        }

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            xml_data['RepAuxFol']['NumOrden'] = wizard.orden
        else:
            xml_data['RepAuxFol']['NumTramite'] = wizard.orden

            # Valida si es el calculo de la balanza por periodo o anual segun los parametros y agrega los datos q le corresponden

        if period:
            dt = datetime.datetime.strptime(period.date_start, '%Y-%m-%d')
            dt2 = datetime.datetime.strptime(period.date_stop, '%Y-%m-%d')
            # Carga los datos que aplican sobre la balanza por periodo
            xml_data['RepAuxFol']['Mes'] = dt.strftime('%m')
            xml_data['RepAuxFol']['Anio'] = dt.strftime('%Y')
            xml_data['RepAuxFol']['TipoSolicitud'] = wizard.solicitud
        elif fiscalyear:
            dt = datetime.datetime.strptime(fiscalyear.date_start, '%Y-%m-%d')
            xml_data['RepAuxFol']['Anio'] = dt.strftime('%Y')
            xml_data['RepAuxFol']['Mes'] = dt.strftime('%m')#'13'
            xml_data['RepAuxFol']['TipoSolicitud'] = wizard.solicitud

        # Revisa si viene en los parametros del context el parametro de TipoEnvio
        if context.get('TipoSolicitud',False):
            xml_data['RepAuxFol']['TipoSolicitud'] = wizard.solicitud
            # Valida si trae la fecha de la ultima modificacion
            if context.get('FechaModBal',False):
                xml_data['RepAuxFol']['FechaModBal'] = context.get('FechaModBal', dt.strftime('%Y-%m-%d'))

        # Agrega al diccionario el arreglo donde se estaran cargando las cuentas
        xml_data['RepAuxFol']['DetAuxFol'] = []

        return xml_data

    def _get_info_account_folios(self, cr, uid, period_id=False, fiscalyear_id=False, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        
        move_obj = self.pool.get('account.move')
        inv_obj = self.pool.get('account.invoice')
        part_obj = self.pool.get('res.partner')
        res = []
        # Obtiene la lista de cuentas del SAT
        #raise osv.except_osv('res', period_id)

        inv_ids = inv_obj.search(cr, uid, [('period_id','=',period_id)], context=context)
        # Agrega a la referencia del context la informacion de los periodos y el ejercicio fiscal segun sea el caso

        ctx = context.copy()
        ctx['state'] = 'posted'
        if period_id:
            ctx['periods'] = [period_id]
        elif fiscalyear_id:
            ctx['fiscalyear'] = fiscalyear_id
        
        print "************* ctx ********* ", ctx

        # Recorre las cuentas obtenidas
        #for acc in acc_obj.browse(cr, uid, acc_ids, context=ctx):
        #     print "************** acc *********** ", acc
        #     print "************** acc credit *********** ", acc.credit
        #     print "************** acc debit *********** ", acc.debit
        #     print "************** acc balance *********** ", acc.balance

        for inv in inv_obj.browse(cr, uid, inv_ids, context=ctx):
            print "************** acc *********** ", inv
            if inv.cfdi_folio_fiscal != False:
                reference = 'account.invoice,'+str(inv.id)
                move_ids = move_obj.search(cr, uid, [('reference','=',reference)], context=context)
            #part_ids = part_obj.search(cr, uid, [('id','=',inv.partner_id)], context=context)

                for move in move_obj.browse(cr, uid, move_ids, context=ctx):
                    data = {

                        'NumUnIdenPol': move.id,
                        'Fecha': move.date,
                    #'Concepto': move.ref,
                        }
                    res.append(data)
                    m_pago = str(inv.pay_method_id).split(', ')[1]
                    pago = str(m_pago).split(')')[0]
                    if int(pago) < 10:
                        pago = '0'+str(pago)
                    m_part = str(inv.partner_id).split(', ')[1]
                    part_id = str(m_part).split(')')[0]
                    part_ids = part_obj.search(cr, uid, [('id','=',part_id)], context=context)

                    data['ComprNal'] = {
                        'UUID_CFDI': inv.cfdi_folio_fiscal,#self._get_info_account_inv(cr, uid, inv.id, context)
                        'MontoTotal': inv.amount_total,
                        'MetPagoAux': pago,
                        }
                    #cr.execute("Select rfc from res_partner where id = %s"%(part_id))
                    #rfc_data = cr.fetchall()
                    
                    for partner in part_obj.browse(cr, uid, part_ids, context=ctx):
                        #raise osv.except_osv('rfc', partner)
                        data['ComprNal']['RFC'] = partner.rfc

                    #res.append(data['ComprNal'])

            

        return res

    def generate_xml_folios(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre balanza anual
        """
        if context is None:
            context = {}
                    
        # Agrega en el context la referencia del Tipo de envio y la fecha de ultima modificacion en caso de ser complementaria
        if wizard.send == 'C':
            context.update({
                'TipoEnvio': wizard.send,
                'FechaModBal': wizard.date_ref,
                'TipoSolicitud': wizard.solicitud,
            })

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            context.update({
                'NumOrden': wizard.orden,
            })
        else:
            context.update({
                'NumTramite': wizard.orden,
            })
        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_folios(cr, uid, wizard=wizard, period=wizard.period_id, company=wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['RepAuxFol']['DetAuxFol'] = self._get_info_account_folios(cr, uid, period_id=wizard.period_id.id, context=context)
        print "************************** data dict ************** ", data_dict

        # Genera archivo XML
        xml_data = xml.dict2xml(data_dict, reference='RepAux')
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data

    def _get_info_mayor(self, cr, uid, wizard=False, period=False, fiscalyear=False, company=False, context=None):
        """
            Crea Diccionario con la informacion general del reporte XML para las polizas
        """
        if context is None:
            context = {}

            #Informacion del certificado de la empresa
        # cert_obj = self.pool.get('res.company.facturae.certificate')
        # cert_ids = cert_obj.search(cr, uid, [('active','=',True)], context=context)

        # for cert in cert_obj.browse(cr, uid, cert_ids, context=context):
        #     xml_data = {
        #         'noCertificado': cert.serial_number,
        #         'Certificado': cert.certificate_file,
        #     } 
        # Genera diccionario con informacion principal de XML
        xml_data = {
            'AuxiliarCtas': {
                'xmlns:AuxiliarCtas': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarCtas',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarCtas http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarCtas/AuxiliarCtas_1_1.xsd',
                'Version': '1.1',
                'RFC': xml.clearspace(company.partner_id.rfc),
                #'elementFormDefault': 'qualified',
                #'attributeFormDefault': 'unqualified'
            }
        }

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            xml_data['AuxiliarCtas']['NumOrden'] = wizard.orden
        else:
            xml_data['AuxiliarCtas']['NumTramite'] = wizard.orden

        #     # Valida si es el calculo de la balanza por periodo o anual segun los parametros y agrega los datos q le corresponden

        if period:
            dt = datetime.datetime.strptime(period.date_start, '%Y-%m-%d')
            dt2 = datetime.datetime.strptime(period.date_stop, '%Y-%m-%d')
            # Carga los datos que aplican sobre la balanza por periodo
            xml_data['AuxiliarCtas']['Mes'] = dt.strftime('%m')
            xml_data['AuxiliarCtas']['Anio'] = dt.strftime('%Y')
            xml_data['AuxiliarCtas']['TipoSolicitud'] = wizard.solicitud
        elif fiscalyear:
            dt = datetime.datetime.strptime(fiscalyear.date_start, '%Y-%m-%d')
            xml_data['AuxiliarCtas']['Anio'] = dt.strftime('%Y')
            xml_data['AuxiliarCtas']['Mes'] = dt.strftime('%m')#'13'
            xml_data['AuxiliarCtas']['TipoSolicitud'] = wizard.solicitud

        # # Revisa si viene en los parametros del context el parametro de TipoEnvio
        if context.get('TipoSolicitud',False):
            xml_data['AuxiliarCtas']['TipoSolicitud'] = wizard.solicitud
        #     # Valida si trae la fecha de la ultima modificacion
            if context.get('FechaModBal',False):
                xml_data['AuxiliarCtas']['FechaModBal'] = context.get('FechaModBal', dt.strftime('%Y-%m-%d'))

        # Agrega al diccionario el arreglo donde se estaran cargando las cuentas
        xml_data['AuxiliarCtas']['Cuenta'] = []

        return xml_data

    def _get_info_account_mayor(self, cr, uid, account_id=False, period_id=False, fiscalyear_id=False, context=None):
        """
            Obtiene un arreglo con la informacion del plan de cuentas sat relacionado con el plan de cuentas de openerp
        """
        acc_obj = self.pool.get('account.account.sat')
        move_ln_obj = self.pool.get('account.move.line')
        cta_obj = self.pool.get('account.account')
        res = []
        # Obtiene la lista de cuentas del SAT

        move_ln_idac = move_ln_obj.search(cr, uid, [('period_id','=',period_id),('state','!=','draft')], context=context) 
        move_ln_idan = move_ln_obj.search(cr, uid, [('period_id','=',int(period_id)-1),('state','!=','draft')], context=context) 
        acc_ids = acc_obj.search(cr, uid, [('id','=',account_id)], context=context)
        acc_id = acc_obj.search(cr, uid, [('parent_id','=',account_id)], context=context)
        cta_ids = cta_obj.search(cr, uid, [('account_sat_id','=',acc_id)], context=context)

        balance_inicial = 0
        balance_final = 0
        # Agrega a la referencia del context la informacion de los periodos y el ejercicio fiscal segun sea el caso
        ctx = context.copy()
        ctx['state'] = 'posted'
        if period_id:
            ctx['periods'] = [period_id]
        elif fiscalyear_id:
            ctx['fiscalyear'] = fiscalyear_id
        
        print "************* ctx ********* ", ctx
        #raise osv.except_osv(cta_ids, str(move_ln_idac)+' '+str(move_ln_idan))
        for cta in cta_obj.browse(cr, uid, cta_ids, context=ctx):         
            for ln_ac in move_ln_obj.browse(cr, uid, move_ln_idac, context=ctx):
                if str(cta.id) in str(ln_ac.account_id):
                    balance_final = balance_final+ln_ac.debit-ln_ac.credit
            for ln_an in move_ln_obj.browse(cr, uid, move_ln_idan, context=ctx):
                if str(cta.id) in str(ln_an.account_id):
                    balance_inicial = balance_inicial+ln_ac.debit-ln_ac.credit

        for acc in acc_obj.browse(cr, uid, acc_ids, context=ctx):
            print "************** acc *********** ", acc
            print "************** acc credit *********** ", acc.credit
            print "************** acc debit *********** ", acc.debit
            print "************** acc balance *********** ", acc.balance

            # Genera diccionario con informacion de la cuenta
            
            data = {
                'NumCta': acc.number,
                'DesCta': acc.name,
                'SaldoIni': acc.balance_init,#balance_inicial,
                'SaldoFin': acc.balance_end#balance_final
            }
            
            res.append(data)

            data['DetalleAux'] = self._get_info_detalle(cr, uid, cta_ids, move_ln_idac, context)
            res.append(data['DetalleAux'])

        return res

    def _get_info_detalle(self, cr, uid, cta_ids, move_ln_idac, context=None):

        res = []

        move_ln_obj = self.pool.get('account.move.line')
        cta_obj = self.pool.get('account.account')

        ctx = context.copy()
        ctx['state'] = 'posted'
        
        print "************* ctx ********* ", ctx

        for cta in cta_obj.browse(cr, uid, cta_ids, context=ctx): 
            for move in move_ln_obj.browse(cr, uid, move_ln_idac, context=ctx):
                if str(cta.id) in str(move.account_id):
                    data = {
                        'Fecha': move.date,
                        'NumUnIdenPol': move.move_id.id,
                        'Concepto': move.name,
                        'Debe': move.debit,
                        'Haber': move.credit
                    }
                    res.append(data)

        return res

    def generate_xml_account_mayor(self, cr, uid, wizard, context=None):
        """
            Crea reporte xml sobre balanza anual
        """
        if context is None:
            context = {}
                    
        # Agrega en el context la referencia del Tipo de envio y la fecha de ultima modificacion en caso de ser complementaria
        if wizard.send == 'C':
            context.update({
                'TipoEnvio': wizard.send,
                'FechaModBal': wizard.date_ref,
                'TipoSolicitud': wizard.solicitud,
            })

        if wizard.solicitud == 'AF' or wizard.solicitud == 'FC':
            context.update({
                'NumOrden': wizard.orden,
            })
        else:
            context.update({
                'NumTramite': wizard.orden,
            })
        # Obtiene la informacion sobre la cabecera del XML
        data_dict = self._get_info_mayor(cr, uid, wizard=wizard, period=wizard.period_id, company=wizard.company_id, context=context)
        # Agrega la informacion de las cuentas
        data_dict['AuxiliarCtas']['Cuenta'] = self._get_info_account_mayor(cr, uid, account_id=wizard.account.id, period_id=wizard.period_id.id, context=context)
        print "************************** data dict ************** ", data_dict

        # Genera archivo XML
        xml_data = xml.dict2xml(data_dict, reference='AuxiliarCtas')
        xml_data = xml.format_xml(xml_data, context=context)
        return xml_data

    ########################################################### Creacion de XML ######################################################
    def create_report_xml(self, cr, uid, ids, context=None):
        """
            Generacion del archivo del reporte XML
        """
        if context is None:
            context = {}
        # Obtiene el periodo sobre el que registra
        this = self.browse(cr, uid, ids[0], context=context)
        doc_xml = False
        out = False
        fname = "-"
        state = 'not_file'
        
        # Genera el xml sobre el plan de cuentas segun la seleccion
        if this.type == 'account':
            doc_xml = self.generate_xml_account(cr, uid, this, context=context)
        elif this.type == 'balance_month':
            doc_xml = self.generate_xml_balance_month(cr, uid, this, context=context)
        elif this.type == 'balance_year':
            doc_xml = self.generate_xml_balance_year(cr, uid, this, context=context)
        elif this.type == 'move':
            doc_xml = self.generate_xml_move(cr, uid, this, context=context)
        elif this.type == 'folios':
            doc_xml = self.generate_xml_folios(cr, uid, this, context=context)
        elif this.type == 'mayor':
            doc_xml = self.generate_xml_account_mayor(cr, uid, this, context=context)

        # Valida que se haya generado el archivo
        if doc_xml:
            state = 'get'
            # Cambia el formato del archivo para cargarlo al wizard
            out = xml.xml2binary(doc_xml)
            # Obtiene el nombre del archivo
            fname = self._get_fname_xml(cr, uid, ids[0], context=context)
        
        # Actualiza la informacion del archivo
        self.write(cr, uid, ids, {'state': state,
                                'file': out,
                                'filename': fname
                                }, context=context)
        
        # Recarga el wizard
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'res_model': 'account.sat.create.xml.report',
            'target': 'new',
        }

account_sat_create_xml_report()