# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Cubic ERP - Teradata SAC. (http://cubicerp.com).
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

from osv import fields, osv
import time
from datetime import datetime, timedelta
from openerp.tools.float_utils import float_compare
from openerp import pooler, tools
import pytz
from pytz import timezone
from tools.translate import _
from tools import ustr
import logging
_logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Configuracion plazos y ubicaciones entregas
# ---------------------------------------------------------

class delivery_term(osv.osv):
    """
        Plazos de entrega
    """
    _name = "delivery.term"
    _description = "Delivery Term"
    _columns = {
        'name': fields.char('Plazo de entrega', size=64, required=True),
        'active': fields.boolean('Activo', help="Si el plazo de entrega se desmarca, permite ocultarlo sin eliminarlo."),
        'note': fields.text('Descripcion', translate=True),
        'value': fields.integer('Cantidad'),
        'unit': fields.selection([
            ('hours', 'Horas'),
            ('days', 'Dias'),
            ], 'Unidad', readonly=False, track_visibility='onchange', select=True),
    }
    _defaults = {
        'active': 1,
        'unit': 'hours'
    }
    _order = "name"

    def get_timezone(self, cr, uid, context=None):
        """
            Obtiene la zona horaria del context o del usuario
        """
        if context is None:
            context = {}
        tz = 'UTC'
        if context.get('tz',False) != False:
            tz = context.get('tz','UTC')
        # Valida si el context trae el dato de la zona horaria
        if tz == 'UTC' or tz == False:
            zone = self.pool.get('res.users').browse(cr, uid, uid, context=context).tz
            # Valida que el usuario tenga una zona horaria
            if zone:
                tz = zone
        return tz

    def get_date_next(self, cr, uid, date, value=0, unit='hours', context=None):
        """
            Obtiene la fecha siguiente en base a los parametros
        """
        res = date
        # Obtiene la zona horaria configurada
        tz_utc = pytz.utc
        tz = self.get_timezone(cr, uid, context=context)
        
        if not date:
            date = datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Inicializa la fecha
        datet = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
        if tz != 'UTC':
            datet = datet.astimezone(timezone(tz))
        #print "************* datetime get date next ************** ", datet
        
        # Valida si se incrementa por horas
        if unit == 'hours':
            datet = datet + timedelta(hours=value)
        elif unit == 'days':
            datet = datet + timedelta(days=value)
        elif unit == 'minutes':
            datet = datet + timedelta(minutes=value)
        
        # Regresa la fecha al formato de UTC
        datet = datet.astimezone(tz_utc)
        res = datet.strftime('%Y-%m-%d %H:%M:%S')
        return res

    def compute(self, cr, uid, id, date_ref=False, context=None):
        """
            Calcula la fecha siguiente que aplica en base al invervalo seleccionado
        """
        result = False
        dt = self.browse(cr, uid, id, context=context)
        if dt:
            result = self.get_date_next(cr, uid, date_ref, dt.value, dt.unit, context=context)
        return result
    
    def validate(self, cr, uid, id, date_ref=False, date_valid=False, context=None):
        """
            Valida que la fecha de entrega sea mayor al rango del termino de entrega especificado
        """
        # Valida que traiga las fechas
        if date_ref == False or date_valid == False:
            return False
        # Obtiene la fecha siguiente en base al termino de entrega
        dt = self.browse(cr, uid, id, context=context)
        if not dt:
            return False
        
        next_date = self.get_date_next(cr, uid, date_ref, dt.value, dt.unit, context=context)
        # Deja un rango de 30 minutos por desface sobre la fecha a validar contra la entrega
        date_valid = self.get_date_next(cr, uid, date_valid, 30, 'minutes', context=context)
        
        #print "*************** valida fechas ********** ", date_valid, " < ", next_date
        
        # Valida que la fecha sea mayor la fecha de entrega a la fecha con la que compara
        if datetime.strptime(date_valid, '%Y-%m-%d %H:%M:%S') < datetime.strptime(next_date, '%Y-%m-%d %H:%M:%S'):
            return False
        return True
    
delivery_term()

class delivery_zone(osv.osv):
    """
        Zonas de entrega
    """
    _name = "delivery.zone"
    _description = "Delivery Zone"
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'active': fields.boolean('Activo', help="Si la zona de entrega se desmarca, permite ocultarlo sin eliminarlo."),
        'note': fields.text('Descripcion', translate=True),
        'city': fields.char('Ciudad', size=64),
        'state_id': fields.many2one('res.country.state', 'Estado', ondelete="restrict")
    }
    _defaults = {
        'active': 1
    }
    _order = "state_id,city"

delivery_zone()

# ---------------------------------------------------------
# Catalogos de Vehiculos, Choferes y Transportistas
# ---------------------------------------------------------

class delivery_driver(osv.osv):
    _name = 'delivery.driver'
    
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'phone': fields.char('Telefono', size=64),
        'employee_id': fields.many2one('hr.employee','Empleado'),
        'user_id': fields.related('employee_id','user_id', type="many2one", relation="res.users", store=True, string="Usuario", readonly=True),
        'active': fields.boolean('Activo'),
        'color': fields.integer('Color Index'),
        #'function': fields.related('partner_id', 'function', type='char', size=64, store=True, string="Puesto"),
        'resource_id': fields.many2one('resource.calendar', 'Horario Trabajo')
    }
    _defaults = {
        'active':   True
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        onlyactive = True
        for arg in args:
            if len(arg)==3 and arg[0]=='active':
                onlyactive = False
        if onlyactive:
            args.append(('active','=',True))
        return super(delivery_driver, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
delivery_driver()

class delivery_van(osv.osv):
    _name = 'delivery.van'
    
    def _get_km(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el kilometraje del ultimo registro de la camioneta
        """
        print "******OBTENIENDO KILOMETRAJE********"
        res = {}
        for van in self.browse(cr, uid, ids, context=context):
            res[van.id] = 0
            # Busca el ultimo registro que hay sobre la camioneta
            cr.execute(" select max(id) as km_id from delivery_van_km where van_id = %s "%(van.id))
            dat = cr.dictfetchall()
            data = dat and dat[0].get('km_id',False) or False
            print "******DATA*******: ", data
            if data:
                # Actualiza el ultimo kilometraje registrado
                res[van.id] = self.pool.get('delivery.van.km').browse(cr, uid, data).value
                print "*******RES[VAN.ID]*******: ", res[van.id]
        return res
    
    def update_km(self, cr, uid, id, km, type='other', context=None):
        """
            Actualiza el kilometraje registrado sobre el vehiculo
        """
        van = self.browse(cr, uid, id, context=context)
        # Valida si el kilometraje a registrar es menor al ultimo registrado
        if km < van.km:
            raise osv.except_osv(_('Error'), _("El kilometraje que esta queriendo registrar es menor al kilometraje actual, en caso de ser correcto el dato pongase en contacto con el administrador del sistema.")) 
        
        # Actualiza el kilometraje del vehiculo
        self.pool.get('delivery.van.km').create(cr, uid, {'van_id': id, 'type': type, 'value': km, 'active': True, 'datetime': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return True
    
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32),
        'driver_id': fields.many2one('delivery.driver','Chofer Asignado'),
        'active': fields.boolean('Activo'),
        'plate': fields.char('Placas', size=32),
        'model': fields.char('Modelo', size=64),
        'brand': fields.char('Marca', size=64),
        'weight_limit': fields.float('Peso limite', help="Indicar el peso limite de carga del vehiculo especificado en Kilogramos"),
        'qty_limit': fields.float('Bultos', help="Indicar cantidad maxima de bultos que puede llevar este vehiculo"),
        'wheels': fields.integer('Numero de Ruedas'),
        'description': fields.text('Descripcion'),
        'partner_id': fields.many2one('res.partner', 'Direccion ubicacion'),
        'van_km_ids': fields.one2many('delivery.van.km', 'van_id', 'Historico Kilometraje', readonly=True),
        'km': fields.function(_get_km, type='integer', string="Kilometraje actual", store=False, readonly=True),
        # Ubicaciones de almacen
        'lot_stock_id': fields.many2one('stock.location', 'Ubicacion Existencias', required=True, domain=[('usage','=','internal')]),
        'lot_virtual_id': fields.many2one('stock.location', 'Ubicacion Virtual', required=True, domain=[('usage','=','view')]),
    }
    _defaults = {
        'active':   True
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        onlyactive = True
        for arg in args:
            if len(arg)==3 and arg[0]=='active':
                onlyactive = False
        if onlyactive:
            args.append(('active','=',True))
        return super(delivery_van, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            # Si trae codigo el vehiculo agrega la referencia
            if record.code:
                name = '[%s] %s'%(record.code,name)
            res.append((record.id,name ))
        return res
    
delivery_van()

class delivery_van_km(osv.osv):
    """
        Historico registro kilometraje vehiculo
    """
    _name = 'delivery.van.km'
    _order = 'id desc'
    
    _columns = {
        #'name': fields.char('Nombre'),
        'van_id': fields.many2one('delivery.van','Vehiculo'),
        'datetime': fields.datetime('Fecha'),
        'type': fields.selection([
            ('in', 'Fin Recorrido'),
            ('out', 'Inicio Recorrido'),
            ('other', 'Otro'),
            ], 'Tipo', readonly=True, track_visibility='onchange', select=True),
        'value': fields.integer('Kilometraje'),
        'active': fields.boolean('Activo'),
    }
    
    defaults = {
        'datetime': fields.datetime.now,
        'type': 'other',
        'active': True
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order='id', context=None, count=False):
        onlyactive = True
        for arg in args:
            if len(arg)==3 and arg[0]=='active':
                onlyactive = False
        print "********ONLYACTIVE**********: ", onlyactive
        if onlyactive:
            args.append(('active','=',True))
        print "********ARGS*******: ", args
        return super(delivery_van_km, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Nombre con el que se visualiza el documento desde otros documentos
        """
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.van_id.name
            # Si trae codigo el vehiculo agrega la referencia
            if record.value:
                print "*********RECORD.VALUE********: ", record.value
                name = '[%s] %s'%(record.value,name)
            res.append((record.id,name ))
        return res
    
delivery_van_km()

#class delivery_carrier(osv.osv):
#    _name = "delivery.carrier"
#    _inherit = "delivery.carrier"
#
#    _columns = {
#        'driver_ids' : fields.one2many('delivery.driver','carrier_id','Delivery Drivers'),
#    }
#
#delivery_carrier()

class delivery_route_out_move(osv.Model):
    """
        Movimientos de stock (Para transportista)
    """
    _name = "delivery.route.out.move"
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Cambia el estado a realizado
        """
        print"*****CAMBIANDO A ESTADO REALIZADO EN MOVIEMIENTO TRANSPORTISTA(ACTION_DONE DROM)****"
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)
    
    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Retorna el producto disponible sobre la tienda
        """
        product_obj = self.pool.get('product.product')
        res = {}
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({ 'states': ('waiting','assigned','done'), 'what': ('in', 'out') })
        #Recorre las lineas del producto
        for line in self.browse(cr, uid, ids, context=context):
            if not line.product_id:
                # Retorna 0 si no hay producto
                res[line.id] = 0.0
            else:
                # Obtiene el id de la ubicacion origen
                if line.location_id:
                    ctx['location'] = line.location_id.id
                # Asigna la stock virtual del producto a la linea del pedido de venta.
                stock = product_obj.get_product_available(cr, uid, [line.product_id.id], context=ctx)
                res[line.id] = stock.get(line.product_id.id, 0.0)
        return res
    
    _columns = {
        'name': fields.char('Descripcion', size=128),
        'route_id': fields.many2one('delivery.route', 'Ruta'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'product_qty': fields.float('Cantidad'),
        'product_uom': fields.many2one('product.uom', 'Unidad de medida', ondelete="cascade"),
        'location_id': fields.many2one('stock.location', 'Ubicacion origen', ondelete="set null"),
        'state': fields.selection([
            ('draft','Por cargar'),
            ('cancel','Cancelado'),
            ('done', 'Realizado')
            ], 'Estado'),
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
        'picking_id': fields.many2one('stock.picking','Salida Almacen', select=True, domain=[], readonly=True, states={'draft': [('readonly', False)]}), 
    }
    
    _defaults = {
        'state': 'draft'
    }
    
delivery_route_out_move()

class delivery_route(osv.osv):
    _name = 'delivery.route'
    
    def onchange_van_id(self, cr, uid, ids, van_id, context=None):
        """
            Obtiene el chofer del vehiculo que esta por default y la ubicacion del embarque para la ruta
        """
        van_obj = self.pool.get('delivery.van')
        res = {}
        # Valida si recibe el id del vehiculo
        if van_id:
            van = van_obj.browse(cr, uid, van_id, context=context)
            # Agrega el chofer por default para el vehiculo
            if van.driver_id:
                res['driver_id'] = van.driver_id.id or False
            # Agrega la informacion de la ubicacion
            if van.lot_stock_id:
                res['lot_stock_id'] = van.lot_stock_id.id or False
            if van.lot_virtual_id:
                res['lot_virtual_id'] = van.lot_virtual_id.id or False
        return {'value': res}
    
    def _get_weight(self, cr, uid, ids, fields, args, context=None):
        """
            Obtiene el peso total de la ruta en base a las entregas
        """
        result = {}
        for route in self.browse(cr, uid, ids):
            res = {
                'weight': 0.0,
                'weight_max': False
            }
            # Recorre las lineas de la ruta para obtener el peso
            for line in route.line_ids:
                # Incrementa el peso de la ruta
                res['weight'] += line.weight
            # Valida si el peso total excede el peso limite de la ruta
            if res['weight'] > route.van_id.weight_limit and route.van_id.weight_limit > 0.0:
                res['weight_max'] = True
            result[route.id] = res
        return result
    
    _order = 'date DESC, name'
    _columns = {
        'name': fields.char('Referencia', size=64, required=True, select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Fecha', select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'driver_id': fields.many2one('delivery.driver','Chofer', required=False, domain=[], readonly=True, states={'draft': [('readonly', False)]}),
        'van_id': fields.many2one('delivery.van','Vehiculo', required=False, domain=[], readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([
                            ('draft','Borrador'),
                            ('confirm','Confirmado'),
                            ('load','Embarque'),
                            ('shipping_carrier', 'En transito transportista'),
                            ('shipping', 'En transito'),
                            ('return', 'Retorno Ruta'),
                            ('entry', 'Ingreso Vehiculo'),
                            ('unload', 'Desembarque'),
                            ('done', 'Terminado'),
                            ('cancel','Cancelado')],'Estado',readonly=True),
        'weight': fields.function(_get_weight, type='float', store={
                                        'delivery.route': (lambda self,cr,uid,ids,context: ids,['line_ids','state'],10), 
                                    }, multi="weight", string='Peso total'),
        'weight_max': fields.function(_get_weight, type='boolean', store={
                                        'delivery.route': (lambda self,cr,uid,ids,context: ids,['line_ids','state'],10), 
                                    }, multi="weight", string='Peso maximo rebasado'),
        'line_ids': fields.one2many('delivery.route.line','route_id','Lines', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'is_carrier': fields.boolean('Contratar Transportista', readonly=True, states={'draft': [('readonly', False)]}),
        'carrier_id': fields.many2one('res.partner', 'Transportista', readonly=True, states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users','Responsable', readonly=True, states={'draft': [('readonly', False)]}),
        'departure_date': fields.datetime('Fecha Salida', readonly=False, states={'done': [('readonly', True)]}),
        'entry_date': fields.datetime('Fecha Salida', readonly=False, states={'done': [('readonly', True)]}),
        'log_ids': fields.one2many('delivery.route.log', 'route_id', 'Registro Ruta', readonly=True),
        'log_line_ids': fields.one2many('delivery.route.line.log', 'route_id', 'Registro Entregas Ruta', readonly=True),
        'km_init': fields.integer("Kilometraje inicial", readonly=True),
        'km_end': fields.integer("Kilometraje final", readonly=True),
        'km': fields.integer("Kilometraje recorrido", readonly=True),
        'location_id': fields.many2one('stock.location', 'Ubicacion Origen', domain=[], readonly=True, states={'draft': [('readonly', False)]}),
        'lot_virtual_id': fields.many2one('stock.location', 'Ubicacion Espera', domain=[], readonly=True, states={'draft': [('readonly', False)]}),
        'lot_stock_id': fields.many2one('stock.location', 'Ubicacion Destino', domain=[('usage','=','internal')], readonly=True, states={'draft': [('readonly', False)]}),
        'note': fields.text('Notas'),
        'delivered': fields.boolean('Entrega finalizada'),
        'loaded': fields.boolean('Cargamento Terminado'),
        'unloaded': fields.boolean('Desembarque finalizado'),
        'purchase_order_id': fields.many2one('purchase.order', 'Orden de compra')
    }
    
    def _get_default_user(self, cr, uid, context=None):
        """
            Usuario que registra la ruta por default
        """
        return uid
    
    _defaults = {
        'state': 'draft',
        'name': '/',
        'user_id': _get_default_user,
        'date': fields.datetime.now,
        'unloaded': False
    }
    
    def create(self, cr, uid, vals, context=None):
        """
            Genera una secuencia sobre la ruta si no se a agregado texto en el campo name
        """
        # Valida si no tiene una referencia establecida
        if ('name' not in vals) or (vals.get('name')=='/'):
            # Obtiene el numero de la secuencia sugerido para identificador de la ruta
            vals['name'] = self.pool.get('ir.sequence').next_by_code(cr, uid, 'delivery.route.seq', context=context)
        new_id = super(delivery_route, self).create(cr, uid, vals, context)
        return new_id
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no se puedan eliminar rutas que ya fueron confirmadas
        """
        for o in self.browse(cr, uid, ids, context=context):
            if o.state not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid action !'), _('No puede eliminar entregas ya validadas, si desea eliminarla debe cancelarla primero!'))
        return super(delivery_route, self).unlink(cr, uid, ids, context=context)
    
    def change_location(self, cr, uid, id, location_id=False, context=None):
        """
             Actualiza la hubicacion de las salidas de almacen a cargar sobre la ruta
        """
        print "******ACTUALIZANDO UBICACION DE SALIDA DE ALMACEN A CARGAR SOBRE RUTA****"
        print "*****LOCATION_ID*****: ", location_id
        move_obj = self.pool.get('stock.move')
        if context is None:
            context = {}
        # Obtiene el detalle de los productos de la ruta
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('route_id','=',id)], context=context)
        # Obtiene los movimientos de la ruta en base a las entregas
        move_ids = move_obj.search(cr, uid, [('picking_id','in',picking_ids)], context=context)
        # Cambia la ubicacion de origen por la de la ruta
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            vals = {'location_id': location_id}
            # Valida si va a guardar la ubicacion anterior
            if context.get('location_prev',False):
                vals['location_prev_id'] = move.location_id.id or False
            # Actualiza la ubicacion
            move_obj.write(cr, uid, [move.id], vals, context=context)
        return True
    
    def change_location_prev(self, cr, uid, id, context=None):
        """
             Actualiza la hubicacion de las salidas de almacen a la hubicacion anterior sobre las entregas no completadas
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        if context is None:
            context = {}
        # Obtiene el detalle de los productos de la ruta
        picking_ids = picking_obj.search(cr, uid, [('route_id','=',id),('state','not in',['done','cancel'])], context=context)
        # Valida que haya entregas no completadas
        if not picking_ids:
            return []
        # Elimina la relacion de la linea de la ruta
        picking_obj.write(cr, uid, picking_ids, {'route_line_id': False, 'delivered': False, 'delivery_state': 'draft'}, context=context)
        
        # Obtiene los movimientos de la ruta en base a las entregas
        move_ids = move_obj.search(cr, uid, [('picking_id','in',picking_ids)], context=context)
        # Cambia la ubicacion de origen por la que tenia inicialmente
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            if move.location_prev_id:
                vals = {'location_id': move.location_prev_id.id, 'location_prev_id': False}
            # Actualiza la ubicacion
            move_obj.write(cr, uid, [move.id], vals, context=context)
        return picking_ids
    
    def create_stock_move_route(self, cr, uid, id, context=None):
        """
            Crea los movimientos para el embarque sobre la ruta
        """
        print "*****CREANDO MOVIMIENTOS PARA EMBARQUE SOBRE LA RUTA*****"
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        move_data = {}
        move_ids = []
        # Obtiene la informacion de la ruta
        route = self.browse(cr, uid, id, context=context)
        # Obtiene el detalle de los productos de la ruta
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('route_id','=',route.id)], context=context)
        # Obtiene los movimientos de la ruta en base a las entregas
        move_ids = move_obj.search(cr, uid, [('picking_id','in',picking_ids)], context=context)
        # Obtiene la informacion de los embarques y genera las lineas de traspasos para el embarque
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Genera la clave para agrupar los movimientos por Producto,Cantidad,Unidad,UbicacionOrigen
            key = "%s,%s,%s"%(move.product_id.id or False,move.product_qty,move.product_uom.id or False)
            #key = "%s,%s,%s,%s"%(move.product_id.id or False,move.product_qty,move.product_uom.id or False,move.location_id.id or False)
            # Valida si existe el registro entre los agrupadores y si no existe lo crea
            if not move_data.get(key, False):
                move_data[key] = {
                    'product_id': move.product_id.id or False,
                    'name': move.product_id.name or '/',
                    'product_qty': move.product_qty,
                    'product_uom': move.product_uom.id or False,
                    #'location_id': move.location_id.id or False
                    'origin': move.picking_id.name
                }
                continue
            # Actualiza la informacion de la cantidad registrada sobre el movimiento
            move_data[key]['product_qty'] += move.product_qty
            move_data[key]['origin'] = "%s, %s"%(move_data[key]['origin'], move.picking_id.name)
        
        # Context para validar el producto disponible sobre el stock
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
        ctx['location'] = route.location_id.id or False
        # Genera los nuevos movimientos en base a la informacion agrupada de las entregas para el embarque
        for key in move_data:
            # Valida que haya producto disponible sobre el almacen origen para el producto solicitado
            product_available = product_obj.get_product_available(cr, uid, [move_data[key]['product_id']], context=ctx).get(move_data[key]['product_id'], 0.0)
            if product_available < move_data[key]['product_qty']:
                value = float(move_data[key]['product_qty']) - float(product_available)
                raise osv.except_osv(_('Error'), _("No hay producto disponible para surtir la Ruta. (Producto: %s, Pendiente: %s, Entregas: %s)"%(move_data[key]['name'],value,move_data[key]['origin'])))
            
            # Genera arreglo con informacion general del movmiento
            vals = {
                'type': 'internal',
                'origin': route.name,
                'route_id': route.id,
                'location_id': route.location_id.id or False,
                'location_dest_id': route.lot_stock_id.id or False,
                'date_expected': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'product_id': move_data[key].get('product_id',False),
                'name': move_data[key].get('name',False),
                'product_qty': move_data[key].get('product_qty',False),
                'product_uom': move_data[key].get('product_uom',False),
            }
            # Agrega la informacion de la entrega
            #vals.update(move_data[key])
            # Agrega campos extra
            vals['product_uos_qty'] = vals.get('product_qty',1)
            vals['product_uos'] = vals.get('product_uom')
            
            # Crea el nuevo registro
            move_id = move_obj.create(cr, uid, vals, context=context)
            move_ids.append(move_id)
        # Confirma los movimientos de stock
        move_obj.action_confirm(cr, uid, move_ids, context=context)
        return move_ids
    
    def _confirm_route(self, cr, uid, ids, context=None):
        """
            Proceso de confirmacion de ruta
        """
        print"******PROCESO DE CONFIRMACIÓN DE RUTA*******"
        line_obj = self.pool.get('delivery.route.line')
        # Recorre los registros de rutas a confirmar
        for route in self.browse(cr, uid, ids, context=context):
            # Recorre las lineas de la ruta
            for line in route.line_ids:
                print"*****VALIDANDO Y CONFIRMANDO LA ENTREGA SOBRE LA RUTA****"
                # Valida y confirma la entrega sobre la ruta
                line_obj.action_confirm(cr, uid, [line.id], context=context)
        print "****ACTUALIZANDO EL ESTADO DE LA RUTA A CONFIRMADO****"
        # Actualiza la ruta a confirmado
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        # Registra el log de confirmacion de la ruta
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='confirm', context=context)
        return True
    
    def _confirm_route_driver(self, cr, uid, ids, context=None):
        """
            Ejecuta proceso de confirmacion de ruta para chofer
        """
        print"******EJECUTANDO EL PROCESO DE CONFIRMACION PARA EL CHOFER******"
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['location_prev'] = True
        
        # Recorre los registros de rutas a confirmar
        for route in self.browse(cr, uid, ids, context=context):
            print"****PONIENDO LA UBICACION VIRTUAL DE LAS SALIDAS DE ALMACEN EN RUTA"
            # Pone la ubicacion virtual de las salidas de almacen en la ruta
            self.change_location(cr, uid, route.id, location_id=route.lot_virtual_id.id, context=ctx)
            print "*****CREANDO LOS NUEVOS MOVIMIENTOS PARA HACER EMBARQUE****"
            # Crea los nuevos movimientos para hacer el embarque
            self.create_stock_move_route(cr, uid, route.id, context=context)
        
        return True
    
    def create_stock_move_route_carrier(self, cr, uid, id, context=None):
        """
            Crea las salidas que se van a generar para el transportista
        """
        print "******CREANDO SALIDAS QUE SE VAN A GENERAR PARA TRANSPORTISTA******"
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('delivery.route.out.move')
        move_data = {}
        move_ids = []
        # Obtiene la informacion de la ruta
        route = self.browse(cr, uid, id, context=context)
        #print "********ROUTE.ID*************: ", route.id
        # Obtiene el detalle de los productos de la ruta
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('route_id','=',route.id)], context=context)
        #print "*********PICKING_IDS********: ", picking_ids
        # Obtiene los movimientos de la ruta en base a las entregas
        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',picking_ids)], context=context)
        #print "**********MOVE_IDS*********: ", move_ids
        # Obtiene la informacion de los embarques y genera las lineas de traspasos para el embarque
        for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context=context):
            # Genera la clave para agrupar los movimientos por Producto,Cantidad,Unidad
            key = "%s,%s,%s"%(move.product_id.id or False,move.product_qty,move.product_uom.id or False)
            #key = "%s,%s,%s,%s"%(move.product_id.id or False,move.product_qty,move.product_uom.id or False,move.location_id.id or False)
            # Valida si existe el registro entre los agrupadores y si no existe lo crea
            if not move_data.get(key, False):
                move_data[key] = {
                    'product_id': move.product_id.id or False,
                    'name': move.product_id.name or '/',
                    'product_qty': move.product_qty,
                    'product_uom': move.product_uom.id or False,
                    #'location_id': move.location_id.id or False
                    'origin': move.picking_id.name
                }
                continue
            # Actualiza la informacion de la cantidad registrada sobre el movimiento
            move_data[key]['product_qty'] += move.product_qty
            move_data[key]['origin'] = "%s, %s"%(move_data[key]['origin'], move.picking_id.name)
        
        
        # Context para validar el producto disponible sobre el stock
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
        ctx['location'] = route.location_id.id or False
        #print "********CTX********: ", ctx
        # Genera los nuevos movimientos en base a la informacion agrupada de las entregas para el embarque
        for key in move_data:
            # Valida que haya producto disponible sobre el almacen origen para el producto solicitado
            product_available = product_obj.get_product_available(cr, uid, [move_data[key]['product_id']], context=ctx).get(move_data[key]['product_id'], 0.0)
            if product_available < move_data[key]['product_qty']:
                value = float(move_data[key]['product_qty']) - float(product_available)
                raise osv.except_osv(_('Error'), _("No hay producto disponible para surtir la Ruta. (Producto: %s, Pendiente: %s, Entregas: %s)"%(move_data[key]['name'],value,move_data[key]['origin'])))
            
            # Genera arreglo con informacion general del movmiento
            vals = {
                'route_id': route.id,
                'location_id': route.location_id.id or False,
                'state': 'draft',
                'product_id': move_data[key].get('product_id',False),
                'name': move_data[key].get('name',False),
                'product_qty': move_data[key].get('product_qty',False),
                'product_uom': move_data[key].get('product_uom',False),
            }
            # Agrega la informacion de la entrega
            #vals.update(move_data[key])
            
            
            # Crea el nuevo registro
            move_id = move_obj.create(cr, uid, vals, context=context)
            move_ids.append(move_id)
        
        return move_ids
    
    def _confirm_route_carrier(self, cr, uid, ids, context=None):
        """
            Confirma la ruta para transportista
        """
        print "******CONFIRMANDO RUTA PARA TRANSPORTISTA********"
        quantity = 0
        res = {}
        details = {}
        details_list = []
        purchase_obj = self.pool.get('purchase.order')
        line_obj = self.pool.get('purchase.order.line')
        # Obtiene la tarifa
        for move in self.browse(cr, uid, ids, context=context):
            pricelist_id = move.carrier_id.property_product_pricelist_purchase.id
        print "*******PRICELIST_ID**********: ", pricelist_id
        # Recorre las rutas a confirmar
        for route in self.browse(cr, uid, ids, context=context):
            # Crea el pedido de compra
            values = {
                'partner_id': route.carrier_id.id,
                'route_id': route.id,
                'from_carrier': True,
                'origin': route.name,
                'location_id': route.location_id.id,
                'pricelist_id': pricelist_id,
            }
            #print "********VALUES********: ", values
            print "******GENERANDO ORDEN DE COMPRA*******"
            purchase_id = purchase_obj.create(cr, uid, values, context=context)
            product = route.carrier_id.concept_id
            
            print "************PURCHASE_ID*******: ", purchase_id
            print "********PRODUCT*********: ", product
            
            # Crea el concepto sobre el pedido de compra
            details = {
                'product_id': product.id,
                'name': product.name,
                'date_planned': route.date,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
                'product_qty': quantity,
                'order_id': purchase_id or False,
                'state': 'draft',
            }
            
            #print "*********DETAILS**********: ", details
            print "****CREANDO LOS DETALLES DE LA ORDEN DE COMPRA DEL TRANSPORTISTA*****"
            line_id = line_obj.create(cr, uid, details, context=context)
            
            print "********LINE_ID*******: ", line_id
            print "******ROUTE.ID*****: ", route.id
            
            print "*****CREANDO LOS ENBARQUES PARA TRANSPORTISTA*******"
            # Crea los nuevos movimientos para hacer el embarque
            self.create_stock_move_route_carrier(cr, uid, route.id, context=context)
        
            # Relaciona la orden de compra con la ruta
            self.write(cr, uid, ids, {'purchase_order_id': purchase_id}, context=context)
        
        return True
    
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Confirma la ruta generada y valida que las entregas no se hayan entregado o esten sobre otra ruta
        """
        print "***********CONFIRMANDO RUTA GENERADA***********"
        # Pasa la ruta a confirmado
        self._confirm_route(cr, uid, ids, context=context)
        
        # Ejecuta proceso para confirmar rutas con transportista
        r_carrier_ids = self.search(cr, uid, [('id','in', ids),('is_carrier','=',True)], context=context)
        if r_carrier_ids:
            purchase_id = self._confirm_route_carrier(cr, uid, ids, context=context)
        # Ejecuta proceso para confirmar rutas con chofer
        r_driver_ids = self.search(cr, uid, [('id','in', ids),('is_carrier','=',False)], context=context)
        if r_driver_ids:
            self._confirm_route_driver(cr, uid, ids, context=context)
        
        return True
    
    def action_prepare_move_stock(self, cr, uid, ids, context=None):
        """
            Abre la ventana que contiene la informacion de la ruta
        """
        print "******ABRIENDO LA VENTANA QUE CONTIENE LA INFORMACION DE LA RUTA********"
        route_id = ids[0]
        move_obj = self.pool.get('stock.move')
        line_obj = self.pool.get('prepare.move.stock.route.line')
        if context is None:
            context={}
        #res = {}
        lines = []
        loaded = True
        # Crea registro provisional para ejecucion de wizard
        res_id = self.pool.get('prepare.move.stock.route').create(cr, uid, {'route_id': route_id}, context=context)
        #print "************** res *********** ", res_id
        
        # Obtiene los movimientos de los productos a cargar en la camioneta
        move_ids = move_obj.search(cr, uid, [('route_id','=',route_id)], context=context)
        #print "****************** valores ruta ***************** ", move_ids
        # Genera la lista de movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Informacion de movimiento
            vals = {
                'name': move.name,
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'product_uom': move.product_uom.id or False,
                'location_id': move.location_id.id or False,
                'location_dest_id': move.location_dest_id.id or False,
                'state': move.state,
                'route_id': route_id,
                'move_id': move.id,
                'wizard_id': res_id
            }
            line_obj.create(cr, uid, vals, context=context)
            lines.append(vals)
            print "*******MOVE.STATE******: ", move.state
            if move.state not in ('cancel','done'):
                loaded = False
        #print "************* ruta ******* ", ids[0]
        #print "************* default ******* ", lines
        print "*****LOADED****: ", loaded
        # Pone el cargamento como finalizado si ya todo esta como entregado
        if loaded:
            print "********CARGANDO EL VEHICULO********"
            self.write(cr, uid, ids, {'loaded': loaded}, context=context)
            
        # Va a la parte de Preparar embarque
        return {
            'name': 'Preparar Embarque',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'prepare.move.stock.route',
            'target' : 'new',
            'context': {'default_route_id': ids[0]},
            'type': 'ir.actions.act_window',
            'res_id': res_id
        }
           
        
    def action_prepare_out_route_move(self, cr, uid, ids, context=None):
        """
            Abre la ventana que contiene la información del transportista
        """
        
        route_id = ids[0]
        move_obj = self.pool.get('delivery.route.out.move')
        line_out_obj = self.pool.get('delivery.route.out.wizard.line')
        if context is None:
            context={}
        #res = {}
        lines = []
        loaded = True
        
        print "*******PREPARANDO EMBARQUE PARA TRANSPORTISTA********"
        
        # Crea registro provisional para ejecucion de wizard
        res_id = self.pool.get('delivery.route.out.wizard').create(cr, uid, {'route_id': route_id},
            context=context)
        
        #print "*********RES_ID*********: ", res_id
        #print "********ROUTE_ID********: ", route_id
        
        # Obtiene los movimientos de los productos a cargar en la camioneta
        move_ids = move_obj.search(cr, uid, [('route_id','=',route_id)], context=context)
        print "****************** valores ruta ***************** ", move_ids
        # Genera la lista de movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Informacion de movimiento
            vals1 = {
                'name': move.name,
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'product_uom': move.product_uom.id or False,
                'location_id': move.location_id.id or False,
                'location_dest_id': move.route_id.carrier_id.property_stock_supplier.id or False,
                'state': move.state,
                'route_id': route_id,
                'move_id': move.id,
                'wizard_id': res_id,
            }
            print "********VALS*********: ", vals1
            line_out_id = line_out_obj.create(cr, uid, vals1, context=context)
            print "**********LINE_OUT_ID********: ", line_out_id
            lines.append(vals1)
            print "********MOVE.STATE********: ", move.state
            if move.state not in ('cancel','done'):
                loaded = False
        print "*****LOADED*****: ", loaded
        if loaded:
            print "********CARGANDO EL VEHICULO********"
            self.write(cr, uid, ids, {'loaded': loaded}, context=context)
        
        return{
            'name': 'Preparar Embarque para Transportista',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.route.out.wizard',
            'context': {'default_route_id': ids[0]},
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id
        }
    
    def action_load_carrier(self, cr, uid, ids, context=None):
        """
            Confirma la ruta generada y valida la entrega al transportista
        """
        print "****CONFIRMANDO RUTA GENERADA Y VALIDANDO ENTREGA A TRANSPORTISTA**"
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'load'}, context=context)
        print"*******ACTUALIZANDO EL ESTADO DEL TRANSPORTISTA A CARGADO******"
        
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='load', context=context)
        
        # Retorna la ventana que muestra el resultado 
        return self.action_prepare_out_route_move(cr, uid, ids, context=context)
            
    def action_load(self, cr, uid, ids, context=None):
        """
            Confirma la ruta generada y valida que las entregas no se hayan entregado o esten sobre otra ruta
        """
        print "*****CONFRIMA LA RUTA GENERADA Y VALIDA LAS ENTREGAS NO ENTREGADAS O SOBRE RUTA"
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'load'}, context=context)
        print "****SE ACTUALIZO EL ESTADO DE DESEMBARQUE A CARGADO*****" 
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='load', context=context)
        
        # Retorna la ventana que muestra el resultado 
        return self.action_prepare_move_stock(cr, uid, ids, context=context)
    
    def action_reaload(self, cr, uid, route_id, context=None):
        """
            Carga el formulario de la ruta especificado
        """
        print"****CARGANDO EL FORMULARIO DE LA RUTA****"
        # Redirecciona al formulario de ruta
        if not route_id: return False
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
            'res_id': route_id
        }
    
    def update_stock(self, cr, uid, ids, context=None):
        """
            Actualiza en la ruta la informacion del embarque chofer
        """
        print"*****ACTUALIZANDO EN LA RUTA LA INFORMACION DEL EMBARQUE CHOFER****"
        res_id = ids[0]
        print"****ACTUALIZANDO EL ESTADO DE EMBARQUE A FINALIZADO"
        # Actualiza el proceso de embarque a finalizado
        self.write(cr, uid, ids, {'loaded': True}, context=context)
       
        # Redirecciona al formulario de ruta
        return self.action_reaload(cr, uid, res_id, context=context)
    
    def update_unload_stock(self, cr, uid, ids, context=None):
        """
            Actualiza en la ruta la informacion del embarque transportista
        """
        print"***ACTUALIZANDO EN LA RUTA LA INFORMACION DEL EMBARQUE TRANSPORTISTA****"
        res_id = ids[0]
        # Actualiza el proceso de embarque a finalizado
        self.write(cr, uid, ids, {'unloaded': True}, context=context)
       
        # Redirecciona al formulario de ruta
        return self.action_reaload(cr, uid, res_id, context=context)    
    
    def action_shipping_carrier(self, cr, uid, ids, context):
        """
            Pone la ubicacion de origen sobre las rutas que se va a hacer la entrega transportista
        """
        print "*********COLOCANDO UBICANCION DE ORIGEN SOBRE LAS RUTAS DONDE SE HACEN LAS ENTREGAS TRANSPORTISTA*****"
        line_obj = self.pool.get('delivery.route.line')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        move_data = {}
        
        # Prepara todas las entregas a por surtir
        for route in self.browse(cr, uid, ids, context=context):
            lines = 0
            # Recorre las lineas de entrega y actualiza su estado
            for line in route.line_ids:
                line_obj.to_delivered_carrier(cr,uid,[line.id],context=context)
                lines += 1
            # Valida que haya lineas para la ruta
            if lines > 0:
                # Crea la salida de por surtir para la ruta
                line_obj.open_route_line(cr, uid, route.id, context=context)
        print"****ACTUALIZANDO AL ESTADO DE EMBARQUE TRANSPORTISTA****"
         #Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'shipping_carrier', 'departure_date': date}, context=context)
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='shipping_carrier', context=context)
        return True    
    
    def action_shipping(self, cr, uid, ids, context=None):
        """
            Pone la ubicacion de origen sobre las rutas que se va a hacer la entrega
        """
        print "*********COLOCANDO UBICANCION DE ORIGEN SOBRE LAS RUTAS DONDE SE HACEN LAS ENTREGAS*****"
        line_obj = self.pool.get('delivery.route.line')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        move_data = {}
        
        # Prepara todas las entregas a por surtir
        for route in self.browse(cr, uid, ids, context=context):
            lines = 0
            # Recorre las lineas de entrega y actualiza su estado
            for line in route.line_ids:
                line_obj.action_open(cr,uid,[line.id],context=context)
                lines += 1
            # Valida que haya lineas para la ruta
            if lines > 0:
                # Crea la salida de por surtir para la ruta
                line_obj.open_route_line(cr, uid, route.id, context=context)
        print"****ACTUALIZANDO LA RUTA AL ESTADO EMBARQUE****"
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'shipping', 'departure_date': date}, context=context)
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='shipping', context=context)
        return True
    
    def action_departure(self, cr, uid, ids, context=None):
        """
            Pide para iniciar con la salida de la ruta, el kilometraje inicial del vehiculo y 
        """
        print "********PIDIENDO INICIO CON LA SALIDA DE LA RUTA********"
        line_obj = self.pool.get('delivery.route.line')
        route = self.browse(cr, uid, ids[0], context=context)
        print "******ROUTE*******: ", route
        
        # Pone la ubicacion del verhiculo en el origen del almacen en la ruta
        self.change_location(cr, uid, route.id, location_id=route.lot_stock_id.id, context=context)
        
        # Valida que este completo el embarque en la ruta
        if not route.loaded:
            raise osv.except_osv(_('Error'), _("Antes de partir, asegurese de que todos los productos se encuentren cargados sobre el vehiculo para las entregas y el embarque este actualizado sobre el sistema."))
        
        van_id = route.van_id.id or False
        # Va a la parte de Preparar embarque
        return {
            'name': 'Salida vehiculo',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'prepare.departure.route',
            'target' : 'new',
            'context': {'default_route_id': ids[0], 'default_van_id': van_id, 'default_departure_date':time.strftime('%Y-%m-%d %H:%M:%S')},
            'type': 'ir.actions.act_window'
        }
    
    def action_return(self, cr, uid, ids, context=None):
        """
            Pasa la ruta a estado en retorno ruta
        """
        print"****PASANDO LA RUTA A ESTADO EN RETORNO RUTA***"
        line_obj = self.pool.get('delivery.route.line')
        move_obj = self.pool.get('stock.move')
        route_ids = []
        
        # Valida que todas las lineas esten entregadas
        for route in self.browse(cr,uid,ids,context=context):
            for line in route.line_ids:
                if line.state in ('draft','planned','open','arrived','delivered'):
                    raise osv.except_osv(_('Error'), _("Para retornar la ruta primero debe completar todas las entregas."))
            
            # Valida si la ruta es de chofer
            if route.is_carrier == False:
                route_ids.append(route.id)
        
        # Actualiza la ruta al estado de Retorno Ruta del chofer
        self.write(cr, uid, route_ids, {'state': 'return'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado del chofer
        self.pool.get('delivery.route.log').add_log_route(cr, uid, route_ids, state='return', context=context)
        
        return True
    
    def action_reshipping(self, cr, uid, ids, context=None):
        """
            Pasa la ruta a estado en En entrega
        """
        print "******PASANDO RUTA A ESTADO DE ENTREGA********"
        line_obj = self.pool.get('delivery.route.line')
        move_obj = self.pool.get('stock.move')
        
        # Valida que todas las lineas esten entregadas
        for route in self.browse(cr,uid,ids,context=context):
            lines = False
            for line in route.line_ids:
                if line.state not in ('return','planned','open','arrived','delivered'):
                    lines = True
            if lines == False:
                raise osv.except_osv(_('Error'), _("No se puede pasar la ruta al estado 'En transito' porque todas las entregas fueron completadas."))
        print"***ACTUALIZANDO LA RUTA A ESTADO DE RETORNO RUTA***"
        # Actualiza la ruta al estado de Retorno Ruta
        self.write(cr, uid, ids, {'state': 'shipping'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='shipping', context=context)
        return True
    
    def create_unload_stock_move(self, cr, uid, id, picking_ids=[], context=None):
        """
            Crea los movimientos para el desembarque sobre la ruta
        """
        print "*****CREANDO MOVIMIENTOS PARA DESEMBARQUE SOBRE RUTA*****"
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        move_data = {}
        move_ids = []
        # Obtiene la informacion de la ruta
        route = self.browse(cr, uid, id, context=context)
        
        # Obtiene los movimientos de la ruta en base a las entregas
        move_ids = move_obj.search(cr, uid, [('picking_id','in',picking_ids)], context=context)
        # Obtiene la informacion de los embarques y genera las lineas de traspasos para el desembarque
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Genera la clave para agrupar los movimientos por Producto,Cantidad,Unidad,UbicacionOrigen
            key = "%s,%s,%s"%(move.product_id.id or False,move.product_qty,move.product_uom.id or False)
            # Valida si existe el registro entre los agrupadores y si no existe lo crea
            if not move_data.get(key, False):
                move_data[key] = {
                    'product_id': move.product_id.id or False,
                    'name': move.product_id.name or '/',
                    'product_qty': move.product_qty,
                    'product_uom': move.product_uom.id or False,
                    'origin': move.picking_id.name
                }
                continue
            # Actualiza la informacion de la cantidad registrada sobre el movimiento
            move_data[key]['product_qty'] += move.product_qty
            move_data[key]['origin'] = "%s, %s"%(move_data[key]['origin'], move.picking_id.name)
        
        # Context para validar el producto disponible sobre el stock
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
        ctx['location'] = route.lot_stock_id.id or False
        # Genera los nuevos movimientos en base a la informacion agrupada de lo no entregado para el desembarque
        for key in move_data:
            # Valida que haya producto disponible sobre el almacen origen para el producto solicitado
            product_available = product_obj.get_product_available(cr, uid, [move_data[key]['product_id']], context=ctx).get(move_data[key]['product_id'], 0.0)
            if product_available < move_data[key]['product_qty']:
                value = float(move_data[key]['product_qty']) - float(product_available)
                raise osv.except_osv(_('Error'), _("No hay producto disponible para descargar la Ruta. (Producto: %s, Pendiente: %s, Entregas: %s)"%(move_data[key]['name'],value,move_data[key]['origin'])))
            
            # Genera arreglo con informacion general del movmiento
            vals = {
                'type': 'internal',
                'origin': route.name,
                'route_id': route.id,
                'location_id': route.lot_stock_id.id or False,
                'location_dest_id': route.location_id.id or False,
                'date_expected': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # Agrega la informacion de la entrega
            vals.update(move_data[key])
            # Agrega campos extra
            vals['product_uos_qty'] = vals.get('product_qty',1)
            vals['product_uos'] = vals.get('product_uom')
            # Crea el nuevo registro
            move_id = move_obj.create(cr, uid, vals, context=context)
            move_ids.append(move_id)
        print "*****CONFIRMANDO LOS MOVIMIENTOS DE STOCK*******"
        # Confirma los movimientos de stock
        move_obj.action_confirm(cr, uid, move_ids, context=context)
        return move_ids
    
    def action_entry(self, cr, uid, ids, context=None):
        """
            Gestiona el ingreso del vehilculo y lo pasa a estado de Ingreso Vehiculo
        """
        print"***GESTIONANDO EL INGRESO DEL VEHICULO, PASANDOLO A ESTADO DE INGRESO VEHICULO**"
        route = self.browse(cr, uid, ids[0], context=context)
        
        # Valida que la ruta este en retorno
        if route.state != 'return':
            raise osv.except_osv(_('Error'), _("No se puede retornar la ruta si no se encuentra en el estatus de 'Retorno Ruta'. (Estado: %s)"%(route.state,)))
        # Cambia las salidas de almacen no entregadas a la hubicacion origen original y la desrelaciona de la ruta
        picking_ids = self.change_location_prev(cr, uid, route.id, context=context)
        # Si no hay entregas sin completar para el desembarque pone la ruta con el desembarque completo
        if not picking_ids:
            # Pone la ruta con desembarque completo porque no hay productos para aplicar desembarque
            self.write(cr, uid, [route.id], {'loaded':True}, context=context)
        else:
            # Prepara los movimientos para descargar la ruta
            self.create_unload_stock_move(cr, uid, route.id, picking_ids, context=context)
        
        # Actualiza la ruta al estado de Terminado
        self.write(cr, uid, ids, {'state': 'entry'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='entry', context=context)
        
        # Vehiculo a descargar
        van_id = route.van_id.id or False
        # Va a la parte de registrar el kilometraje final
        return {
            'name': 'Ingreso vehiculo',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reception.entry.route',
            'target' : 'new',
            'context': {'default_route_id': ids[0], 'default_van_id': van_id, 'default_entry_date':time.strftime('%Y-%m-%d %H:%M:%S')},
            'type': 'ir.actions.act_window'
        }
    
    def prepare_unload_stock_route(self, cr, uid, ids, context=None):
        """
            Abre la ventana que contiene la informacion de la ruta para el desembarque
        """
        print "****ABRIENDO VENTANA CON INFORMACION DE LA RUTA PARA EL DESEMBARQUE********"
        route_id = ids[0]
        move_obj = self.pool.get('stock.move')
        line_obj = self.pool.get('prepare.unload.stock.route.line')
        if context is None:
            context={}
        #res = {}
        lines = []
        unloaded = True
        # Crea registro provisional para ejecucion de wizard
        res_id = self.pool.get('prepare.unload.stock.route').create(cr, uid, {'route_id': route_id}, context=context)
        # Obtiene la ubicacion origen de donde salen los movimientos
        lot_stock_id = self.pool.get('delivery.route').browse(cr, uid, route_id, context=context).lot_stock_id.id or False
        # Obtiene los movimientos de los productos a cargar en la camioneta
        move_ids = move_obj.search(cr, uid, [('route_id','=',route_id),('location_id','=',lot_stock_id)], context=context)
        # Genera la lista de movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Informacion de movimiento
            vals = {
                'name': move.name,
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'product_uom': move.product_uom.id or False,
                'location_id': move.location_id.id or False,
                'location_dest_id': move.location_dest_id.id or False,
                'state': move.state,
                'route_id': route_id,
                'move_id': move.id,
                'wizard_id': res_id
            }
            # Crea la linea con el movimientos a entregar
            line_obj.create(cr, uid, vals, context=context)
            lines.append(vals)
            if move.state not in ('cancel','done'):
                unloaded = False
        # Pone el cargamento como finalizado si ya todo esta como descargado del vehiculo
        if unloaded:
            self.write(cr, uid, ids, {'unloaded': unloaded}, context=context)
        
        # Va a la parte de Preparar desembarque
        return {
            'name': 'Preparar Desembarque',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'prepare.unload.stock.route',
            'target' : 'new',
            'context': {'default_route_id': route_id},
            'type': 'ir.actions.act_window',
            'res_id': res_id
        }
    
    def action_unload(self, cr, uid, ids, context=None):
        """
            Pasa la ruta a estado en retorno ruta
        """
        print"***PASANDO LA RUTA A ESTADO EN RETORNO RUTA****"
        # Actualiza la ruta al estado de Retorno Ruta
        self.write(cr, uid, ids, {'state': 'unload'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='unload', context=context)
        
        # Abre el wizard para realizar la descarga del vehiculo
        return self.prepare_unload_stock_route(cr, uid, ids, context=context)
    
    def action_apply_all_lines(self, cr, uid, ids, context=None):
        """
            Ejecuta la entrega de todas las lineas de la ruta
        """
        print"*********ENTREGANDO TODAS LAS LINEAS DE LA RUTA*****"
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        rline_obj = self.pool.get('delivery.route.line')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        # Obtiene la informacion de la ruta
        route = self.browse(cr, uid, ids[0], context=context)
        print"******ROUTE******: ", route
        # Obtiene el detalle de los productos de la ruta
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('route_id','=',route.id)], context=context)
        # Recorremos las salidas de almacen a entregar
        for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
            # Generamos arreglo para las entregas de la salida del almacen
            partial_data = {
                'delivery_date' : date
            }
            
            # Recorremos las lineas del almacen
            for move in picking.move_lines:
                line_uom = move.product_uom
                
                # Calcula la cantidad del producto en base a la unidad de medida base
                qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, move.product_qty, line_uom.id)
    
                # Valida el factor de la linea
                if line_uom.factor and line_uom.factor != 0:
                    if float_compare(qty_in_line_uom, move.product_qty, precision_rounding=line_uom.rounding) != 0:
                        raise osv.except_osv(_('Warning!'), _('La unidad de redondeo medida no permite que usted envíe "%s %s", solo redondeo de "%s %s" es aceptado por la unidad de medida.') % (wizard_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
                # Valida que el movimiento no este entregado
                if move.state != 'done':
                    initial_uom = move.product_uom
                    #Compute the quantity for respective wizard_line in the initial uom
                    qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, move.product_qty, initial_uom.id)
                    without_rounding_qty = (move.product_qty / line_uom.factor) * initial_uom.factor
                    if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
                        raise osv.except_osv(_('Warning!'), _('La unidad de redondeo medida no permite que usted envíe "%s %s", solo redondeo de "%s %s" es aceptado por la unidad de medida.') % (wizard_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
                    # Agrega la informacion del producto a entregar
                    partial_data['move%s' % (move.id)] = {
                        'product_id': move.product_id.id or False,
                        'product_qty': move.product_qty,
                        'product_uom': move.product_uom.id or False,
                        'prodlot_id': move.prodlot_id.id or False,
                    }
            # Aplica la salida de almacen sobre los productos a entregar
            picking_obj.do_partial(cr, uid, [picking.id], partial_data, context=context)
            
            print"****INDICANDO QUE LA LINEA FUE ENTREGADA****"
            # Indica que la linea fue entregada
            rline_obj.write(cr, uid, [picking.route_line_id.id], {'delivered': True}, context=context)
            print"****PONIENDO LA LINEA DE LA RUTA COMO ENTREGADO*****"
            # Pone la linea de la ruta como entregado
            rline_obj.action_done_carrier(cr, uid, [picking.route_line_id.id], context=context)
        return True
    
    
    def action_done_carrier(self, cr, uid, ids, context=None):
        """
            Pasa la ruta a estado en Terminado de transportista
        """
        print "****PASANDO LA RUTA A ESTADO TERMINADO DE TRANSPORTISTA (ACTION_DONE_CARRIER DR)****"
        # Se realizan todas las entrega de las lineas de la ruta
        self.action_apply_all_lines(cr, uid, ids, context=context)
        print "*****ACTUALIZANDO LA RUTA AL ESTADO TERMINADO (ACTION_DONE_CARRIER DR)***"
        # Actualiza la ruta al estado de Terminado
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='done', context=context)
        return True
        
    
    def action_done(self, cr, uid, ids, context=None):
        """
            Pasa la ruta a estado en Terminado
        """
        print "*****PASANDO LA RUTA A ESTADO TERMINADO****"
        # Actualiza la ruta al estado de Terminado
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.log').add_log_route(cr, uid, ids, state='done', context=context)
        return True
    
    
    def action_cancel(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('delivery.route.line')
        for route in self.browse(cr,uid,ids,context=context):
            for line in route.line_ids:
                line_obj.action_cancel(cr,uid,[line.id],context=context)
        self.write(cr, uid, ids, {'state': 'cancel','confirm_cs':False}, context=context)
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('delivery.route.line')
        for route in self.browse(cr,uid,ids,context=context):
            for line in route.line_ids:
                line_obj.action_draft(cr,uid,[line.id],context=context)
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True
    
delivery_route()

class delivery_route_line(osv.osv):
    _name = 'delivery.route.line'
    
    def _get_driver(self, cr, uid, ids, field, args, context=None):
        """
            Obtiene al chofer
        """
        result = {}
        for route in self.browse(cr, uid, ids):
            res = False
            if route.route_id:
                res = route.route_id.driver_id and route.route_id.driver_id.id or False
            result[route.id] = res
        return result
    
    def _get_origin(self, cr, uid, ids, fields, args, context=None):
        """
            Origen del Albaran
        """
        result = {}
        for route in self.browse(cr, uid, ids):
            res = {}
            res['origin'] = route.picking_id.origin or route.picking_id.name or ""
            res['sale_order_id'] = route.picking_id.sale_id and route.picking_id.sale_id.id or False
            res['purchase_id'] = route.picking_id.purchase_id and route.picking_id.purchase_id.id or False
            res['address_id'] = route.picking_id.partner_id and route.picking_id.partner_id.id or False
            res['picking_note'] = route.picking_id.note or " "
            result[route.id] = res
        return result
    
    def _route_to_update_after_picking_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('delivery.route.line').search(cr, uid, [('picking_id','in',ids)]) or []
    
    _store_origin = {
        'delivery.route.line': (lambda self,cr,uid,ids,context: ids,['picking_id'],10), 
        'stock.picking': (_route_to_update_after_picking_change, ['sale_id','purchase_id','origin','note','partner_id'], 10),
    }
    
    def _route_to_update_after_parent_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('delivery.route.line').search(cr, uid, [('route_id','in',ids)]) or []
    
    def onchange_picking_id(self, cr, uid, ids, picking_id, context=None):
        """
            Llena la referencia con el nombre del pedido al cambiar de almacen
        """
        route_line_log_obj = self.pool.get('delivery_route_line_log')
        line_ids = []
        value = {}
        
        stock_picking_obj = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        reference = stock_picking_obj.origin        
        print "********REFERENCE***********: ", reference
        
        value = {
            'name': reference
        }
        
        
        return {'value': value}
    
    _store_drivers = {
        'delivery.route.line': (lambda self,cr,uid,ids,context: ids,['route_id'],10), 
        'delivery.route': (_route_to_update_after_parent_change, ['driver_id'], 10),
    }
    
    _columns = {
        'sequence': fields.integer('Orden'),
        'route_id': fields.many2one('delivery.route','Ruta entrega', required=False, readonly=True, states={'draft': [('readonly', False)]}, ondelete="cascade"),
        'picking_id': fields.many2one('stock.picking','Salida Almacen', required=True, select=True, domain=[], readonly=True, states={'draft': [('readonly', False)]}),            
        'invoice_id': fields.related('picking_id', 'invoice_id', store=False, relation="account.invoice", type='many2one', string="Factura", readonly=True),
        'name': fields.char('Descripcion', size=256),
        'origin': fields.function(_get_origin, type='char', size=256, store=_store_origin, multi="origin", string='Origen'),
        'purchase_id': fields.function(_get_origin, type='many2one', obj='purchase.order', store=_store_origin, multi="origin", string='Orden de Compra'),
        'sale_order_id': fields.function(_get_origin, type='many2one', obj='sale.order', store=_store_origin, multi="origin", string='Pedido de Venta'),
        'picking_note': fields.function(_get_origin, type='html', multi="origin", string='Notas'),
        'address_id': fields.function(_get_origin,type='many2one',relation='res.partner', multi="origin", string='Direccion Entrega', store=True),
        'schedule_id': fields.related('address_id', 'schedule_id', type="many2one",
            relation="delivery.schedule", string="Horario de entrega", store=True),
        'state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('delivered_carrier', 'En entrega transportista'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')], string='Estado entrega', store=True, readonly=True),
        'visit_date': fields.datetime('Fecha Entrega', states={'done': [('required', True)], 'done':[('readonly',True)], 'delivered':[('readonly',True)],}),
        'note': fields.text('Notes'),
        'color': fields.integer('Color Index'),
        'exceptions': fields.boolean('Recibido con excepciones'),
        'delivered': fields.boolean('Entregado'),
        # Informacion de peso y numero de bultos sobre la entrega
        'qty': fields.related('picking_id', 'number_of_packages', readonly=True, type='float', string='Bultos', help="Bultos contenidos por el pedido"),
        'weight': fields.related('picking_id', 'weight', type='float', readonly=True, string='Peso', help="Peso total del pedido"),
        # Informacion de direccion cliente
        'street': fields.related('address_id', 'street', type='char', size=256, string='Calle'),
        'street2': fields.related('address_id', 'street2', type='char', size=128, string='Colonia'),
        'l10n_mx_street3': fields.related('address_id', 'l10n_mx_street3', type='char', size=32, string='No Ext.'),
        'l10n_mx_street4': fields.related('address_id', 'l10n_mx_street4', type='char', size=32, string='No Int.'),
        'city': fields.related('address_id', 'city', type='char', size=64, string='Ciudad'),
        'l10n_mx_city2': fields.related('address_id', 'l10n_mx_city2', type='char', size=64, string='Localidad'),
        'zip': fields.related('address_id', 'zip', type='char', size=16, string='CP'),
        'partner_phone': fields.related('address_id', 'phone', type='char', size=128, string='Telefono', readonly=True),
        'partner_mobile': fields.related('address_id', 'mobile', type='char', size=128, string='Celular', readonly=True),
        'state_id': fields.related('address_id', 'state_id', type='many2one', relation="res.country.state", string="Estado", readonly=True),
        'zone_id': fields.related('address_id', 'property_delivery_zone', type='many2one', relation="delivery.zone", string="Zona", readonly=True, store=True),
        # Lineas de entrega
        'move_lines': fields.related('picking_id', 'move_lines', type='one2many', relation="stock.move", string="Producto a entregar", readonly=True),
        # Informacion chofer
        'driver_id': fields.function(_get_driver, type='many2one', relation="delivery.driver", store=_store_drivers, string='Chofer'),
        'driver_phone': fields.related('driver_id', 'phone', type='char', size=64, string='Telefono Chofer'),
        'user_id': fields.many2one('res.users', 'Chofer'),
        'log_line_ids': fields.one2many('delivery.route.line.log', 'route_line_id', 'Registro Entregas Ruta', readonly=True),
    }
    _order = 'sequence'

    _defaults = {
        'state': 'draft'
    }
    
    def _check_picking_repeat(self, cr, uid, ids, context=None):
        """
            Valida que no este repetido el registro sobre la ruta
        """
        for line in self.browse(cr, uid, ids, context=context):
            line_ids = self.search(cr, uid, [('id','!=',line.id),('picking_id','=',line.picking_id.id or False),('route_id','=',line.route_id.id or False)], context=context)
            if line_ids:
                return False
        return True

    _constraints = [
        (_check_picking_repeat, 'No puede agregar salidas de almacen repetidas sobre las lineas de entrega en la ruta.', ['picking_id']),
    ]
    
    def _read_group_route_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        context = context or {}
        route_obj = self.pool.get('delivery.route')
        args = [('state', '=', 'draft')]
        if 'force_dts_id_kanban' in context:
            args.append(('dts_id', '=', context['force_dts_id_kanban']))
        route_ids = route_obj.search(cr, uid, args, order='name', context=context)
        result = route_obj.name_get(cr, uid, route_ids, context=context)
        fold = {}
        return result, fold
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Valida que no se puedan eliminar entregas de la ruta que ya fueron planeadas o en proceso de entrega
        """
        print"****VALIDANDO QUE NO SE PUEDAN ELIMINAR ENTREGAS PLANEADAS O EN PROCESO DE ENTREGA DE LA RUTA****"
        for o in self.browse(cr, uid, ids, context=context):
            if o.state not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid action !'), _('No puede eliminar entregas ya planeadas, si desea eliminarla debe cancelarla primero!'))
        return super(delivery_route_line, self).unlink(cr, uid, ids, context=context)
    
    def open_route_line(self, cr, uid, route_id, context=None):
        """
            Crea en el log un registro de por surtir para la ruta sin indicar la entrega
        """
        print"****** CREANDO EN EL LOG UN REGISTRO DE POR SURTIR  PARA LA RUTA SIN INDICAR ENTREGA (OPEN_ROUTE_LINE DRL)*****"
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route(cr, uid, route_id, state='open', context=context)
        return True
    
    def action_return_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado Devuelto en la salida del almacen
        """
        print"****COLOCANDO EL ESTADO DEVUELTO EN LA SALIDA DEL ALMACEN****"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'return'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Devuelto</b>', context)
        return True
    
    def action_return(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado Devuelto
        """
        print"PASANDO LA ENTREGA A ESTADO DEVUELTO*****"
        route_ids = []
        # Agrega el registro del estado arribado
        for line in self.browse(cr,uid,ids,context=context):
            self.action_return_do_line(cr, uid, line, context=context)
            # Agrega la ruta para generar la linea para el estado de por surtir
            if not line.route_id.id in route_ids:
                route_ids.append(line.route_id.id)

        # Actualiza la ruta al estado devuelto
        self.write(cr, uid, ids, {'state': 'return'}, context=context)
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='return', context=context)
        
        # Registra en estado por surtir una linea pendiente para el log por cada ruta
        for route_id in route_ids:
            self.open_route_line(cr, uid, route_id, context=context)
        return True

    def action_prepare_delivery_stock(self, cr, uid, ids, context=None):
        """
            Abre la ventana que contiene los productos a entregar al cliente
        """
        print "******ABRIENDO LA VENTANA QUE CONTIENE LOS PRODUCTOS A ENTREGAR AL CLIENTE****"
        rline = self.browse(cr, uid, ids[0], context=context)
        move_obj = self.pool.get('stock.move')
        line_obj = self.pool.get('prepare.delivery.stock.route.line')
        if context is None:
            context={}
        lines = []
        loaded = True
        #print "********** preparar para crear ruta ********** "
        # Crea registro provisional para ejecucion de wizard
        res_id = self.pool.get('prepare.delivery.stock.route').create(cr, uid, {'route_line_id': rline.id, 'route_id': rline.route_id.id or False, 'picking_id': rline.picking_id.id or False, 'partner_id': rline.address_id.id or False}, context=context)
        #print "************* ruta creada *********** ", res_id

        # Obtiene los movimientos de los productos a entregar al cliente
        move_ids = move_obj.search(cr, uid, [('picking_id','=',rline.picking_id.id or False)], context=context)
        #print "***************** move_ids ********** ", move_ids
        # Genera la lista de movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Informacion de movimiento
            vals = {
                'name': move.name,
                'product_id': move.product_id.id or False,
                'product_qty': move.product_qty,
                'product_uom': move.product_uom.id or False,
                'location_id': move.location_id.id or False,
                'location_dest_id': move.location_dest_id.id or False,
                'state': move.state,
                'route_line_id': rline.id,
                'picking_id': rline.picking_id.id or False,
                'move_id': move.id,
                'wizard_id': res_id
            }
            line_id = line_obj.create(cr, uid, vals, context=context)
            #print "************ linea creada ************* ", line_id
            lines.append(line_id)
            if move.state not in ('cancel','done'):
                loaded = False
        
        # Pone el cargamento como finalizado si ya todo esta como entregado
        if loaded:
            self.write(cr, uid, ids, {'delivered': loaded}, context=context)
            # Pone el producto como entregado
            self.action_done(cr, uid, ids, context=context)
        #print "*************** cargar linea *********** "

        # Va a la parte de Entregar producto
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'delivery_routes', 'prepare_delivery_stock_route_form_view')
        return {
            'name': 'Entregar producto',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'prepare.delivery.stock.route',
            'target' : 'new',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'res_id': res_id
        }

    def action_delivered_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado En entrega en la salida del almacen
        """
        print"*****PONIENDO EL ESTADO EN ENTREGA EN LA SALIDA DEL ALMACEN****"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'delivered'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> En entrega</b>', context)
        return True
    
    def action_delivered(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado En entrega
        """
        print"****PASANDO LA ENTREGA A ESTADO EN ENTREGA****"
        # Agrega el registro del estado arribado
        for line in self.browse(cr,uid,ids,context=context):
            self.action_delivered_do_line(cr, uid, line, context=context)
        
        # Actualiza la ruta al estado en entrega
        self.write(cr, uid, ids, {'state': 'delivered'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='delivered', context=context)
        # Abre el wizard para entregar los productos de la ruta
        return self.action_prepare_delivery_stock(cr, uid, ids, context=context)
    
    def to_delivered_carrier(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado EN ENTREGA TRANSPORTISTA,
        """
        #print "******PASANDO A ESTADO POR SURTIR********"
        #picking_obj = self.pool.get('stock.picking')
        #for line in self.browse(cr,uid,ids,context=context):
        #    self.action_open_do_line(cr, uid, line, context=context)
        print"****PASANDO A ESTADO EN ENTREGA TRANSPORTISTA (TO_DELIVERED_CARRIER DRL)*******"
        self.write(cr, uid, ids, {'state': 'delivered_carrier'}, context=context)
        return True
    
    def action_done_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado Entregado en la salida del almacen
        """
        print"****COLOCANDO EL ESTADO ENTREGADO EN LA SALIDA DEL ALMACEN (ACTION_DONE_DO_LINE DRL)****"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'done', 'delivered':True}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Entregado</b>', context)
        return True
    
    def action_done_carrier(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado Entregado
        """
        print "****PASANDO LA ENTREGA A ESTADO ENTREGADO (ACTION_DONE_CARRIER DRL)****"
        route_ids = [] 
        # Agrega el registro del estado entregado
        for line in self.browse(cr,uid,ids,context=context):
            self.action_done_do_line(cr, uid, line, context=context)
            # Agrega la ruta para generar la linea para el estado de por surtir
            if not line.route_id.id in route_ids:
                route_ids.append(line.route_id.id)
        
        # Actualiza el estado de la entrega a entregado
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='done', context=context)
        
        # Registra en estado por surtir una linea pendiente para el log por cada ruta
        #for route_id in route_ids:
        #    self.open_route_line(cr, uid, route_id, context=context)
        return True

    
    def action_done(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado Entregado
        """
        print "****PASANDO LA ENTREGA A ESTADO ENTREGADO****"
        route_ids = [] 
        # Agrega el registro del estado entregado
        for line in self.browse(cr,uid,ids,context=context):
            self.action_done_do_line(cr, uid, line, context=context)
            # Agrega la ruta para generar la linea para el estado de por surtir
            if not line.route_id.id in route_ids:
                route_ids.append(line.route_id.id)
        print "*****ACTUALIZANDO LA ENTREGA AL ESTADO ENTREGADO (ACTION_DONE DRL)"
        # Actualiza la ruta al estado entregado
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='done', context=context)
        
        # Registra en estado por surtir una linea pendiente para el log por cada ruta
        for route_id in route_ids:
            self.open_route_line(cr, uid, route_id, context=context)
        return True

    def action_not_found_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado No encontrado en la salida del almacen
        """
        print "*****COLOCANDO EL ESTADO NO ENCONTRADO EN LA SALIDA DEL ALMACEN****"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'not_found'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> No encontrado</b>', context)
        return True
    
    def action_not_found(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado No encontrado
        """
        print"****PASANDO LA ENTREGA A ESTADO NO ENCONTRADO*****"
        route_ids = [] 
        # Agrega el registro del estado no encontrado
        for line in self.browse(cr,uid,ids,context=context):
            self.action_not_found_do_line(cr, uid, line, context=context)
            # Agrega la ruta para generar la linea para el estado de por surtir
            if not line.route_id.id in route_ids:
                route_ids.append(line.route_id.id)

        # Actualiza la ruta al estado entregado
        self.write(cr, uid, ids, {'state': 'not_found'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='not_found', context=context)
        
        # Registra en estado por surtir una linea pendiente para el log por cada ruta
        for route_id in route_ids:
            self.open_route_line(cr, uid, route_id, context=context)
        return True
    
    def action_arrived_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado arrivado en la salida del almacen
        """
        print"******PONIENDO EL ESTADO ARRIVADO EN LA SALIDA DEL ALMACEN"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'arrived'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Arribado</b>', context)
        return True
    
    def action_arrived(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado arrivado
        """
        print "PASANDO LA ENTREGA A ESTADO ARRIVADO****"
        route_obj = self.pool.get('delivery.route')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Agrega el registro del estado arribado
        for line in self.browse(cr,uid,ids,context=context):
            # Valida que no haya otra entrega pendiente sobre la ruta
            line_ids = self.search(cr, uid, [('route_id','=', line.route_id.id or False),('state','in',['arrived','delivered'])])
            if line_ids:
                raise osv.except_osv(_('Error'), _('La ruta %s tiene entregas en proceso de entrega, complete los registros antes de continuar'%(line.route_id.name)))
            # Cambia la entrega a arribado
            self.action_arrived_do_line(cr, uid, line, context=context)
        
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'arrived', 'visit_date': date}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='arrived', context=context)
        return True
    
    def action_reopen_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado Por surtir en la salida del almacen
        """
        print"*****PONIENDO EL ESTADO POR SURTIR EN LA SALIDA DE ALMACEN****"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'open'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Por surtir</b>', context)
        return True
    
    def action_reopen(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado Por surtir
        """
        print "****PASANDO LA ENTREGA A ESTADO POR SURTIR"
        route_obj = self.pool.get('delivery.route')
        print "***ACTUALIZANDO EL ESTADO DE LA RUTA A EMBARQUE***"
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'open'}, context=context)
        
        # Agrega el registro del estado arribado
        for line in self.browse(cr,uid,ids,context=context):
            # Valida que no haya otra entrega pendiente sobre la ruta
            line_ids = self.search(cr, uid, [('route_id','=', line.route_id.id or False),('state','in',['arrived','delivered'])])
            if line_ids:
                raise osv.except_osv(_('Error'), _('La ruta %s tiene entregas en proceso de entrega, complete los registros antes de continuar'%(line.route_id.name)))
            # Valida que la ruta no este en estado retorno
            if line.route_id.state == 'return':
                # Pasa la ruta a estado en transito
                route_obj.action_reshipping(cr, uid, [line.route_id.id], context=context)
                # Genera un log de por surtir
                self.open_route_line(cr, uid, line.route_id.id, context=context)
            # Valida que la ruta no este en estado diferente al de entrega
            elif line.route_id.state != 'shipping':
                raise osv.except_osv(_('Error'), _('La ruta %s no se encuentra en proceso de entrega.'%(line.route_id.name)))
            # Cambia la entrega a arribado
            self.action_reopen_do_line(cr, uid, line, context=context)
        
        # Registra el log sobre la actualizacion sobre la transicion de estado
        #self.pnool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='open', context=context)
        return True
    
    def action_cancel_move_stock(self, cr, uid, picking_id, context=None):
        """
            Cambia los movimientos entregados a estado pendiente de entrega
        """
        print "****CAMBIANDO LOS MOVIMIENTOS ENTREGADOS A ESTADO PENDIENTE DE ENTREGA***"
        move_obj = self.pool.get('stock.move')
        line_obj = self.pool.get('prepare.delivery.stock.route.line')
        if context is None:
            context={}
        line_ids = []
        # Obtiene los movimientos de los productos a entregar al cliente
        move_ids = move_obj.search(cr, uid, [('picking_id','=',picking_id)], context=context)
        # Recorre los movimientos
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            # Obtiene los movimientos cancelados o terminados
            if move.state not in ('cancel','done'):
                line_ids.append(move.id)
        if line_ids:
            # Cambia el movimiento a pendiente de entrega
            move_obj.cancel_assign(cr, uid, line_ids, context=context)
        return True
    
    def action_cancel_do_line(self, cr, uid, line, context=None):
        """
            Pone el estado cancelado en la salida del almacen
        """
        print "*****COLOCANDO EL ESTADO CANCELADO EN SALIDA DEL ALMANCEN******"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'cancel'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Cancelado</b>', context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado cancelado
        """
        print "*****PASANDO LA ENTREGA A ESTADO CANCELADO****"
        route_obj = self.pool.get('delivery.route')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        route_ids = [] 
        
        # Agrega el registro del estado arribado
        for line in self.browse(cr,uid,ids,context=context):
            # Cambia los movimientos que ya se entregaron a pendientes de nuevo
            self.action_cancel_move_stock(cr, uid, line.picking_id.id or False, context=context)
            # Cambia la entrega a arribado
            self.action_cancel_do_line(cr, uid, line, context=context)
        
            # Agrega la ruta para generar la linea para el estado de por surtir
            if not line.route_id.id in route_ids:
                route_ids.append(line.route_id.id)
        print "***ACTUALIZANDO EL ESTADO DE LA RUTA A CANCELADO***"
        # Actualiza la ruta al estado de Embarque
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        # Registra el log sobre la actualizacion sobre la transicion de estado
        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='cancel', context=context)
        
        # Registra en estado por surtir una linea pendiente para el log por cada ruta
        for route_id in route_ids:
            self.open_route_line(cr, uid, route_id, context=context)
        return True
    
    def action_open_do_line(self, cr, uid, line, context=None):
        """
            Confirma la ruta sobre la salida de almacen
        """
        print"*******CONFIRMANDO RUTA SOBRE SALIDA DE ALMACEN*******"
        self.pool.get('stock.picking').write(cr,uid,[line.picking_id.id],{'delivery_state':'open'}, context=context)
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta En Transito <b> Por Surtir</b>', context)
        return True
    
    def action_open(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado por surtir,
        """
        print "******PASANDO A ESTADO POR SURTIR********"
        picking_obj = self.pool.get('stock.picking')
        for line in self.browse(cr,uid,ids,context=context):
            self.action_open_do_line(cr, uid, line, context=context)
        print"****PASANDO A ESTADO ABIERTO*******"
        self.write(cr, uid, ids, {'state': 'open'}, context=context)
        return True
    
    def action_confirm_do_line(self, cr, uid, line, context=None):
        """
            Confirma la ruta sobre la salida de almacen
        """
        print "********CONFIRMANDO RUTA SOBRE SALIDA DE ALMACEN**********"
        self.pool.get('stock.picking').write(cr, uid, line.picking_id.id,{'delivery_state':'planned', 'route_line_id': line.id},context=context)
        print "******PASANDO EL ESTADO DE LA ENTREGA A PLANEADO*******"
        self.notify_related_order(cr, uid, line, 'Proceso entrega Ruta <b> Planeado</b>', context)
        return True
        
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Confirma las lineas de entrega para cargarlas sobre la ruta
        """
        "******CONFIRMANDO RUTA**********"
        
        picking_obj = self.pool.get('stock.picking')
        
        # Recorre las lineas a confirmar
        for line in self.browse(cr, uid, ids, context=context):
            # Valida que la salida de almacen este facturada
            if not line.picking_id.invoice_id:
                raise osv.except_osv(_('Error'), _('La entrega %s (origen:%s) no se encuentra facturada'%(line.picking_id.name,line.picking_id.origin)))
            if not line.picking_id.invoice_id.state in ['open','paid','repaid']:
                raise osv.except_osv(_('Error'), _('La entrega %s (origen:%s) no se encuentra facturada'%(line.picking_id.name,line.picking_id.origin)))
            # Valida que la salida de almacen no este como entregada
            if line.picking_id.delivered:
                raise osv.except_osv(_('Error'), _('La entrega %s (origen:%s) ya fue entregada en otra ruta'%(line.picking_id.name,line.picking_id.origin)))
            # Valida que la salida de almacen no se encuentre en proceso de entrega
            if line.picking_id.route_line_id:
                raise osv.except_osv(_('Error'), _('La entrega %s (origen:%s) ya se encuentra sobre una ruta de entrega'%(line.picking_id.name,line.picking_id.origin)))
            print "******CONFIRMANDO LA RUTA SOBRE LA SALIDA DE ALMACEN********"
            # Confirma la ruta sobre la salida de almacen
            self.action_confirm_do_line(cr, uid, line, context=context)
        print "*********LINE*************: ", line
        # Pone la linea de la ruta en el estado planeado
        self.write(cr, uid, ids, {'state':'planned'}, context=context)
        return True
    
    def notify_related_order(self, cr, uid, line, delivery_state, context=None):
        """
            Notificacion del estatus de la ruta sobre el pedido de venta
        """
        print "*****NOTIFICACION DE ESTATUS DE LA RUTA SOBRE EL PEDIDO"
        res_id = False
        model  = False
        # Identifica si la nota se genera sobre una venta o una compra
        if line.sale_order_id:
            res_id = line.sale_order_id.id
            model  = 'sale.order'
        elif line.purchase_id:
            res_id = line.purchase_id.id
            model  = 'purchase.order'
        
        if res_id and model:
            drivers = ''
            body = str(delivery_state)
            if line.visit_date:
                body += " at " + str(line.visit_date)
            body += "<br />"
            if line.route_id.name:
                body += "<b>Route</b>: " + str(line.route_id.name) + "<br />"
            if line.route_id.driver_id:
                drivers += str(line.route_id.driver_id.name.encode('utf-8'))
                if line.route_id.driver_id.employee_id and line.route_id.driver_id.employee_id.mobile_phone:
                    drivers += " (" + str(line.route_id.driver_id.employee_id.mobile_phone) + ")"
            elif line.route_id.carrier_id:
                drivers += str(line.route_id.carrier_id.name.encode('utf-8'))
            if drivers:
                body += "by: " + drivers + ")"
            
            self.pool.get('mail.message').create(cr, uid, {
                'type': 'notification',
                'record_name': 'Delivery Route Line',
                'body': body,
                'res_id': res_id,
                'model': model,
            })
        return True
    
    _group_by_full = {
        'route_id': _read_group_route_ids,
    }
    
delivery_route_line()

# ---------------------------------------------------------
# Registro de bitacora de entregas (Rutas)
# ---------------------------------------------------------

class delivery_route_log(osv.osv):
    _name = 'delivery.route.log'
    
    def add_log_route(self, cr, uid, route_ids, state='draft', context=None):
        """
            Registra sobre el log de la ruta 
        """
        route_obj = self.pool.get('delivery.route')
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time = 0.00
        # Obtiene el ultimo registro del log
        log_ids = self.search(cr, uid, [('route_id','in',route_ids),('close','=',False)])
        # Actualiza la fecha final sobre el log
        for log in self.browse(cr, uid, log_ids, context=context):
            date_start = datetime.strptime(log.date_start, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
            date_end = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
            #print "**************** date_start ******** ", type(date_start), " ** ", date_start
            #print "**************** date_end ******** ", type(date_end), " ** ", date_end
            
            date_diff = date_end - date_start
            #print "**************** diferencia segundos ******** ", date_diff.seconds
            time = (float(date_diff.seconds) / 60.0) / 60.0
            date_end = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
            #print "*******************  horas ************** ", time
            # Actualiza el log
            self.write(cr, uid, [log.id], {'date_end': date_end, 'time': time, 'close': True}, context=context)
        # Inicializa fecha de inicio para nuevos log
        date_start = date_now
        # Recorre los ids de las rutas
        for route_id in route_ids:
            # Agrega el nuevo log sobre la ruta
            name = 'Transicion ruta '
            route_name = route_obj.read(cr, uid, [route_id], ['name'])[0]['name']
            #print "***************** route name ********** ", route_name, "  ", name, " - ", route_id, ' ++ ', state
            if route_name:
                name = "%s - %s"%(name,route_name)
            # Crea el nuevo registro
            log_id = self.create(cr, uid, {
                'name': name,
                'route_id': route_id,
                'user_id': uid,
                'state': state,
                'date_start': date_start,
                'group_date': date_start[:10],
            }, context=context)
        return True
    
    _order = 'date_start DESC'
    _columns = {
        'name': fields.char('Referencia', size=128, select=True),
        'route_id': fields.many2one('delivery.route', 'Ruta', required=True),
        'user_id': fields.many2one('res.users','Responsable', required=True),
        'state': fields.selection([
                            ('draft','Borrador'),
                            ('confirm','Confirmado'),
                            ('load','Embarque'),
                            ('shipping_carrier', 'En transito transportista'),
                            ('shipping', 'En transito'),
                            ('return', 'Retorno Ruta'),
                            ('unload', 'Desembarque'),
                            ('entry', 'Ingreso vehiculo'),
                            ('done', 'Terminado'),
                            ('cancel','Cancelado')],'Estado',readonly=True),
        'date_start': fields.datetime('Fecha inicio'),
        'date_end': fields.datetime('Fecha fin'),
        'group_date': fields.date('Fecha'),
        'time': fields.float('Duracion', readonly=True),
        'close': fields.boolean('Cerrado')
    }
    
delivery_route_log()

class delivery_route_line_log(osv.osv):
    _name = 'delivery.route.line.log'
    
    def add_log_route_line(self, cr, uid, line_ids, state='draft', context=None):
        """
            Registra sobre el log de la entrega de la ruta 
        """
        print"*****REGISTRANDO SOBRE EL LOG DE LA ENTREGA DE LA RUTA (ACTION_LOG_ROUTE_LINE DRLL)"
        line_obj = self.pool.get('delivery.route.line')
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time = 0.00
        
        # Obtiene el ultimo registro del log con linea definida
        log_ids = self.search(cr, uid, [('route_line_id','in',line_ids),('close','=',False)])
        # Actualiza la fecha final sobre el log
        for log in self.browse(cr, uid, log_ids, context=context):
            date_start = datetime.strptime(log.date_start, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
            date_end = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
            # Obtiene la diferencia de la fecha inicial y fecha final
            date_diff = date_end - date_start
            time = (float(date_diff.seconds) / 60.0) / 60.0
            date_end = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
            # Actualiza el log
            self.write(cr, uid, [log.id], {'date_end': date_end, 'time': time, 'close': True}, context=context)
        
        # Obtiene la ruta de la primera linea
        route_id = line_obj.browse(cr, uid, line_ids[0], context=context).route_id.id
        # Obtiene el ultimo registro del log sobre la ruta con linea no definida
        log_route_ids = self.search(cr, uid, [('route_id','=',route_id),('route_line_id','=',False),('close','=',False)])
        
        # Si no encuentra la linea actualiza el log sobre la ruta
        if log_ids:
            # Elimina el registro de log por surtir
            self.unlink(cr, uid, log_route_ids, context=context)
        else:
            # Actualiza la fecha final sobre el log
            for log in self.browse(cr, uid, log_route_ids, context=context):
                date_start = datetime.strptime(log.date_start, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
                date_end = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S').replace(tzinfo = pytz.utc)
                # Actualiza nombre de transicion con la informacion del nombre de la entrega de la ruta
                name = 'Transicion entrega '
                line_name = line_obj.read(cr, uid, [line_ids[0]], ['name'])[0]['name']
                if line_name:
                    name = "%s - %s"%(name,line_name)
                
                # Obtiene la diferencia de la fecha inicial y fecha final
                date_diff = date_end - date_start
                time = (float(date_diff.seconds) / 60.0) / 60.0
                date_end = datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')
                # Actualiza el log y agrega el identificador de la linea
                self.write(cr, uid, [log.id], {'date_end': date_end, 'time': time, 'close': True, 'route_line_id': line_ids[0], 'name': name}, context=context)
            
        # Inicializa fecha de inicio para nuevos log
        date_start = date_now
        # Recorre los ids de las rutas
        for line_id in line_ids:
            # Agrega el nuevo log sobre la ruta
            name = 'Transicion entrega '
            line_name = line_obj.read(cr, uid, [line_id], ['name'])[0]['name']
            #print "***************** route name ********** ", line_name, "  ", name, " - ", line_id, ' ++ ', state
            if line_name:
                name = "%s - %s"%(name,line_name)
            # Crea el nuevo registro
            log_id = self.create(cr, uid, {
                'name': name,
                'route_line_id': line_id,
                'user_id': uid,
                'state': state,
                'date_start': date_start,
                'group_date': date_start[:10],
            }, context=context)
        return True
    
    def add_log_route(self, cr, uid, route_id, state='open', context=None):
        """
            Registra sobre el log de la entrega de la ruta (Sin identificar la linea de entrega)
        """
        print"REGISTRANDO SOBRE LOG DE ENTREGA DE LA RUTA (ADD_LOG_ROUTE DRLL)"
        route_obj = self.pool.get('delivery.route')
        line_obj = self.pool.get('delivery.route.line')
        date_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time = 0.00
        # Valida que no haya un registro pendiente sobre la ruta
        log_ids = self.search(cr, uid, [('route_line_id','=',False),('close','=',False),('route_id','=',route_id)])
        if log_ids:
            raise osv.except_osv(_('Error'), _("No se puede registrar mas de una linea pendiente de registrar para la misma ruta.")) 
        
        # Revisa que haya entregas pendientes sobre la ruta
        line_ids = line_obj.search(cr, uid, [('state','in',['open']),('route_id','=',route_id)])
        if not line_ids:
            # Pone la ruta en estado de Regreso
            route_obj.action_return(cr, uid, [route_id], context=context)
            return True

        # Agrega el nuevo log sobre la ruta
        name = 'Transicion entrega '
        # Crea el nuevo registro
        log_id = self.create(cr, uid, {
            'name': name,
            'route_id': route_id,
            'user_id': uid,
            'state': state,
            'date_start': date_start,
            'group_date': date_start[:10],
        }, context=context)
        return True
    
    _order = 'date_start DESC'
    _columns = {
        'name': fields.char('Referencia', size=64, select=True),
        'route_line_id': fields.many2one('delivery.route.line','Linea Ruta'),
        'partner_id': fields.related('route_line_id', 'address_id', type='many2one', relation='res.partner',
                string="Cliente", store=True),
        'zone_id': fields.related('route_line_id', 'zone_id', type='many2one', relation='delivery.zone',
                string="Zona", store=True),
        'route_id': fields.related('route_line_id', 'route_id', type="many2one", relation="delivery.route", store={
                'delivery.route.line.log': (lambda self, cr, uid, ids, c={}: ids, ['route_line_id'], 20),
            }, string="Ruta", readonly=True),
        'picking_id': fields.related('route_line_id', 'picking_id', type="many2one", relation="stock.picking", store=True, string="Entrega", readonly=True),
        #'route_id': fields.many2one('delivery.route','Ruta', required=True),
        #'picking_id': fields.many2one('stock.picking','Registro de Almacen', required=True),
        'user_id': fields.many2one('res.users','Responsable', required=True),
        'state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('delivered_carrier', 'En entrega transportista'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')],'Estado',readonly=True),
        'date_start': fields.datetime('Fecha inicio'),
        'date_end': fields.datetime('Fecha fin'),
        'group_date': fields.date('Fecha'),
        'time': fields.float('Duracion', readonly=True),
        'close': fields.boolean('Cerrado')
    }
    
delivery_route_line_log()

# Horario de entrega del cliente
class delivery_schedule(osv.Model):
    _name = 'delivery.schedule'
    
    _columns = {
        'name': fields.char('Nombre', size=30, required=True),
        'line_ids': fields.one2many('delivery.schedule.line', 'schedule_id', 'Linea del horario'),
        'note': fields.text('Nota'),
    }
    
delivery_schedule()

class delivery_schedule_line(osv.Model):
    _name = 'delivery.schedule.line'
    
    _columns = {
        'name': fields.char('Nombre', size=30),
        'day_week': fields.selection([
            ('0', 'Lunes'),
            ('1', 'Martes'),
            ('2', 'Miercoles'),
            ('3', 'Jueves'),
            ('4', 'Viernes'),
            ('5', 'Sabado'),
            ('6', 'Domingo')], 'Dia de la semana'),
        'start_hour': fields.float('Hora de apertura'),
        'close_hour': fields.float('Hora de cierre'),
        'date': fields.date('Fecha'),
        'schedule_id': fields.many2one('delivery.schedule', 'Horario')
    }

delivery_schedule_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
