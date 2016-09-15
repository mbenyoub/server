# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
from tools.translate import _
import time
from datetime import datetime
from datetime import timedelta
import openerp.addons.decimal_precision as dp

class stock_move(osv.osv):
    _name = "stock.move"
    _inherit = "stock.move"
    
    def _product_available(self, cr, uid, ids, name, arg, context=None):
        """
            Retorna el producto disponible sobre la tienda
        """
        product_obj = self.pool.get('product.product')
        res = {}
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
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
    
    def _route_line_to_update_after_picking_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Ejecuta actualizacion para actualizar la linea de la ruta sobre el movimiento en caso de que haya una modificacion
        """
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.move').search(cr, uid, [('picking_id','in',ids)]) or []
    
    _columns = {
        'virtual_available': fields.function(_product_available, type='float', string='Disponible'),
        'zone_id': fields.related('picking_id', 'zone_id', type='many2one', relation='delivery.zone', store=True, string="Zona", readonly=True),
        'route_line_id': fields.related('picking_id', 'route_line_id', type='many2one', relation='delivery.route.line', store={
            'stock.move': (lambda self,cr,uid,ids,context: ids,['picking_id'],10), 
            'stock.picking': (_route_line_to_update_after_picking_change, ['route_line_id'], 10),
        }, string="Linea Ruta", readonly=True),
        'route_id': fields.many2one('delivery.route', 'Ruta entrega', readonly=True),
        'location_prev_id': fields.many2one('stock.location', 'Ubicacion origen anterior', readonly=True)
    }
    
stock_move()

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _name = "stock.picking"
    
    def action_pop_order(self, cr, uid, ids, context=None):
        mo_ids = False
        context = context or {}
        
        id = ids or context.get('active_ids', False) or False
        if id:        
            for picking in self.browse(cr, uid, [id[0]], context=context):
                if picking.sale_id:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _("Related Sale Order"),
                        'view_mode': 'form,tree',
                        'view_id': False,
                        'view_type': 'form',
                        'res_model': 'sale.order',
                        'res_id': picking.sale_id.id,
                        'context': context
                    }
                elif picking.purchase_id:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _("Related Purchase Order"),
                        'view_mode': 'form,tree',
                        'view_id': False,
                        'view_type': 'form',
                        'res_model': 'purchase.order',
                        'res_id': picking.purchase_id.id,
                        'context': context
                    }
        return {}
    
    def _pick_to_update_after_po_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.picking').search(cr, uid, [('purchase_id', 'in', ids)]) or []
    
    def _cal_weight(self, cr, uid, ids, fields_name, args, context=None):
        """
            Obtiene el peso total sobre la entrega y la cantidad total de productos a entregar
        """
        #print "****************** stock.pick fields ************ ", fields_name
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            total_weight = total_weight_net = quantity = 0.00
            # Recorre las lineas del albaran
            for move in picking.move_lines:
                # Suma el peso total por linea y la cantidad de bultos
                total_weight += move.weight
                total_weight_net += move.weight_net
                quantity += move.product_qty
            # Retorna total obtenido
            res[picking.id] = {
                                'weight': total_weight,
                                'weight_net': total_weight_net,
                                'number_of_packages': quantity
                              }
            #print "************** res picking ", picking.id, " **************** ", res[picking.id]
        return res
    
    def _get_picking_line(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a las lineas de entrega
        """
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    def _get_picking_invoice(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a la factura
        """
        result = {}
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.picking').search(cr, uid, [('invoice_id','in',ids)]) or []
    
    _columns = {
        'delivery_date': fields.datetime('Fecha de entrega'),
        'route_line_id': fields.many2one('delivery.route.line', 'Linea de Entrega', readonly=True),
        'route_id': fields.related('route_line_id', 'route_id', type='many2one', relation='delivery.route', method=True, string='Ruta Entrega', readonly=True, store=True),
        'route_state' : fields.related('route_id', 'state', type='selection', selection=[
                            ('draft','Borrador'),
                            ('confirm','Confirmado'),
                            ('load','Embarque'),
                            ('shipping', 'En transito'),
                            ('return', 'Retorno Ruta'),
                            ('unload', 'Desembarque'),
                            ('entry', 'Ingreso'),
                            ('done', 'Terminado'),
                            ('cancel','Cancelado')], method=True, string='Estatus Entrega', readonly=True, store=True),
        'delivered': fields.boolean('Entregado en ruta', select=True),
        'street': fields.related('partner_id', 'street', type='char', size=128, string='Street'),
        'delivery_state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')], 'Estado Entrega'),
        
        # Zonas de entrega
        'zone_id': fields.many2one('delivery.zone','Zona'),
        'delivery_term_id': fields.many2one('delivery.term','Plazo de entrega', required=True),
        # Informacion de total de bultos y peso por la salida del almacen
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                store={
               'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
               'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
        }),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        'number_of_packages': fields.function(_cal_weight, type='float', string='Numero de bultos', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        # Relacion de factura con salida de almacen
        'invoice_id': fields.many2one('account.invoice','Factura', selected=True),
        'inv_state': fields.related('invoice_id','state', type='selection', string='Estado Factura', selection=[
            ('draft','Borrador'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Abierto'),
            ('paid','Pagado'),
            ('cancel','Cancelado'),
            ('repaid','Saldado'),], store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['invoice_id'], 20),
                 'account.invoice': (_get_picking_invoice, ['state'], 20),
            }),
    }
    
    def _get_delivery_term_default(self, cr, uid, context=None):
        """
            Obtiene el termino de entrega de 48 horas por default
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'delivery_routes', 'delivery_term_01').id
        except:
            pass
        return res
    
    _defaults = {
        'delivered': False,
        'delivery_state': "draft",
        'delivery_term_id': _get_delivery_term_default
    }

#    def write(self, cr, uid, ids, vals, context=None):
#        if 'delivered' in vals.keys():
#            for o in self.browse(cr, uid, ids, context=context):
#                if o.route_line_id:
#                    raise osv.except_osv(_('Invalid action !'), _('Cannot update a Picking(s) which are already delivery routed (%s) !'%o.route_id.name))
#        return  super(stock_picking, self).write(cr, uid, ids, vals, context=context)

    
    def unlink(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids, context=context):
            if o.route_line_id:
                self.pool.get('delivery.route.line').unlink(cr, uid, [o.route_line_id.id], context=context)
        return super(stock_picking, self).unlink(cr, uid, ids, context=context)
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        context = context or {}
        new_args = []
        if 'update_pts' in context and len(args) > 1:
            for arg in args:
                if arg[0] != 'id':
                    new_args.append(arg)
        else:
            new_args = args
        return super(stock_picking, self).search(cr, uid, new_args, offset=offset, limit=limit, order=order, context=context, count=count)
        
    
#    def _read_group_dts_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
#        context = context or {}
#        domain  = domain or []
#        delivery_ids  = []
#        delivery_ids2 = []
#        has_dts_set   = False
#        delivery_obj = self.pool.get('delivery.time')
#        if domain:
#            for arg in domain:
#                if arg[0] == 'dts_id.start_date':
#                    min_date = datetime.now().strftime('%Y-%m-%d') + ' 00:00:00'
#                    #max_date = datetime.now() + timedelta(days=1)
#                    max_date = datetime.now().strftime('%Y-%m-%d') + ' 23:59:59'        
#                    cr.execute("SELECT id FROM delivery_time WHERE type='dts' AND active=True AND start_date>='" + min_date + "' AND start_date<='" + max_date + "'")
#                    delivery_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                elif arg[0] == 'dts_id':
#                    has_dts_set = [(arg[0],arg[1],arg[2])]
#        fold = {}
#        
#        if has_dts_set:
#            delivery_ids2 = delivery_obj.search(cr, uid, has_dts_set)
#            if delivery_ids2:
#                for id in delivery_ids:
#                    if id not in delivery_ids2:
#                        fold[id] = True
#                delivery_ids.extend(delivery_ids2)
#        result = delivery_obj.name_get(cr, uid, delivery_ids, context=context)
#        return result, fold
#    
#    
#    _group_by_full = {
#        'dts_id': _read_group_dts_ids,
#    }

stock_picking()

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _name = "stock.picking.out"
    
    def _cal_weight(self, cr, uid, ids, fields_name, args, context=None):
        """
            Obtiene el peso total sobre la entrega y la cantidad total de productos a entregar
        """
        #print "****************** fields ************ ", fields_name
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            total_weight = total_weight_net = quantity = 0.00
            # Recorre las lineas del albaran
            for move in picking.move_lines:
                # Suma el peso total por linea y la cantidad de bultos
                total_weight += move.weight
                total_weight_net += move.weight_net
                quantity += move.product_qty
            # Retorna total obtenido
            res[picking.id] = {
                                'weight': total_weight,
                                'weight_net': total_weight_net,
                                'number_of_packages': quantity
                              }
            #print "************ res picking ************** ", res[picking.id]
        return res

    def _get_picking_line(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a las lineas de entrega
        """
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    def _get_picking_invoice(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a la factura
        """
        result = {}
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.picking').search(cr, uid, [('invoice_id','in',ids)]) or []
    
    _columns = {
        'delivery_date': fields.datetime('Fecha de entrega'),
        'route_line_id': fields.many2one('delivery.route.line', 'Linea de Entrega', method=True, readonly=True),
        'route_id': fields.related('route_line_id', 'route_id', type='many2one', relation='delivery.route', method=True, string='Ruta Entrega', readonly=True, store=True),
        'route_state' : fields.related('route_id', 'state', type='selection', selection=[
                            ('draft','Borrador'),
                            ('confirm','Confirmado'),
                            ('load','Embarque'),
                            ('shipping', 'En transito'),
                            ('return', 'Retorno Ruta'),
                            ('unload', 'Desembarque'),
                            ('entry', 'Ingreso Ruta'),
                            ('done', 'Terminado'),
                            ('cancel','Cancelado')], method=True, string='Estatus Entrega', readonly=True, store=True),
        'delivered': fields.boolean('Entregado en ruta', select=True),
        'street': fields.related('partner_id', 'street', type='char', size=128, string='Street'),
        'delivery_state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')], 'Estado Entrega'),
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
        # Zonas de entrega
        'zone_id': fields.many2one('delivery.zone','Zona'),
        'delivery_term_id': fields.many2one('delivery.term','Plazo de entrega', required=True),
        # Informacion de total de bultos y peso por la salida del almacen
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                store={
               'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
               'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
        }),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        'number_of_packages': fields.function(_cal_weight, type='float', string='Numero de bultos', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        # Relacion de factura con salida de almacen
        'invoice_id': fields.many2one('account.invoice','Factura', selected=True),
        'inv_state': fields.related('invoice_id','state', type='selection', string='Estado Factura', selection=[
            ('draft','Borrador'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Abierto'),
            ('paid','Pagado'),
            ('cancel','Cancelado'),
            ('repaid','Saldado'),], store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['invoice_id'], 20),
                 'account.invoice': (_get_picking_invoice, ['state'], 20),
            }),
    }
    
    def _get_delivery_term_default(self, cr, uid, context=None):
        """
            Obtiene el termino de entrega de 48 horas por default
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'delivery_routes', 'delivery_term_01').id
        except:
            pass
        return res
    
    _defaults = {
        'delivered': False,
        'delivery_state': "draft",
        'delivery_term_id': _get_delivery_term_default
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        context = context or {}
        new_args = []
        if 'update_pts' in context and len(args) > 1:
            for arg in args:
                if arg[0] != 'id':
                    new_args.append(arg)
        else:
            new_args = args
        return super(stock_picking_out, self).search(cr, uid, new_args, offset=offset, limit=limit, order=order, context=context, count=count)

stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _name = "stock.picking.in"
    
    def _pick_to_update_after_po_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.picking.in').search(cr, uid, [('purchase_id', 'in', ids),('type','=','in')]) or []
    
    def _cal_weight(self, cr, uid, ids, fields_name, args, context=None):
        """
            Obtiene el peso total sobre la entrega y la cantidad total de productos a entregar
        """
        #print "****************** fields ************ ", fields_name
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            total_weight = total_weight_net = quantity = 0.00
            # Recorre las lineas del albaran
            for move in picking.move_lines:
                # Suma el peso total por linea y la cantidad de bultos
                total_weight += move.weight
                total_weight_net += move.weight_net
                quantity += move.product_qty
            # Retorna total obtenido
            res[picking.id] = {
                                'weight': total_weight,
                                'weight_net': total_weight_net,
                                'number_of_packages': quantity
                              }
            #print "************ res picking ************** ", res[picking.id]
        return res
        
    def _get_picking_line(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a las lineas de entrega
        """
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    def _get_picking_invoice(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los almacenes relacionados a la factura
        """
        result = {}
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.picking').search(cr, uid, [('invoice_id','in',ids)]) or []
    
    _columns = {
        'delivery_date': fields.datetime('Fecha de entrega'),
        'route_line_id': fields.many2one('delivery.route.line', 'Linea de Entrega', method=True, readonly=True),
        'route_id': fields.related('route_line_id', 'route_id', type='many2one', relation='delivery.route', method=True, string='Ruta Entrega', readonly=True, store=True),
        'route_state' : fields.related('route_id', 'state', type='selection', selection=[
                            ('draft','Borrador'),
                            ('confirm','Confirmado'),
                            ('load','Embarque'),
                            ('shipping', 'En transito'),
                            ('return', 'Retorno Ruta'),
                            ('unload', 'Desembarque'),
                            ('entry', 'Ingreso Ruta'),
                            ('done', 'Terminado'),
                            ('cancel','Cancelado')], method=True, string='Estatus Entrega', readonly=True, store=True),
        'delivered': fields.boolean('Entregado en ruta', select=True),
        'street': fields.related('partner_id', 'street', type='char', size=128, string='Street'),
        'delivery_state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')], 'Estado Entrega'),
        
        'zone_id': fields.many2one('delivery.zone','Zona'),
        'delivery_term_id': fields.many2one('delivery.term','Plazo de entrega', required=True),
        
        # Informacion de total de bultos y peso por la salida del almacen
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                store={
               'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
               'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
        }),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        'number_of_packages': fields.function(_cal_weight, type='float', string='Numero de bultos', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight',
                  store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 }),
        # Relacion de factura con salida de almacen
        'invoice_id': fields.many2one('account.invoice','Factura', selected=True),
        'inv_state': fields.related('invoice_id','state', type='selection', string='Estado Factura', selection=[
            ('draft','Borrador'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Abierto'),
            ('paid','Pagado'),
            ('cancel','Cancelado'),
            ('repaid','Saldado'),], store={
                 'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['invoice_id'], 20),
                 'account.invoice': (_get_picking_invoice, ['state'], 20),
            }),
    }
    
    def _get_delivery_term_default(self, cr, uid, context=None):
        """
            Obtiene el termino de entrega de 48 horas por default
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'delivery_routes', 'delivery_term_01').id
        except:
            pass
        return res
    
    _defaults = {
        'delivered': False,
        'delivery_state': "draft",
        'delivery_term_id': _get_delivery_term_default
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        context = context or {}
        new_args = []
        if 'update_pts' in context and len(args) > 1:
            for arg in args:
                if arg[0] != 'id':
                    new_args.append(arg)
        else:
            new_args = args
        return super(stock_picking_in, self).search(cr, uid, new_args, offset=offset, limit=limit, order=order, context=context, count=count)
    
#    def _read_group_dts_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
#        context = context or {}
#        domain  = domain or []
#        delivery_ids  = []
#        delivery_ids2 = []
#        has_dts_set   = False
#        delivery_obj = self.pool.get('delivery.time')
#        if domain:
#            for arg in domain:
#                if arg[0] == 'dts_id.start_date':
#                    min_date = datetime.now().strftime('%Y-%m-%d') + ' 00:00:00'
#                    #max_date = datetime.now() + timedelta(days=1)
#                    max_date = datetime.now().strftime('%Y-%m-%d') + ' 23:59:59'        
#                    cr.execute("SELECT id FROM delivery_time WHERE type='dts' AND active=True AND start_date>='" + min_date + "' AND start_date<='" + max_date + "'")
#                    delivery_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                elif arg[0] == 'dts_id':
#                    has_dts_set = [(arg[0],arg[1],arg[2])]
#        fold = {}
#        
#        if has_dts_set:
#            delivery_ids2 = delivery_obj.search(cr, uid, has_dts_set)
#            if delivery_ids2:
#                for id in delivery_ids:
#                    if id not in delivery_ids2:
#                        fold[id] = True
#                delivery_ids.extend(delivery_ids2)
#        result = delivery_obj.name_get(cr, uid, delivery_ids, context=context)
#        return result, fold
#    
#    _group_by_full = {
#        'dts_id': _read_group_dts_ids,
#    }

stock_picking_in()
