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
from openerp import netsvc
from openerp.tools.translate import _

class delivery_time(osv.osv):
    _inherit = 'delivery.time'
    
    def search(self, cr, uid, args, offset=0, limit=None, order='name', context=None, count=False):
        # now = datetime.now()
        # args.append(('name','>=',datetime.strftime(now,'%y%m%d')))
        return super(delivery_time, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

delivery_time()

class delivery_return_type(osv.osv):
    _name = 'delivery.return.type'
    _order = 'sequence'
    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'sequence': fields.integer('Sequence'),
    }
    
delivery_return_type()
    
class delivery_return_reason(osv.osv):
    _name = 'delivery.return.reason'
    
    _columns = {
        'type': fields.many2one('delivery.return.type', 'Type', required=True),
        'reason': fields.char('Name', size=1024, required=False),
        'route_line_id': fields.many2one('delivery.route.line', 'Delivery Route Line'),
    }
    
delivery_return_reason()

class delivery_route(osv.osv):
    _inherit = 'delivery.route'
    
    def _auto_init(self, cr, context=None):
        super(delivery_route, self)._auto_init(cr, context=context)
        cr.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'delivery_scheduler_running'")
        if not cr.fetchone():
            cr.execute('CREATE TABLE delivery_scheduler_running (running boolean)')
            cr.commit()
            cr.execute('INSERT INTO delivery_scheduler_running (running) VALUES (FALSE)')
    
    def set_confirm_cs(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'confirm_cs': True}, context=context)
        return True
    
delivery_route()

class delivery_route_line(osv.osv):
    _inherit = 'delivery.route.line'
    
    def search(self, cr, uid, args, offset=0, limit=None, order='dts_name', context=None, count=False):
        context = context or {}
        new_order = context.get('sorting', order)
        return super(delivery_route_line, self).search(cr, uid, args, offset=offset, limit=limit, order=new_order, context=context, count=count)
    
    def set_not_vip(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'vip':False})

    def set_vip(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'vip':True})
    
    def write(self, cr, uid, ids, vals, context=None):
        if type(ids) != type([]):
            ids = [ids]
        context = context or {}
        if ('route_id' in vals or 'color' in vals or 'sequence' in vals) and not 'force_update' in context:
            for line in self.browse(cr, uid, ids):
                if line.state == 'draft':
                    current_dts = context.get('force_dts_id_kanban', False) or False
                    # if current_dts:
                    #    vals.update({'dts_id':current_dts})
                    if 'route_id' in vals and vals['route_id']:
                        route_state = self.pool.get('delivery.route').read(cr, uid, [vals['route_id']], ['state', 'name'])
                        if route_state[0]['state'] != 'draft': 
                            print('The Route %s is confirmed, you can not add lines to it.' % (route_state[0]['name']))
                            raise osv.except_osv(_('Error'), _('The Route %s is confirmed, you can not add lines to it.' % (route_state[0]['name'])))
                        
                        elif 'update_color' in context and context['update_color'] == 1:
                            current_color = str(line.color)
                            cr.execute("SELECT color FROM (select count(*) as cpt, color as color from delivery_route_line WHERE route_id=" + str(vals['route_id']) + " AND color != " + current_color + " AND color IS NOT null AND color > 0 GROUP BY color) t ORDER BY cpt DESC")
                            color = cr.fetchone()
                            if color and color[0]:
                                vals.update({'color':color[0]})
                            
                            elif current_dts:
                                cr.execute("SELECT DISTINCT color FROM delivery_route_line WHERE (dts_id=" + str(current_dts) + " OR id = " + str(line.id) + ") AND color IS NOT null AND color > 0")
                                colors = map(lambda x: x[0], cr.fetchall())
                                color = False
                                
                                for idx in range(1, 22):
                                    if idx not in colors and not color and idx != current_color:
                                        color = idx
                                if color:
                                    vals.update({'color':color})
                                else:
                                    print('No more Route available for the DTS %s.' % (line.dts_id.name))
                                    raise osv.except_osv(_('Error'), _('No more Route available for the DTS %s.' % (line.dts_id.name)))
                    
                    elif 'check4color' in context and context['check4color'] and 'color' in vals:
                        cr.execute("SELECT DISTINCT route_id FROM delivery_route_line WHERE dts_id=" + str(line.dts_id.id) + " AND color = " + str(vals['color']) + " AND color > 0 AND state not in ('draft','cancel')")
                        route_line_ids = map(lambda x: x[0], cr.fetchall())
                        if route_line_ids:
                            print('The Route Line %s (origin: %s) can not be put in a confirmed Route (%s).' % (line.picking_id.name, line.picking_id.origin, route_line_ids))
                            raise osv.except_osv(_('Error'), _('The Route Line %s (origin: %s) can not be put in a confirmed Route (%s).' % (line.picking_id.name, line.picking_id.origin, route_line_ids)))
                else:
                    print('The Route Line %s (origin: %s) is confirmed. You can not change it.' % (line.picking_id.name, line.picking_id.origin))
                    raise osv.except_osv(_('Error'), _('The Route Line %s (origin: %s) is confirmed. You can not change it.' % (line.picking_id.name, line.picking_id.origin)))
        return super(delivery_route_line, self).write(cr, uid, ids, vals, context=context)
    
    
    def set_van(self, cr, uid, ids, van=0, context=None):
        self.write(cr, uid, ids, {'color': van}, context=context)
        return True
    def set_van_0(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 0, context)
    def set_van_1(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 1, context)
    def set_van_2(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 2, context)
    def set_van_3(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 3, context)
    def set_van_4(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 4, context)
    def set_van_5(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 5, context)
    def set_van_6(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 6, context)
    def set_van_7(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 7, context)
    def set_van_8(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 8, context)
    def set_van_9(self, cr, uid, ids, context=None):
        return self.set_van(cr, uid, ids, 9, context)
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        context = context or {}
        if 'view_name' in context and view_type == 'kanban':
            view_ids = self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'delivery.route.line'), ('name', '=', context['view_name'])], context=context)
            if view_ids:
                view_id = view_ids[0]
                del context['view_name']
        return super(delivery_route_line, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    
    
    def _get_neighborhood(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for route in self.browse(cr, uid, ids):
            # res[route.id] = route.picking_id and route.picking_id.sale_id and route.picking_id.sale_id.deliver_zone or route.picking_id and route.picking_id.partner_id and route.picking_id.partner_id.vm_district or False
            res[route.id] = route.picking_id and route.picking_id.partner_id and route.picking_id.partner_id.deliver_zone or False
        return res
    
    def _get_dts_id(self, cr, uid, ids, fields, args, context=None):
        context = context or {}
        res = {}
        for route in self.browse(cr, uid, ids):
            if route.state in ['draft'] and context.get('set_dts', True):
                res[route.id] = route.picking_id and route.picking_id.pts_id and route.picking_id.pts_id.dts_id and route.picking_id.pts_id.dts_id.id or False
            else:
                res[route.id] = route.dts_id and route.dts_id.id or False
        return res
    
    def _get_dts_name(self, cr, uid, ids, fields, args, context=None):
        context = context or {}
        res = {}
        for route in self.browse(cr, uid, ids):
            if route.state in ['draft'] and context.get('set_dts', True):
                res[route.id] = route.picking_id and route.picking_id.pts_id and route.picking_id.pts_id.dts_id and route.picking_id.pts_id.dts_id.name or 'n/a'
            else:
                res[route.id] = route.dts_name or 'n/a'
        return res
    
    def _get_special_time(self, cr, uid, ids, fields, args, context=None):
        tz = pytz.timezone('Asia/Shanghai')
        result = {}
        for route in self.browse(cr, uid, ids):
            res = {}
            customer_date = ''
            route_dts_id = route.dts_id and route.dts_id.id
            so_dts_id    = route.picking_id.sale_id.dts_id and route.picking_id.sale_id.dts_id.id
            
            if so_dts_id and route_dts_id != so_dts_id:
                customer_date = route.picking_id.sale_id.dts_id.name
            
            elif route.picking_id.sale_id:
                date_start = route.picking_id.sale_id.start_date or False
                date_end = route.picking_id.sale_id.end_date or False
                
                if date_start:
                    date_start = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')            
                    date_start = pytz.utc.localize(date_start).astimezone(tz)
                    
                    customer_date = datetime.strftime(date_start, '%H:%M')
                    #LY if customer_date is 00:00, no special time. 
                    if customer_date != '00:00':    
                        if date_end:
                            date_end = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')            
                            date_end = pytz.utc.localize(date_end).astimezone(tz)
                            customer_date += ' - '
                            customer_date += datetime.strftime(date_end, '%H:%M')
            res['customer_date'] = customer_date or ' '
            result[route.id] = res
        return result
    
    def _get_street(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for route in self.browse(cr, uid, ids):
            res[route.id] = route.picking_id and route.picking_id.partner_id and route.picking_id.partner_id.street or ' n/a'
        return res
    
    def _route_to_update_after_picking_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('delivery.route.line').search(cr, uid, [('picking_id', 'in', ids)]) or []
    
    def _route_to_update_after_dts_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('dts_id', 'in', ids)]) or []
        return self.pool.get('delivery.route.line')._route_to_update_after_picking_change(cr, uid, picking_ids, None, None, context=context)
    
    def _route_to_update_after_so_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('delivery.route.line').search(cr, uid, [('sale_order_id', 'in', ids)]) or []
    
    def _route_to_update_after_po_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('delivery.route.line').search(cr, uid, [('purchase_id', 'in', ids)]) or []
    
    def _route_to_update_after_partner_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('partner_id', 'in', ids)]) or []
        return self.pool.get('delivery.route.line')._route_to_update_after_picking_change(cr, uid, picking_ids, None, None, context=context)
    
    _store_dts = {
        'delivery.route.line': (lambda self, cr, uid, ids, context: ids, ['picking_id'], 10),
        'stock.picking': (_route_to_update_after_picking_change, ['pts_id'], 10),
    }
    _store_dts_name = {
        'delivery.route.line': (lambda self, cr, uid, ids, context: ids, ['picking_id'], 10),
        'stock.picking': (_route_to_update_after_picking_change, ['pts_id'], 10),
        'delivery.time': (_route_to_update_after_dts_change, ['name'], 10),
    }
    _store_special_time = {
        'delivery.route.line': (lambda self, cr, uid, ids, context: ids, ['picking_id'], 12),
        'stock.picking': (_route_to_update_after_picking_change, ['sale_id','dts_id'], 12),
        'sale.order': (_route_to_update_after_so_change, ['dts_id'], 12),
    }
    _store_neighborhood = {
        'delivery.route.line': (lambda self, cr, uid, ids, context: ids, ['picking_id'], 10),
        'stock.picking': (_route_to_update_after_picking_change, ['partner_id'], 10),
        'res.partner': (_route_to_update_after_partner_change, ['vm_district'], 10),
    }
    
    _store_amount = {
        'delivery.route.line': (lambda self, cr, uid, ids, context: ids, ['picking_id', 'adjustment'], 10),
        'stock.picking': (_route_to_update_after_picking_change, ['sale_id', 'purchase_id', 'origin'], 10),
        'purchase.order': (_route_to_update_after_po_change, ['amount_total'], 10),
    }
    
    _store_street = {
        'delivery.route.line': (lambda self,cr,uid,ids,context: ids,['picking_id'],10), 
        'stock.picking': (_route_to_update_after_picking_change, ['partner_id'], 10),
    }
    
    def _get_amount(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for route in self.browse(cr, uid, ids):
            res = {}
            res['amount_total'] = 0.0
            res['amount_unpaid'] = 0.0
            res['to_be_received'] = 0.0
            
            if route.picking_id and route.picking_id.sale_id:
                res['amount_total'] = route.picking_id.sale_id.amount_total
                res['amount_unpaid'] = res['amount_total']
                res['to_be_received'] = res['amount_unpaid'] + route.adjustment
            elif route.picking_id and route.picking_id.purchase_id:
                res['amount_total'] = route.picking_id.purchase_id.amount_total
                res['amount_unpaid'] = 0.0
                res['to_be_received'] = res['amount_unpaid'] + route.adjustment
            result[route.id] = res
        return result
    
    _columns = {
        'dts_id': fields.function(_get_dts_id, type='many2one', obj='delivery.time', store=_store_dts, string='Delivery Time', _classic_read=True),
        'dts_name': fields.function(_get_dts_name, type='char', size=124, store=_store_dts_name, string='Delivery Time'),
        'return_reasons': fields.one2many('delivery.return.reason', 'route_line_id', 'Return Reasons', readonly=False),
        'delivered_cpt': fields.related('picking_id', 'delivered_cpt', type='integer', string='Delivered x times', readonly=True),
        'customer_date': fields.function(_get_special_time, type='char', size=64, store=_store_special_time, multi="special_time", string=_('Customer Delivery Time')),
        'neighborhood': fields.function(_get_neighborhood, type='char', size=255, store=_store_neighborhood, string=_('Neighborhood')),
        'street': fields.function(_get_street, type='char', size=128, store=_store_street, string='Street'),
        'vip': fields.boolean('is VIP ?'),
        'amount_total':  fields.function(_get_amount, type='float', multi="amount", store=_store_amount, string='Total'),
        'amount_unpaid': fields.function(_get_amount, type='float', multi="amount", store=_store_amount, string='Unpaid'),
        'adjustment': fields.float('Adjustment'),
        'cs_remark': fields.text('CS Remark'),
        'to_be_received': fields.function(_get_amount, type='float', multi="amount", store=_store_amount, string='To be Received'),
        'amount_received': fields.float('Received'),
        'account_checked': fields.boolean('Checked'),
        'account_remark': fields.text('Remark Accounting'),
    }

delivery_route_line()

class res_users(osv.osv):
    _inherit = 'res.users'
    
    _columns = {
        'dts_id': fields.many2one('delivery.time', 'Last Used Delivery Time'),
    }
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
