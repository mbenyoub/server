# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class requisition_credit_cancel_wizard(osv.osv_memory):
    """
        Solicita el motivo de la cancelacion de la factura
    """
    _name = "requisition.credit.cancel.wizard"
    
    _columns = {
        'requisition_id': fields.many2one('requisition.credit.credit', 'Solicitud', select=True, ondelete='cascade', required=True),
        'date': fields.date('Fecha de Cancelacion'),
        'type': fields.selection([
            ('cancel', 'Cancelar'),
            ('none', 'Anular'),
            ('reject', 'Rechazar'),
            ], string="Tipo de Cancelacion", required=True),
        'description': fields.text('Motivo', required=True)
    }
    
    _defaults = {
        'date': fields.datetime.now,
        'type': 'cancel',
    }
    
    def action_requisition_cancel(self, cr, uid, ids, context=None):
        """
            Cancela la solicitud de credito
        """
        if context is None:
            context = {}
        req_obj = self.pool.get('requisition.credit.credit')
        
        # Obtiene la informacion de la cancelacion de la solicitud
        data = self.browse(cr, uid, ids[0], context=context)
        req_id = data.requisition_id.id
        
        # Actualiza la informacion de la solicitud de credito
        req_obj.write(cr, uid, [req_id], {
            'state': data.type,
            'cancel_date': data.date,
            'cancel_description': data.description
        }, context=context)
        
        return True

requisition_credit_cancel_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
