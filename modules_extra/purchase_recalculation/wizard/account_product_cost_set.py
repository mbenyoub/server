# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP s.a. (<http://www.openerp.com>)
#    Copyright (C) 2013-TODAY Mentis d.o.o. (<http://www.mentis.si/openerp>)
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
from tools.translate import _
from datetime import datetime
import time
import openerp.addons.decimal_precision as dp

class account_product_cost_set(osv.TransientModel):
    _name="account.product.cost.set"
    _description="Set Product Costs"
    
    _columns={
        'period_id': fields.many2one('account.period', "Period", required=True,
            help="Period for which recalculation will be done."),
        'product_id': fields.many2one('product.product', "Product", domain=[('cost_method','=','average')], required=False,
            help="Product for which recalculation will be done. If not set recalculation will be done for all products with cost method set 'Average Price'"),
        'type': fields.selection((('0', 'Set cost price on existing account move lines'),
                                  ('1', 'Create new cost move per period/product'),
                                  ('2', 'Create new cost move per period/product category'),
                                  ('3', 'Create new cost move per period')), 'Type', required=True)
    }
    _defaults={
        'period_id': False,
        'product_id': False,
        'type': '0'
    }
    
    def _do_recalculation(self, cr, uid, ids, context=None):
        _recalc_id = self.browse(cr, uid, ids[0], context)
        _period_id = False
        _dates = {}
        _digits = {}

        # najdem ustrezna obdobja
        if _recalc_id.period_id:
            _period_id = _recalc_id.period_id
        else:
            raise osv.except_osv(_('Error!'), _('Cannot find suitable dates for recalculation.'))
        
        _date_from = _period_id.date_start
        _date_to = _period_id.date_stop
            
        # najdem ustrezne izdelke
        _product_ids = []
        
        if _recalc_id.product_id:
            _product_ids.append(_recalc_id.product_id.id)
        else:
            _location_ids = self.pool.get('stock.location').search(cr, uid, [('usage','=','internal')])
            _sql_string = '  SELECT sm.product_id AS id \n ' \
                          '    FROM stock_move AS sm \n ' \
                          '         INNER JOIN product_template AS pt ON pt.id = sm.product_id \n ' \
                          '                                              AND pt.cost_method = \'average\' \n ' \
                          '   WHERE sm.date >=  \'{date_from}\' \n' \
                          '         AND sm.date <= \'{date_to}\' \n ' \
                          '         AND sm.state = \'done\' \n ' \
                          '         AND sm.location_id IN {locations} \n ' \
                          '         AND sm.location_dest_id NOT IN {locations} \n ' \
                          'GROUP BY sm.product_id \n ' \
                          'ORDER BY sm.product_id;'.format(date_from = _date_from + ' 00:00:00',
                                                           date_to = _date_to + ' 23:59:59',
                                                           locations = tuple(_location_ids)).replace(',)', ')')
            cr.execute(_sql_string)
            _products_tup = cr.fetchall()
            for _tup in _products_tup:
                _product_ids.append(_tup[0])

        _digits_obj = self.pool.get('decimal.precision')
        _digits_id = _digits_obj.search(cr, uid, [('name','=','Product Price')])
        if len(_digits_id) > 0:
            _digits['price'] = _digits_obj.browse(cr, uid, _digits_id[0])['digits']
        else:
            _digits['price'] = 2
        
        _digits_id = _digits_obj.search(cr, uid, [('name','=','Account')])
        if len(_digits_id) > 0:
            _digits['account'] = _digits_obj.browse(cr, uid, _digits_id[0])['digits']
        else:
            _digits['account'] = 2

        # preračunam posamezen izdelek
        _products = self.pool.get('product.product').browse(cr, uid, _product_ids, context)
        for _product in _products:            
            _dates['date_from'] = _date_from + ' 00:00:00'
            _dates['date_to'] = _date_to + ' 23:59:59'

            _cost_price_id = self.pool.get('product.period.cost').search(cr, uid, [('product_id','=',_product.id),('period_id','=',_period_id.id)])
            if len(_cost_price_id) <> 0:
                _cost_price = self.pool.get('product.period.cost').browse(cr, uid, _cost_price_id[0], context)
            else:
                raise osv.except_osv(_('Error!'),_('Cost price for selected period does not exist!'))

            # posodobim vrednosti prodaje na povprečno ceno za obdobje
            _product._set_period_cost(_dates, _digits, _cost_price.price_unit)

        return True
    
    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if self._do_recalculation(cr, uid, ids, context):
            return {'type': 'ir.actions.act_window_close'}
        else:
            return False
