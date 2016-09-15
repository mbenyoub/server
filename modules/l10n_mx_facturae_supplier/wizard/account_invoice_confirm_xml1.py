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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
import xml.dom.minidom
import base64
import codecs
try:
    from SOAPpy import WSDL
except:
    print "Package SOAPpy missed"
    pass

class account_invoice_confirm_xml(osv.osv_memory):
    _name = 'account.invoice.confirm.xml'
    _description = 'Valida XML Factura'
    
    def validate_structure_xml_node(self, cr, uid, node, attrs, directory, context=None):
        """
            Valida que el nodo del xml contenga los attributos necesarios
        """
        msg = "Atributo no Valido \n\n Valide que la estructura del xml sea correcta para una factura de CFDI v 3.2. \n"
        # Recorre los registros
        for attr in attrs:
            # Valida si existe el attributo
            if not node.getAttribute(attr):
                raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s, Atributo: %s")%(msg,directory,attr))
        return True
        
    def validate_structure_xml(self, cr, uid, invoice, doc_xml, context=None):
        """
            Valida que el xml tenga una estructura valida
        """
        decimal_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        msg1 = "Etiqueta no Valida \n\n Valide que la estructura del xml sea correcta para una factura de CFDI v-3.2. \n"
        msg2 = "Atributo no Valido \n\n Valide que la estructura del xml sea correcta para una factura de CFDI v-3.2. \n"
        tag = ''
        tag2 = ''
        attrs = []
        attr = ''
        node = None
        
        # Valida que la estructura del xml sobre el comprobante sea valida
        try:
            data_xml = xml.dom.minidom.parseString(doc_xml)
        except:
            raise osv.except_osv(_('Error!'), _("A ocurrido un error al validar el archivo. Confirme que el archivo adjunto es un XML valido."))
        
        try:
            tag = 'cfdi:Comprobante'
            # Valida que exista la etiqueta de comprobante
            comprobante = data_xml.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        # Valida los atributos del campo
        attrs = ['xmlns:cfdi','version','xmlns:xsi','xsi:schemaLocation','serie','folio','fecha','tipoDeComprobante','formaDePago','noCertificado','subTotal','total','LugarExpedicion','NumCtaPago','certificado','sello']
        self.validate_structure_xml_node(cr, uid, comprobante, attrs, tag, context=context)
        
        # Valida que contenga los attibutos requeridos
        attr = 'xmlns:cfdi'
        # Valida que el comprobante sea cfdi
        if comprobante.getAttribute(attr) != u'http://www.sat.gob.mx/cfd/3':
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s, Atributo: %s")%(msg2,tag,attr))
        attr = 'version'
        # Valida que el comprobante sea cfdi
        if comprobante.getAttribute(attr) != '3.2':
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s, Atributo: %s")%(msg2,tag,attr))
        
        try:
            # Valida que la estructura xml sobre el emisor sea valida
            tag = 'cfdi:Emisor'
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        # Valida que contenga los attibutos requeridos
        attrs = ['rfc','nombre']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que exista la etiqueta del nodo
            tag2 = tag
            tag = 'cfdi:DomicilioFiscal'
            tag2 =  '%s\%s'%(tag2,tag)
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag2))
        # Valida que contenga los attibutos requeridos
        attrs = ['calle','noExterior','colonia','localidad','municipio','estado','pais','codigoPostal']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que exista la etiqueta del nodo
            tag2 = 'cfdi:Emisor'
            node = comprobante.getElementsByTagName(tag2)[0]
            tag = 'cfdi:ExpedidoEn'
            tag2 =  '%s\%s'%(tag2,tag)
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag2))
        # Valida que contenga los attibutos requeridos
        attrs = ['calle','noExterior','colonia','localidad','municipio','estado','pais','codigoPostal']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que exista la etiqueta del nodo
            tag2 = 'cfdi:Emisor'
            node = comprobante.getElementsByTagName(tag2)[0]
            tag = 'cfdi:RegimenFiscal'
            tag2 =  '%s\%s'%(tag2,tag)
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag2))
        # Valida que contenga los attibutos requeridos
        attrs = ['Regimen']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que la estructura xml sobre el emisor sea valida
            tag = 'cfdi:Receptor'
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        # Valida que contenga los attibutos requeridos
        attrs = ['rfc','nombre']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que exista la etiqueta del nodo
            tag2 = tag
            tag = 'cfdi:Domicilio'
            tag2 =  '%s\%s'%(tag2,tag)
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag2))
        # Valida que contenga los attibutos requeridos
        attrs = ['calle','localidad','pais','codigoPostal']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que la estructura xml sobre el emisor sea valida
            tag = 'cfdi:Conceptos'
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        
        try:
            # Valida que haya conceptos en el xml
            tag2 = tag
            tag = 'cfdi:Concepto'
            tag2 =  '%s\%s'%(tag2,tag)
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        
        try:
            # Valida que la estructura xml sobre el emisor sea valida
            tag = 'cfdi:Impuestos'
            # Valida que exista la etiqueta del nodo
            node = comprobante.getElementsByTagName(tag)[0]
        except:
            raise osv.except_osv(_('Error!'), _("%s Etiqueta: %s")%(msg1,tag))
        # Valida que contenga los attibutos requeridos
        attrs = ['totalImpuestosTrasladados']
        self.validate_structure_xml_node(cr, uid, node, attrs, tag, context=context)
        
        try:
            # Valida que la informacion principal del xml coincida con la registrada en la factura
            num = comprobante.getAttribute('folio')
            serie = comprobante.getAttribute('serie')
            total = comprobante.getAttribute('total')
            rfc_supplier = comprobante.getElementsByTagName('cfdi:Emisor')[0].getAttribute('rfc')
            rfc_company = comprobante.getElementsByTagName('cfdi:Receptor')[0].attributes['rfc'].value
            amount_tax = comprobante.getElementsByTagName('cfdi:Impuestos')[0].getAttribute('totalImpuestosTrasladados')
        except:
            raise osv.except_osv(_('Error!'), _("Ocurrio un error al tratar de obtener la informacion general de la factura"))
        rfc_invoice = invoice.partner_id.rfc
        #Valida el rfc del proveedor
        if rfc_invoice != rfc_supplier:
            raise osv.except_osv(_('Error!'), _("El RFC del proveedor es invalido, compruebe que se utiliza el mismo rfc que el del XML. \n (RFC XML: %s, RFC Proveedor: %s) ")%(rfc_supplier,rfc_invoice))
        rfc_invoice = invoice.company_id.partner_id.rfc
        #Valida el rfc de la compañia
        if rfc_invoice != rfc_company:
            raise osv.except_osv(_('Error!'), _("El RFC de la compañia es invalido, compruebe que se utiliza el mismo rfc que el del XML. \n (RFC XML: %s, RFC Compañia: %s) ")%(rfc_company,rfc_invoice))
        # Valida que reciba el numero de la factura
        if int(num) == 0:
            raise osv.except_osv(_('Error!'), _("El folio de la factura en el xml es invalido. %s ")%(num))
        # Valida el monto total de la factura
        xml_total = round(float(total), decimal_precision)
        inv_total = round(invoice.amount_total, decimal_precision)
        res = False
        # Valida el total de la factura dejando un margen de error de 1 peso
        if (xml_total == inv_total):
            res = True
        elif (xml_total + 1.00 >= inv_total) and (xml_total <= inv_total):
            res = True
        elif (inv_total + 1.00 >= xml_total) and (inv_total <= xml_total):
            res = True
        if not res:
            raise osv.except_osv(_('Error!'), _("El total de la factura no coincide. \n (Total XML: %s, Total Factura: %s) ")%(total, invoice.amount_total))
        # Valida el total de impuestos
        xml_total = round(float(amount_tax), decimal_precision)
        inv_total = round(invoice.amount_tax, decimal_precision)
        res = False
        # Valida el total de los impuestos dejando un margen de error de 1 peso
        if (xml_total == inv_total):
            res = True
        elif (xml_total + 1.00 >= inv_total) and (xml_total <= inv_total):
            res = True
        elif (inv_total + 1.00 >= xml_total) and (inv_total <= xml_total):
            res = True
        if not res:
            raise osv.except_osv(_('Error!'), _("El total de los impuestos no coincide en la factura. \n (Impuestos XML: %s, Impuestos Factura: %s) ")%(amount_tax, invoice.amount_tax))
        # Agrega la serie al folio
        if serie:
            num = '%s-%s'%(serie,num)
        return num
    
    def action_validate_xml(self, cr, uid, ids, context=None):
        """
            Valida que el xml sea valido
        """
        att_obj = self.pool.get('ir.attachment')
        inv_obj = self.pool.get('account.invoice')
        
        # Obtiene la informacion del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)
        doc_xml = base64.decodestring(wizard.xml_file)
        # Valida la estructura del xml
        number = self.validate_structure_xml(cr, uid, wizard.invoice_id, doc_xml, context=context)
        
        fname = '%s_%s.xml'%(wizard.invoice_id.partner_id.rfc,number)
        # Crea un nuevo documento en los adjuntos de la factura
        data_attach = {
                'name': 'XML Factura Proveedor %s.xml '%(number) ,
                'datas': wizard.xml_file,
                'type': 'binary',
                'file_type': 'application/xml',
                'datas_fname': fname,
                'store_fname': fname,
                'description': 'Factura-E XML Proveedor',
                'res_model': 'account.invoice',
                'res_id': wizard.invoice_id.id,
                'index_content': doc_xml
            }
        att_id = att_obj.create(cr, uid, data_attach, context=context)
        
        # Relaciona el documento creado con la factura
        inv_obj.write(cr, uid, [wizard.invoice_id.id], {'file_xml': att_id, 'check_total': wizard.invoice_id.amount_total, 'supplier_invoice_number': number}, context=context)
        return True
    
    def action_validate_xml_and_confirm(self, cr, uid, ids, context=None):
        """
            Valida que el xml sea valido, pasa a estado abierto factura de proveedor
        """
        self.action_validate_xml(cr, uid, ids, context=context)
        
        # Obtiene la informacion del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)
        # Pasa la factura a estado abierto
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'account.invoice', \
                                        wizard.invoice_id.id, 'invoice_open', cr)
        return True
    
    #def action_validate_xml(self, cr, uid, ids, context=None):
    #    """
    #        Valida que el xml sea valido
    #    """
    #    pac_params_obj = self.pool.get('params.pac')
    #    inv_obj = self.pool.get('account.invoice')
    #    user = ""
    #    password = ""
    #    wsdl_url = ""
    #    namespace = ""
    #    wsdl_client = None
    #    msg = ''
    #    status = ''
    #    
    #    # Obtiene la informacion del wizard
    #    wizard = self.browse(cr, uid, ids[0], context=context)
    #    
    #    # Obtiene la informacion de los parametros PAC para la validacion
    #    pac_params_ids = pac_params_obj.search(cr, uid, [
    #        ('method_type', '=', 'pac_sf_confirmar'), (
    #        'company_id', '=', wizard.invoice_id.company_emitter_id.id), (
    #        'active', '=', True)], limit=1, context=context)
    #    if pac_params_ids:
    #        pac_params = pac_params_obj.browse(
    #            cr, uid, pac_params_ids, context)[0]
    #        user = pac_params.user
    #        password = pac_params.password
    #        wsdl_url = pac_params.url_webservice
    #        namespace = pac_params.namespace
    #        if 'testing' in wsdl_url:
    #            msg += _(u'WARNING, SIGNED IN TEST!!!!\n\n')
    #        wsdl_client = WSDL.SOAPProxy(wsdl_url, namespace)
    #    else:
    #        raise osv.except_osv(_('Error!'), _("Parametro RecibeCFD no registrado, contacte con el administrador para que Actualice la informacion de params PAC."))
    #    
    #    print "********************* user ********************* ", user
    #    print "********************* password ********************* ", password
    #    print "********************* wsdl_url ********************* ", wsdl_url
    #    print "********************* namespace ********************* ", namespace
    #    print "********************* wsdl_client ********************* ", wsdl_client
    #    
    #    # Valida que la informacion del xml coincida con la registrada en la factura
    #    doc_xml = base64.decodestring(wizard.xml_file)
    #    data_xml = xml.dom.minidom.parseString(doc_xml)
    #    
    #    # Validacion de xml por webservice
    #    cfdi = base64.encodestring(
    #        doc_xml.replace(codecs.BOM_UTF8, ''))
    #    
    #    print "************************ cfdi ******************* ", cfdi
    #    params = [
    #        user, password, cfdi]
    #    wsdl_client.soapproxy.config.dumpSOAPOut = 0
    #    wsdl_client.soapproxy.config.dumpSOAPIn = 0
    #    wsdl_client.soapproxy.config.debug = 0
    #    wsdl_client.soapproxy.config.dict_encoding = 'UTF-8'
    #    resultado = wsdl_client.recibeCFD(*params)
    #    
    #    print "**************** resultado ****************** ", resultado
    #    htz=int(inv_obj._get_time_zone(cr, uid, inv_ids, context=context))
    #    msg += resultado['resultados'] and resultado[
    #        'resultados']['mensaje'] or ''
    #    status = resultado['resultados'] and resultado[
    #        'resultados']['status'] or ''
    #    if status == '200' or status == '307':
    #        fecha_timbrado = resultado[
    #            'resultados']['fechaTimbrado'] or False
    #        fecha_timbrado = fecha_timbrado and time.strftime(
    #            '%Y-%m-%d %H:%M:%S', time.strptime(
    #            fecha_timbrado[:19], '%Y-%m-%dT%H:%M:%S')) or False
    #        fecha_timbrado = fecha_timbrado and datetime.strptime(
    #            fecha_timbrado, '%Y-%m-%d %H:%M:%S') + timedelta(
    #            hours=htz) or False
    #        cfdi_data = {
    #            'cfdi_cbb': resultado['resultados']['qrCode'] or False,  # ya lo regresa en base64
    #            'cfdi_sello': resultado['resultados'][
    #                'selloSAT'] or False,
    #            'cfdi_no_certificado': resultado['resultados'][
    #                'certificadoSAT'] or False,
    #            'cfdi_cadena_original': resultado['resultados'][
    #                'cadenaOriginal'] or False,
    #            'cfdi_fecha_timbrado': fecha_timbrado,
    #            'cfdi_xml': base64.decodestring(resultado[
    #                'resultados']['cfdiTimbrado'] or ''),  # este se necesita en uno que no es base64
    #            'cfdi_folio_fiscal': resultado['resultados']['uuid'] or '',
    #        }
    #        if cfdi_data.get('cfdi_xml', False):
    #            url_pac = '</"%s"><!--Para validar el XML CFDI puede descargar el certificado del PAC desde la siguiente liga: https://solucionfactible.com/cfdi/00001000000102699425.zip-->' % (
    #                comprobante)
    #            cfdi_data['cfdi_xml'] = cfdi_data[
    #                'cfdi_xml'].replace('</"%s">' % (comprobante), url_pac)
    #            file = base64.encodestring(
    #                cfdi_data['cfdi_xml'] or '')
    #            # self.cfdi_data_write(cr, uid, [invoice.id],
    #            # cfdi_data, context=context)
    #            cfdi_xml = cfdi_data.pop('cfdi_xml')
    #            if cfdi_xml:
    #                self.write(cr, uid, inv_ids, cfdi_data)
    #                cfdi_data['cfdi_xml'] = cfdi_xml
    #            msg = msg + _(
    #                "\nAsegúrese de que el archivo realmente ha generado correctamente en la SAT\nhttps://www.consulta.sat.gob.mx/sicofi_web/moduloECFD_plus/ValidadorCFDI/Validador%20cfdi.html")
    #        else:
    #            msg = msg + "\nCan't extract the file XML of PAC"
    #    elif status == '500' or status == '307':  # documento no es un cfd version 2, probablemente ya es un CFD version 3
    #        msg = _("Probablemente el archivo XML ya ha sido timbrado previamente y no es necesario volverlo a subir.\nO puede ser que el formato del archivo, no es el correcto.\nPor favor, visualice el archivo para corroborarlo y seguir con el siguiente paso o comuniquese con su administrador del sistema.\n") + (
    #            resultado['resultados']['mensaje'] or '') + (
    #            resultado['mensaje'] or '')
    #    else:
    #        msg = _("Ocurrio un error con la informacion de la factura. Contacte con el administrador.\n") + (
    #            resultado['resultados']['mensaje'] or '') + (
    #            resultado['mensaje'] or '')
    #        # Agrega exepcion para el mensaje porque no se detiene el flujo
    #        raise osv.except_osv('Error Factura Electronica! - ' + status, msg)
    #        #msg = msg + \
    #        #    "\nNo se pudo extraer el archivo XML del PAC"
    #
    #    return {'file': file, 'msg': msg, 'status': status, 'cfdi_xml': cfdi_xml}
    
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Factura', readonly=True, select=1, ondelete='restrict', required=True, help="Referencia sobre factura"),
        'xml_file': fields.binary('XML Asociado', required=True,
            filters='*.xml', help='Archivo XML recibido por el proveedor para validar la factura'),
        'state': fields.related('invoice_id','state', type='char', readonly=True, string='Estado factura'),
    }
    
account_invoice_confirm_xml()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
