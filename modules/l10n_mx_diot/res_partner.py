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

import time
import base64
from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.osv):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner'
    
    def action_create_diot(self, cr, uid, ids, context=None):
        """
            Genera el archivo diot
        """
        ##print************* DIOT ****************"
        
        partner = self.browse(cr, uid, ids[0], context=context)
        
        # Obtiene la informacion para generar el archivo
        diot_array = []
        diot_array.append(str(partner.diot_type1) if partner.diot_type1 else '00')
        diot_array.append(str(partner.diot_type2) if partner.diot_type2 else '00')
        diot_array.append(partner.vat[2:] if partner.vat else '')
        diot_array.append(str(partner.diot_fiscal_number) if partner.diot_fiscal_number else '')
        diot_array.append(str(partner.diot_name_ex) if partner.diot_name_ex else '')
        diot_array.append(str(partner.country_id.code) if partner.country_id.code != 'MX' else '0' if partner.country_id else '0')
        diot_array.append(str(partner.diot_nationality) if partner.diot_nationality else '')
        diot_array.append(str(partner.diot_act_value) if partner.diot_act_value else '0')
        diot_array.append(str(partner.diot_act_value2) if partner.diot_act_value2 else '0')
        diot_array.append(str(partner.diot_act_value3) if partner.diot_act_value3 else '0')
        diot_array.append(str(partner.diot_act_value4) if partner.diot_act_value4 else '0')
        diot_array.append(str(partner.diot_act_value5) if partner.diot_act_value5 else '0')
        diot_array.append(str(partner.diot_act_value6) if partner.diot_act_value6 else '0')
        diot_array.append(str(partner.diot_act_value7) if partner.diot_act_value7 else '0')
        diot_array.append(str(partner.diot_act_value8) if partner.diot_act_value8 else '0')
        diot_array.append(str(partner.diot_act_value9) if partner.diot_act_value9 else '0')
        diot_array.append(str(partner.diot_act_value10) if partner.diot_act_value10 else '0')
        diot_array.append(str(partner.diot_act_value11) if partner.diot_act_value11 else '0')
        diot_array.append(str(partner.diot_act_value12) if partner.diot_act_value12 else '0')
        diot_array.append(str(partner.diot_act_value13) if partner.diot_act_value13 else '0')
        
        data = ('|').join(diot_array)
        
        attachment_obj = self.pool.get('ir.attachment')
        
        #print "***************** data ****************** ", data
        
        ##print******************** ids ***************** ", ids
        
        # Si existe otro archivo con diot en los adjuntos lo elimina
        attach_ids = attachment_obj.search(cr, uid, [('description','=','Archivo DIOT'), ('res_id','=',ids[0]), ('res_model','=','res.partner')], context=context)
        if attach_ids:
            attachment_obj.unlink(cr, uid, attach_ids, context=context)
        
        # Genera el adjunto con el archivo diot
        data_attach = {
            'name': 'DIOT',
            'datas': base64.encodestring(data or '') or False,
            'datas_fname': 'DIOT.txt',
            'description': 'Archivo DIOT',
            'res_model': 'res.partner',
            'res_id': ids[0],
        }
        attach = attachment_obj.create(cr, uid, data_attach, context=context)
        
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'base', 'view_attachment_form')
        res_id = res and res[1] or False
        
        #~ Redirecciona al formulario de solicitud
        return {
            'name':_("Adjuntos"),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'ir.attachment', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id' : attach, # id of the object to which to redirected
        }
    
    _columns = {
        'type_of_third':fields.selection([
            ('04', ' 04 - Proveedor Nacional'),
            ('05', ' 05 - Proveedor Extranjero'),
            ('15', ' 15 - Proveedor Global')],
            'Tipo de tercero (DIOT)', help='Tipo de tercero de este contacto'),
        'type_of_operation':fields.selection([
            ('03', ' 03 - Prestacion de servicios profesionales'),
            ('06', ' 06 - Arrendamiento de Inmuebles'),
            ('85', ' 85 - Otros')],
            'Tipo de operacion (DIOT)', help='Tipo de operaciones realizadas por este contacto'),
        'country_of_residence':fields.selection([
            ('AR', 'AR - Argentina'),
            ('AT', 'AT - Austria'),
            ('AU', 'AU - Australia'),
            ('BE', 'BE - Belgica'),
            ('BC', 'BC - Belice'),
            ('BO', 'BO - Bolivia'),
            ('BR', 'BR - Brasil'),
            ('CA', 'CA - Canada'),
            ('CL', 'CL - Chile'),
            ('CM', 'CM - Camerun'),
            ('CN', 'CN - China'),
            ('CO', 'CO - Colombia'),
            ('CR', 'CR - Republica de Costa Rica'),
            ('CU', 'CU - Cuba'),
            ('DM', 'DM - Republica Dominicana'),
            ('DZ', 'DZ - Argelia'),
            ('EC', 'EC - Ecuador'),
            ('EG', 'EG - Egipto'),
            ('EH', 'EH - Sahara del Oeste'),
            ('EO', 'EO - Estado Independiente de Samoa Occidental'),
            ('ES', 'ES - España'),
            ('ET', 'ET - Etiopia'),
            ('GR', 'GR - Grecia'),
            ('GT', 'GT - Guatemala'),
            ('GU', 'GU - Guam'),
            ('GW', 'GW - Guinea Bissau'),
            ('GY', 'GY - Republica de Guyana'),
            ('GZ', 'GZ - Islas de Guernesey, Jersey, Alderney, '\
                'Isla Great Sark, Herm, Little Sark, Berchou, Jethou, '\
                'Lihou (Islas del Canal)'),
            ('HK', 'HK - Hong Kong'),
            ('HM', 'HM - Islas Heard and Mc Donald'),
            ('HN', 'HN - República de Honduras'),
            ('HT', 'HT - Haiti'),
            ('HU', 'HU - Hungaria'),
            ('ID', 'ID - Indonesia'),
            ('IE', 'IE - Irlanda'),
            ('IH', 'IH - Isla del Hombre'),
            ('IL', 'IL - Israel'),
            ('IN', 'IN - India'),
            ('IO', 'IO - Territorio Britanico en el Océano Indico'),
            ('IP', 'IP - Islas Pacifico'),
            ('IQ', 'IQ - Iraq'),
            ('IR', 'IR - Iran'),
            ('IS', 'IS - Islandia'),
            ('IT', 'IT - Italia'),
            ('JM', 'JM - Jamaica'),
            ('JO', 'JO - Reino Hachemita de Jordania'),
            ('JP', 'JP - Japon'),
            ('KE', 'KE - Kenia'),
            ('KH', 'KH - Campuchea Democratica'),
            ('KI', 'KI - Kiribati'),
            ('KM', 'KM - Comoros'),
            ('KN', 'KN - San Kitts'),
            ('KP', 'KP - Republica Democratica de Corea'),
            ('KR', 'KR - Republica de Corea'),
            ('KW', 'KW - Estado de Kuwait'),
            ('KY', 'KY - Islas Caiman'),
            ('LA', 'LA - Republica Democratica de Laos'),
            ('LB', 'LB - Libano'),
            ('NL', 'NL - Holanda'),
            ('NO', 'NO - Noruega'),
            ('NP', 'NP - Nepal'),
            ('NR', 'NR - Republica de Nauru'),
            ('NT', 'NT - Zona Neutral'),
            ('NU', 'NU - Niue'),
            ('NV', 'NV - Nevis'),
            ('NZ', 'NZ - Nueva Zelanda'),
            ('OM', 'OM - Sultania de Oman'),
            ('PA', 'PA - República de Panama'),
            ('PE', 'PE - Peru'),
            ('PY', 'PY - Paraguay'),
            ('SV', 'SV - El Salvador'),
            ('UA', 'UA - Ucrania'),
            ('UG', 'UG - Uganda'),
            ('UM', 'UM - Islas Menores alejadas de Estados Unidos'),
            ('US', 'US - Estados Unidos de América'),
            ('UY', ' UY- Republica Oriental del Uruguay'),
            ('VA', 'VA - Vaticano'),
            ('VE', 'VE - Venezuela'),
            ('XX', 'XX - Otro'),
            ('YD', 'YD - Yemen Democratica'),
            ('YE', 'YE - Republica del Yemen'),
            ('YU', 'YU - Paises de las EX- Yugoslavia'),
            ('ZA', 'ZA - Sudafrica'),
            ('ZC', 'ZC - Zona Especial Canaria'),
            ('ZM', 'ZM - Zambia'),
            ('ZO', 'ZO - Zona Libre de Ostrava'),
            ('ZR', 'ZR - Zaire'),
            ('ZW', 'ZW - Zimbawe'),
            ], 'Pais de Residencia  (DIOT)', help='Estado utilizado para la DIOT'),
        'number_fiscal_id' : fields.char('Numero ID Fiscal (DIOT)', size=100),
        'nationality' : fields.char('Nacionalidad (DIOT)', size=100),
        'foreign_name': fields.char('Nombre del extranjero'),
    }
    
    _defaults = {
        'type_of_third': '04',
        'type_of_operation': '85'
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
