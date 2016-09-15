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

# ---------------------------------------------------------
# Account journal - Diarios contables
# ---------------------------------------------------------

class account_journal(osv.Model):
    """
        Modificacion series sobre creacion de diarios
    """
    _inherit='account.journal'

    def _get_cfdi_prefix(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Revisa si el diario es un CFDI y obtiene el prefijo del folio
        """
        res = {}
        
        # Recorre los registros
        for journal in self.browse(cr, uid, ids, context=context):
            # Inicializa los valores a retornar
            res[journal.id] = {
                'prefix2': '',
                'cfdi': False
            }
            
            # Valida si tiene una secuencia el diario
            if journal.sequence_id:
                # Verifica si hay aprobaciones sobre el diario y cambia los valores de retorno
                if journal.sequence_id.approval_ids:
                    for app in journal.sequence_id.approval_ids:
                        res[journal.id] = {
                            'prefix2': app.serie,
                            'cfdi': True
                        }
                        break
        return res

    _columns = {
        'prefix': fields.related('sequence_id', 'prefix', type='char', size=64, string="Prefijo", required=True),
        'number_next_actual': fields.related('sequence_id', 'number_next_actual', type='integer', required=True, string="Numero Siguiente Factura"),
        'prefix2': fields.function(_get_cfdi_prefix, string='Prefijo', multi='cfdi', type='char', store=True, size=64),
        'cfdi': fields.function(_get_cfdi_prefix, string='Es CFDI', multi='cfdi', type='boolean', store=True)
    }
    
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
