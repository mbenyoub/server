# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Author: Yannick Gouin <yannick.gouin@elico-corp.com>
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
import pytz
from openerp import netsvc, tools
from openerp.tools.translate import _
import time

class picking_batch(osv.osv):
    _name = "picking.batch"
    _columns = {
        'name': fields.char('Name', size=32, translate=True),
        'picking_ids': fields.one2many('stock.picking', 'batch_id', 'Contains'),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': True,
    }

picking_batch()

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"
    
    def ics_datetime(self, idate):
        """
            Obtiene el formato de fecha con la zona horaria que aplica
        """
        if idate:
            #returns the datetime as UTC, because it is stored as it in the database
            return datetime.strptime(idate, tools.DEFAULT_SERVER_DATETIME_FORMAT).replace(tzinfo=pytz.timezone('UTC'))
        return False
    
    def _get_priority_delivery(self, cr, uid, ids, fields_name, args, context=None):
        """
            Obtiene el color que le corresponde a la entrega segun su estado y la prioridad de entrega
        """
        res = {}
        config = self.pool.get('delivery.config.settings').get_config_settings(cr, uid, context=context)
        delivery_term_obj = self.pool.get('delivery.term')
        
        # Obtiene la fecha actual
        datetime_order = time.strftime("%Y-%m-%d %H:%M:%S") 
        #print "******************** datetime_order ************** ", datetime_order
        datetime_order = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print "******************** datetime_order ************** ", datetime_order
        ics_date = self.ics_datetime(datetime_order)
        #print "******************** ics_date ************** ", ics_date
        
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context)
        #print "******************** date_start ************** ", date_start, " - ", type(date_start)
        
        #delivery_date = self.browse(cr, uid, 80, context=context).delivery_date
        ##print "**************** fecha entrga ************* ", delivery_date
        
        # Obtiene el punto medio de la fecha sobre producto por surtir y sobre en tiempo
        delivery_term = delivery_term_obj.browse(cr, uid, config.get('delivery_term_id',False))
        date_one = delivery_term_obj.get_date_next(cr, uid, datetime_order, delivery_term.value, delivery_term.unit, context=context)
        #print "**************** fecha a 48hrs ************* ", date_one
        date_mid = delivery_term_obj.get_date_next(cr, uid, datetime_order, round(delivery_term.value / 2,0), delivery_term.unit, context=context)
        #print "**************** fecha a 24hrs ************* ", date_mid
        date_qt =  delivery_term_obj.get_date_next(cr, uid, datetime_order, round(delivery_term.value / 4, 0), delivery_term.unit, context=context)
        #print "**************** fecha a 12hrs ************* ", date_qt
        
        # Pone a todos los registros por default en blanco
        for id in ids:
            res[id] = {
                'color': 0,
                'priority': 'none'
            }
            
        
        # Identifica las entregas que estan en tiempo
        pick_ids = self.search(cr, uid, [('delivery_date','>=',date_mid),('delivery_date','<=',date_one),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color1']
                res[id]['priority'] = 'ontime'
        
        # Identifica las entregas que estan por surtir
        pick_ids = self.search(cr, uid, [('delivery_date','>=',date_qt),('delivery_date','<=',date_mid),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color2']
                res[id]['priority'] = 'todeliver'
        
        # Identifica las entregas que estan urgente
        pick_ids = self.search(cr, uid, [('delivery_date','>=',datetime_order),('delivery_date','<=',date_qt),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color3']
                res[id]['priority'] = 'urgent'
        
        # Identifica las entregas que estan vencido
        pick_ids = self.search(cr, uid, [('delivery_date','<',datetime_order),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color4']
                res[id]['priority'] = 'defeated'
        
        # Identifica las entregas que estan programado
        pick_ids = self.search(cr, uid, [('delivery_date','>',date_one),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color5']
                res[id]['priority'] = 'program'
        
        return res
    
    _columns = {
        'batch_id': fields.many2one('picking.batch', 'Picking Batch', change_default=True),
        'so_payment_method': fields.char('Payment Method', size=32),
        #'color': fields.integer('Color Index'),
        'color': fields.function(_get_priority_delivery, type='integer', string="Color index", multi='priority'),
        'priority': fields.function(_get_priority_delivery, type='selection', multi='priority', selection=[
            ('ontime','En tiempo'),
            ('todeliver','Por Surtir'),
            ('urgent','Urgente'),
            ('defeated','Vencido'),
            ('program','Programado'),
            ('none','Desconocido')], string='Prioridad entrega', store=False),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        pts_id = False
        if type(ids) != type([]):
            ids = [ids]
        #if 'dts_id' in vals:
        #    move_pool = self.pool.get('stock.move')
        #    proc_pool = self.pool.get('procurement.order')
        #    pts_pool = self.pool.get('delivery.time')
        #    drl_pool = self.pool.get('delivery.route.line')
        #    
        #    if 'pts_id' not in vals:
        #        pts_id = pts_pool.search(cr, uid, [('active', '=', True), ('type', '=', 'pts'), ('dts_id', '=', vals['dts_id'])], order='start_date DESC')
        #        if pts_id:
        #            pts_id = pts_id[0]
        #            vals.update({'pts_id':pts_id})
        #    else:
        #        pts_id = vals['pts_id']
        #    
        #    if pts_id:
        #        move_ids = move_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('picking_id', 'in', ids)])
        #        if move_ids:
        #            move_pool.write(cr, uid, move_ids, {'pts_id':pts_id})
        #            proc_ids = proc_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('move_id', 'in', move_ids)])
        #            if proc_ids:
        #                proc_pool.write(cr, uid, proc_ids, {'pts_id':pts_id})
        #    
#            Actually DONE in fields.function
#            route_lines = drl_pool.search(cr, uid, [('state', 'in', ['draft']), ('picking_id', 'in', ids)])
#            if route_lines:
#                drl_pool.write(cr, uid, route_lines, {'dts_id': vals['dts_id']})
        return super(stock_picking, self).write(cr, uid, ids, vals, context=context)
    
    def pts_id_change(self, cr, uid, ids, pts_id, context=None):
        res = {}
        context = context or {}
        if type(ids) != type([]):
            ids = [ids]
        move_pool = self.pool.get('stock.move')
        proc_pool = self.pool.get('procurement.order')
        pts_pool = self.pool.get('delivery.time')
        drl_pool = self.pool.get('delivery.route.line')
        
        if pts_id:
            pts = pts_pool.browse(cr, uid, [pts_id])[0]
            #self.write(cr, uid, ids, {'dts_id':pts and pts.dts_id and pts.dts_id.id or False})
            res['dts_id'] = pts and pts.dts_id and pts.dts_id.id or False
        
        move_ids = move_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('picking_id', 'in', ids)])
        if move_ids:
            vals = {'pts_id':pts_id}
            if pts_id:
                vals.update({'date_expected':pts.dts_id.start_date})
            move_pool.write(cr, uid, move_ids, vals)
            proc_ids = proc_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('move_id', 'in', move_ids)])
            if proc_ids:
                proc_pool.write(cr, uid, proc_ids, {'pts_id':pts_id})
        
#        Actually DONE in fields.function
#        route_lines = drl_pool.search(cr, uid, [('state', 'in', ['draft']), ('picking_id', 'in', ids)])
#        if route_lines and 'dts_id' in res:
#            drl_pool.write(cr, uid, route_lines, {'dts_id': res['dts_id']})
        return {'value': res}

stock_picking()

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    
    def _get_priority_delivery(self, cr, uid, ids, fields_name, args, context=None):
        """
            Obtiene el color que le corresponde a la entrega segun su estado y la prioridad de entrega
        """
        res = {}
        config = self.pool.get('delivery.config.settings').get_config_settings(cr, uid, context=context)
        delivery_term_obj = self.pool.get('delivery.term')
        
        # Obtiene la fecha actual
        datetime_order = time.strftime("%Y-%m-%d %H:%M:%S") 
        #print "******************** datetime_order ************** ", datetime_order
        datetime_order = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print "******************** datetime_order ************** ", datetime_order
        ics_date = self.ics_datetime(datetime_order)
        #print "******************** ics_date ************** ", ics_date
        
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context)
        #print "******************** date_start ************** ", date_start, " - ", type(date_start)
        
        #delivery_date = self.browse(cr, uid, 80, context=context).delivery_date
        ##print "**************** fecha entrga ************* ", delivery_date
        
        # Obtiene el punto medio de la fecha sobre producto por surtir y sobre en tiempo
        delivery_term = delivery_term_obj.browse(cr, uid, config.get('delivery_term_id',False))
        date_one = delivery_term_obj.get_date_next(cr, uid, datetime_order, delivery_term.value, delivery_term.unit, context=context)
        #print "**************** fecha a 48hrs ************* ", date_one
        date_mid = delivery_term_obj.get_date_next(cr, uid, datetime_order, round(delivery_term.value / 2,0), delivery_term.unit, context=context)
        #print "**************** fecha a 24hrs ************* ", date_mid
        date_qt =  delivery_term_obj.get_date_next(cr, uid, datetime_order, round(delivery_term.value / 4, 0), delivery_term.unit, context=context)
        #print "**************** fecha a 12hrs ************* ", date_qt
        
        # Pone a todos los registros por default en blanco
        for id in ids:
            res[id] = {
                'color': 0,
                'priority': 'none'
            }
            
        
        # Identifica las entregas que estan en tiempo
        pick_ids = self.search(cr, uid, [('delivery_date','>=',date_mid),('delivery_date','<=',date_one),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color1']
                res[id]['priority'] = 'ontime'
        
        # Identifica las entregas que estan por surtir
        pick_ids = self.search(cr, uid, [('delivery_date','>=',date_qt),('delivery_date','<=',date_mid),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color2']
                res[id]['priority'] = 'todeliver'
        
        # Identifica las entregas que estan urgente
        pick_ids = self.search(cr, uid, [('delivery_date','>=',datetime_order),('delivery_date','<=',date_qt),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color3']
                res[id]['priority'] = 'urgent'
        
        # Identifica las entregas que estan vencido
        pick_ids = self.search(cr, uid, [('delivery_date','<',datetime_order),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color4']
                res[id]['priority'] = 'defeated'
        
        # Identifica las entregas que estan programado
        pick_ids = self.search(cr, uid, [('delivery_date','>',date_one),('id','in',ids)])
        if pick_ids:
            for id in pick_ids:
                res[id]['color'] = config['color5']
                res[id]['priority'] = 'program'
        
        return res
    
    _columns = {
        'batch_id': fields.many2one('picking.batch', 'Picking Batch', change_default=True),
        'so_payment_method': fields.char('Payment Method', size=32),
        
        'color': fields.function(_get_priority_delivery, type='integer', string="Color index", multi='priority'),
        'priority': fields.function(_get_priority_delivery, type='selection', multi='priority', selection=[
            ('ontime','En tiempo'),
            ('todeliver','Por Surtir'),
            ('urgent','Urgente'),
            ('defeated','Vencido'),
            ('program','Programado'),
            ('none','Desconocido')], string='Prioridad entrega', store=False),
    }
        
    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        pts_id = False
        if type(ids) != type([]):
            ids = [ids]
        if 'dts_id' in vals:
            move_pool = self.pool.get('stock.move')
            proc_pool = self.pool.get('procurement.order')
            pts_pool = self.pool.get('delivery.time')
            drl_pool = self.pool.get('delivery.route.line')
            
            if 'pts_id' not in vals:
                pts_id = pts_pool.search(cr, uid, [('active', '=', True), ('type', '=', 'pts'), ('dts_id', '=', vals['dts_id'])], order='start_date DESC')
                if pts_id:
                    pts_id = pts_id[0]
                    vals.update({'pts_id':pts_id})
            else:
                pts_id = vals['pts_id']
            
            if pts_id:
                move_ids = move_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('picking_id', 'in', ids)])
                if move_ids:
                    move_pool.write(cr, uid, move_ids, {'pts_id':pts_id})
                    proc_ids = proc_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('move_id', 'in', move_ids)])
                    if proc_ids:
                        proc_pool.write(cr, uid, proc_ids, {'pts_id':pts_id})
            
#            Actually DONE in fields.function
#            route_lines = drl_pool.search(cr, uid, [('state', 'in', ['draft']), ('picking_id', 'in', ids)])
#            if route_lines:
#                drl_pool.write(cr, uid, route_lines, {'dts_id': vals['dts_id']})
        return super(stock_picking_out, self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, data, context=None):
        """
        create route line 
        """
        if not data.get('pts_id', False) and data.get('origin', False):
            so_obj = self.pool.get('sale.order')
            so_ids = so_obj.search(cr, uid, [('name', '=', data.get('origin'))]) or []
            for so in so_obj.browse(cr, uid, so_ids):
                data.update({'pts_id':so.pts_id and so.pts_id.id or False, 'dts_id':so.pts_id and so.pts_id.dts_id and so.pts_id.dts_id.id or False})
        
        return_type = data.get('return', 'none')
        sp = super(stock_picking_out, self).create(cr, uid, data, context=context)
        if data.get('pts_id', False) and return_type not in ['customer', 'supplier']:
            self.pool.get('delivery.route.line').create(cr, uid, {'picking_id':sp, })
        return sp

stock_picking_out()


class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    
    _columns = {
        'batch_id': fields.many2one('picking.batch', 'Picking Batch', change_default=True),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        pts_id = False
        if type(ids) != type([]):
            ids = [ids]
        if 'dts_id' in vals:
            move_pool = self.pool.get('stock.move')
            proc_pool = self.pool.get('procurement.order')
            pts_pool = self.pool.get('delivery.time')
            drl_pool = self.pool.get('delivery.route.line')
            
            if 'pts_id' not in vals:
                pts_id = pts_pool.search(cr, uid, [('active', '=', True), ('type', '=', 'pts'), ('dts_id', '=', vals['dts_id'])], order='start_date DESC')
                if pts_id:
                    pts_id = pts_id[0]
                    vals.update({'pts_id':pts_id})
            else:
                pts_id = vals['pts_id']
            
            if pts_id:
                move_ids = move_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('picking_id', 'in', ids)])
                if move_ids:
                    move_pool.write(cr, uid, move_ids, {'pts_id':pts_id})
                    proc_ids = proc_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('move_id', 'in', move_ids)])
                    if proc_ids:
                        proc_pool.write(cr, uid, proc_ids, {'pts_id':pts_id})
                        
#            Actually DONE in fields.function
#            route_lines = drl_pool.search(cr, uid, [('state', 'in', ['draft']), ('picking_id', 'in', ids)])
#            if route_lines:
#                drl_pool.write(cr, uid, route_lines, {'dts_id': vals['dts_id']})
        return super(stock_picking_in, self).write(cr, uid, ids, vals, context=context)
    
    
    def pts_id_change(self, cr, uid, ids, pts_id, context=None):
        res = {}
        context = context or {}
        if type(ids) != type([]):
            ids = [ids]
        move_pool = self.pool.get('stock.move')
        proc_pool = self.pool.get('procurement.order')
        pts_pool = self.pool.get('delivery.time')
        drl_pool = self.pool.get('delivery.route.line')
        
        if pts_id:
            pts = pts_pool.browse(cr, uid, [pts_id])[0]
            #self.write(cr, uid, ids, {'dts_id':pts and pts.dts_id and pts.dts_id.id or False})
            res['dts_id'] = pts and pts.dts_id and pts.dts_id.id or False
        
        move_ids = move_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('picking_id', 'in', ids)])
        if move_ids:
            vals = {'pts_id':pts_id}
            if pts_id:
                vals.update({'date_expected':pts.dts_id.start_date})
            move_pool.write(cr, uid, move_ids, vals)
            proc_ids = proc_pool.search(cr, uid, [('state', 'not in', ['cancel', 'done']), ('move_id', 'in', move_ids)])
            if proc_ids:
                proc_pool.write(cr, uid, proc_ids, {'pts_id':pts_id})
        
#        Actually DONE in fields.function
#        route_lines = drl_pool.search(cr, uid, [('state', 'in', ['draft']), ('picking_id', 'in', ids)])
#        if route_lines and 'dts_id' in res:
#            drl_pool.write(cr, uid, route_lines, {'dts_id': res['dts_id']})
        return {'value': res}
    

    def create(self, cr, uid, data, context=None):
        """
        create route line 
        """
        if not data.get('pts_id', False) and data.get('origin', False):
            so_obj = self.pool.get('sale.order')
            so_ids = so_obj.search(cr, uid, [('name', '=', data.get('origin'))]) or []
            for so in so_obj.browse(cr, uid, so_ids):
                data.update({'pts_id':so.pts_id and so.pts_id.id or False, 'dts_id':so.pts_id and so.pts_id.dts_id and so.pts_id.dts_id.id or False})
        
        purchase_id = data.get('purchase_id', False)
        return_type = data.get('return', 'none')
        
        sp = super(stock_picking_in, self).create(cr, uid, data, context=context)
        if data.get('pts_id', False) and return_type not in ['customer', 'supplier'] and not purchase_id:
            self.pool.get('delivery.route.line').create(cr, uid, {'picking_id':sp, })
        return sp

stock_picking_in()


class stock_tracking(osv.osv):
    _inherit = "stock.tracking"
    
    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Picking Related', change_default=True),
        'ul_id': fields.many2one('product.ul', 'Picking Box', change_default=True),
    }
stock_tracking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
