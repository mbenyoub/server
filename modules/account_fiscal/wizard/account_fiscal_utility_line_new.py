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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_fiscal_utility_line_new(osv.osv_memory):
    """ Actualizar perdida de forma manual """
    _name = 'account.fiscal.utility.line.new'
    _description = 'Nueva linea de perdida fiscal'
    
    def action_add_line_new(self, cr, uid, ids, context=None):
        """
            Agrega el codigo hijo al indice fiscal
        """
        line_obj = self.pool.get('account.fiscal.utility.line')
        
        # Recorre los registros
        for line in self.browse(cr, uid, ids, context=context):
            # Agrega el nuevo registro
            values = {
                'utility_id': line.utility_id.id,
                'remnant_before': line.remnant_before,
                'inpc_id1': line.inpc_id1.id,
                'inpc_id2': line.inpc_id2.id,
                'remnant_amortized': line.remnant_amortized,
                'fiscalyear_amortized': line.fiscalyear_amortized
            }
            line_id = line_obj.create(cr, uid, values, context=context)
        return True
        
    _columns = {
        'utility_id': fields.many2one('account.fiscal.utility', 'Perdida/Utilidad', ondelete='cascade', required=True),
        'remnant_before': fields.float('Remanente Anterior', digits=(16,4)),
        'inpc_id1': fields.many2one('account.fiscal.inpc', 'INPC anterior', select=True),
        'inpc_id2': fields.many2one('account.fiscal.inpc', 'INPC actual', select=True),
        'remnant_amortized': fields.float('Perdida amortizada (Utilidad)', digits=(16,4)),
        'fiscalyear_amortized': fields.integer('Ejercicio Fiscal amortizado', size=4),
    }

account_fiscal_utility_line_new()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
