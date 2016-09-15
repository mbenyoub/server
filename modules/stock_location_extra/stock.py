# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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

class stock_picking(osv.Model):
    _inherit = 'stock.picking'
    
    def _get_journal(self, cr, uid, context=None):
        """
            Pone el primer diario que encuentre registrado por default
        """
        journal_obj = self.pool.get('stock.journal')
        res = journal_obj.search(cr, uid, ['name', '=', 'Delivery Orders'], limit=1)
        print "************ journal_ids ********* ", res
        return res and res[0] or False
    
    #def _default_delivery_schedule(self, cr, uid, context=None):
    #    """
    #        Función para colocar el horario de entrega por default
    #    """
    #    prop = self.pool.get('ir.property').get(cr, uid, 'stock_journal_property', 'stock.journal', context=context)
    #    
    #    print "**********PROP***********: ", prop
    #    
    #    return prop and prop.id or False
    #
    _defauls = {
        'stock_journal_id': _get_journal,
    }

stock_picking()

class stock_picking_out(osv.Model):
    _inherit = 'stock.picking.out'
    
    def _get_journal(self, cr, uid, context=None):
        """
            Pone el primer diario que encuentre registrado por default
        """
        journal_obj = self.pool.get('stock.journal')
        res = journal_obj.search(cr, uid, [], limit=1)
        print "************ journal_ids ********* ", res
        return res and res[0] or False

    _defauls = {
        'stock_journal_id': _get_journal
    }

stock_picking_out()