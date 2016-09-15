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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

#----------------------------------------------------------
# Incoterms
#----------------------------------------------------------

class stock_journal(osv.Model):
    _inherit = "stock.journal"
    _description = "Stock Journal"
    _columns = {
        'default': fields.boolean('Default'),
    }
    
    _defaults = {
        'default': False
    }

stock_journal()

class stock_picking_in(osv.Model):
    _inherit = "stock.picking.in"
    
    def _get_stock_journal(self, cr, uid, context=None):
        """
            Obtiene el diario de existencias que se marque por default
        """
        if context is None: context = {}
        journal_ids = self.pool.get('stock.journal').search(cr, uid, [('default','=',True)], context=context)
        #print "**************** journal ids *************** ", journal_ids
        if journal_ids:
            return journal_ids[0]
        return False
    
    _defaults = {
        'stock_journal_id': _get_stock_journal
    }

stock_picking_in()

class stock_picking_out(osv.Model):
    _inherit = "stock.picking.out"
    
    def _get_stock_journal(self, cr, uid, context=None):
        """
            Obtiene el diario de existencias que se marque por default
        """
        if context is None: context = {}
        journal_ids = self.pool.get('stock.journal').search(cr, uid, [('default','=',True)], context=context)
        #print "**************** journal ids *************** ", journal_ids
        if journal_ids:
            return journal_ids[0]
        return False
    
    _defaults = {
        'stock_journal_id': _get_stock_journal
    }

stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
