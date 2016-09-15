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

from openerp.osv import osv, fields
from tools.translate import _
import base64
import pooler
from time import strftime
from string import upper
from string import join
import datetime
import tempfile
import os
from dateutil.relativedelta import *
import csv

class wizard_account_move_edit(osv.Model):
    _name = 'wizard.account.move.edit'
    _description = 'Account - move.line edit'

    _columns = {
        'name': fields.char('Nombre'),
        'move_id': fields.many2one('account.move', 'Poliza', ondelete="cascade", required=True),
        'journal_id': fields.many2one('account.journal', 'Diario', required=True),
        'company_id': fields.many2one('res.company', 'compañia'),
        #'line_id': fields.related('move_id', 'line_id', type='one2many', relation='account.move.line', string='Apuntes contables')
        'line_id': fields.one2many('account.move.line', 'w_edit_id', string='Apuntes contables')
    }
    
    def onchange_move(self, cr, uid, ids, move_id, context=None):
        """
            Obtiene la informacion de los movimientos
        """
        line_obj = self.pool.get('account.move.line')
        if not move_id:
            return {}
        
        line_ids = line_obj.search(cr, uid, [('move_id','=',move_id)], context=context)
        
        return {'value': {'line_id': line_ids}}
    
    def action_apply(self, cr, uid, ids, context=None):
        """
            Aplica los cambios realizados sobre los movimientos generados
        """
        move_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        
        self.write(cr, uid, ids, {}, context=context)
        
        # Actualiza la informacion de las lineas de movimiento
        data = self.browse(cr, uid, ids[0], context=context)
        #print "**************** line id ************ ", data.line_id
        
        self.pool.get('account.move').write(cr, uid, [data.move_id.id], {}, context=context)
        
        self.unlink(cr, uid, ids, context=context)
        return True

wizard_account_move_edit()

class account_move_line(osv.Model):
    _inherit = "account.move.line"
    
    def onchange_edit(self, cr, uid, ids, state, context=None):
        """
            Actualiza la informacion del nuevo movimiento
        """
        line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        res = {}
        #print "**************** context *************** ", context
        if context.get('move_id',False):
            res['move_id'] = context.get('move_id')
        if context.get('next_val',0.0) != 0.0:
            amount = context.get('next_val',0.0)
            if amount >= 0.0:
                res['credit'] = amount
            else:
                res['debit'] = amount
        if context.get('name',False):
            res['name'] = context.get('name')
        
        return {'value': res}
    
    _columns = {
        'w_edit_id': fields.many2one('wizard.account.move.edit', 'wizard'),
    }
    
account_move_line()