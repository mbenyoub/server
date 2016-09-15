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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp
from openerp import netsvc

# ---------------------------------------------------------
# Account move - Tabla de impuestos
# ---------------------------------------------------------

class account_move(osv.Model):
    _inherit = "account.move"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        links = self.pool.get('links.get.request')
        return links._links_get(cr, uid, context=context)
    
    _columns = {
        'reference': fields.reference('Referencia', selection=_links_get, size=128, readonly=True),
    }
    
    def action_view_move_line(self, cr, uid, ids, context=None):
        """
            Redirecciona a la vista lista de los apuntes contables de la poliza por medio de una ventana
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_mx_account_move', 'view_wizard_account_move_edit')
        
        move = self.browse(cr, uid, ids[0], context=context)
        
        return {
            'name':_("Apuntes Contables"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'wizard.account.move.edit',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[]",
            'context': {
                'default_move_id': ids[0],
                'default_journal_id': move.journal_id.id or False,
                'manual': True,
                'default_company_id': move.company_id.id or False,
                'journal_id': move.journal_id.id or False,
                'company_id': move.company_id.id or False,
                'period_id': move.period_id.id or False,
                'default_name': move.name,
                'date': move.date
            },
        }
    
    #def action_view_move_line(self, cr, uid, ids, context=None):
    #    """
    #        Redirecciona a la vista lista de los apuntes contables de la poliza por medio de una ventana
    #    """
    #    # Obtiene la vista a cargar
    #    if not ids: return []
    #    dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_move_line_tree')
    #    dummy, view_id_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_form')
    #    
    #    return {
    #        'name':_("Apuntes Contables"),
    #        'view_mode': 'tree,form',
    #        'view_id': view_id,
    #        'view_type': 'form',
    #        'views': [(view_id, 'tree'),(view_id_form, 'form')],
    #        'res_model': 'account.move.line',
    #        'type': 'ir.actions.act_window',
    #        'target': 'new',
    #        'domain': "[('move_id','=',%s)]"%(ids[0],),
    #        'context': {'default_move_id': ids[0]},
    #    }

account_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
