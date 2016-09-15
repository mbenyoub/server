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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_asset_drop_wizard(osv.osv_memory):
    """
        Solicita el motivo de la baja del activo
    """
    _name = "account.asset.drop.wizard"

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Activo', select=True, ondelete='cascade', required=True),
        'date': fields.date('Fecha de Baja', required=True),
        'drop_ref': fields.text('Referencia de Cierre', required="1"),
        'select_qty': fields.boolean('Seleccionar cantidad'),
        'quantity': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'))
    }
    
    _defaults = {
        'date': fields.datetime.now,
        'quantity': 1,
        'select_qty': False
    }
    
    def action_asset_drop(self, cr, uid, ids, context=None):
        """
            Da de baja el activo
        """
        if context is None:
            context = {}
        
        asset_obj = self.pool.get('account.asset.asset')
        data = self.browse(cr, uid, ids, context=context)[0]
        context['date'] = data.date
        context['ref'] = data.drop_ref
        
        # Valida que la cantidad seleccionada no sea mayor a la disponible sobre el activo
        if data.asset_id.product_qty < data.quantity:
            raise osv.except_osv(_('Warning!'),_("La cantidad del activo %s, es mayor a la cantidad disponible (Disponible: %s)!"%(data.asset_id.name, data.asset_id.product_qty)))
        # Valida que el activo se encuentre en ejecucion
        if data.asset_id.state != 'open':
            if data.asset_id.state != 'close':
                raise osv.except_osv(_('Warning!'),_("Compruebe que el activo %s se encuentra disponible para darlo de baja (Estado actual: %s)!"%(data.asset_id.name, data.asset_id.state)))
        
        # Ejecuta funcion para dar de baja el activo
        asset_obj.create_move_drop(cr, uid, data.asset_id.id, data.quantity, context=context)
        return True

account_asset_drop_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
