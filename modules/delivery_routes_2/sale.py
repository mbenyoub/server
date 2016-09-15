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

from osv import osv, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from openerp import netsvc
from openerp.tools.translate import _

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        """
            Agrega la zona y el intervalo de tiempo sobre la entrega
        """
        # Funcion de SUPER para heredar la funcionalidad anterior
        valor = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)
        
        # Agrega la informacion de la zona y de 
        valor['delivery_term_id'] = order.delivery_term_id.id or False
        valor['zone_id'] = order.zone_id.id or False
        valor['delivery_date'] = order.due_date
        return valor
    
    def onchange_partner_shipping_id(self, cr, uid, ids, part, part_shipping, context=None):
        """
            Agrega la informacion de las zonas de entrega
        """
        zone_id = False
        delivery_term = False
        res = {'value':{}}
        partner_obj = self.pool.get('res.partner')
        if part_shipping:
            # Obtiene la zona y los terminos de entrega para el pedido
            partner = partner_obj.browse(cr, uid, part_shipping, context=context)
            if partner:
                if partner.property_delivery_zone:
                    zone_id = partner.property_delivery_zone.id
                res['value']['zone_id'] = zone_id
                if partner.property_delivery_term:
                    delivery_term = partner.property_delivery_term.id
                res['value']['delivery_term_id'] = delivery_term
        # Si la direccion no tiene el valor lo obtiene del cliente directamente
        if not res['value'].get('zone_id', False) or not res['value'].get('delivery_term_id',False):
            # Obtiene la zona y los terminos de entrega para el pedido
            partner = partner_obj.browse(cr, uid, part, context=context)
            if partner:
                # Si no esta la zona la agrega al pedido desde el cliente
                if not res['value'].get('zone_id', False) and partner.property_delivery_zone:
                    zone_id = partner.property_delivery_zone.id
                res['value']['zone_id'] = zone_id
                # Si no hay termino de entrega lo agrega al pedido desde el cliente
                if not res['value'].get('delivery_term_id') and partner.property_delivery_term:
                    delivery_term = partner.property_delivery_term.id
                res['value']['delivery_term_id'] = delivery_term
        #print "**************** resultado zona y termino entrega ************* ", res
        return res
    
    def onchange_datetime_order(self, cr, uid, ids, datetime_order, delivery_term_id, context=None):
        """
            Actualiza la fecha de entrega por default
        """
        res = {}
        delivery_obj = self.pool.get('delivery.term')
        
        if datetime_order and delivery_term_id:
            # date_order = datetime.strptime(datetime_order, '%Y-%m-%d')
            # res['date_order'] = date_order.strftime('%Y-%m-%d')
            res['date_order'] = datetime_order[:10]
            # Actualiza la fecha de entrega
            #res['due_date'] = delivery_obj.compute(cr, uid, delivery_term_id, datetime_order, context=context)
        return {'value': res}
    
    def action_button_confirm(self, cr, uid, ids, context=None):
        """
            Obtiene la fecha de notificacion
        """
        deliv_term_obj = self.pool.get('delivery.term')
        datetime_order = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = time.strftime('%Y-%m-%d')
        
        # Recorre los registros sobre el pedido de venta
        for order in self.browse(cr, uid, ids, context=context):
            vals = {
                'datetime_order': datetime_order,
                'date_order': date
            }
            #~ Valida que este asignada la fecha de confirmacion
            if order.due_date:
                #print "************** fecha actual ********** ", datetime_order
                #print "************** fecha entrega ********** ", order.due_date
                
                # Valida que la fecha de la venta tenga una fecha de entrega
                date_valid = deliv_term_obj.validate(cr, uid, order.delivery_term_id.id, date_ref=datetime_order, date_valid=order.due_date, context=None)
                if not date_valid:
                    raise osv.except_osv(_('Error!'),_("La fecha de entrega del pedido debe tener un margen minimo de '%s' sobre la fecha del pedido!"%(order.delivery_term_id.name,)))
            else:
                vals['due_date'] = deliv_term_obj.compute(cr, uid, order.delivery_term_id.id or False, datetime_order, context=context)
                # Actualiza la fecha de promesa
            self.write(cr, uid, [order.id], vals, context=context)
        
        # Actualiza el total y el pedido
        self.button_dummy(cr, uid, ids, context=context)
        res = super(sale_order,self).action_button_confirm(cr, uid, ids, context=context)
        return res
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Limpia la fecha del pedido para que la agregue al momento de confirmar
        """
        if default is None:
            default = {}
        default.update({
            'date_order':False,
            'datetime_order':False,
        })
        # Continua con la funcionalidad original
        return super(sale_order, self).copy(cr, uid, id, default, context)
    
    _columns = {
        'due_date': fields.datetime('Fecha de Entrega', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'datetime_order': fields.datetime('Fecha del pedido', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'zone_id': fields.many2one('delivery.zone','Zona', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'delivery_term_id': fields.many2one('delivery.term','Plazo de entrega', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'date_order': fields.date('Date', required=False, readonly=True, select=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        
        # Ver para eliminarlo de el modulo de entregas
        'so_payment_method': fields.char('Payment Method', size=32, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
    }
    
    def _get_datetime_default(self, cr, uid, context=None):
        datetime = time.strftime('%Y-%m-%d %H:%M:%S')
        return datetime
    
    _defaults = {
        #'datetime_order': _get_datetime_default
    }

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
