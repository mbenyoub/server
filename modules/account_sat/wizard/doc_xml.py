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

import tempfile
import base64
import os
from xml.dom import minidom
# import libxml2
# import libxslt
# import zipfile
# import StringIO
# import OpenSSL
import hashlib
import codecs

# ---------------------------------------------------------
# Generacion XML
# ---------------------------------------------------------
    
def exec_command_pipe(name, *args):
    """
    @param name :
    """
    # Agregue esta funcion, ya que con la nueva funcion original, de tools no
    # funciona
    prog = tools.find_in_path(name)
    if not prog:
        raise Exception('Couldn\'t find %s' % name)
    if os.name == "nt":
        cmd = '"'+prog+'" '+' '.join(args)
    else:
        cmd = prog+' '+' '.join(args)
    return os.popen2(cmd, 'b')

# TODO: Eliminar esta funcionalidad, mejor agregar al path la aplicacion
# que deseamos
def find_in_subpath(name, subpath):
    """
    @param name :
    @param subpath :
    """
    if os.path.isdir(subpath):
        path = [dir for dir in map(lambda x: os.path.join(subpath, x),
                os.listdir(subpath)) if os.path.isdir(dir)]
        for dir in path:
            val = os.path.join(dir, name)
            if os.path.isfile(val) or os.path.islink(val):
                return val
    return None

# TODO: Agregar una libreria para esto
def conv_ascii(text):
    """
        @param text : text that need convert vowels accented & characters to ASCII
        Converts accented vowels, ñ and ç to their ASCII equivalent characters
    """
    old_chars = [
        'a', 'e', 'i', 'o', 'u', 'à', 'è', 'ì', 'ò', 'ù', 'ä', 'ë', 'ï', 'ö',
        'ü', 'â', 'ê', 'î', 'ô', 'û', 'Á', 'É', 'Í', 'Ó', 'Ú', 'À', 'È', 'Ì',
        'Ò', 'Ù', 'Ä', 'Ë', 'Ï', 'Ö', 'Ü', 'Â', 'Ê', 'Î', 'Ô', 'Û', 'ñ', 'Ñ',
        'ç', 'Ç', 'ª', 'º', '°', ' ', 'Ã', 'Ø','á','é','í','ó','ú'
    ]
    new_chars = [
        'a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o',
        'u', 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I',
        'O', 'U', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I', 'O', 'U', 'n', 'N',
        'c', 'C', 'a', 'o', 'o', ' ', 'A', '0','a','e','i','o','u'
    ]
    for old, new in zip(old_chars, new_chars):
        try:
            text = text.replace(unicode(old, 'UTF-8'), new)
        except:
            try:
                text = text.replace(old, new)
            except:
                raise osv.except_osv(_('Warning !'), _(
                    "Ocurrio un error al decodificar el texto ASCII [%s] en el caracter [%s]") % (text, old))
    return text

def clearline(text):
    """
        Elimina espacios y saltos de linea sobre el texto
    """
    text = text.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    return text

def clearspace(text):
    """
        Elimina espacios y saltos de linea sobre el texto y espacios en blanco
    """
    text = clearline(text).replace(' ','')
    return text

def _dict_key(key, reference=False):
    """
        Agrega la referencia a la etiqueta

        @param data_dict : Dictionary with data from invoice
    """
    if reference:
        key = "%s:%s"%(reference,clearspace(key))
    return key

def format_xml(doc_xml, fname='reporte-xml', context=None):
    """
        Agrega a la informacion general sobre la estructura del xml (Encabezado, identacion, encodeo, etc.)
    """
    # Genera archivo temporal para xml
    (fileno_xml, fname_xml) = tempfile.mkstemp(
        '.xml', fname)
    fname_txt = fname_xml + '.txt'
    f = open(fname_xml, 'w')
    doc_xml.writexml(
        f, indent='    ', addindent='    ', newl='\r\n', encoding='UTF-8')
    f.close()
    os.close(fileno_xml)
    
    # Agrega formato sobre estructura xml y encodeo de caracteres
    data_xml = doc_xml.toxml('UTF-8')
    data_xml = codecs.BOM_UTF8 + data_xml
    data_xml = data_xml.replace(
        '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="UTF-8"?>\n')
    return data_xml

def _dict_iteritems_sort(data_dict, reference):
        """
            Ordena los items y retorna un listado con la informacion de [elemento, atributo]
            
            @param data_dict : Dictionary with data
            @param reference : Valor a concatenar sobre el atributo
        """
        # Obtiene los atributos del elemento
        keys = data_dict.keys()
        key_item_sort = []
        
        print "******************* keys ******************** ", keys
        
        # Reordena el diccionario
        for key_too in keys:
            value = data_dict[key_too]
            # Valida que el contenido relacionado sea un diccionario o una lista
            if (isinstance(value, dict) or isinstance(value, list)) and reference:
                key_too = _dict_key(key_too,reference)
            # Ordena el arreglo a la estructura de (elemento, atributo)
            key_item_sort.append([key_too, value])
        return key_item_sort

def dict2xml(data_dict, node=False, doc=False, reference=False, context=None):
    """
        Genera estructura de archivo XML a partir de un diccionario de datos
        
        @param data_dict : Diccionario con los attributos del XML a generar
        @param node : Nodo del XML donde se va a agregar el diccionario
        @param doc : Documento XML generado, donde se va a trabajar
    """
    # Valida que el context sea un diccionario
    if context is None:
        context = {}
    
    # Valida si hay un nodo padre sobre el campo a registrar en el diccionario
    parent = False
    if node:
        parent = True
    
    print "************ data dict funcion ************* ", data_dict
    
    # Recorre el diccionario de datos
    for element, attribute in _dict_iteritems_sort(data_dict, reference):
        #Correccion en convertir a str contabilidad electronica#
        try:
            print "************* element *************** ", element
            print "************* attribute ************ ", attribute
        except UnicodeEncodeError:
            pass 
        # Si no existe un documento ligado lo crea
        if not parent:
            doc = minidom.Document()
        # Valida si el atributo es un diccionario
        if isinstance(attribute, dict):
            # Valida si hay un nodo padre relacionado
            if not parent:
                # Crea nodo y agrega sus atributos
                node = doc.createElement(element)
                dict2xml(attribute, node, doc, reference)
            else:
                # Crea nodo hijo y sus atributos
                child = doc.createElement(element)
                dict2xml(attribute, child, doc, reference)
                # Relaciona nodo creado con el nodo padre
                node.appendChild(child)
        # Valida si el atributo es un arreglo
        elif isinstance(attribute, list):
            # Recorre los registros
            for attr in attribute:
                # Crea un nuevo nodo
                if isinstance(attr, dict):
                    child = doc.createElement(element)
                    # Agrega los atributos sobre el nodo
                    dict2xml(attr, child, doc, reference)
                    # Relaciona con el nodo padre
                    node.appendChild(child)
                # Agrega texto al nodo
                elif isinstance(attr, str) or isinstance(attr, unicode):
                    node.text = conv_ascii(attr)
                else:
                    node.text = str(attr)  
        else:
            # Si es un registro de tipo string agrega el attributo sobre el registro
            if isinstance(attribute, str) or isinstance(attribute, unicode):
                attribute = conv_ascii(attribute)
            else:
                attribute = str(attribute)
            # Valida si se va a registrar un texto sobre el nodo del xml
            if element == 'xml-text':
                # Registra texto sobre el nodo
                node.text = attribute
            else:
                # Agrega atributo sobre e nodo
                node.setAttribute(element, attribute)
    # Relaciona el nodo generado sobre el nodo padre
    if not parent:
        doc.appendChild(node)
    return doc

def xml2binary(xml_data):
    """
        Transforma un xml a un archivo binario en formato string a travez del metodo encode
        
        @param xml_data : Archivo XML a transformar
    """
    binary = base64.encodestring(xml_data)
    return binary

def binary2file(binary_data, file_prefix="", file_suffix=""):
    """
        Transforma el campo de binario a archivo
        
        @param binary_data : Field binary with the information of certificate
                of the company
        @param file_prefix : Name to be used for create the file with the
                information of certificate
        @file_suffix : Sufix to be used for the file that create in this function
    """
    (fileno, fname) = tempfile.mkstemp(file_suffix, file_prefix)
    f = open(fname, 'wb')
    f.write(base64.decodestring(binary_data))
    f.close()
    os.close(fileno)
    return fname

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: