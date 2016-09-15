# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: moylop260 (moylop260@vauxoo.com)
#    Financed by: http://www.sfsoluciones.com (aef@sfsoluciones.com)
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
from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import tools
from openerp import netsvc
from openerp.tools.misc import ustr
import wizard
import base64
import xml.dom.minidom
import time
import StringIO
import csv
import tempfile
import os
import sys
import codecs
from xml.dom import minidom
import urllib
import pooler
from tools.translate import _
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import time
from datetime import datetime, timedelta
try:
    from SOAPpy import WSDL
except:
    print "Package SOAPpy missed"
    pass
import time


class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    _columns = {
        'cfdi_cbb': fields.binary('CFD-I CBB'),
        'cfdi_sello': fields.text('CFD-I Sello', help='Sign assigned by the SAT'),
        'cfdi_no_certificado': fields.char('CFD-I Certificado', size=32,
            help='Serial Number of the Certificate'),
        'cfdi_cadena_original': fields.text('CFD-I Cadena Original',
            help='Original String used in the electronic invoice'),
        'cfdi_fecha_timbrado': fields.datetime('CFD-I Fecha Timbrado',
            help='Date when is stamped the electronic invoice'),
        'cfdi_fecha_cancelacion': fields.datetime('CFD-I Fecha Cancelacion',
            help='If the invoice is cancel, this field saved the date when is cancel'),
        'cfdi_folio_fiscal': fields.char('CFD-I Folio Fiscal', size=64,
            help='Folio used in the electronic invoice'),
    }

    def cfdi_data_write(self, cr, uid, ids, cfdi_data, context={}):
        """
        @params cfdi_data : * TODO
        """
        if not context:
            context = {}
        attachment_obj = self.pool.get('ir.attachment')
        cfdi_xml = cfdi_data.pop('cfdi_xml')
        if cfdi_xml:
            self.write(cr, uid, ids, cfdi_data)
            cfdi_data[
                'cfdi_xml'] = cfdi_xml  # Regresando valor, despues de hacer el write normal
            """for invoice in self.browse(cr, uid, ids):
                #fname, xml_data = self.pool.get('account.invoice').\
                    _get_facturae_invoice_xml_data(cr, uid, [inv.id],
                    context=context)
                fname_invoice = invoice.fname_invoice and invoice.\
                    fname_invoice + '.xml' or ''
                data_attach = {
                    'name': fname_invoice,
                    'datas': base64.encodestring( cfdi_xml or '') or False,
                    'datas_fname': fname_invoice,
                    'description': 'Factura-E XML CFD-I',
                    'res_model': 'account.invoice',
                    'res_id': invoice.id,
                }
                attachment_ids = attachment_obj.search(cr, uid, [('name','=',\
                    fname_invoice),('res_model','=','account.invoice'),(
                    'res_id', '=', invoice.id)])
                if attachment_ids:
                    attachment_obj.write(cr, uid, attachment_ids, data_attach,
                        context=context)
                else:
                    attachment_obj.create(cr, uid, data_attach, context=context)
                """
        return True

    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'cfdi_cbb': False,
            'cfdi_sello': False,
            'cfdi_no_certificado': False,
            'cfdi_cadena_original': False,
            'cfdi_fecha_timbrado': False,
            'cfdi_folio_fiscal': False,
            'cfdi_fecha_cancelacion': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    """
    TODO: reset to draft considerated to delete these fields?
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'cfdi_cbb': False,
            'cfdi_sello':False,
            'cfdi_no_certificado':False,
            'cfdi_cadena_original':False,
            'cfdi_fecha_timbrado': False,
            'cfdi_folio_fiscal': False,
            'cfdi_fecha_cancelacion': False,
        })
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, args)
    """

    def _get_file(self, cr, uid, inv_ids, context={}):
        if not context:
            context = {}
        id = inv_ids[0]
        invoice = self.browse(cr, uid, [id], context=context)[0]
        fname_invoice = invoice.fname_invoice and invoice.fname_invoice + \
            '.xml' or ''
        aids = self.pool.get('ir.attachment').search(cr, uid, [(
            'datas_fname', '=', invoice.fname_invoice+'.xml'), (
            'res_model', '=', 'account.invoice'), ('res_id', '=', id)])
        xml_data = ""
        if aids:
            brow_rec = self.pool.get('ir.attachment').browse(cr, uid, aids[0])
            if brow_rec.datas:
                xml_data = base64.decodestring(brow_rec.datas)
        else:
            fname, xml_data = self._get_facturae_invoice_xml_data(
                cr, uid, inv_ids, context=context)
            self.pool.get('ir.attachment').create(cr, uid, {
                'name': fname_invoice,
                'datas': base64.encodestring(xml_data),
                'datas_fname': fname_invoice,
                'res_model': 'account.invoice',
                'res_id': invoice.id,
            }, context=context)
        self.fdata = base64.encodestring(xml_data)
        msg = _("Press in the button  'Upload File'")
        return {'file': self.fdata, 'fname': fname_invoice,
                'name': fname_invoice, 'msg': msg}

    def add_node(self, node_name=None, attrs=None, parent_node=None,
        minidom_xml_obj=None, attrs_types=None, order=False):
        """
            @params node_name : Name node to added
            @params attrs : Attributes to add in node
            @params parent_node : Node parent where was add new node children
            @params minidom_xml_obj : File XML where add nodes
            @params attrs_types : Type of attributes added in the node
            @params order : If need add the params in order in the XML, add a
                    list with order to params
        """
        if not order:
            order = attrs
        new_node = minidom_xml_obj.createElement(node_name)
        for key in order:
            if attrs_types[key] == 'attribute':
                new_node.setAttribute(key, attrs[key])
            elif attrs_types[key] == 'textNode':
                key_node = minidom_xml_obj.createElement(key)
                text_node = minidom_xml_obj.createTextNode(attrs[key])

                key_node.appendChild(text_node)
                new_node.appendChild(key_node)
        parent_node.appendChild(new_node)
        return new_node

    def add_addenta_xml(self, cr, ids, xml_res_str=None, comprobante=None, context={}):
        """
         @params xml_res_str : File XML
         @params comprobante : Name to the Node that contain the information the XML
        """
        # if xml_res_str:
        #     node_Addenda = xml_res_str.getElementsByTagName('cfdi:Addenda')
        #     if len(node_Addenda) == 0:
        #         nodeComprobante = xml_res_str.getElementsByTagName(
        #             comprobante)[0]
        #         node_Addenda = self.add_node(
        #             'cfdi:Addenda', {}, nodeComprobante, xml_res_str, attrs_types={})
        #         node_Partner_attrs = {
        #             'xmlns:sf': "http://timbrado.solucionfactible.com/partners",
        #             'xsi:schemaLocation': "http://timbrado.solucionfactible.com/partners https://solucionfactible.com/timbrado/partners/partners.xsd",
        #             'id': "150731"
        #         }
        #         node_Partner_attrs_types = {
        #             'xmlns:sf': 'attribute',
        #             'xsi:schemaLocation': 'attribute',
        #             'id': 'attribute'
        #         }
        #         node_Partner = self.add_node('sf:Partner', node_Partner_attrs,
        #             node_Addenda, xml_res_str, attrs_types=node_Partner_attrs_types)
        #     else:
        #         node_Partner_attrs = {
        #             'xmlns:sf': "http://timbrado.solucionfactible.com/partners",
        #             'xsi:schemaLocation': "http://timbrado.solucionfactible.com/partners https://solucionfactible.com/timbrado/partners/partners.xsd",
        #             'id': "150731"
        #         }
        #         node_Partner_attrs_types = {
        #             'xmlns:sf': 'attribute',
        #             'xsi:schemaLocation': 'attribute',
        #             'id': 'attribute'
        #         }
        #         node_Partner = self.add_node('sf:Partner', node_Partner_attrs,
        #             node_Addenda, xml_res_str, attrs_types=node_Partner_attrs_types)
        return xml_res_str

    def _get_type_sequence(self, cr, uid, ids, context=None):
        ir_seq_app_obj = self.pool.get('ir.sequence.approval')
        invoice = self.browse(cr, uid, ids[0], context=context)
        sequence_app_id = ir_seq_app_obj.search(cr, uid, [(
            'sequence_id', '=', invoice.invoice_sequence_id.id)], context=context)
        type_inv = 'cfd22'
        if sequence_app_id:
            type_inv = ir_seq_app_obj.browse(
                cr, uid, sequence_app_id[0], context=context).type
        if type_inv == 'cfdi32':
            comprobante = 'cfdi:Comprobante'
        else:
            comprobante = 'Comprobante'
        return comprobante
        
        
    def _get_time_zone(self, cr, uid, invoice_id, context=None):
        res_users_obj = self.pool.get('res.users')
        userstz = res_users_obj.browse(cr, uid, [uid])[0].partner_id.tz
        a=0
        if userstz:
            hours = timezone(userstz)
            fmt = '%Y-%m-%d %H:%M:%S %Z%z'
            now = datetime.now()
            loc_dt = hours.localize(datetime(now.year,now.month,now.day,now.hour,now.minute,now.second))
            timezone_loc=(loc_dt.strftime(fmt))
            diff_timezone_original=timezone_loc[-5:-2]
            timezone_original=int(diff_timezone_original)
            s= str(datetime.now(pytz.timezone(userstz)))
            s=s[-6:-3]
            timezone_present=int(s)*-1
            a=  timezone_original + ((timezone_present + timezone_original)*-1)
        return a


    def _upload_ws_file(self, cr, uid, inv_ids, fdata=None, context={}):
        """
        @params fdata : File.xml codification in base64
        """
        
        #print"*********************** upload ws file ********************** "
        
        comprobante = self._get_type_sequence(
            cr, uid, inv_ids, context=context)
        pac_params_obj = self.pool.get('params.pac')
        cfd_data = base64.decodestring(fdata or self.fdata)
        
        #print"*********************** cfd_data *********************** ", cfd_data
        
        xml_res_str = xml.dom.minidom.parseString(cfd_data)
        xml_res_addenda = self.add_addenta_xml(
            cr, uid, xml_res_str, comprobante, context=context)
        xml_res_str_addenda = xml_res_addenda.toxml('UTF-8')
        
        #print"****************** xml_res_str_addenda **************** ", xml_res_str_addenda
        
        compr = xml_res_addenda.getElementsByTagName(comprobante)[0]
        date = compr.attributes['fecha'].value
        date_format = datetime.strptime(
            date, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
        context['date'] = date_format
        invoice_ids = inv_ids
        invoice = self.browse(cr, uid, invoice_ids, context=context)[0]
        currency = invoice.currency_id.name
        currency_enc = currency.encode('UTF-8', 'strict')
        rate = invoice.currency_id.rate and (1.0/invoice.currency_id.rate) or 1
        file = False
        msg = ''
        status = ''
        cfdi_xml = False
        pac_params_ids = pac_params_obj.search(cr, uid, [
            ('method_type', '=', 'pac_sf_firmar'), (
            'company_id', '=', invoice.company_emitter_id.id), (
            'active', '=', True)], limit=1, context=context)
        if pac_params_ids:
            pac_params = pac_params_obj.browse(
                cr, uid, pac_params_ids, context)[0]
            user = pac_params.user
            password = pac_params.password
            wsdl_url = pac_params.url_webservice
            namespace = pac_params.namespace
            if 'testing' in wsdl_url:
                msg += _(u'WARNING, SIGNED IN TEST!!!!\n\n')
            wsdl_client = WSDL.SOAPProxy(wsdl_url, namespace)
            
            #print"************************* wsdl_client ******************** ", wsdl_client
            
            if True:  # if wsdl_client: - No funciona con esta validacion
                file_globals = self._get_file_globals(
                    cr, uid, invoice_ids, context=context)
                fname_cer_no_pem = file_globals['fname_cer']
                cerCSD = fname_cer_no_pem and base64.encodestring(
                    open(fname_cer_no_pem, "r").read()) or ''
                fname_key_no_pem = file_globals['fname_key']
                keyCSD = fname_key_no_pem and base64.encodestring(
                    open(fname_key_no_pem, "r").read()) or ''
                cfdi = base64.encodestring(
                    xml_res_str_addenda.replace(codecs.BOM_UTF8, ''))
                
                #print"******************** cfdi ************************* ", cfdi
                
                zip = False  # Validar si es un comprimido zip, con la extension del archivo
                contrasenaCSD = file_globals.get('password', '')
                params = [
                    user, password, cfdi, zip]
                wsdl_client.soapproxy.config.dumpSOAPOut = 0
                wsdl_client.soapproxy.config.dumpSOAPIn = 0
                wsdl_client.soapproxy.config.debug = 0
                wsdl_client.soapproxy.config.dict_encoding = 'UTF-8'
                
                #print"********************* params *************** ", params
                
                resultado = wsdl_client.timbrar(*params)
                
                #print"**************** resultado timbrado ***************** ", resultado
                
                htz=int(self._get_time_zone(cr, uid, inv_ids, context=context))
                msg += resultado['resultados'] and resultado[
                    'resultados']['mensaje'] or ''
                status = resultado['resultados'] and resultado[
                    'resultados']['status'] or ''
                if status == '200' or status == '307':
                    fecha_timbrado = resultado[
                        'resultados']['fechaTimbrado'] or False
                    fecha_timbrado = fecha_timbrado and time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.strptime(
                        fecha_timbrado[:19], '%Y-%m-%dT%H:%M:%S')) or False
                    fecha_timbrado = fecha_timbrado and datetime.strptime(
                        fecha_timbrado, '%Y-%m-%d %H:%M:%S') + timedelta(
                        hours=htz) or False
                    cfdi_data = {
                        'cfdi_cbb': resultado['resultados']['qrCode'] or False,  # ya lo regresa en base64
                        'cfdi_sello': resultado['resultados'][
                            'selloSAT'] or False,
                        'cfdi_no_certificado': resultado['resultados'][
                            'certificadoSAT'] or False,
                        'cfdi_cadena_original': resultado['resultados'][
                            'cadenaOriginal'] or False,
                        'cfdi_fecha_timbrado': fecha_timbrado,
                        'cfdi_xml': base64.decodestring(resultado[
                            'resultados']['cfdiTimbrado'] or ''),  # este se necesita en uno que no es base64
                        'cfdi_folio_fiscal': resultado['resultados']['uuid'] or '',
                    }
                    if cfdi_data.get('cfdi_xml', False):
                        url_pac = '</"%s"><!--Para validar el XML CFDI puede descargar el certificado del PAC desde la siguiente liga: https://solucionfactible.com/cfdi/00001000000102699425.zip-->' % (
                            comprobante)
                        cfdi_data['cfdi_xml'] = cfdi_data[
                            'cfdi_xml'].replace('</"%s">' % (comprobante), url_pac)
                        file = base64.encodestring(
                            cfdi_data['cfdi_xml'] or '')
                        # self.cfdi_data_write(cr, uid, [invoice.id],
                        # cfdi_data, context=context)
                        cfdi_xml = cfdi_data.pop('cfdi_xml')
                        if cfdi_xml:
                            self.write(cr, uid, inv_ids, cfdi_data)
                            cfdi_data['cfdi_xml'] = cfdi_xml
                        msg = msg + _(
                            "\nMake Sure to the file really has generated correctly to the SAT\nhttps://www.consulta.sat.gob.mx/sicofi_web/moduloECFD_plus/ValidadorCFDI/Validador%20cfdi.html")
                    else:
                        msg = msg + "\nCan't extract the file XML of PAC"
                elif status == '500' or status == '307':  # documento no es un cfd version 2, probablemente ya es un CFD version 3
                    msg = _("Probably the file XML already has stamping previously and it isn't necessary to upload again.\nOr can be that the format of file is incorrect.\nPlease, visualized the file for corroborate and followed with the next step or contact you administrator of system.\n") + (
                        resultado['resultados']['mensaje'] or '') + (
                        resultado['mensaje'] or '')
                else:
                    msg = _("Ocurrio un error con la informacion de la factura. Contacte con el administrador.\n") + (
                        resultado['resultados']['mensaje'] or '') + (
                        resultado['mensaje'] or '')
                    # Agrega exepcion para el mensaje porque no se detiene el flujo
                    raise osv.except_osv('Error Factura Electronica! - ' + status, msg)
                    #msg = msg + \
                    #    "\nNo se pudo extraer el archivo XML del PAC"
            elif status == '500' or status == '307':  # documento no es un cfd version 2, probablemente ya es un CFD version 3
                msg = "Probablemente el archivo XML ya ha sido timbrado previamente y no es necesario volverlo a subir.\nO puede ser que el formato del archivo, no es el correcto.\nPor favor, visualice el archivo para corroborarlo y seguir con el siguiente paso o comuniquese con su administrador del sistema.\n" + \
                    (resultado['resultados']['mensaje'] or '') + (
                        resultado['mensaje'] or '')
            else:
                msg += '\n' + resultado['mensaje'] or ''
                if not status:
                    status = 'parent_' + resultado['status']
        else:
            msg = 'Not found information from web services of PAC, verify that the configuration of PAC is correct'
        return {'file': file, 'msg': msg, 'status': status, 'cfdi_xml': cfdi_xml}

    def _get_file_cancel(self, cr, uid, inv_ids, context={}):
        inv_ids = inv_ids[0]
        atta_obj = self.pool.get('ir.attachment')
        atta_id = atta_obj.search(cr, uid, [('res_id', '=', inv_ids), (
            'name', 'ilike', '%.xml')], context=context)
        res = {}
        if atta_id:
            atta_brw = atta_obj.browse(cr, uid, atta_id, context)[0]
            inv_xml = atta_brw.datas or False
        else:
            inv_xml = False
            raise osv.except_osv(('State of Cancellation!'), (
                "This invoice hasn't stamped, so that not possible cancel."))
        return {'file': inv_xml}

    def sf_cancel(self, cr, uid, inv_ids, context=None):
        context_id = inv_ids[0]
        company_obj = self.pool.get('res.company.facturae.certificate')
        pac_params_obj = self.pool.get('params.pac')

        invoice_brw = self.browse(cr, uid, context_id, context)
        company_brw = company_obj.browse(cr, uid, [
                                         invoice_brw.company_id.id], context)[0]
        pac_params_srch = pac_params_obj.search(cr, uid, [(
            'method_type', '=', 'pac_sf_cancelar'), ('company_id', '=',
            invoice_brw.company_emitter_id.id), ('active', '=', True)],
            context=context)

        if pac_params_srch:
            pac_params_brw = pac_params_obj.browse(
                cr, uid, pac_params_srch, context)[0]
            user = pac_params_brw.user
            password = pac_params_brw.password
            wsdl_url = pac_params_brw.url_webservice
            namespace = pac_params_brw.namespace
            #---------constantes
            #~ user = 'testing@solucionfactible.com'
            #~ password = 'timbrado.SF.16672'
            #~ wsdl_url = 'http://testing.solucionfactible.com/ws/services/Timbrado?wsdl'
            #~ namespace = 'http://timbrado.ws.cfdi.solucionfactible.com'

            wsdl_client = False
            wsdl_client = WSDL.SOAPProxy(wsdl_url, namespace)
            if True:  # if wsdl_client:
                file_globals = self._get_file_globals(
                    cr, uid, [context_id], context=context)
                fname_cer_no_pem = file_globals['fname_cer']
                cerCSD = fname_cer_no_pem and base64.encodestring(
                    open(fname_cer_no_pem, "r").read()) or ''
                fname_key_no_pem = file_globals['fname_key']
                keyCSD = fname_key_no_pem and base64.encodestring(
                    open(fname_key_no_pem, "r").read()) or ''
                zip = False  # Validar si es un comprimido zip, con la extension del archivo
                contrasenaCSD = file_globals.get('password', '')
                uuids = invoice_brw.cfdi_folio_fiscal  # cfdi_folio_fiscal

                params = [
                    user, password, uuids, cerCSD, keyCSD, contrasenaCSD]
                wsdl_client.soapproxy.config.dumpSOAPOut = 0
                wsdl_client.soapproxy.config.dumpSOAPIn = 0
                wsdl_client.soapproxy.config.debug = 0
                wsdl_client.soapproxy.config.dict_encoding = 'UTF-8'
                result = wsdl_client.cancelar(*params)

                status = result['resultados'] and result[
                    'resultados']['status'] or ''
                # agregados
                uuid_nvo = result['resultados'] and result[
                    'resultados']['uuid'] or ''
                msg_nvo = result['resultados'] and result[
                    'resultados']['mensaje'] or ''

                status_uuid = result['resultados'] and result[
                    'resultados']['statusUUID'] or ''
                msg_status = {}
                res = False
                
                #print"******************* satus cancel ******************* ", status
                
                if status == '200':
                    folio_cancel = result['resultados'] and result[
                        'resultados']['uuid'] or ''
                    msg_global = _('\n- The process of cancellation has completed correctly.\n- The uuid cancelled is: ') + folio_cancel+_(
                        '\n\nMessage Technical:\n')
                    msg_tecnical = 'Status:', status, ' uuid:', uuid_nvo,\
                        ' msg:', msg_nvo, 'Status uuid:', status_uuid
                    res = True
                else:
                    msg_global = _(
                        '\n- Have occurred errors that not permit complete the process of cancellation, make sure that the invoice that tried cancel has been stamped previously.\n\nMessage Technical:\n')
                    msg_tecnical = 'status:', status, ' uuidnvo:', uuid_nvo,\
                    ' MENSJAE:NVO', msg_nvo, 'STATUS UUID:', status_uuid

                if status_uuid == '201':
                    msg_SAT = _(
                        '- Status of response of the SAT: 201. The folio was canceled with success.')
                    self.write(cr, uid, context_id, {'cfdi_fecha_cancelacion':\
                    time.strftime('%Y-%m-%d %H:%M:%S')})
                    res = True
                elif status_uuid == '202':
                    msg_SAT = _(
                        '- Status of response of the SAT: 202. The folio already has cancelled previously.')
                elif status_uuid == '203':
                    msg_SAT = _(
                        '- Status of response of the SAT: 203. The voucher that tries cancel not corresponds the taxpayer with that signed the request of cancellation.')
                elif status_uuid == '204':
                    msg_SAT = _(
                        '- Status of response of the SAT: 204. The CFDI not aply for cancellation.')
                elif status_uuid == '205':
                    msg_SAT = _(
                        '- Status of response of the SAT: 205. Not found the folio of CFDI for his cancellation.')
                else:
                    msg_SAT = _('- Status of response of SAT unknown')
                msg_global = msg_SAT + msg_global + str(msg_tecnical)
                
                if res == False:
                    # Agrega exepcion para el mensaje porque no se detiene el flujo
                    raise osv.except_osv('Error al Cancelar Factura Electronica! - ' + status, msg_global)
        else:
            msg_global = _(
                'Not found information of webservices of PAC, verify that the configuration of PAC is correct')
        return {'message': msg_global}

    def write_cfd_data(self, cr, uid, ids, cfd_datas, context={}):
        """
        @param cfd_datas : Dictionary with data that is used in facturae CFDI
        """
        if not cfd_datas:
            cfd_datas = {}
        comprobante = self._get_type_sequence(cr, uid, ids, context=context)
        # obtener cfd_data con varios ids
        # for id in ids:
        id = ids[0]
        if True:
            data = {}
            cfd_data = cfd_datas
            noCertificado = cfd_data.get(
                comprobante, {}).get('noCertificado', '')
            certificado = cfd_data.get(comprobante, {}).get('certificado', '')
            sello = cfd_data.get(comprobante, {}).get('sello', '')
            cadena_original = cfd_data.get('cadena_original', '')
            data = {
                'no_certificado': noCertificado,
                'certificado': certificado,
                'sello': sello,
                'cadena_original': cadena_original,
            }
            self.write(cr, uid, [id], data, context=context)
        return True
