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

class res_partner(osv.Model):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner'
    
    def action_create_diot(self, cr, uid, ids, context=None):
        """
            Genera el archivo diot
        """
        #print "************* DIOT ****************"
        
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
        
        #print "******************** ids ***************** ", ids
        
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
        'diot_type1': fields.selection([
            ('04','Proveedor Nacional'),
            ('05','Proveedor Extranjero'),
            ('15','Proveedor Global')], 'Tipo de tercero'),
        'diot_type2': fields.selection([
            ('03','Prestacion de servicios profesionales'),
            ('06','Arrendamiento de Inmuebles'),
            ('85','Otros')], 'Tipo de operacion'),
        'rfc': fields.char('RFC'),
        'diot_fiscal_number': fields.char('Numero de id fiscal', size=128),
        'diot_name_ex': fields.char('Nombre del extranjero'),
        'diot_nationality': fields.char('Nacionalidad'),
        'diot_act_value': fields.integer('Valor de los actios'),
        'diot_act_value2': fields.integer('Valor de los actos'),
        'diot_act_value3': fields.integer('Valor de los actos'),
        'diot_act_value4': fields.integer('Valor de los actos'),
        'diot_act_value5': fields.integer('Monto del IVA pagado'),
        'diot_act_value6': fields.integer('Valor de los actos o actividades pagados'),
        'diot_act_value7': fields.integer('Monto del IVA pagado'),
        'diot_act_value8': fields.integer('Monto del IVA pagado no acreditable'),
        'diot_act_value9': fields.integer('Valor de los actos o actividades'),
        'diot_act_value10': fields.integer('Valor de los demás actos o actividades pagados'),
        'diot_act_value11': fields.integer('Valor de los actos o actividades pagados'),
        'diot_act_value12': fields.integer('IVA Retenido por el contribuyente'),
        'diot_act_value13': fields.integer('IVA correspondiente a las devoluciones'),
    }
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
