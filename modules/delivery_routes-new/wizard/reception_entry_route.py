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

class reception_entry_route_wizard(osv.osv_memory):
    _name = 'reception.entry.route'
    
    _columns = {
        'route_id': fields.many2one('delivery.route', 'Ruta', readonly=True),
        'van_id': fields.many2one('delivery.van','Vehiculo', readonly=True),
        'entry_date': fields.datetime('Fecha Llegada', readonly=True),
        'km_end': fields.integer("Kilometraje Final"),
    }
    
    defaults = {
        'entry_date': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def action_entry(self, cr, uid, ids, context=None):
        """
            Actualiza la entrega sobre la ruta actualizando el kilometraje final de la ruta
        """
        route_obj = self.pool.get('delivery.route')
        route_ids = []
        # Actualiza el kilometraje y la fecha de partida sobre la ruta
        data = self.browse(cr, uid, ids[0], context=context)
        
        # Valida que el kilometraje del vehiculo no sea menor al kilometraje inicial
        if data.route_id.km_init > data.km_end:
            raise osv.except_osv(_('Error!'), _('El kilometraje inicial no puede ser mayor al kilometraje final! (km inicial: %s, km final: %s).'%(data.route_id.km_init,data.km_end)))
        
        # Registra y valida el kilometraje sobre el vehiculo
        if data.van_id:
            self.pool.get('delivery.van').update_km(cr, uid, data.van_id.id, data.km_end, type='out', context=context)
        # Actualiza la ruta a En Entrega
        if data.route_id:
            route_ids.append(data.route_id.id)
        # Actualiza el kilometraje recorrido en la ruta
        route_obj.write(cr, uid, route_ids, {'km_end': data.km_end, 'km': data.km_end - data.route_id.km_init, 'entry_date': data.entry_date}, context=context)
        # Proceso de entregado
        return True
    
reception_entry_route_wizard()
