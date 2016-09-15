#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import sys
from suds.client import Client
import unicodedata

# Convierte string a xml
from xml.etree import cElementTree as ET

# Url Webservice
url = 'http://localhost:8080/WebServiceAkkadian/ServicioWeb?wsdl'

class crm_kober_ws_control(osv.Model):
    _name = "crm.kober.ws.control"
    _table = "ws_control"
    
    def cron_ws_control(self, cr, uid, context=None):
        """
            Funcion que se ejecuta con el cron cada determinado tiempo
        """
        top = 5
        # Actualiza los clientes
        self.ws_get_cte_create(cr, uid, top, context=context)
        self.ws_get_cte_update(cr, uid, top, context=context)
        self.ws_get_cte_delete(cr, uid, top, context=context)
        print "*********** cron - updated clientes ************ "
        # Actualiza los contactos
        self.ws_get_ctecto_create(cr, uid, top, context=context)
        self.ws_get_ctecto_update(cr, uid, top, context=context)
        self.ws_get_ctecto_delete(cr, uid, top, context=context)
        print "*********** cron - updated contactos ************ "
        # Actualiza las direcciones del cliente
        self.ws_get_cteenviara_create(cr, uid, top, context=context)
        self.ws_get_cteenviara_update(cr, uid, top, context=context)
        self.ws_get_cteenviara_delete(cr, uid, top, context=context)
        print "*********** cron - updated direcciones ************ "
        # Actualiza los productos
        self.ws_get_art_create(cr, uid, top, context=context)
        self.ws_get_art_update(cr, uid, top, context=context)
        self.ws_get_art_delete(cr, uid, top, context=context)
        print "*********** cron - updated productos ************ "
        # Actualiza las listas de precios
        self.ws_get_listapreciosd_create(cr, uid, top, context=context)
        self.ws_get_listapreciosd_update(cr, uid, top, context=context)
        self.ws_get_listapreciosd_delete(cr, uid, top, context=context)
        print "*********** cron - updated listas de precios ************ "
        # Actualiza las ventas
        self.ws_get_ventas_create(cr, uid, top, context=context)
        self.ws_get_ventas_update(cr, uid, top, context=context)
        print "*********** cron - updated ventas ************ "
        return True
    
    def action_update_ws(self, cr, uid, ids, context=None):
        """
            Actualiza las tareas del Webservice de intelisis a openerp
        """
        print "***************************************************"
        print "***************************************************"
        print "***************************************************"
        print "***************************************************"
        print " ************* Actualiza webservice **************** ", ids
        
        top = 10
        
        for control in self.browse(cr, uid, ids, context=context):
            print "******************** control *************** ", control.ws_name
            #~ if control.ws_name == 'Cte':
                #~ # Actualiza los clientes
                #~ self.ws_get_cte_create(cr, uid, top, context=context)
                #~ self.ws_get_cte_update(cr, uid, top, context=context)
                #~ self.ws_get_cte_delete(cr, uid, top, context=context)
            #~ elif control.ws_name == 'CteCto':
                #~ # Actualiza los contactos
                #~ self.ws_get_ctecto_create(cr, uid, top, context=context)
                #~ self.ws_get_ctecto_update(cr, uid, top, context=context)
                #~ self.ws_get_ctecto_delete(cr, uid, top, context=context)
            #~ elif control.ws_name == 'CteEnviarA':
                #~ # Actualiza las direcciones del cliente
                #~ self.ws_get_cteenviara_create(cr, uid, top, context=context)
                #~ self.ws_get_cteenviara_update(cr, uid, top, context=context)
                #~ self.ws_get_cteenviara_delete(cr, uid, top, context=context)
            #~ elif control.ws_name == 'Art':
                #~ # Actualiza los productos
                #~ self.ws_get_art_create(cr, uid, top, context=context)
                #~ self.ws_get_art_update(cr, uid, top, context=context)
                #~ self.ws_get_art_delete(cr, uid, top, context=context)
                #~ break
            #~ elif control.ws_name == 'ListaPreciosD':
                #~ # Actualiza las listas de precios
                #~ self.ws_get_listapreciosd_create(cr, uid, top, context=context)
                #~ self.ws_get_listapreciosd_update(cr, uid, top, context=context)
                #~ self.ws_get_listapreciosd_delete(cr, uid, top, context=context)
            #~ elif control.ws_name == 'Venta':
                #~ # Actualiza las ventas
                #~ self.ws_get_ventas_create(cr, uid, top, context=context)
                #~ self.ws_get_ventas_update(cr, uid, top, context=context)
            #~ 
        # Actualiza la fecha de la ultima actualizacion del registro
        #self.write(cr, uid, ids, {'ws_date_update': time.strftime('%Y-%m-%d')}, context=None)
        print "************************* Fin del flujo ************************"
        return True
    
    def remove_tildes(self, string):
        """
            Elimina Acentos y caracteres especiales de la cadena para poder importarla
        """
        # Valida que sea de tipo texto
        if type(string) != 'unicode':
            string = unicode(string)
        # Eliminia caracteres especiales
        string = string.replace(u'\xd1', 'NNN')
        string = string.replace(u'\xf1', 'nnn')
        # Elimina espacios extra al inicio y final
        string = string.strip()
        return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))
    
    ##############
    ##    Metodos para Cliente
    ##############
    
    def ws_get_cte_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los nuevos clientes
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        print "************ contecta webservice *********** ", url
        client = Client(url)
        result = client.service.Get_Cte("N", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        print  "************** result encodeado ************** ", result
        tree = ET.XML(str(result))
        print "*********** result xml ************** ", tree
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        print "*********** xml valido ************** "
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Nombre': 'name',
            'Agente': 'user_id',
            'Direccion': 'street',
            'DireccionNumero': 'street3',
            'Delegacion': 'delegation',
            'Colonia': 'street2',
            'Poblacion': 'city',
            'Estado': 'state_id',
            'Pais': 'country_id',
            'CodigoPostal': 'zip',
            'RFC': 'vat2',
            'Telefonos': 'phone',
            'FAX': 'fax',
            'Grupo': 'category_id',
            'Categoria': 'category',
            'Familia': 'family',
            'Credito': 'credit',
            'PedidosParciales': 'partial_order',
            'Tipo': 'type_client',
            'Descuento': 'discount',
            'Condicion': 'condition',
            'DefMoneda': 'currency_id',
            'ListaPreciosEsp': 'price_list_esp',
            'Estatus': 'status',
            'Alta': 'date_create',
            'BloquearMorosos': 'block_morosos',
            'TieneMovimientos': 'have_mov',
            'SucursalCliente': 'branch_id',
            'SucursalNombre': 'branch',
            'TMEws_id': 'ws_id',
            'Cliente': 'client',
            'Rama': 'bunch',
        }
        
        # Equivalencias de campos intelisis-open sobre tipos de datos
        field_type = {
            'Nombre': 'char',
            'Agente': 'many2one',
            'Direccion': 'char',
            'DireccionNumero': 'char',
            'Delegacion': 'char',
            'Colonia': 'char',
            'Poblacion': 'char',
            'Estado': 'many2one',
            'Pais': 'many2one',
            'CodigoPostal': 'char',
            'RFC': 'char',
            'Telefonos': 'char',
            'FAX': 'char',
            'Grupo': 'many2one',
            'Categoria': 'char',
            'Familia': 'char',
            'Credito': 'char',
            'PedidosParciales': 'boolean',
            'Tipo': 'selection',
            'Descuento': 'float',
            'Condicion': 'char',
            'DefMoneda': 'many2one',
            'ListaPreciosEsp': 'char',
            'Estatus': 'selection',
            'Alta': 'date',
            'BloquearMorosos': 'char',
            'TieneMovimientos': 'boolean',
            'SucursalCliente': 'many2one',
            'SucursalNombre': 'char',
            'TMEws_id': 'char',
            'Cliente': 'char',
            'Rama': 'char',
        }
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        user_obj = self.pool.get('res.users')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        category_obj = self.pool.get('res.partner.category')
        currency_obj = self.pool.get('res.currency')
        branch_obj = self.pool.get('crm.access.branch')
        
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                print "************* row ********** ", field.tag, " *** ", field.text, " ** ", type(field.text)
                # Recorre los campos del cliente
                if field.tag == 'Agente':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    user_ids = user_obj.search(cr, uid, [('code', '=', field.text),])
                    if not user_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = 1
                    else:
                        vals[field_name[field.tag]] = user_ids[0]
                elif field.tag == 'Sucursal' or field.tag == 'SucursalNombre':
                    # Si es sucursal no hace nada
                    continue
                elif field.tag == 'SucursalEmpresa':
                    # Obtiene el id de la sucursal
                    branch_ids = branch_obj.search(cr, uid, [('code', '=', int(field.text) if field.text else 0),])
                    if not branch_ids:
                        #~ Si no esta la sucursal registrada, la da de alta
                        branch_name = row.find('Sucursal').text
                        branch_id = branch_obj.create(cr, uid, {'code': int(field.text) if field.text else 0, 'name': branch_name})
                        vals[field_name[field.tag]] = branch_id
                        print "************ suc no encontrada *********** ", branch_id
                    else:
                        print "************ suc encontrada *********** ", branch_ids
                        vals[field_name[field.tag]] = branch_ids[0]
                elif field.tag == 'SucursalCliente':
                    # Obtiene el id de la sucursal
                    branch_ids = branch_obj.search(cr, uid, [('code', '=', int(field.text) if field.text else 0),])
                    if not branch_ids:
                        #~ Si no esta la sucursal registrada, la da de alta
                        branch_name = row.find('SucursalNombre').text
                        branch_id = branch_obj.create(cr, uid, {'code': int(field.text) if field.text else 0, 'name': branch_name})
                        vals[field_name[field.tag]] = branch_id
                        print "************ suc no encontrada *********** ", branch_id
                    else:
                        print "************ suc encontrada *********** ", branch_ids
                        vals[field_name[field.tag]] = branch_ids[0]
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                elif field.tag == 'Estado':
                    # Busca el id del estado en openerp, si no existe lo da de alta
                    state_ids = state_obj.search(cr, uid, [('name', '=', field.text),])
                    if not state_ids:
                        # Revisa si esta dado de alta el pais
                        pais = row.find('Pais').text
                        pais = str(pais.encode('utf-8')) if pais else 'Mexico'
                        print "************ pais ************** ", pais, " ***** ", type(pais)
                        if pais == 'Mexico' or pais == 'México' or 'MEXICO':
                            country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                        else:
                            country_ids = country_obj.search(cr, uid, [('name', '=', pais),])
                            if not cuntry_ids:
                                # Si no esta dado de alta el pais crea el nuevo registro
                                country_id = country_obj.create(cr, uid, {'name': pais, 'code': pais[:2], })
                            else:
                                country_id = country_ids[0]
                        #~ Si no esta el estado registrado, crea el nuevo registro
                        code = str(field.text)
                        code = code[:3]
                        state_id = state_obj.create(cr, uid, {'name': str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' ', 'code': code, 'country_id': country_id })
                        # Agrega el id al cliente
                        vals[field_name[field.tag]] = state_id
                    else:
                        vals[field_name[field.tag]] = state_ids[0]
                elif field.tag == 'Pais':
                    # Revisa si pais es diferente de mexico, sino retorna el id
                    if field.text == 'Mexico' or field.text == 'México' or field.text == 'MEXICO':
                        country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                    else:
                        country_ids = country_obj.search(cr, uid, [('name', '=', field.text),])
                        if not cuntry_ids:
                            code = str(field.text)
                            # Si no esta dado de alta el pais crea el nuevo registro
                            country_id = country_obj.create(cr, uid, {'name': field.text, 'code': code[:2], })
                        else:
                            country_id = country_ids[0]
                    # Agrega el id al cliente
                    vals[field_name[field.tag]] = country_id
                elif field.tag == 'Grupo':
                    # Si no esta el grupo en las categorias lo agrega, relacionado con los tags de open
                    category_ids = category_obj.search(cr, uid, [('name', '=', field.text),])
                    if not category_ids:
                        #~ Si no esta la categoria registrada, crea el registro
                        category_id = category_obj.create(cr, uid, {'name': field.text, 'active': True })
                        vals[field_name[field.tag]] = category_id
                    else:
                        vals[field_name[field.tag]] = category_ids[0]
                elif field.tag == 'DefMoneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = int(currency_id)
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                
            # Agrega campos predefinidos
            vals['is_company'] = True
            vals['customer'] = True
            vals['spin_required'] = False
            vals['spin'] = ''
            
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals, type(vals)
            partner_id = partner_obj.create(cr, uid, vals, context=context)
            print "********************** partner *************** ", partner_id
        #~ context['webservice'] = False
    
    def ws_get_cte_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los clientes modificados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_Cte("A", top)
        result = result.decode('ascii', 'replace')
        print "************** result update ***************** ", result, ' ****** ', type(result)
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Nombre': 'name',
            'Agente': 'user_id',
            'Direccion': 'street',
            'DireccionNumero': 'street3',
            'Delegacion': 'delegation',
            'Colonia': 'street2',
            'Poblacion': 'city',
            'Estado': 'state_id',
            'Pais': 'country_id',
            'CodigoPostal': 'zip',
            'RFC': 'vat2',
            'Telefonos': 'phone',
            'FAX': 'fax',
            'Grupo': 'category_id',
            'Categoria': 'category',
            'Familia': 'family',
            'Credito': 'credit',
            'PedidosParciales': 'partial_order',
            'Tipo': 'type_client',
            'Descuento': 'discount',
            'Condicion': 'condition',
            'DefMoneda': 'currency_id',
            'ListaPreciosEsp': 'price_list_esp',
            'Estatus': 'status',
            'Alta': 'date_create',
            'BloquearMorosos': 'block_morosos',
            'TieneMovimientos': 'have_mov',
            'SucursalCliente': 'branch_id',
            'SucursalNombre': 'branch',
            'TMEws_id': 'ws_id',
            'Cliente': 'client',
            'Rama': 'bunch',
        }
        
        # Equivalencias de campos intelisis-open sobre tipos de datos
        field_type = {
            'Nombre': 'char',
            'Agente': 'many2one',
            'Direccion': 'char',
            'DireccionNumero': 'char',
            'Delegacion': 'char',
            'Colonia': 'char',
            'Poblacion': 'char',
            'Estado': 'many2one',
            'Pais': 'many2one',
            'CodigoPostal': 'char',
            'RFC': 'char',
            'Telefonos': 'char',
            'FAX': 'char',
            'Grupo': 'many2one',
            'Categoria': 'char',
            'Familia': 'char',
            'Credito': 'char',
            'PedidosParciales': 'boolean',
            'Tipo': 'selection',
            'Descuento': 'float',
            'Condicion': 'char',
            'DefMoneda': 'many2one',
            'ListaPreciosEsp': 'char',
            'Estatus': 'selection',
            'Alta': 'date',
            'BloquearMorosos': 'char',
            'TieneMovimientos': 'boolean',
            'SucursalCliente': 'many2one',
            'SucursalNombre': 'char',
            'TMEws_id': 'char',
            'Cliente': 'char',
            'Rama': 'char',
        }
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        user_obj = self.pool.get('res.users')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        category_obj = self.pool.get('res.partner.category')
        currency_obj = self.pool.get('res.currency')
        branch_obj = self.pool.get('crm.access.branch')
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a actualizar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                # Recorre los campos del cliente
                if field.tag == 'Agente':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    user_ids = user_obj.search(cr, uid, [('code', '=', field.text),])
                    if not user_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = user_ids[0]
                elif field.tag == 'Sucursal' or field.tag == 'SucursalNombre':
                    # Si es sucursal no hace nada
                    continue
                elif field.tag == 'SucursalEmpresa':
                    # Obtiene el id de la sucursal
                    branch_ids = branch_obj.search(cr, uid, [('code', '=', int(field.text) if field.text else 0),])
                    if not branch_ids:
                        #~ Si no esta la sucursal registrada, la da de alta
                        branch_name = row.find('Sucursal').text
                        branch_id = branch_obj.create(cr, uid, {'code': int(field.text) if field.text else 0, 'name': branch_name})
                        vals[field_name[field.tag]] = branch_id
                    else:
                        vals[field_name[field.tag]] = branch_ids[0]
                elif field.tag == 'SucursalCliente':
                    # Obtiene el id de la sucursal
                    branch_ids = branch_obj.search(cr, uid, [('code', '=', int(field.text) if field.text else 0),])
                    if not branch_ids:
                        #~ Si no esta la sucursal registrada, la da de alta
                        branch_name = row.find('SucursalNombre').text
                        branch_id = branch_obj.create(cr, uid, {'code': int(field.text) if field.text else 0, 'name': branch_name})
                        vals[field_name[field.tag]] = branch_id
                    else:
                        vals[field_name[field.tag]] = branch_ids[0]
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                elif field.tag == 'Estado':
                    # Busca el id del estado en openerp, si no existe lo da de alta
                    state_ids = state_obj.search(cr, uid, [('name', '=', field.text),])
                    if not state_ids:
                        # Revisa si esta dado de alta el pais
                        pais = row.find('Pais').text
                        pais = str(pais.encode('utf-8')) if pais else 'Mexico'
                        print "************ pais ************** ", pais, " ***** ", type(pais)
                        if pais == 'Mexico' or pais == 'México' or 'MEXICO':
                            country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                        else:
                            country_ids = country_obj.search(cr, uid, [('name', '=', pais),])
                            if not cuntry_ids:
                                # Si no esta dado de alta el pais crea el nuevo registro
                                country_id = country_obj.create(cr, uid, {'name': pais, 'code': pais[:2], })
                            else:
                                country_id = country_ids[0]
                        #~ Si no esta el estado registrado, crea el nuevo registro
                        code = str(field.text)
                        code = code[:3]
                        state_id = state_obj.create(cr, uid, {'name': str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' ', 'code': code, 'country_id': country_id })
                        # Agrega el id al cliente
                        vals[field_name[field.tag]] = state_id
                    else:
                        vals[field_name[field.tag]] = state_ids[0]
                elif field.tag == 'Pais':
                    # Revisa si pais es diferente de mexico, sino retorna el id
                    if field.text == 'Mexico' or field.text == 'México' or field.text == 'MEXICO':
                        country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                    else:
                        country_ids = country_obj.search(cr, uid, [('name', '=', field.text),])
                        if not cuntry_ids:
                            code = str(field.text)
                            # Si no esta dado de alta el pais crea el nuevo registro
                            country_id = country_obj.create(cr, uid, {'name': field.text, 'code': code[:2], })
                        else:
                            country_id = country_ids[0]
                    # Agrega el id al cliente
                    vals[field_name[field.tag]] = country_id
                elif field.tag == 'Grupo':
                    # Si no esta el grupo en las categorias lo agrega, relacionado con los tags de open
                    category_ids = category_obj.search(cr, uid, [('name', '=', field.text),])
                    if not category_ids:
                        #~ Si no esta la categoria registrada, crea el registro
                        category_id = category_obj.create(cr, uid, {'name': field.text, 'active': True })
                        vals[field_name[field.tag]] = category_id
                    else:
                        vals[field_name[field.tag]] = category_ids[0]
                elif field.tag == 'DefMoneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = currency_id
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            print "******************* resultado ***************** ", vals
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            print "************* partner ids ********** ", partner_ids, " ****** ", ws_id
            
            if not partner_ids:
                print "************** write - create cte ***************"
                # Agrega campos predefinidos
                vals['is_company'] = True
                vals['customer'] = True
                vals['spin_required'] = False
                vals['spin'] = ''
                # Agrega el nuevo registro
                partner_id = partner_obj.create(cr, uid, vals, context=context)
                print "********************** write - partner create *************** ", partner_id
            else:
                print "************** write - write cte ***************"
                # Modifica el registro
                partner_obj.write(cr, uid, partner_ids, vals, context=context)
                print "***************** write - partner modificado ********************** "
        #~ context['webservice'] = False
    
    def ws_get_cte_delete(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los clientes eliminados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_Cte("E", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        print "************* result ***************** ", result
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        
        # Recorre XML
        for row in tree.find('Rows'):
            # Recorre los campos a eliminar
            for field in row:
                # Busca el registro por medio del id del cliente
                ws_id = row.find('TMEws_id').text
                partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
                # Valida si se encontraron registros
                if len(partner_ids):
                    # Elimina el cliente 
                    partner_obj.unlink(cr, uid, partner_ids, context=context)
        #~ context['webservice'] = False
    
    def ws_put_cte(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los clientes a modificar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Obtiene el ws_id
            ws_id = partner.ws_id
            
            # Obtiene la moneda
            if partner.currency_id.name == 'USD':
                moneda = 'Dolares'
            else:
                moneda = 'Pesos'
            
            grupo = u''
            
            # Obtiene el grupo
            if partner.category_id:
                grupo_obj = partner.category_id
                grupo = grupo_obj.name
                grupo = grupo.encode('ascii', 'replace')
            else:
                grupo = ''
            
            # Obtiene la sucursal del cilente
            branch_id = str(partner.branch_id.code) if partner.branch_id.code else '0'
            if branch_id != '0' and len(branch_id) < 2:
                branch_id = '0' + branch_id
            
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                branch_id, # Sucursal
                str(partner.user_id.code) if partner.user_id else 'Null', # Agente
            ]
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
                
            print "**************** vals string array **************** ", vals_string_array
            
            p = self.remove_tildes(partner.name)
            print "************** name sin tildes **************** ", p
            
            # Genera la cadena con la informacion del cliente
            vals = [
                "Nombre = '" + self.remove_tildes(partner.name) + "'" if partner.name else "Nombre = ''",
                "Direccion = '" + self.remove_tildes(partner.street) + "'" if partner.street else "Direccion = ''",
                "DireccionNumero = '" + self.remove_tildes(partner.street3) + "'" if partner.street3 else "DireccionNumero = ''",
                "Delegacion = '" + self.remove_tildes(partner.delegation) + "'" if partner.delegation else "Delegacion = ''",
                "Colonia = '" + self.remove_tildes(partner.street2) + "'" if partner.street2 else "Colonia = ''",
                "Poblacion = '" + self.remove_tildes(partner.city) + "'" if partner.city else "Poblacion = ''",
                "Estado = '" + self.remove_tildes(partner.state_id.name) + "'" if partner.state_id else "Estado = ''",
                "Pais = '" + self.remove_tildes(partner.country_id.name) + "'" if partner.country_id else "Pais = ''",
                "CodigoPostal = '" + self.remove_tildes(partner.zip) + "'" if partner.zip else "CodigoPostal = ''",
                "RFC = '" + self.remove_tildes(partner.vat2) + "'" if partner.vat2 else "RFC = ''",
                "Telefonos = '" + self.remove_tildes(partner.phone) + "'" if partner.phone else "Telefonos = ''",
                "FAX = '" + self.remove_tildes(partner.fax) + "'" if partner.fax else "FAX = ''",
                "Categoria = '" + self.remove_tildes(partner.category) + "'" if partner.category else "Categoria = ''",
                "Grupo = '" + self.remove_tildes(grupo) + "'",
                "Familia = '" + self.remove_tildes(partner.family) + "'" if partner.family else "Familia = ''",
                "Credito = '" + self.remove_tildes(partner.credit) + "'" if partner.credit else "Credito = ''",
                "PedidosParciales = '" + self.remove_tildes(partner.partial_order) + "'" if partner.partial_order else "PedidosParciales = False",
                "Tipo = '" + self.remove_tildes(partner.type_client) + "'" if partner.type_client else "Tipo = ''",
                "Descuento = '" + self.remove_tildes(partner.discount) + "'" if partner.discount else "Descuento = ''",
                "Condicion = '" + self.remove_tildes(partner.condition) + "'" if partner.condition else "Condicion = ''",
                "DefMoneda = '" + self.remove_tildes(moneda) + "'",
                "ListaPreciosEsp = '" + self.remove_tildes(partner.price_list_esp) + "'" if partner.price_list_esp else "ListaPreciosEsp = ''",
                "Estatus = '" + self.remove_tildes(partner.status) + "'" if partner.status else "Estatus = ''",
                "Rama = '" + self.remove_tildes(partner.bunch) + "'" if partner.bunch else "Rama = ''",
            ]
            vals_string = u''
            vals_string = ", ".join(vals)
            print "******************** update ", ws_id, " ******************* ", vals_string
            
            # Conexion a webservice para la modificacion de clientes 
            client = Client(url)
            result = client.service.Put_Cte(vals_string, vals_string_array, ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = True
        return res
    
    def ws_post_cte(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los clientes a crear
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Obtiene la moneda
            if partner.currency_id.name == 'USD':
                moneda = 'Dolares'
            else:
                moneda = 'Pesos'
            
            grupo = u''
            
            print "******************* category_id ***** ", partner.category_id
            
            # Obtiene el grupo
            if partner.category_id:
                grupo_obj = partner.category_id
                grupo = grupo_obj.name
                grupo = grupo.encode('ascii', 'replace')
            else:
                grupo = u''
                
            print "**************** grupo ************** ", type(grupo)
            print "**************** grupo ************** ", grupo
            
            # Obtiene la sucursal del cilente
            branch_id = str(partner.branch_id.code) if partner.branch_id.code else '0'
            if branch_id != '0' and len(branch_id) < 2:
                branch_id = '0' + branch_id
                
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                branch_id, # Sucursal
                str(partner.user_id.code) if partner.user_id else 'Null', # Agente
            ]
            vals_string_array = u''
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
                
            print "*********** status *************** ", partner.status
            print "********** vals string array ************* ", vals_string_array
            
            # Genera la cadena con la informacion del cliente
            vals = [
                "'" + self.remove_tildes(partner.name) + "'" if partner.name else "''",
                "'" + self.remove_tildes(partner.street) + "'" if partner.street else "''",
                "'" + self.remove_tildes(partner.street3) + "'" if partner.street3 else "''",
                "'" + self.remove_tildes(partner.delegation) + "'" if partner.delegation else "''",
                "'" + self.remove_tildes(partner.street2) + "'" if partner.street2 else "''",
                "'" + self.remove_tildes(partner.city) + "'" if partner.city else "''",
                "'" + self.remove_tildes(partner.state_id.name) + "'" if partner.state_id else "''",
                "'" + self.remove_tildes(partner.country_id.name) + "'" if partner.country_id else "''",
                "'" + self.remove_tildes(partner.zip) + "'" if partner.zip else "''",
                "'" + self.remove_tildes(partner.vat2) + "'" if partner.vat2 else "''",
                "'" + self.remove_tildes(partner.phone) + "'" if partner.phone else "''",
                "'" + self.remove_tildes(partner.fax) + "'" if partner.fax else "''",
                "'" + self.remove_tildes(partner.category) + "'" if partner.category else "''",
                "'" + self.remove_tildes(grupo) + "'",
                "'" + self.remove_tildes(partner.family) + "'" if partner.family else "''",
                "'" + self.remove_tildes(partner.credit) + "'" if partner.credit else "''",
                "'" + self.remove_tildes(partner.partial_order) + "'" if partner.partial_order else "False",
                "'" + self.remove_tildes(partner.type_client) + "'" if partner.type_client else "''",
                "'" + self.remove_tildes(partner.discount) + "'" if partner.discount else "''",
                "'" + self.remove_tildes(partner.condition) + "'" if partner.condition else "''",
                "'" + self.remove_tildes(partner.price_list_esp) + "'" if partner.price_list_esp else "''",
                "'" + self.remove_tildes(moneda) + "'" if moneda else "''",
                "'" + self.remove_tildes(partner.status) + "'" if partner.status else "''",
                "convert(datetime, '" + self.remove_tildes(partner.date_create).replace('-','') + "')" if partner.date_create else "convert(datetime, '')",
                "'" + self.remove_tildes(partner.bunch) + "'" if partner.bunch else "''",
            ]
            vals_string = u''
            vals_string = ",".join(vals)
            print "******************** create ******************* ", vals_string
            
            # Conexion a webservice para la creacion de clientes 
            client = Client(url)
            result = client.service.Post_Cte(vals_string, vals_string_array)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            message = tree.find('Message')
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text == '100':
                partner_obj.write(cr, uid, [partner.id], {'ws_id': message.find('ws_id').text, 'client': message.find('cliente').text}, context=context)
            else:
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = True
        return res
    
    def ws_delete_cte(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los clientes a eliminar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a eliminar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            ws_id = partner.ws_id
            print "************ delete Cte **************** ", ws_id
            # Conexion a webservice para la eliminacion de clientes 
            client = Client(url)
            result = client.service.Delete_Cte(ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = True
        return res
    
    ##############
    ##    Metodos para Contacto
    ##############
    
    def ws_get_ctecto_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los nuevos contactos
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_CteCto("N", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Cliente': 'parent_id',
            'Nombre': 'name',
            'Cargo': 'function',
            'FechaNacimiento': 'date_birh',
            'Telefono': 'phone',
            'Extencion': 'extension',
            'eMail': 'email',
            'Atencion': 'attention',
            'Tratamiento': 'title',
            'Tipo': 'type_contact',
            'Sexo': 'sex',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open sobre los tipos de datos
        field_type = {
            'Cliente': 'many2one',
            'Nombre': 'char',
            'Cargo': 'char',
            'FechaNacimiento': 'date',
            'Telefono': 'char',
            'Extencion': 'char',
            'eMail': 'char',
            'Atencion': 'char',
            'Tratamiento': 'many2one',
            'Tipo': 'char',
            'Sexo': 'selection',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar el contacto
        partner_obj = self.pool.get('res.partner')
        title_obj = self.pool.get('res.partner.title')
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                print "************* row ********** ", field.tag, " *** ", field.text
                # Recorre los campos del contacto
                if field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                        #~ Agrega el usuario al cliente 
                        partner = partner_obj.browse(cr, uid, partner_ids[0], context=context)
                        vals['user_id'] = partner.user_id.id or False
                elif field.tag == 'Tratamiento':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    title_ids = title_obj.search(cr, uid, [('name', '=', field.text),])
                    if not title_ids:
                        #~ Si no esta el titulo registrado, crea el registro
                        title_id = category_obj.create(cr, uid, {'name': field.text})
                        vals[field_name[field.tag]] = title_id
                    else:
                        vals[field_name[field.tag]] = title_ids[0]
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                
            # Agrega campos predefinidos
            vals['is_company'] = False
            vals['customer'] = True
            
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals
            partner_id = partner_obj.create(cr, uid, vals, context=context)
            print "********************** partner *************** ", partner_id
        #~ context['webservice'] = False
    
    def ws_get_ctecto_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los contactos modificados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_CteCto("A", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Cliente': 'parent_id',
            'Nombre': 'name',
            'Cargo': 'function',
            'FechaNacimiento': 'date_birh',
            'Telefonos': 'phone',
            'Extencion': 'extension',
            'eMail': 'email',
            'Atencion': 'attention',
            'Tratamiento': 'title',
            'Tipo': 'type_contact',
            'Sexo': 'sex',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open sobre los tipos de datos
        field_type = {
            'Cliente': 'many2one',
            'Nombre': 'char',
            'Cargo': 'char',
            'FechaNacimiento': 'date',
            'Telefonos': 'char',
            'Extencion': 'char',
            'eMail': 'char',
            'Atencion': 'selection',
            'Tratamiento': 'many2one',
            'Tipo': 'char',
            'Sexo': 'selection',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar el contacto
        partner_obj = self.pool.get('res.partner')
        title_obj = self.pool.get('res.partner.title')
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                print "************* row ********** ", field.tag, " *** ", field.text
                # Recorre los campos del contacto
                if field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                        #~ Agrega el usuario al cliente 
                        partner = partner_obj.browse(cr, uid, partner_ids[0], context=context)
                        vals['user_id'] = partner.user_id.id or False
                elif field.tag == 'Tratamiento':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    title_ids = title_obj.search(cr, uid, [('name', '=', field.text),])
                    if not title_ids:
                        #~ Si no esta el titulo registrado, crea el registro
                        title_id = category_obj.create(cr, uid, {'name': field.text})
                        vals[field_name[field.tag]] = title_id
                    else:
                        vals[field_name[field.tag]] = title_ids[0]
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            print "******************* resultado ***************** ", vals
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            if not partner_ids:
                # Agrega campos predefinidos
                vals['is_company'] = False
                vals['customer'] = True
                # Agrega el nuevo registro
                partner_id = partner_obj.create(cr, uid, vals, context=context)
                print "********************** write - partner create *************** ", partner_id
            else:
                # Modifica el registro
                partner_obj.write(cr, uid, partner_ids, vals, context=context)
                print "***************** write - partner modificado ********************** "
        #~ context['webservice'] = False
    
    def ws_get_ctecto_delete(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los contactos eliminados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_CteCto("E", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        
        # Recorre XML
        for row in tree.find('Rows'):
            # Recorre los campos a eliminar
            for field in row:
                # Busca el registro por medio del id del cliente
                ws_id = row.find('TMEws_id').text
                partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
                # Si existe el registro lo elimina
                if len(partner_ids):
                    # Elimina el cliente 
                    partner_obj.unlink(cr, uid, partner_ids, context=context)
        #~ context['webservice'] = False
    
    def ws_put_ctecto(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los contactos a modificar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el contacto
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Obtiene el ws_id
            ws_id = partner.ws_id
            
            print "********************* ws_id **************** ", ws_id
            
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                str(partner.parent_id.ws_id) if partner.parent_id.ws_id else 'Null' # Cliente
            ]
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
            
            # Genera la cadena con la informacion del contacto
            vals = [
                "Nombre = '" + self.remove_tildes(partner.name) + "'" if partner.name else "Nombre =  ''",
                "Cargo = '" + self.remove_tildes(partner.function) + "'" if partner.function else "Cargo =  ''",
                "FechaNacimiento = convert(datetime, '" + self.remove_tildes(partner.date_birth).replace('-','') + "')" if partner.date_birth else "FechaNacimiento =  convert(datetime,'')",
                "Telefonos = '" + self.remove_tildes(partner.phone) + "'" if partner.phone else "Telefonos =  ''",
                "Extencion = '" + self.remove_tildes(partner.extension) + "'" if partner.extension else "Extencion =  ''",
                "eMail = '" + self.remove_tildes(partner.email) + "'" if partner.email else "eMail =  ''",
                "Atencion = '" + self.remove_tildes(partner.attention) + "'" if partner.attention else "Atencion =  ''",
                "Tratamiento = '" + self.remove_tildes(partner.title.name) + "'" if partner.title else "Tratamiento =  ''",
                "Tipo = '" + self.remove_tildes(partner.type_contact) + "'" if partner.type_contact else "Tipo =  ''",
                "Sexo = '" + self.remove_tildes(partner.sex) + "'" if partner.sex else "Sexo =  ''",
            ]
            vals_string = ','.join(vals)
            print "******************** update ", ws_id, " ******************* ", vals_string
            
            # Conexion a webservice para la modificacion de clientes 
            client = Client(url)
            result = client.service.Put_CteCto(vals_string, vals_string_array, ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    def ws_post_ctecto(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los contactos a crear
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el contacto
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Valida que el partner tenga asignado un padre
            print "************ ws valida padre crear contacto *********** ", partner.parent_id
            if not partner.parent_id:
                print "********** contacto sin padre *********** "
                continue
            
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                str(partner.parent_id.ws_id) if partner.parent_id.ws_id else 'Null', # Cliente
            ]
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
                
            print "******************** vals_string_array ***************** ", type(vals_string_array)
            print "******************** vals_string_array ***************** ", vals_string_array
            
            # Genera la cadena con la informacion del contacto
            vals = [
                "'" + self.remove_tildes(partner.name) + "'" if partner.name else "''",
                "'" + self.remove_tildes(partner.function) + "'" if partner.function else "''",
                "convert(datetime, '" + self.remove_tildes(partner.date_birth).replace('-','') + "')" if partner.date_birth else "convert(datetime, '')",
                "'" + self.remove_tildes(partner.phone) + "'" if partner.phone else "''",
                "'" + self.remove_tildes(partner.extension) + "'" if partner.extension else "''",
                "'" + self.remove_tildes(partner.email) + "'" if partner.email else "''",
                "'" + self.remove_tildes(partner.attention) + "'" if partner.attention else "''",
                "'" + self.remove_tildes(partner.title.name) + "'" if partner.title.name else "''",
                "'" + self.remove_tildes(partner.type_contact) + "'" if partner.type_contact else "''",
                "'" + self.remove_tildes(partner.sex) + "'" if partner.sex else "''",
            ]
            vals_string = ",".join(vals)
            print "******************** create ******************* ", vals_string
            
            # Conexion a webservice para la creacion de clientes 
            client = Client(url)
            result = client.service.Post_CteCto(vals_string, vals_string_array)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text == '100':
                print "************* ws de ctecto creado ************* ", tree.find('Message').text
                partner_obj.write(cr, uid, [partner.id], {'ws_id': tree.find('Message').text}, context=context)
            else:
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    def ws_delete_ctecto(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con los contactos a eliminar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a eliminar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            ws_id = partner.ws_id
            # Conexion a webservice para la eliminacion de contactos 
            client = Client(url)
            result = client.service.Delete_CteCto(ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    ##############
    ##    Metodos para Direcciones del cliente
    ##############
    
    def ws_get_cteenviara_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las nuevas direcciones
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        print "************ contecta webservice *********** ", url
        client = Client(url)
        result = client.service.Get_CteEnviarA("N", top)
        result1 = result.encode("utf-8")
        tree = ET.XML(str(result1))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Cliente': 'parent_id',
            'Nombre': 'name',
            'Direccion': 'street',
            'Delegacion': 'delegation',
            'Colonia': 'street2',
            'Poblacion': 'city',
            'Estado': 'state_id',
            'Pais': 'country_id',
            'CodigoPostal': 'zip',
            'Zona': 'region',
            'Telefonos': 'phone',
            'FAX': 'fax',
            'Estatus': 'status',
            'ListaPreciosEsp': 'price_list_esp',
            'Descuento': 'discount',
            'Condicion': 'condition',
            'Grupo': 'category_id',
            'Categoria': 'category',
            'Familia': 'family',
            'TieneMovimientos': 'have_mov',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Cliente': 'many2one',
            'Nombre': 'char',
            'Direccion': 'char',
            'Delegacion': 'char',
            'Colonia': 'char',
            'Poblacion': 'char',
            'Estado': 'many2one',
            'Pais': 'many2one',
            'CodigoPostal': 'char',
            'Zona': 'char',
            'Telefonos': 'char',
            'FAX': 'char',
            'Estatus': 'selection',
            'ListaPreciosEsp': 'char',
            'Descuento': 'float',
            'Condicion': 'char',
            'Grupo': 'many2one',
            'Categoria': 'selection',
            'Familia': 'selection',
            'TieneMovimientos': 'boolean',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar la direccion
        partner_obj = self.pool.get('res.partner')
        user_obj = self.pool.get('res.users')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        category_obj = self.pool.get('res.partner.category')
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                # Recorre los campos del cliente
                if field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                        #~ Agrega el usuario al cliente 
                        partner = partner_obj.browse(cr, uid, partner_ids[0], context=context)
                        vals['user_id'] = partner.user_id.id or False
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                elif field.tag == 'Estado':
                    # Busca el id del estado en openerp, si no existe lo da de alta
                    state_ids = state_obj.search(cr, uid, [('name', '=', field.text),])
                    if not state_ids:
                        # Revisa si esta dado de alta el pais
                        pais = row.find('Pais').text
                        pais = str(pais.encode('utf-8')) if pais else 'Mexico'
                        if pais == 'Mexico' or pais == 'México' or 'MEXICO':
                            country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                        else:
                            country_ids = country_obj.search(cr, uid, [('name', '=', pais),])
                            if not cuntry_ids:
                                # Si no esta dado de alta el pais crea el nuevo registro
                                country_id = country_obj.create(cr, uid, {'name': pais, 'code': pais[:2], })
                            else:
                                country_id = country_ids[0]
                        #~ Si no esta el estado registrado, crea el nuevo registro
                        code = str(field.text)
                        code = code[:3]
                        state_id = state_obj.create(cr, uid, {'name': str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' ', 'code': code, 'country_id': country_id })
                        print "***************** state_id ************* ", state_id
                        print "************** field name ************* ", field.tag, " - ", field_name[field.tag]
                        # Agrega el id al cliente
                        vals[field_name[field.tag]] = state_id
                    else:
                        vals[field_name[field.tag]] = state_ids[0]
                elif field.tag == 'Pais':
                    # Revisa si pais es diferente de mexico, sino retorna el id
                    if field.text == 'Mexico' or field.text == 'México' or field.text == 'MEXICO':
                        country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                    else:
                        country_ids = country_obj.search(cr, uid, [('name', '=', field.text),])
                        if not cuntry_ids:
                            code = str(field.text)
                            # Si no esta dado de alta el pais crea el nuevo registro
                            country_id = country_obj.create(cr, uid, {'name': field.text, 'code': code[:2], })
                        else:
                            country_id = country_ids[0]
                    # Agrega el id al cliente
                    vals[field_name[field.tag]] = country_id
                elif field.tag == 'Grupo':
                    # Si no esta el grupo en las categorias lo agrega, relacionado con los tags de open
                    category_ids = category_obj.search(cr, uid, [('name', '=', field.text),])
                    if not category_ids:
                        #~ Si no esta la categoria registrada, crea el registro
                        category_id = category_obj.create(cr, uid, {'name': field.text, 'active': True })
                        vals[field_name[field.tag]] = category_id
                    else:
                        vals[field_name[field.tag]] = category_ids[0]
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                
            # Agrega campos predefinidos
            vals['is_company'] = False
            vals['is_address'] = True
            vals['spin_required'] = False
            vals['customer'] = True
            
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals
            partner_id = partner_obj.create(cr, uid, vals, context=context)
            print "********************** partner *************** ", partner_id
        #~ context['webservice'] = False
    
    def ws_get_cteenviara_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las direcciones de los clientes modificadas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_CteEnviarA("A", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Cliente': 'parent_id',
            'Nombre': 'name',
            'Direccion': 'street',
            'Delegacion': 'delegation',
            'Colonia': 'street2',
            'Poblacion': 'city',
            'Estado': 'state_id',
            'Pais': 'country_id',
            'CodigoPostal': 'zip',
            'Zona': 'region',
            'Telefonos': 'phone',
            'FAX': 'fax',
            'Estatus': 'status',
            'ListaPreciosEsp': 'price_list_esp',
            'Descuento': 'discount',
            'Condicion': 'condition',
            'Grupo': 'category_id',
            'Categoria': 'category',
            'Familia': 'family',
            'TieneMovimientos': 'have_mov',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Cliente': 'many2one',
            'Nombre': 'char',
            'Direccion': 'char',
            'Delegacion': 'char',
            'Colonia': 'char',
            'Poblacion': 'char',
            'Estado': 'many2one',
            'Pais': 'many2one',
            'CodigoPostal': 'char',
            'Zona': 'char',
            'Telefonos': 'char',
            'FAX': 'char',
            'Estatus': 'selection',
            'ListaPreciosEsp': 'char',
            'Descuento': 'float',
            'Condicion': 'char',
            'Grupo': 'many2one',
            'Categoria': 'selection',
            'Familia': 'selection',
            'TieneMovimientos': 'boolean',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para actualizar la direccion
        partner_obj = self.pool.get('res.partner')
        user_obj = self.pool.get('res.users')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        category_obj = self.pool.get('res.partner.category')
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                # Recorre los campos del cliente
                if field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                        #~ Agrega el usuario al cliente 
                        partner = partner_obj.browse(cr, uid, partner_ids[0], context=context)
                        vals['user_id'] = partner.user_id.id or False
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                elif field.tag == 'Estado':
                    # Busca el id del estado en openerp, si no existe lo da de alta
                    state_ids = state_obj.search(cr, uid, [('name', '=', field.text),])
                    if not state_ids:
                        # Revisa si esta dado de alta el pais
                        pais = row.find('Pais').text
                        pais = str(pais.encode('utf-8')) if pais else 'Mexico'
                        if pais == 'Mexico' or pais == 'México' or 'MEXICO':
                            country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                        else:
                            country_ids = country_obj.search(cr, uid, [('name', '=', pais),])
                            if not cuntry_ids:
                                # Si no esta dado de alta el pais crea el nuevo registro
                                country_id = country_obj.create(cr, uid, {'name': pais, 'code': pais[:2], })
                            else:
                                country_id = country_ids[0]
                        #~ Si no esta el estado registrado, crea el nuevo registro
                        code = str(field.text)
                        code = code[:3]
                        state_id = state_obj.create(cr, uid, {'name': str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' ', 'code': code, 'country_id': country_id })
                        print "***************** state_id ************* ", state_id
                        print "************** field name ************* ", field.tag, " - ", field_name[field.tag]
                        # Agrega el id al cliente
                        vals[field_name[field.tag]] = state_id
                    else:
                        vals[field_name[field.tag]] = state_ids[0]
                elif field.tag == 'Pais':
                    # Revisa si pais es diferente de mexico, sino retorna el id
                    if field.text == 'Mexico' or field.text == 'México' or field.text == 'MEXICO':
                        country_id = country_obj.search(cr, uid, [('code', '=', 'MX'),])[0]
                    else:
                        country_id = country_obj.search(cr, uid, [('name', '=', field.text),])[0]
                        if not cuntry_id:
                            code = str(field.text)
                            # Si no esta dado de alta el pais crea el nuevo registro
                            country_id = country_obj.create(cr, uid, {'name': str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' ', 'code': code[:2], })
                    # Agrega el id al cliente
                    vals[field_name[field.tag]] = country_id
                elif field.tag == 'Grupo':
                    # Si no esta el grupo en las categorias lo agrega, relacionado con los tags de open
                    category_ids = category_obj.search(cr, uid, [('name', '=', field.text),])
                    if not category_ids:
                        #~ Si no esta la categoria registrada, crea el registro
                        category_id = category_obj.create(cr, uid, {'name': field.text, 'active': True })
                        vals[field_name[field.tag]] = category_id
                    else:
                        vals[field_name[field.tag]] = category_ids[0]
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            print "******************* resultado ***************** ", vals
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            if not partner_ids:
                # Agrega campos predefinidos
                vals['is_company'] = False
                vals['is_address'] = True
                vals['spin_required'] = False
                vals['customer'] = True
                # Agrega el nuevo registro
                partner_id = partner_obj.create(cr, uid, vals, context=context)
                print "********************** write - partner create *************** ", partner_id
            else:
                # Modifica el registro
                partner_obj.write(cr, uid, partner_ids, vals, context=context)
                print "***************** write - partner modificado ********************** "
        #~ context['webservice'] = False
    
    def ws_get_cteenviara_delete(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las direcciones eliminadas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de direcciones a eliminar 
        client = Client(url)
        result = client.service.Get_CteEnviarA("E", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        
        # Recorre XML
        for row in tree.find('Rows'):
            # Recorre los campos a eliminar
            for field in row:
                # Busca el registro por medio del id del cliente
                ws_id = row.find('TMEws_id').text
                partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', ws_id),])
                # Valida si se encontraron registros
                if len(partner_ids):
                    # Elimina el cliente 
                    partner_obj.unlink(cr, uid, partner_ids, context=context)
        #~ context['webservice'] = False
    
    def ws_put_cteenviara(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con las direcciones de clientes a modificar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Obtiene el ws_id
            ws_id = partner.ws_id
            
            # Obtiene el grupo
            if partner.category_id:
                grupo_obj = partner.category_id
                grupo = grupo_obj.name
            else:
                grupo = ''
            
            # Nombre del Agente que atiende al cliente
            agente = partner.user_id.code if partner.user_id else '',
            
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                str(partner.parent_id.ws_id) if partner.parent_id.ws_id else 'Null',  # Cliente
            ]
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
            
            # Genera la cadena con la informacion del cliente
            vals = [
                "Nombre = '" + self.remove_tildes(partner.name) + "'" if partner.name else "Nombre = ''",
                "Direccion = '" + self.remove_tildes(partner.street) + "'" if partner.street else "Direccion = ''",
                "Delegacion = '" + self.remove_tildes(partner.delegation) + "'" if partner.delegation else "Delegacion = ''",
                "Colonia = '" + self.remove_tildes(partner.street2) + "'" if partner.street2 else "Colonia = ''",
                "Poblacion = '" + self.remove_tildes(partner.city) + "'" if partner.city else "Poblacion = ''",
                "Estado = '" + self.remove_tildes(partner.state_id.name) + "'" if partner.state_id else "Estado = ''",
                "Pais = '" + self.remove_tildes(partner.country_id.name) + "'" if partner.country_id else "Pais = ''",
                "CodigoPostal = '" + self.remove_tildes(partner.zip) + "'" if partner.zip else "CodigoPostal = ''",
                "Zona = '" + self.remove_tildes(partner.region) + "'" if partner.region else "Zona = ''",
                "Telefonos = '" + self.remove_tildes(partner.phone) + "'" if partner.phone else "Telefonos = ''",
                "FAX = '" + self.remove_tildes(partner.fax) + "'" if partner.fax else "FAX = ''",
                "Estatus = '" + self.remove_tildes(partner.status) + "'" if partner.status else "Estatus = ''",
                "ListaPreciosEsp = '" + self.remove_tildes(partner.price_list_esp) + "'" if partner.price_list_esp else "ListaPreciosEsp = ''",
                "Descuento = '" + self.remove_tildes(partner.discount) + "'" if partner.discount else "Descuento = ''",
                "Condicion = '" + self.remove_tildes(partner.condition) + "'" if partner.condition else "Condicion = ''",
                "Grupo = '" + self.remove_tildes(grupo) + "'",
                "Categoria = '" + self.remove_tildes(partner.category) + "'" if partner.category else "Categoria = ''",
                "Familia = '" + self.remove_tildes(partner.family) + "'" if partner.family else "Familia = ''"
            ]
            vals_string = ','.join(vals)
            print "******************** update ", ws_id, " ******************* ", vals_string
            
            # Conexion a webservice para la modificacion de direccion 
            client = Client(url)
            result = client.service.Put_CteEnviarA(vals_string, vals_string_array, ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    def ws_post_cteenviara(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con las direcciones a crear
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a actualizar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            # Obtiene el grupo
            if partner.category_id:
                grupo_obj = partner.category_id
                grupo = grupo_obj.name.encode('ascii', 'replace')
            else:
                grupo = ''
            
            # Informacion del cliente que provienen de un catalogo
            vals_array = [
                str(partner.parent_id.ws_id) if partner.parent_id.ws_id else 'Null', # Cliente
                str(partner.user_id.code) if partner.user_id else 'Null', # Agente
            ]
            if len(vals_array) == 1:
                vals_string_array = vals_array[0]
            else:
                vals_string_array = ",".join(vals_array)
            
            # Genera la cadena con la informacion del cliente
                vals = [
                    "'" + self.remove_tildes(partner.name) + "'" if partner.name else "''",
                    "'" + self.remove_tildes(partner.street) + "'" if partner.street else "''", # Direccion
                    "'" + self.remove_tildes(partner.street2) + "'" if partner.street2 else "''", # Colonia
                    "'" + self.remove_tildes(partner.delegation) + "'" if partner.delegation else "''", # Delegacion
                    "'" + self.remove_tildes(partner.city) + "'" if partner.city else "''", # Poblacion
                    "'" + self.remove_tildes(partner.state_id.name) + "'" if partner.state_id else "''", # Estado
                    "'" + self.remove_tildes(partner.country_id.name) + "'" if partner.country_id else "''", # Pais
                    "'" + self.remove_tildes(partner.region) + "'" if partner.region else "''", # Zona
                    "'" + self.remove_tildes(partner.zip) + "'" if partner.zip else "''", # CodigoPostal
                    "'" + self.remove_tildes(partner.phone) + "'" if partner.phone else "''", # Telefonos
                    "'" + self.remove_tildes(partner.fax) + "'" if partner.fax else "''", # FAX
                    "'" + self.remove_tildes(partner.status) + "'" if partner.status else "''",
                    "'" + self.remove_tildes(partner.price_list_esp) + "'" if partner.price_list_esp else "''", # ListaPreciosEsp
                    "'" + self.remove_tildes(partner.condition) + "'" if partner.condition else "''",
                    "'" + self.remove_tildes(partner.discount) + "'" if partner.discount else "''",
                    "'" + self.remove_tildes(partner.category) + "'" if partner.category else "''",
                    "'" + self.remove_tildes(grupo) + "'",
                    "'" + self.remove_tildes(partner.family) + "'" if partner.family else "''",
                ]
            vals_string = ",".join(vals)
            print "******************** create ******************* ", vals_string
            
            # Conexion a webservice para la creacion de clientes 
            client = Client(url)
            result = client.service.Post_CteEnviarA(vals_string, vals_string_array)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text == '100':
                # Actualiza el ws_id
                partner_obj.write(cr, uid, [partner.id], {'ws_id': tree.find('Message').text}, context=context)
            else:
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    def ws_delete_cteenviara(self, cr, uid, ids, context=None):
        """
            Actualizacion de campos de openerp a intelisis con las direcciones a eliminar
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        res = True
        
        # Recorre los registros a eliminar
        for partner in partner_obj.browse(cr, uid, ids, context=context):
            ws_id = partner.ws_id
            # Conexion a webservice para la eliminacion de clientes 
            client = Client(url)
            result = client.service.Delete_CteEnviarA(ws_id)
            result = result.encode('ascii', 'replace')
            print "******************** result ******************** ", result
            result = result.encode("utf-8")
            tree = ET.XML(str(result))
            
            # Valida que el resultado haya sido el deseado
            if tree.find('Value').text != '100':
                # Error en el webservice
                raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
                res = False
        #~ context['webservice'] = False
        return res
    
    ##############
    ##    Metodos para Productos
    ##############
    
    def ws_get_art_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los productos
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de productos nuevos 
        print "************ contecta webservice *********** ", url
        client = Client(url)
        result = client.service.Get_Art("N", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        print "**************** result **************** ", result
        tree = ET.XML(str(result))
        print "*********** result xml ************** ", tree
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        print "*********** xml valido ************** "
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Articulo': 'name',
            'Descripcion1': 'description',
            'Descripcion2': 'description2',
            'NombreCorto': 'default_code',
            'Grupo': 'group_value',
            'Categoria': 'category',
            'Familia': 'family',
            'UnidadTraspaso': 'uom_id',
            'Tipo': 'type',
            'PrecioLista': 'list_price',
            'Estatus': 'status',
            'Precio2': 'price2',
            'Precio3': 'price3',
            'Precio4': 'price4',
            'Precio5': 'price5',
            'Precio6': 'price6',
            'Precio7': 'price7',
            'Precio8': 'price8',
            'Precio9': 'price9',
            'Precio10': 'price10',
            'TieneMovimientos': 'have_mov',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Articulo': 'char',
            'Descripcion1': 'text',
            'Descripcion2': 'text',
            'NombreCorto': 'char',
            'Grupo': 'char',
            'Categoria': 'char',
            'Familia': 'char',
            'UnidadTraspaso': 'many2one',
            'Tipo': 'selection',
            'PrecioLista': 'float',
            'Estatus': 'selection',
            'Precio2': 'float',
            'Precio3': 'float',
            'Precio4': 'float',
            'Precio5': 'float',
            'Precio6': 'float',
            'Precio7': 'float',
            'Precio8': 'float',
            'Precio9': 'float',
            'Precio10': 'float',
            'TieneMovimientos': 'boolean',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar el producto
        uom_obj = self.pool.get('product.uom')
        uom_categ_obj = self.pool.get('product.uom.categ')
        product_obj = self.pool.get('product.product')
        
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                
                print " ************** field ", field.tag, " - ", field.text, " **************** ", field_type[field.tag]
                
                # Recorre los registros
                if field.tag == 'Tipo':
                    # Valida si el tipo es normal o servicio
                    if field.text == 'Servicio':
                        vals[field_name[field.tag]] = 'service'
                    else:
                        vals[field_name[field.tag]] = 'product'
                elif field.tag == 'UnidadTraspaso':
                    # Si no esta la unidad, la agrega
                    uom_ids = uom_obj.search(cr, uid, [('name', '=', field.text),])
                    if not uom_ids:
                        # Crea la categoria de la unidad de medida
                        uom_categ_id = uom_categ_obj.create(cr, uid, {'name': field.text})
                        print "***************** unidad categoria ***************** ", uom_categ_id
                        #~ Si no esta la unidad registrada, crea el registro
                        uom_id = uom_obj.create(cr, uid, {'name': field.text, 'category_id': uom_categ_id, 'uom_type': 'reference', 'rounding': 1.0, 'factor': 1.0, 'active': True})
                        vals[field_name[field.tag]] = uom_id
                        vals['uom_po_id'] = uom_id
                        print "****************** unidad id ***************** ", uom_id
                    else:
                        vals[field_name[field.tag]] = uom_ids[0]
                        vals['uom_po_id'] = uom_ids[0]
                        print "****************** unidad ids ***************** ", uom_ids
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO' or field.text == 'DESCONTINUADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals
            product_id = product_obj.create(cr, uid, vals, context=context)
            print "********************** partner *************** ", product_id
    
    def ws_get_art_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los productos modificados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_Art("A", top)
        result = result.encode('ascii', 'replace')
        print "*************** result *************** ", result
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        print "************ xml result ************* ", tree
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Articulo': 'name',
            'Descripcion1': 'description',
            'Descripcion2': 'description2',
            'NombreCorto': 'default_code',
            'Grupo': 'group_value',
            'Categoria': 'category',
            'Familia': 'family',
            'UnidadTraspaso': 'uom_id',
            'Tipo': 'type',
            'PrecioLista': 'list_price',
            'Estatus': 'status',
            'Precio2': 'price2',
            'Precio3': 'price3',
            'Precio4': 'price4',
            'Precio5': 'price5',
            'Precio6': 'price6',
            'Precio7': 'price7',
            'Precio8': 'price8',
            'Precio9': 'price9',
            'Precio10': 'price10',
            'TieneMovimientos': 'have_mov',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Articulo': 'char',
            'Descripcion1': 'text',
            'Descripcion2': 'text',
            'NombreCorto': 'char',
            'Grupo': 'char',
            'Categoria': 'char',
            'Familia': 'char',
            'UnidadTraspaso': 'many2one',
            'Tipo': 'selection',
            'PrecioLista': 'float',
            'Estatus': 'selection',
            'Precio2': 'float',
            'Precio3': 'float',
            'Precio4': 'float',
            'Precio5': 'float',
            'Precio6': 'float',
            'Precio7': 'float',
            'Precio8': 'float',
            'Precio9': 'float',
            'Precio10': 'float',
            'TieneMovimientos': 'boolean',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar el producto
        uom_obj = self.pool.get('product.uom')
        uom_categ_obj = self.pool.get('product.uom.categ')
        product_obj = self.pool.get('product.product')
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a actualizar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                if field.tag == 'Tipo':
                    # Valida si el tipo es normal o servicio
                    if field.text == 'Servicio':
                        vals[field_name[field.tag]] = 'service'
                    else:
                        vals[field_name[field.tag]] = 'product'
                elif field.tag == 'UnidadTraspaso':
                    # Si no esta la unidad, la agrega
                    uom_ids = uom_obj.search(cr, uid, [('name', '=', field.text),])
                    if not uom_ids:
                        # Crea la categoria de la unidad de medida
                        uom_categ_id = uom_categ_obj.create(cr, uid, {'name': field.text})
                        #~ Si no esta la unidad registrada, crea el registro
                        uom_id = uom_obj.create(cr, uid, {'name': field.text, 'category_id': uom_categ_id, 'uom_type': 'reference', 'rounding': 1.0, 'factor': 1.0, 'active': True})
                        vals[field_name[field.tag]] = uom_id
                        vals['uom_po_id'] = uom_id
                    else:
                        vals[field_name[field.tag]] = uom_ids[0]
                        vals['uom_po_id'] = uom_ids[0]
                elif field.tag == 'Estatus':
                    # Valida que el estatus sea correcto
                    if field.text == 'ALTA' or field.text == 'BAJA' or field.text == 'BLOQUEADO' or field.text == 'DESCONTINUADO':
                        vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else 'ALTA'
                    else:
                        vals[field_name[field.tag]] = 'ALTA'
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            print "******************* resultado ***************** ", vals
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            product_ids = product_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            if not product_ids:
                # Agrega el nuevo registro
                product_id = product_obj.create(cr, uid, vals, context=context)
                print "********************** write - product create *************** ", product_id
            else:
                # Modifica el registro
                product_obj.write(cr, uid, product_ids, vals, context=context)
                print "***************** write - producto modificado ********************** "
    
    def ws_get_art_delete(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con los productos eliminados
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de productos a eliminar
        client = Client(url)
        result = client.service.Get_Art("E", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Objetos requeridos para eliminar el producto
        product_obj = self.pool.get('product.product')
        
        # Recorre XML
        for row in tree.find('Rows'):
            # Recorre los campos a eliminar
            for field in row:
                # Busca el registro por medio del id del producto
                ws_id = row.find('TMEws_id').text
                product_ids = product_obj.search(cr, uid, [('ws_id', '=', ws_id),])
                # Valida si se encontraron registros
                if len(product_ids):
                    # Elimina el producto 
                    product_obj.unlink(cr, uid, product_ids, context=context)
    
    ##############
    ##    Metodos para Listas de Precios
    ##############
    
    def ws_get_listapreciosd_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las listas de precios
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de listas de precios nuevas 
        print "************ contecta webservice *********** ", url
        client = Client(url)
        result = client.service.Get_ListaPreciosD("N", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        print "************************** result ************************** ", result
        tree = ET.XML(str(result))
        print "*********** result xml ************** ", tree
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        print "*********** xml valido ************** "
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Lista': 'name',
            'Moneda': 'currency_id',
            'Artws_id': 'product_id',
            'Precio': 'list_price',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos 
        field_type = {
            'Lista': 'char',
            'Moneda': 'many2one',
            'Artws_id': 'many2one',
            'Precio': 'float',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar la lista de precios
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        list_price_obj = self.pool.get('product.list.price')
        
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                # Recorre los registros
                if field.tag == 'Artws_id':
                    # Obtiene el id del producto en openerp, si no lo encuentra deja el campo vacio
                    product_ids = product_obj.search(cr, uid, [('ws_id', '=', str(field.text)),])
                    if not product_ids:
                        #~ Si no esta el producto registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = product_ids[0]
                elif field.tag == 'Articulo':
                    continue;
                elif field.tag == 'Moneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = currency_id
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals
            list_price_id = list_price_obj.create(cr, uid, vals, context=context)
            print "********************** partner *************** ", list_price_id
    
    def ws_get_listapreciosd_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las listas de precio modificadas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de clientes nuevos 
        client = Client(url)
        result = client.service.Get_ListaPreciosD("A", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Lista': 'name',
            'Moneda': 'currency_id',
            'Artws_id': 'product_id',
            'Precio': 'list_price',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos 
        field_type = {
            'Lista': 'char',
            'Moneda': 'many2one',
            'Artws_id': 'many2one',
            'Precio': 'float',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar el cliente
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        list_price_obj = self.pool.get('product.list.price')
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            # Recorre los campos a actualizar
            for field in row:
                # Valida que el field tenga valor
                if not field.text: 
                   continue
                if field.tag == 'Artws_id':
                    # Obtiene el id del producto en openerp, si no lo encuentra deja el campo vacio
                    product_ids = product_obj.search(cr, uid, [('ws_id', '=', str(field.text)),])
                    if not product_ids:
                        #~ Si no esta el producto registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = product_ids[0]
                elif field.tag == 'Articulo':
                    continue;
                elif field.tag == 'Moneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = currency_id
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            print "******************* resultado ***************** ", vals
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            list_price_ids = list_price_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            if not list_price_ids:
                # Agrega el nuevo registro
                list_price_id = list_price_obj.create(cr, uid, vals, context=context)
                print "********************** write - partner create *************** ", list_price_id
            else:
                # Modifica el registro
                list_price_obj.write(cr, uid, list_price_ids, vals, context=context)
                print "***************** write - lista precio modificada ********************** "
    
    def ws_get_listapreciosd_delete(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las listas de precio eliminadas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de listas de precios a eliminar
        client = Client(url)
        result = client.service.Get_ListaPreciosD("E", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Objetos requeridos para registrar la lista de precios
        list_price_obj = self.pool.get('product.list.price')
        
        # Recorre XML
        for row in tree.find('Rows'):
            # Recorre los campos a eliminar
            for field in row:
                # Busca el registro por medio del id del cliente
                ws_id = row.find('TMEws_id').text
                list_price_ids = list_price_obj.search(cr, uid, [('ws_id', '=', ws_id),])
                # Valida si se encontraron registros
                if len(list_price_ids):
                    # Elimina el cliente 
                    list_price_obj.unlink(cr, uid, list_price_ids, context=context)
    
    ##############
    ##    Metodos para Facturas
    ##############
    
    def ws_get_ventas_create(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las Facturas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de facturas nuevas 
        print "************ contecta webservice *********** ", url
        client = Client(url)
        result = client.service.Get_Ventas("N", top)
        result = result.encode('ascii', 'replace')
        result = result.encode("utf-8")
        print "*********** result xml ************** ", result
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Mov': 'mov',
            'MovId': 'name',
            'FechaEmision': 'date_invoice',
            'Moneda': 'currency_id',
            'Observaciones': 'notes',
            'Estatus': 'status',
            'Cliente': 'partner_id2',
            'EnviarA': 'partner_id',
            'Agente': 'user_id',
            'FechaRequerida': 'date_req',
            'Condicion': 'condition',
            'Vencimiento': 'date_expired',
            'Descuento': 'discount',
            'DescuentoGlobal': 'global_discount',
            'Importe': 'amount_untaxed2',
            'Impuestos': 'amount_tax2',
            'Ejercicio': 'exercise',
            'Periodo': 'period',
            'FechaRegistro': 'date_start',
            'FechaConclusion': 'date_finish',
            'ListaPreciosEsp': 'price_list_esp',
            'Sucursal': 'branch',
            'SucursalVenta': 'branch_sale',
            'TMEws_id': 'ws_id',
        }
        
        field_detail = {
            'FacturaId': 'invoice_id',
            'Cantidad': 'quantity',
            'Almacen': 'stock',
            'Articulo': 'product_id',
            'Precio': 'price_unit',
            'Impuesto': 'invoice_line_tax_id',
            'Unidad': 'uos_id',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Mov': 'selection',
            'MovId': 'char',
            'FechaEmision': 'date',
            'Moneda': 'many2one',
            'Observaciones': 'text',
            'Estatus': 'selection',
            'Cliente': 'many2one',
            'EnviarA': 'many2one',
            'Agente': 'many2one',
            'FechaRequerida': 'date',
            'Condicion': 'char',
            'Vencimiento': 'date',
            'Descuento': 'char',
            'DescuentoGlobal': 'char',
            'Importe': 'float',
            'Impuestos': 'float',
            'Ejercicio': 'char',
            'Periodo': 'char',
            'FechaRegistro': 'date',
            'FechaConclusion': 'date',
            'ListaPreciosEsp': 'char',
            'Sucursal': 'char',
            'SucursalVenta': 'char',
            'TMEws_id': 'char',
        }
        
        field_detail_type = {
            'FacturaId': 'many2one',
            'Cantidad': 'float',
            'Almacen': 'char',
            'Articulo': 'many2one',
            'Precio': 'float',
            'Impuesto': 'many2one',
            'Unidad': 'many2one',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar la lista de precios
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        user_obj = self.pool.get('res.users')
        product_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        uom_categ_obj = self.pool.get('product.uom.categ')
        tax_obj = self.pool.get('account.tax')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        branch_obj = self.pool.get('crm.access.branch')
        
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            inv_lines = []
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text and field.tag != 'VentasD': 
                   continue
                # Recorre los registros
                if field.tag == 'Id':
                    continue
                elif field.tag == 'VentasD':
                    print "************** entra ventasd ******************** "
                    line_data = {}
                    # Recorre los detalles de la factura
                    for lines in field:
                        print "************** detalle linea ******************** ", lines
                        for line in lines:
                            # Valida que el field de la linea tenga valor
                            if not line.text: 
                               continue
                            if line.tag == 'Articulo':
                                # Obtiene el id del producto en openerp, si no lo encuentra deja el campo vacio
                                product_ids = product_obj.search(cr, uid, [('ws_id', '=', line.text),])
                                if not product_ids:
                                    #~ Si no esta el producto registrado, deja el campo vacio
                                    line_data[field_detail[line.tag]] = None
                                else:
                                    line_data[field_detail[line.tag]] = product_ids[0]
                                line_data['name'] = line.text
                            elif line.tag == 'Unidad':
                                # Si no esta la unidad, la agrega
                                uom_ids = uom_obj.search(cr, uid, [('name', '=', line.text),])
                                if not uom_ids:
                                    # Crea la categoria de la unidad de medida
                                    uom_categ_id = uom_categ_obj.create(cr, uid, {'name': line.text})
                                    #~ Si no esta la unidad registrada, crea el registro
                                    uom_id = uom_obj.create(cr, uid, {'name': line.text, 'category_id': uom_categ_id, 'uom_type': 'reference', 'rounding': 1.0, 'factor': 1.0, 'active': True})
                                    line_data[field_detail[line.tag]] = uom_id
                                else:
                                    line_data[field_detail[line.tag]] = uom_ids[0]
                            elif line.tag == 'Impuesto':
                                # Obtiene los impuestos a aplicar
                                iva = '%' + str(line.text).replace('.0','') + '%'
                                print "**************** iva *********** ", iva
                                tax_ids = tax_obj.search(cr, uid, [('name', 'like', iva),('type_tax_use','=','sale')])
                                line_data[field_detail[line.tag]] = [[6, False, tax_ids]]
                            else:
                                # Valida el tipo de dato del campo
                                if field_detail_type[line.tag] == 'boolean':
                                    # Agrega el valor a los registros booleanos
                                    line_data[field_detail[line.tag]] = bool(line.text)
                                elif field_detail_type[line.tag] == 'float':
                                    # Agrega el valor a los registros flotantes
                                    line_data[field_detail[line.tag]] = float(line.text)
                                elif field_detail_type[line.tag] == 'int':
                                    # Agrega el valor a los registros enteros
                                    line_data[field_detail[line.tag]] = int(line.text)
                                elif field_detail_type[line.tag] == 'text':
                                    # Agrega el valor a los registros text
                                    if line.text:
                                        line_data[field_detail[line.tag]] = str(line.text.encode('utf-8'))
                                    else:
                                        line_data[field_detail[line.tag]] = ''
                                elif field_detail_type[line.tag] == 'date':
                                    # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                                    if line.text:
                                        if len(line.text) >= 10:
                                            date_value =  line.text
                                            date_value = date_value[:10]
                                            # Agrega el valor a los registros de fecha
                                            line_data[field_detail[line.tag]] = date_value[:10]
                                else:
                                    # Agrega el valor a los registros char y selection
                                    if line.text:
                                        line_data[field_detail[line.tag]] = str(line.text.encode('utf-8'))
                                    else:
                                        line_data[field_detail[line.tag]] = ''
                        line_data['account_id'] = 282
                        print "**************** line data ************* ", line_data
                        # Crea la linea de la factura
                        inv_line_id = invoice_line_obj.create(cr, uid, line_data, context=context)
                        inv_lines.append(int(inv_line_id))
                        #inv_lines.append(line_data)
                    # Agrega a la factura las lineas
                    vals['invoice_line'] = [(6, 0, inv_lines)]
                    print "************** inv_lines *************** ", inv_lines
                elif field.tag == 'Agente':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    user_ids = user_obj.search(cr, uid, [('code', '=', field.text),])
                    if not user_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = user_ids[0]
                elif field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                elif field.tag == 'EnviarA':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                elif field.tag == 'Moneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = currency_id
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            vals['state'] = 'open'
            vals['type'] = 'in_invoice'
            vals['number'] = vals['name']
            
            # Agrega el nuevo registro
            print "******************* resultado ***************** ", vals
            invoice_id = invoice_obj.create(cr, uid, vals, context=context)
            print "********************** venta *************** ", invoice_id
            # Crea las lineas de factura
            #for line_data in inv_lines:
            #        line_data['invoice_id'] = invoice_id
            #        print "************** line data ***************** ", line_data
            #        inv_line_id = invoice_line_obj.create(cr, uid, line_data, context=context)
    
    def ws_get_ventas_update(self, cr, uid, top, context=None):
        """
            Actualizacion de campos de intelisis a openerp con las facturas modificadas
        """
        # Agrega al context el parametro de webservice que indica que proviene del webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        # Conexion a webservice para la obtencion de facturas modificadas
        client = Client(url)
        result = client.service.Get_Ventas("A", top)
        result = result.encode("utf-8")
        tree = ET.XML(str(result))
        
        # Valida que el resultado haya sido el deseado
        if tree.find('Value').text != '100':
            # Error en el webservice
            raise osv.except_osv('Webservice ERROR! (' + tree.find('Value').text + ')', 'A ocurrido un error al actualizar el webservice - ' + tree.find('Message').text)
        
        # Equivalencias de campos intelisis-open
        field_name = {
            'Mov': 'mov',
            'MovId': 'name',
            'FechaEmision': 'date_invoice',
            'Moneda': 'currency_id',
            'Observaciones': 'notes',
            'Estatus': 'status',
            'Cliente': 'partner_id2',
            'EnviarA': 'partner_id',
            'Agente': 'user_id',
            'FechaRequerida': 'date_req',
            'Condicion': 'condition',
            'Vencimiento': 'date_expired',
            'Descuento': 'discount',
            'DescuentoGlobal': 'global_discount',
            'Importe': 'amount_untaxed2',
            'Impuestos': 'amount_tax2',
            'Ejercicio': 'exercise',
            'Periodo': 'period',
            'FechaRegistro': 'date_start',
            'FechaConclusion': 'date_finish',
            'ListaPreciosEsp': 'price_list_esp',
            'Sucursal': 'branch',
            'SucursalVenta': 'branch_sale',
            'TMEws_id': 'ws_id',
        }
        
        field_detail = {
            'FacturaId': 'invoice_id',
            'Cantidad': 'quantity',
            'Almacen': 'stock',
            'Articulo': 'product_id',
            'Precio': 'price_unit',
            'Impuesto': 'invoice_line_tax_id',
            'Unidad': 'uos_id',
            'TMEws_id': 'ws_id',
        }
        
        # Equivalencias de campos intelisis-open con los tipos de datos
        field_type = {
            'Mov': 'selection',
            'MovId': 'char',
            'FechaEmision': 'date',
            'Moneda': 'many2one',
            'Observaciones': 'text',
            'Estatus': 'selection',
            'Cliente': 'many2one',
            'EnviarA': 'many2one',
            'Agente': 'many2one',
            'FechaRequerida': 'date',
            'Condicion': 'char',
            'Vencimiento': 'date',
            'Descuento': 'char',
            'DescuentoGlobal': 'char',
            'Importe': 'float',
            'Impuestos': 'float',
            'Ejercicio': 'char',
            'Periodo': 'char',
            'FechaRegistro': 'date',
            'FechaConclusion': 'date',
            'ListaPreciosEsp': 'char',
            'Sucursal': 'char',
            'SucursalVenta': 'char',
            'TMEws_id': 'char',
        }
        
        field_detail_type = {
            'FacturaId': 'many2one',
            'Cantidad': 'float',
            'Almacen': 'char',
            'Articulo': 'many2one',
            'Precio': 'float',
            'Impuesto': 'many2one',
            'Unidad': 'many2one',
            'TMEws_id': 'char',
        }
        
        # Objetos requeridos para registrar la lista de precios
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        user_obj = self.pool.get('res.users')
        product_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        uom_categ_obj = self.pool.get('product.uom.categ')
        tax_obj = self.pool.get('account.tax')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        branch_obj = self.pool.get('crm.access.branch')
        
        print "************ recorre xml ************** "
        
        # Recorre XML
        for row in tree.find('Rows'):
            vals = {}
            inv_lines = []
            # Recorre los campos a agregar
            for field in row:
                # Valida que el field tenga valor
                if not field.text and field.tag != 'VentasD': 
                   continue
                # Recorre los registros
                if field.tag == 'Id':
                    continue
                elif field.tag == 'VentasD':
                    print "************** entra ventasd ******************** "
                    line_data = {}
                    # Recorre los detalles de la factura
                    for lines in field:
                        print "************** detalle linea ******************** ", lines
                        for line in lines:
                            # Valida que el field de la linea tenga valor
                            if not line.text: 
                               continue
                            if line.tag == 'Articulo':
                                # Obtiene el id del producto en openerp, si no lo encuentra deja el campo vacio
                                product_ids = product_obj.search(cr, uid, [('ws_id', '=', line.text),])
                                if not product_ids:
                                    #~ Si no esta el producto registrado, deja el campo vacio
                                    line_data[field_detail[line.tag]] = None
                                else:
                                    line_data[field_detail[line.tag]] = product_ids[0]
                                line_data['name'] = line.text
                            elif line.tag == 'Unidad':
                                # Si no esta la unidad, la agrega
                                uom_ids = uom_obj.search(cr, uid, [('name', '=', line.text),])
                                if not uom_ids:
                                    # Crea la categoria de la unidad de medida
                                    uom_categ_id = uom_categ_obj.create(cr, uid, {'name': line.text})
                                    #~ Si no esta la unidad registrada, crea el registro
                                    uom_id = uom_obj.create(cr, uid, {'name': line.text, 'category_id': uom_categ_id, 'uom_type': 'reference', 'rounding': 1.0, 'factor': 1.0, 'active': True})
                                    line_data[field_detail[line.tag]] = uom_id
                                else:
                                    line_data[field_detail[line.tag]] = uom_ids[0]
                            elif line.tag == 'Impuesto':
                                # Obtiene los impuestos a aplicar
                                iva = '%' + str(line.text).replace('.0','') + '%'
                                print "**************** iva *********** ", iva
                                tax_ids = tax_obj.search(cr, uid, [('name', 'like', iva),('type_tax_use','=','sale')])
                                line_data[field_detail[line.tag]] = [[6, 0, tax_ids]]
                            else:
                                # Valida el tipo de dato del campo
                                if field_detail_type[line.tag] == 'boolean':
                                    # Agrega el valor a los registros booleanos
                                    line_data[field_detail[line.tag]] = bool(line.text)
                                elif field_detail_type[line.tag] == 'float':
                                    # Agrega el valor a los registros flotantes
                                    line_data[field_detail[line.tag]] = float(line.text)
                                elif field_detail_type[line.tag] == 'int':
                                    # Agrega el valor a los registros enteros
                                    line_data[field_detail[line.tag]] = int(line.text)
                                elif field_detail_type[line.tag] == 'text':
                                    # Agrega el valor a los registros text
                                    if line.text:
                                        line_data[field_detail[line.tag]] = str(line.text.encode('utf-8'))
                                    else:
                                        line_data[field_detail[line.tag]] = ''
                                elif field_detail_type[line.tag] == 'date':
                                    # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                                    if line.text:
                                        if len(line.text) >= 10:
                                            date_value =  line.text
                                            date_value = date_value[:10]
                                            # Agrega el valor a los registros de fecha
                                            line_data[field_detail[line.tag]] = date_value[:10]
                                else:
                                    # Agrega el valor a los registros char y selection
                                    if line.text:
                                        line_data[field_detail[line.tag]] = str(line.text.encode('utf-8'))
                                    else:
                                        line_data[field_detail[line.tag]] = ''
                        line_data['account_id'] = 282
                        print "**************** line data ************* ", line_data
                        # Crea la linea de la factura
                        inv_line_id = invoice_line_obj.create(cr, uid, line_data, context=context)
                        inv_lines.append(int(inv_line_id))
                        #inv_lines.append(line_data)
                    # Agrega a la factura las lineas
                    vals['invoice_line'] = [(6, 0, inv_lines)]
                    print "************** inv_lines *************** ", inv_lines
                elif field.tag == 'Agente':
                    # Obtiene el id del vendedor en openerp, si no lo encuentra deja el campo vacio
                    user_ids = user_obj.search(cr, uid, [('code', '=', field.text),])
                    if not user_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = user_ids[0]
                elif field.tag == 'Cliente':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                elif field.tag == 'EnviarA':
                    # Obtiene el id del cliente en openerp, si no lo encuentra deja el campo vacio
                    partner_ids = partner_obj.search(cr, uid, [('ws_id', '=', field.text),])
                    if not partner_ids:
                        #~ Si no esta el usuario registrado, deja el campo vacio
                        vals[field_name[field.tag]] = None
                    else:
                        vals[field_name[field.tag]] = partner_ids[0]
                elif field.tag == 'Moneda':
                    # Revisa si es pesos o dolares
                    if field.text == 'Dolares':
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'USD'),])[0]
                    else:
                        currency_id = currency_obj.search(cr, uid, [('name', '=', 'MXN'),])[0]
                    vals[field_name[field.tag]] = currency_id
                else:
                    # Valida el tipo de dato del campo
                    if field_type[field.tag] == 'boolean':
                        # Agrega el valor a los registros booleanos
                        vals[field_name[field.tag]] = bool(field.text) if field.text == 'True' or field.text == 'true' or field.text == True else False
                    elif field_type[field.tag] == 'float':
                        # Agrega el valor a los registros flotantes
                        vals[field_name[field.tag]] = float(field.text) if field.text else 0.0
                    elif field_type[field.tag] == 'int':
                        # Agrega el valor a los registros enteros
                        vals[field_name[field.tag]] = int(field.text) if field.text else 0
                    elif field_type[field.tag] == 'text':
                        # Agrega el valor a los registros texto
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
                    elif field_type[field.tag] == 'date':
                        # Valida que el formato de fecha contenga los caracteres minimos sino lo omite
                        if field.text:
                            if len(field.text) >= 10:
                                date_value =  field.text
                                date_value = date_value[:10]
                                # Agrega el valor a los registros de fecha
                                vals[field_name[field.tag]] = date_value[:10]
                    else:
                        # Agrega el valor a los registros char y selection
                        if field.text:
                            vals[field_name[field.tag]] = str(field.text).replace('nnn', str('ñ')).replace('NNN', str('Ñ')).strip() if field.text else ' '
                        else:
                            vals[field_name[field.tag]] = ''
            
            # Identifica el campo a modificar
            ws_id = row.find('TMEws_id').text
            invoice_ids = invoice_obj.search(cr, uid, [('ws_id', '=', ws_id),])
            
            if not invoice_ids:
                vals['state'] = 'open'
                vals['type'] = 'in_invoice'
                vals['number'] = vals['name']
                # Agrega el nuevo registro
                invoice_id = invoice_obj.create(cr, uid, vals, context=context)
                
                #for line_data in inv_lines:
                #    line_data['invoice_id'] = invoice_id
                #    inv_line_id = invoice_line_obj.create(cr, uid, line_data, context=context)
                print "********************** write - invoice create *************** ", invoice_id
            else:
                # Elimina las lineas anteriores
                invoice_line_ids = invoice_line_obj.search(cr, uid, [('invoice_id', '=', invoice_ids[0]),])
                # Valida si se encontraron registros
                if len(invoice_line_ids):
                    list_price_obj.unlink(cr, uid, invoice_line_ids, context=context)
                
                # Modifica el registro
                invoice_obj.write(cr, uid, invoice_ids, vals, context=context)
                print "***************** write - invoice modificada ********************** "
    
    _columns = {
        'ws_name': fields.char('Nombre', size=128, required=True, readonly=True),
        'ws_cve': fields.char('Codigo', size=64, required=True),
        'ws_number': fields.integer('Numero siguiente', required=True),
        'ws_update': fields.boolean('Actualizar'),
        'ws_date_update': fields.date('Ultima actualizacion', readonly=True),
    }
    
    _defaults = {
        'ws_number': 1,
        'ws_update': False
    }
    
crm_kober_ws_control()
