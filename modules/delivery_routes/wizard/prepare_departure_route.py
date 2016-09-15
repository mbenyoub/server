# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Salda?a (riss_600@hotmail.com)
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

from openerp.osv import osv, fields
from tools.translate import _
import time

class prepare_departure_route_wizard(osv.osv_memory):
    _name = 'prepare.departure.route'
    
    _columns = {
        'route_id': fields.many2one('delivery.route', 'Ruta', readonly=True),
        'van_id': fields.many2one('delivery.van','Vehiculo', readonly=True),
        'departure_date': fields.datetime('Fecha Salida', readonly=True),
        'km_init': fields.integer("Kilometraje inicial"),
    }
    
    defaults = {
        'departure_date': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def action_departure(self, cr, uid, ids, context=None):
        """
            Actualiza la entrega sobre la ruta actualizando el kilometraje inicial
        """
        print"******PREPARANDO SALIDA********"
        route_obj = self.pool.get('delivery.route')
        route_ids = []
        # Actualiza el kilometraje y la fecha de partida sobre la ruta
        data = self.browse(cr, uid, ids[0], context=context)
        
        # Registra y valida el kilometraje sobre el vehiculo
        if data.van_id:
            self.pool.get('delivery.van').update_km(cr, uid, data.van_id.id, data.km_init, type='out', context=context)
        # Actualiza la ruta a En Entrega
        if data.route_id:
            route_ids.append(data.route_id.id)
        # Actualiza el kilometraje recorrido en la ruta
        route_obj.write(cr, uid, route_ids, {'km_init': data.km_init}, context=context)
        # Proceso de entregado
        return route_obj.action_shipping(cr, uid, route_ids, context=context)
    
prepare_departure_route_wizard()
