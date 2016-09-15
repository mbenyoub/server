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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_invoice_cancel_wizard(osv.osv_memory):
    """
        Solicita el motivo de la cancelacion de la factura
    """
    _name = "account.invoice.cancel.wizard"
    
    def _get_method_selection(self, cr, uid, context=None):
        """
            Obtiene la lista de las opciones sobre la cancelacion de la factura
        """
        if context is None:
            context = {}
        
        # From module of PAC inherit this function and add new methods
        res = []
        # Retorna las opciones disponibles 
        res.append(('01','Cancelar Factura'))
        res.append(('02','Cancelar y Devolver'))
        res.append(('03','Cancelar y Duplicar'))
        
        if context.get('type_invoice', False) == 'in_invoice':
            res.append(('04','Cambiar a borrador'))
        return res
    
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Activo', select=True, ondelete='set null', required=True),
        'date': fields.date('Fecha de Cancelacion', required=True),
        'cancel_ref': fields.text('Referencia de Cancelacion', required=True),
        'type_cancel': fields.selection(_get_method_selection, "Referencia de Cancelacion", type='char', size=64, required=True),
    }
    
    _defaults = {
        'date': fields.datetime.now,
    }
    
    def action_invoice_cancel(self, cr, uid, ids, context=None):
        """
            Cancela la factura y agrega el detalle
        """
        if context is None:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        deduction_obj = self.pool.get('account.fiscal.deduction')
        wf_service = netsvc.LocalService("workflow")
        
        # Obtiene la informacion de la cancelacion de la factura
        data = self.browse(cr, uid, ids[0], context=context)
        context['date'] = data.date
        context['reference'] = data.cancel_ref
        inv_id = data.invoice_id.id
        
        # Busca las deducciones que apliquen sobre las facturas a cancelar y las elimina
        deduction_ids = deduction_obj.search(cr, uid, [('invoice_id','=',inv_id)])
        if deduction_ids:
            deduction_obj.unlink(cr, uid, deduction_ids, context=context)
        
        # Proceso de cancelacion sobre la factura
        if data.type_cancel == '02':
            # Ejecuta funcion para cancelar el registro
            inv_obj.action_invoice_cancel(cr, uid, inv_id, context=context)
            # Actualiza el workflow de la factura
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_cancel', cr)
        
            # Devuelve los productos relacionados a la factura
            if invoice.shipped:
                # Valida que haya albaranes 
                if invoice.picking_ids:
                    # Valida si va a ser una entrada o una salida de inventario
                    type = 'in'
                    if invoice.type in ['out_refund','in_invoice']:
                        type = 'out'
                    # Genera el albaran con lo facturado
                    self._apply_picking(cr, uid, data.invoice_id, data.invoice_id.invoice_line, type, context=context)
        elif data.type_cancel == '03':
            # Ejecuta funcion para cancelar el registro
            inv_obj.action_invoice_cancel(cr, uid, inv_id, context=context)
            # Actualiza el workflow de la factura
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_cancel', cr)
            # Duplica la factura
            inv_id = inv_obj.copy(cr, uid, inv_id)
            
            # Redirecciona a la factura duplicada
            if not ids: return []
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
            return {
                'name':_("Factura"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': {},
                'res_id': inv_id
            }
             
        elif data.type_cancel == '04':
            # Obtiene la poliza que se genero al validar la factura y la elimina
            move_id = data.invoice_id.move_id.id
            account_move_obj = self.pool.get('account.move')
            #print "************* id factura ************ ", inv_id
            
            # Cambia la factura a estado borrador y elimina los movimientos
            inv_obj.write(cr, uid, [inv_id], {'state':'draft', 'move_id':False})
            # Elimina la poliza de la factura
            account_move_obj.button_cancel(cr, uid, [move_id], context=context)
            account_move_obj.unlink(cr, uid, [move_id], context=context)
            
            # Cancela la factura
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_delete(uid, 'account.invoice', inv_id, cr)
            wf_service.trg_create(uid, 'account.invoice', inv_id, cr)
            
        else:
            # Ejecuta funcion para cancelar el registro
            inv_obj.action_invoice_cancel(cr, uid, data.invoice_id.id, context=context)
            # Actualiza el workflow de la factura
            wf_service.trg_validate(uid, 'account.invoice', data.invoice_id.id, 'invoice_cancel', cr)
        
        inv_obj._log_event(cr, uid, [data.invoice_id.id], -1.0, 'Cancel Invoice')
        return True

account_invoice_cancel_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
