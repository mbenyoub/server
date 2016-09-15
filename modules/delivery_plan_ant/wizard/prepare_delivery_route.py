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
from openerp import pooler
from openerp import netsvc

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

# ---------------------------------------------------------
# Proceso para agilizar la creacion de rutas en el sistema
# ---------------------------------------------------------

class preparte_delivery_route(osv.osv_memory):
    """
        Prepara la ruta 
    """
    _name = "prepare.delivery.route.wizard"
    
    def onchange_zone_id(self, cr, uid, ids, zone_ids, priority, street, quantity, weight, context=None):
        """
            Aplica filtro sobre las salidas de almacen que se van a aplicar para generar la ruta
        """
        picking_obj = self.pool.get('stock.picking')
        location_id = False
        res = []
        print "*************** cambia filtros zona ******************* "
        # Obtiene las salidas de almacen en base a los filtros
        picking_search = [('delivery_state','=','draft'),('delivered','=',False),('route_line_id','=',False),('route_id','=',False),('state','not in',['cancel','done'])]
        zone_ids = zone_ids[0][2]
        if len(zone_ids) > 0:
            picking_search.append(('zone_id','in',zone_ids))
        # Valida si va a filtrar por la colonia
        if street:
            street = '%%' + street + '%%'
            picking_search.append(('partner_id.street2','ilike',street))
        # Valida si va a filtrar por la cantidad maxima sobre el pedido
        if quantity > 0:
            picking_search.append(('number_of_packages','<=',quantity))
        # Valida si va a filtrar por el peso maximo sobre el pedido
        if weight > 0:
            picking_search.append(('weight','<=',weight))
        
        #print "************** picking_search **************** ", picking_search
        # Genera la busqueda de las salidas de almacen
        picking_ids = picking_obj.search(cr, uid, picking_search, context=context)
        priority = priority[0][2]
        #print "*********** priority ************ ", priority
        priority_filter = []
        # Obtiene la lista de prioridades que aplican
        if priority:
            for pty in self.pool.get('delivery.priority').browse(cr, uid, priority, context=context):
                priority_filter.append(pty.value)
        # Numero para secuencia
        num = 10
        # Agrega la informacion nueva de las lineas en base al filtro
        for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
            #print "******** prioridad ************ ", picking.priority, picking.priority in priority
            # Si trae informacion sobre prioridad filtra los datos por la prioridad
            if len(priority_filter) > 0:
                if not (picking.priority in priority_filter):
                    continue
            if picking.partner_id.schedule_id:
                print "******HORARIO**********: ", picking.partner_id.schedule_id.id or False
                schedule = picking.partner_id.schedule_id.id or False
            else:
                print"*******NO SE ENCUENTRA EL HORARIO*********", picking.partner_id.schedule_id or False
                schedule = 0
                
            res.append({
                'name': picking.origin,
                'picking_id': picking.id,
                'partner_id': picking.partner_id.id or False,
                'invoice_id': picking.invoice_id.id or False,
                'street': picking.partner_id.street or False,
                'street2': picking.partner_id.street2 or False,
                'state': picking.delivery_state,
                'zone_id': picking.zone_id.id or False,
                'qty': picking.number_of_packages,
                'weight': picking.weight,
                'priority': picking.priority,
                'sequence': num,
                'delivery_date': picking.delivery_date,
                'schedule_id': schedule
            })
            num += 10
            # Obtiene la ubicacion origen de una de las tiendas
            if location_id == False:
                for line in picking.move_lines:
                    location_id = line.location_id.id or False
                    break
        # Genera el diccionario para el retorno de la informacion al onchange
        value = {'line_ids': res}
        if location_id:
            value['location_id'] = location_id
        return {'value': value}
    
    def onchange_van_id(self, cr, uid, ids, van_id, context=None):
        """
            Obtiene el chofer del vehiculo que esta por default
        """
        van_obj = self.pool.get('delivery.van')
        res = {}
        # Valida si recibe el id del vehiculo
        if van_id:
            # Agrega el chofer por default para el vehiculo
            van = van_obj.browse(cr, uid, van_id, context=context)
            if van.driver_id:
                res['driver_id'] = van.driver_id.id
        return {'value': res}
    
    _columns = {
        #'zone_id': fields.many2one('delivery.zone', 'Zona Entrega', ondelete="cascade", domain=[('active','=',True)], help="Seleccionar la zona de la que se va a generar la ruta."),
        'zone_ids': fields.many2many('delivery.zone', 'wizard_delivery_zone_rel', 'wizard_id', 'zone_id', 'Zona Entrega', domain=[('active','=',True)], help="Seleccionar las zonas de la que se va a generar la ruta."),
        'priority': fields.many2many('delivery.priority', 'wizard_delivery_priority_rel', 'wizard_id', 'priority', 'Prioridad Entrega', help="Seleccionar las prioridades sobre las que desea generar la ruta."),
        'street': fields.char('Colonia', size=64, help="Filtrar por alguna coincidencia sobre la colonia. (No aplica si el valor queda en blanco)"),
        'quantity': fields.float('Bultos Maximo', help="Cantidad maxima de bultos por entrega. (No aplica si el valor queda en cero o en blanco)"),
        'weight': fields.float('Peso Maximo', help="Peso maximo permitido por entrega. (No aplica si el valor queda en cero o en blanco)"),
        #'priority': fields.selection([
        #    ('ontime','En tiempo'),
        #    ('todeliver','Por Surtir'),
        #    ('urgent','Urgente'),
        #    ('defeated','Vencido'),
        #    ('program','Programado'),
        #    ],'Prioridad entrega', select=True),
        'driver_id': fields.many2one('delivery.driver','Chofer', required=False, domain=[]),
        'van_id': fields.many2one('delivery.van','Vehiculo', required=False, domain=[]),
        'is_carrier': fields.boolean('Contratar Transportista'),
        'carrier_id': fields.many2one('res.partner', 'Transportista'),
        'line_ids': fields.one2many('prepare.delivery.route.line.wizard', 'wizard_id', 'Entregas Ruta'),
        'location_id': fields.many2one('stock.location', 'Ubicacion Origen', domain=[]),
    }
    
    _defaults = {
        #'priority': 'urgent'
        #'zone_ids': []
    }
    
    def action_prepare_delivery_route(self, cr, uid, ids, context=None):
        """
            Crea una Ruta con la informacion recabada
        """
        route_obj = self.pool.get('delivery.route')
        rline_obj = self.pool.get('delivery.route.line')
        picking_obj = self.pool.get('stock.picking')
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}
        route_id = False
        pick_ids = []
        user_id = False
        # Obtiene la informacion para la creacion de la ruta
        data = self.browse(cr, uid, ids[0], context=context)
        
        # Asigna las entregass al usuario si hay un conductor
        if data.driver_id:
            user_id = data.driver_id.user_id.id or False
        
        # Valida que haya notas de venta para insertar sobre la factura global
        if not data.line_ids:
            raise osv.except_osv(_('Aviso!'),_("No hay entregas registradas sobre la ruta!"))
        
        # Obtiene el numero de la secuencia sugerido para identificador de la ruta
        number = obj_seq.next_by_code(cr, uid, 'delivery.route.seq', context=context)
        
        # Crea el diccionario con la informacion para crear la ruta
        vals = {
            'name': number,
            'state': 'draft',
            'date_due': time.strftime('%Y-%m-%d'),
            'user_id': uid,
            'is_carrier': data.is_carrier,
            'carrier_id': data.carrier_id.id or False,
            'driver_id': data.driver_id.id or False,
            'van_id': data.van_id.id or False,
            'lot_stock_id': data.van_id and data.van_id.lot_stock_id.id or False,
            'lot_virtual_id': data.van_id and data.van_id.lot_virtual_id.id or False,
            'location_id': data.location_id.id or False
        }
        # Crea la nueva ruta
        route_id = route_obj.create(cr, uid, vals, context=context)
        
        # Recorre las lineas de las entregas
        for line in data.line_ids:
            # Crea el nuevo registro sobre la linea de la ruta
            vals = {
                'name': line.name,
                'sequence': line.sequence,
                'route_id': route_id,
                'picking_id': line.picking_id.id or False,
                'qty': line.qty,
                'weight': line.weight,
                'state': 'draft',
                'user_id': user_id
            }
            rline_obj.create(cr, uid, vals, context=context)
        
        # Redirecciona a la factura creada
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'delivery_routes', 'view_delivery_route_form')

        return {
            'name':_("Ruta de Entrega"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'delivery.route',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : route_id, # id of the object to which to redirected
        }
    
preparte_delivery_route()

class preparte_delivery_route_line(osv.osv_memory):
    """
        Salidas de almacen
    """
    _name = "prepare.delivery.route.line.wizard"
    
    _columns = {
        'name': fields.char('Referencia'),
        'sequence': fields.integer('Orden'),
        'wizard_id': fields.many2one('prepare.delivery.route.wizard', 'Wizard', ondelete="cascade"),
        'picking_id': fields.many2one('stock.picking', 'Salida de Almacen', ondelete="cascade", domain=[('state_meeting','=','draft')]),
        'partner_id': fields.many2one('res.partner', 'Cliente'),
        'schedule_id': fields.related('partner_id', 'schedule_id', type="many2one",
            relation="delivery.schedule", string="Horario de entrega", store=True),
        'street': fields.char('Calle'),
        'street2': fields.char('Colonia'),
        'zone_id': fields.many2one('delivery.zone', 'Zona Entrega', ondelete="cascade"),
        'priority': fields.selection([
            ('ontime','En tiempo'),
            ('todeliver','Por Surtir'),
            ('urgent','Urgente'),
            ('defeated','Vencido'),
            ('program','Programado'),
            ],'Prioridad entrega', select=True),
        'qty': fields.float('Bultos', help="Bultos contenidos por el pedido"),
        'weight': fields.float('Peso', help="Peso total del pedido"),
        'state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_fuound', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado (Almacen)'),
                            ('cancel','Cancelado')], 'Estado Entrega'),
        'delivery_date': fields.datetime('Fecha de entrega'),
        'invoice_id': fields.many2one('account.invoice', 'Factura')
    }
    
preparte_delivery_route_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
