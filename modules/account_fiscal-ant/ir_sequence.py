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

class ir_sequence(osv.osv):
    """
        Agregar funcion para secuencias para poder decrementar el numero
    """
    _inherit='ir.sequence'
    
    def _last(self, cr, uid, seq_ids, context=None):
        """
            Actualiza el numero anterior de la secuencia
        """
        if not seq_ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        sequences = self.read(cr, uid, seq_ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            # Obtiene el numero anterior
            cr.execute("SELECT last_value FROM ir_sequence_%03d" % seq['id'])
            seq['number_last'] = cr.fetchone()
            # Actualiza el numero sobre la secuencia
            sql = "SELECT setval('ir_sequence_%03d',%d,false)" %(seq['id'], seq['number_last'][0])
            #print "******************** sql ************************ ", sql
            cr.execute(sql)
        else:
            cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            cr.execute("UPDATE ir_sequence SET number_next=number_next-number_increment WHERE id=%s ", (seq['id'],))
        d = self._interpolation_dict()
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_last'] + interpolated_suffix

    def last_by_id(self, cr, uid, sequence_id, context=None):
        """ Draw an interpolated string using the specified sequence."""
        self.check_access_rights(cr, uid, 'read')
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context) + [False]
        ids = self.search(cr, uid, ['&',('id','=', sequence_id),('company_id','in',company_ids)])
        return self._last(cr, uid, ids, context)

    def last_by_code(self, cr, uid, sequence_code, context=None):
        """ Draw an interpolated string using a sequence with the requested code.
            If several sequences with the correct code are available to the user
            (multi-company cases), the one from the user's current company will
            be used.

            :param dict context: context dictionary may contain a
                ``force_company`` key with the ID of the company to
                use instead of the user's current company for the
                sequence selection. A matching sequence for that
                specific company will get higher priority. 
        """
        self.check_access_rights(cr, uid, 'read')
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context) + [False]
        ids = self.search(cr, uid, ['&', ('code', '=', sequence_code), ('company_id', 'in', company_ids)])
        return self._last(cr, uid, ids, context)

ir_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
