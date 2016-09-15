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
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
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
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

#----------------------------------------------------------
# Price lists
#----------------------------------------------------------

class requisition_credit_credit(osv.osv):
    _name = "requisition.credit.credit"
    _name_get = "number"
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        """
            Agrega el campo RFC al modulo de requisition y actualiza el tipo de solicitud
        """
        partner_obj = self.pool.get('res.partner')
        
        # Inicializa variable de retorno
        res = {
            'rfc': '',
            'current_credit': 0.0,
            'type': 'credit'
        }
        
        # validamos que se reciba un partner sobre el registro
        if partner_id:
            # Obtenemos el registro de area seleccionada
            partner = partner_obj.browse(cr, uid, partner_id, context=context)
            res['rfc'] = partner.rfc
            res['current_credit'] = partner.credit_limit
            # Si el cliente ya contiene un limite de credito cambia la solicitud a ampliacion
            if partner.credit_limit > 0.0:
                res['type'] = 'extension'
        return {'value': res}
    
    def action_draft(self, cr, uid, ids, context=None):
        """
            Transicion a estado borrador
        """
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def action_open(self, cr, uid, ids, context=None):
        """
            Boton action del estado open
        """
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)
    
    def action_progress(self, cr, uid, ids, context=None):
        """
            Boton action del estado draft
        """
        return self.write(cr, uid, ids, {'state': 'progress'}, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Boton action del estado draft
        """
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Accion de confirmar que se aplica el credito, actualiza el credito sobre el cliente
        """
        partner_obj = self.pool.get('res.partner')
        date = time.strftime('%Y-%m-%d')
        
        # Recorre los registros para actualizar los datos
        for requisition in self.browse(cr, uid, ids, context=context):
            # Valida el tipo de solicitud a aplicar
            if requisition.type == 'credit':
                # Si es credito reemplaza el resultado sobre el cliente
                partner_obj.write(cr, uid, [requisition.partner_id.id], {'credit_limit': requisition.credit})
            else:
                # Aplica la ampliacion sobre el credito del cliente
                partner_obj.write(cr, uid, [requisition.partner_id.id], {'credit_limit': requisition.credit + requisition.partner_id.credit_limit})
        
        # Actualiza a Aceptado en la solicitud
        self.write(cr, uid, ids, {'state': 'done', 'confirm_date': date}, context=context)
        return True
    
    def action_cancel_wizard(self, cr, uid, ids, context=None):
        """
            Muestra la venta con la funcionalidad para cancelar la factura
        """
        if context is None:
            context = {}
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'requisition_credit', 'view_requisition_credit_cancel_wizard')
        
        # Obtiene los parametros que van por default
        context['default_requisition_id'] = ids[0]
        context['default_type'] = 'cancel'
        
        return {
            'name':_("Cancelacion de credito"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'requisition.credit.cancel.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
    
    def check_type_credit(self, cr, uid, ids, field_name, arg, context=None):
        """
            Valida si el credito es mayor al credito actual
        """
        res = {}
        # Recorre los registros
        for requisition in self.browse(cr, uid, ids, context=context):
            # Inicializa el resultado para la solicitud
            res[requisition.id] = True
            # Valida que el tipo de solicitud sea un credito
            if requisition.type == 'credit':
                # Valida que el credito sea mayor al credito actual
                if requisition.credit < requisition.current_credit or requisition.credit==0:
                    res[requisition.id] = False
        return res
    
    def create(self, cr, uid, vals, context=None):
        """
            Llama a la funcion create para crear un nuevo documento
        """
        if context is None:
            context = {}
        doc_type_obj = self.pool.get('requisition.credit.document.type')
        doc_obj = self.pool.get('requisition.credit.document')
            
        # Ejecutamos funcion original
        res = super(requisition_credit_credit, self).create(cr, uid, vals, context=context)
        
        # Buscamos los tipos de documentos que se van a archivar
        document_ids = doc_type_obj.search(cr, uid, [('active','=',True)], context=context)
        if document_ids:
            # Creamos el nuevo documento para asignar sobre el credito
            for docs in doc_type_obj.browse(cr, uid, document_ids, context=context):
                doc_obj.create(cr, uid, {
                            'credit_id': res,
                            'name': docs.name,
                        }, context=context)
        return res

    def _get_number(self, cr, uid, ids, context=None):
        """
            Obtiene el numero de la solicitud por secuencia
        """
        obj_seq = self.pool.get('ir.sequence')
        mov_number = '/'
        try:
            mov_number = obj_seq.next_by_code(cr, uid, 'requisition.credit', context=context)
        except:
            pass
        return mov_number

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Cliente', domain=[('customer','=',True)], required=True),
        'rfc': fields.related('partner_id', 'rfc', type="char", string ='RFC' ,size=10),
        'user_id': fields.many2one('res.users','Solicitante', required=True),
        'note': fields.text('Descripcion'),
        'credit': fields.float('Monto'),
        'current_credit':fields.related('partner_id', 'credit_limit', type="float", string ='Credito actual'),
        'verify': fields.function(check_type_credit, string='Verificar_tipo', type='boolean'),
        'type': fields.selection([('credit','Credito'),('extension','Ampliacion')], string="Tipo Solicitud"),
        'requisition_date': fields.date('Fecha Requisicion'),
        'cancel_date': fields.date('Fecha de Cancelacion'),
        'cancel_description': fields.text('Motivo'),
        'confirm_date': fields.date('Fecha Confirmacion'),
        #'document1': fields.boolean('IFE'),
        #'document1_file': fields.binary('archivo', help="archivo a importar"),
        #'document2': fields.boolean('Comprobante Domicilio'),
        #'document2_file': fields.binary('archivo',  help="archivo a importar"),
        #'document3': fields.boolean('Buro Credito'),
        #'document3_file': fields.binary('archivo',  help="archivo a importar"),
        'color': fields.integer('Color Index'),
        'number': fields.char('Numero de Folio', size=64, readonly=True),
        'state': fields.selection([
            ('draft', 'Solicitud borrador'),
            ('open', 'Abierto'),
            ('progress', 'En proceso'),
            ('none', 'Anulado'),
            ('reject', 'Rechazado'),
            ('done', 'Aceptado'),
            ('cancel', 'Cancelado'),
            ], 'Estado', required=True, readonly=True, track_visibility='onchange',
                help='* The \'Draft\' Estado solicitud en borrador. \
                    \n* The \'Progress\' Estado solicitud en proceso de aceptacion. \
                    \n* The \'Done\' Estado solicitud aceptada. \
                    \n* The \'Open\' Estado solicitud abierta. \
                    \n* The \'Reject\' Estado solicitud rechazada. \
                    \n* The \'Cancelled\' Estado solicitud cancelada.'),
        'document_ids': fields.one2many('requisition.credit.document', 'credit_id', 'Documentos'),
        
    }
    
    def _get_user_default(self, cr, uid, context=None):
        """
            Obtiene el usuario logeado por default
        """
        return uid
    
    _defaults = {
        'state': 'open',
        'number': _get_number,
        'requisition_date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': _get_user_default
    }
    
    def _validate_credit(self, cr, uid, ids, context=None):
        """
            Valida que el credito sea mayor a cero
        """
        result = True
        # Recorre los partners
        for req in self.browse(cr, uid, ids, context=context):
            if req.credit == 0.0:
                result = False
        return result
    
    _constraints = [(_validate_credit, "El credito a aplicar no puede cer cero!", ['credit']),]
    
requisition_credit_credit()

class requisition_credit_document(osv.osv):
    _name = "requisition.credit.document"
    
    def onchange_file(self, cr, uid, ids, file, context=None):
        """
            Agrega el campo RFC al modulo de requisition y actualiza el tipo de solicitud
        """
        res = {}
        if file:
            res['apply'] = True
        return {'value': res}
    
    _columns = {
        'credit_id': fields.many2one('requisition.credit.credit', 'Documento'),
        'name': fields.char('Nombre'),
        'file': fields.binary('Archivo', help="Archivo a importar"),
        'apply': fields.boolean('Recibido'),
    }
    
    _defaults = {
        'apply': False
    }
    
requisition_credit_document()

class requisition_credit_document_type(osv.osv):
    _name = "requisition.credit.document.type"
    _columns = {
        'name': fields.char('Nombre'),
        'note': fields.text('Descripcion'),
        'active': fields.boolean('Activo'),
    }
    
    
requisition_credit_document_type()
