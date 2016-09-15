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

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def _so_to_update_after_dts_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('sale.order').search(cr, uid, [('pts_id', 'in', ids)]) or []
    
    _store_dts_id = {
        'sale.order': (lambda self, cr, uid, ids, context: ids, ['pts_id'], 10),
        'delivery.time': (_so_to_update_after_dts_change, ['dts_id'], 10),
    }    
    
    _columns = {
        'batch_id': fields.many2one('picking.batch', 'Picking Batch', change_default=True),
        # 'so_payment_method': fields.char('Payment Method', size=32),
    }
    
    def action_cancel_order_with_moves_not_delivered(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        drl_obj = self.pool.get('delivery.route.line')
        #proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            try:
                for pick in sale.picking_ids:
                    for mov in pick.move_lines:
                        if mov.state not in ('done','cancel'):
                            mov.write({'state':'cancel'})
                                    
                for pick in sale.picking_ids:
                    if pick.state != 'cancel':
                        #wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
                        pick.write({'state':'cancel'})
                for inv in sale.invoice_ids:
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
                for line in sale.order_line:
                    if line.procurement_id:
                        wf_service.trg_validate(uid, 'procurement.order', line.procurement_id.id, 'button_check', cr)
                
                #cancel delivery route line
                drl_ids = drl_obj.search(cr, uid, [('sale_order_id','=',sale.id),('state','!=','cancel')])
                drl_obj.action_cancel(cr,uid,drl_ids,context=context)
                
                order_ref = context.get('order_ref',False)
                self.write(cr, uid, [sale.id], {'state':'shipping_except','client_order_ref':order_ref})
                cr.commit()
            except:
                _logger.info('==== #LY action_cancel_order_with_moves_not_delivered fail %s===='%(sale.id))
        return True
    
    def action_cancel_order_with_moves(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        drl_obj = self.pool.get('delivery.route.line')
        #proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            try:
                if sale.state == 'done':
                        return False
                for pick in sale.picking_ids:
                    if pick.state == 'done':
                        return False
                    for mov in pick.move_lines:
                        if mov.state == 'done':
                            return False
                for inv in sale.invoice_ids:
                    if inv.state == 'paid':
                        return False
                    
                for pick in sale.picking_ids:
                    wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
                for pick in sale.picking_ids:
                    if pick.state != 'cancel':
                        wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
                                    
                for inv in sale.invoice_ids:
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
                for line in sale.order_line:
                    if line.procurement_id:
                        wf_service.trg_validate(uid, 'procurement.order', line.procurement_id.id, 'button_check', cr)
                
                #cancel delivery route line
                drl_ids = drl_obj.search(cr, uid, [('sale_order_id','=',sale.id),('state','!=','cancel')])
                drl_obj.action_cancel(cr,uid,drl_ids,context=context)
                
                sale_order_line_obj.write(cr, uid, [l.id for l in  sale.order_line], {'state': 'cancel'})
                self.write(cr, uid, [sale.id], {'state': 'cancel'})
                cr.commit()
            except:
                _logger.info('==== #LY action_cancel_order_with_moves fail %s===='%(sale.id))
        return True

    #def _prepare_order_line_procurement(self, cr, uid, order, pt_id, line, move_id, date_planned, context=None):
    #    return {
    #        'name': line.name,
    #        'origin': order.name,
    #        'date_planned': date_planned,
    #        'product_id': line.product_id.id,
    #        'product_qty': line.product_uom_qty,
    #        'product_uom': line.product_uom.id,
    #        'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
    #        'product_uos': (line.product_uos and line.product_uos.id) or line.product_uom.id,
    #        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
    #        'procure_method': line.type,
    #        'move_id': move_id,
    #        'company_id': order.company_id.id,
    #        'note': line.name,
    #        'pts_id': pt_id,
    #    }
    
    def _prepare_order_line_move_fc(self, cr, uid, order, line, picking_id, pt_id, date_planned, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id) or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0,
            'pts_id':pt_id,
        }
    
    #def _prepare_order_picking(self, cr, uid, order, dt_id, pt_id, context=None):
    #    # SHOULD USE ir_sequence.next_by_code() or ir_sequence.next_by_id()
    #    pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
    #    return {
    #        'name': pick_name,
    #        'origin': order.name,
    #        'date': order.date_order,
    #        'type': 'out',
    #        'state': 'auto',
    #        'move_type': order.picking_policy,
    #        'sale_id': order.id,
    #        'partner_id': order.partner_shipping_id.id,
    #        'note': order.note,
    #        'invoice_state': (order.order_policy == 'picking' and '2binvoiced') or 'none',
    #        'company_id': order.company_id.id,
    #        'dts_id':dt_id,
    #        'pts_id':pt_id,
    #    }
    
    def _prepare_pts_dts(self, cr, uid, order, context=None):
        if not context:
            context = {}
        tz = pytz.timezone('Asia/Shanghai')
        tz2 = pytz.timezone('America/Anchorage')
        delivery_time_obj = self.pool.get('delivery.time')
        time_slot_obj = self.pool.get('delivery.time.slot')
        val={}
        
        dts = False
        pts = False
        pt_id = False
        dt_id = False
        min_date = False
        slot_id = False
        now = datetime.now()
        address = order.partner_shipping_id or order.partner_id or False
        
        if order.start_date:
            min_date = order.start_date
            dts = order.start_date
            dts = datetime.strptime(dts, '%Y-%m-%d %H:%M:%S')            
            dts = pytz.utc.localize(dts).astimezone(tz)
        if order.date_order:
            pts = datetime.strptime(order.date_order, '%Y-%m-%d')
            pts = pytz.utc.localize(pts).astimezone(tz)
        if not pts:
            pts = dts
        
        if dts:
            start_date = datetime.strftime(dts, '%Y-%m-%d')
            from_time = datetime.strftime(dts, '%H:%M')
            #LY remove the shanghai restrict out
            # if address and (not address.city or address.city.lower() in ['shanghai']):
            #     from_time = datetime.strftime(dts, '%H:%M')
            # else:  # eg: in Nanjing
            #     from_time = '09:30'
            name = datetime.strftime(dts, '%y%m%d')
            name_pts = name
            start_date_pts = start_date
            
            slot_ids = time_slot_obj.search(cr, uid, [('max_time', '>=', from_time), ('type', '=', 'dts')], order='max_time')
            if slot_ids:
                slot = time_slot_obj.browse(cr, uid, slot_ids[0])
                name += slot.name
                end_date = start_date + ' ' + slot.end_time
                start_date += ' ' + slot.start_time 
                start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
                start_date = pytz.utc.localize(start_date).astimezone(tz2)
                start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M')
                end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
                end_date = pytz.utc.localize(end_date).astimezone(tz2)
                end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M')
                
                dt_ids = delivery_time_obj.search(cr, uid, [('name', '=', name), ('type', '=', 'dts'), ('slot_id', '=', slot.id)])
                if dt_ids:
                    dt_id = dt_ids[0]
                else:
                    dt_id = delivery_time_obj.create(cr, uid, {
                        'name':name,
                        'start_date': start_date,
                        'end_date': end_date,
                        'active': True,
                        'type': 'dts',
                        'slot_id': slot.id,
                        }, context)
                    cr.commit()
        
        if pts and dt_id:
            date_pts = datetime.strftime(pts, '%Y-%m-%d')
            from_time = datetime.strftime(pts, '%H:%M')
            if date_pts < datetime.strftime(dts, '%Y-%m-%d'):
                date_pts = datetime.strftime(dts, '%Y-%m-%d')
                from_time = '00:00'
            
            pts_slot_ids = time_slot_obj.search(cr, uid, [('max_time', '>=', from_time), ('type', '=', 'pts'), ('dts_id', '=', slot.id)], order='max_time')
            if pts_slot_ids:
                pts_slot = time_slot_obj.browse(cr, uid, pts_slot_ids[0])
                name_pts += pts_slot.name
                end_date_pts = start_date_pts + ' ' + pts_slot.end_time
                start_date_pts += ' ' + pts_slot.start_time
                start_date_pts = datetime.strptime(start_date_pts, '%Y-%m-%d %H:%M')
                start_date_pts = pytz.utc.localize(start_date_pts).astimezone(tz2)
                start_date_pts = datetime.strftime(start_date_pts, '%Y-%m-%d %H:%M')
                end_date_pts = datetime.strptime(end_date_pts, '%Y-%m-%d %H:%M')
                end_date_pts = pytz.utc.localize(end_date_pts).astimezone(tz2)
                end_date_pts = datetime.strftime(end_date_pts, '%Y-%m-%d %H:%M')
            
                pt_ids = delivery_time_obj.search(cr, uid, [('name', '=', name_pts), ('type', '=', 'pts'), ('slot_id', '=', pts_slot.id)])
                if pt_ids:
                    pt_id = pt_ids[0]
                else:
                    pt_id = delivery_time_obj.create(cr, uid, {
                        'name':name_pts,
                        'start_date': start_date_pts,
                        'end_date': end_date_pts,
                        'active': True,
                        'type': 'pts',
                        'slot_id': pts_slot.id,
                        'dts_id': dt_id,
                        }, context)
                    cr.commit()
                val['pts_id'] = pt_id
        if val:
            order.write(val)
        return min_date, dt_id, pt_id
    
    #def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
    #    """Create the required procurements to supply sales order lines, also connecting
    #    the procurements to appropriate stock moves in order to bring the goods to the
    #    sales order's requested location.
    #
    #    If ``picking_id`` is provided, the stock moves will be added to it, otherwise
    #    a standard outgoing picking will be created to wrap the stock moves, as returned
    #    by :meth:`~._prepare_order_picking`.
    #
    #    Modules that wish to customize the procurements or partition the stock moves over
    #    multiple stock pickings may override this method and call ``super()`` with
    #    different subsets of ``order_lines`` and/or preset ``picking_id`` values.
    #
    #    :param browse_record order: sales order to which the order lines belong
    #    :param list(browse_record) order_lines: sales order line records to procure
    #    :param int picking_id: optional ID of a stock picking to which the created stock moves
    #                           will be added. A new picking will be created if ommitted.
    #    :return: True
    #    """
    #    val = {}
    #    move_obj = self.pool.get('stock.move')
    #    picking_obj = self.pool.get('stock.picking')
    #    procurement_obj = self.pool.get('procurement.order')
    #    proc_ids = []
    #    
    #    min_date, dt_id, pt_id = self._prepare_pts_dts(cr, uid, order)
    #    # min_date, dt_id, pt_id = order.date_order, order.dts_id.id, order.pts_id.id
    #    #print '<<<<<<<<<<<<<<  %s, %s, %s' % (min_date, dt_id, pt_id)
    #    
    #    for line in order_lines:
    #        if line.state == 'done':
    #            continue
    #
    #        date_planned = min_date or self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
    #
    #        if line.product_id:
    #            if line.product_id.type in ('product', 'consu'):
    #                if not picking_id:
    #                    picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, dt_id, pt_id, '', '', context=context))
    #                move_id = move_obj.create(cr, uid, self._prepare_order_line_move_fc(cr, uid, order, line, picking_id, pt_id, date_planned, context=context))
    #            else:
    #                # a service has no stock move
    #                move_id = False
    #
    #            proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, pt_id, line, move_id, date_planned, context=context))
    #            proc_ids.append(proc_id)
    #            line.write({'procurement_id': proc_id})
    #            self.ship_recreate(cr, uid, order, line, move_id, proc_id)
    #
    #    wf_service = netsvc.LocalService("workflow")
    #    if picking_id:
    #        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
    #    for proc_id in proc_ids:
    #        wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
    #    
    #    if order.state == 'shipping_except':
    #        val['state'] = 'progress'
    #        val['shipped'] = False
    #
    #        if (order.order_policy == 'manual'):
    #            for line in order.order_line:
    #                if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
    #                    val['state'] = 'manual'
    #                    break
    #    order.write(val)
    #    return True

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
