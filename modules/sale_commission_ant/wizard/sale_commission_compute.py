#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas(joropeza@akkadian.com.mx)
#              Roberto Ivan Serrano Saldaña(riss_600@hotmail.com)
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

class sale_commission_compute_wizard(osv.osv_memory):
    _name = "sale.commission.compute"
    _description = "Compute commission"
    
    def _get_period_default(self, cr, uid, context=None):
        """
            Obtiene el periodo por default
        """
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids[0]
    
    _columns = {
        'period_id': fields.many2one('account.period', 'Periodo'),
        'type_commission': fields.selection([('invoiced', 'Facturado'), ('paid', 'Pagado')], 'Tipo de comisión'),

    }
    
    _defaults = {
        'period_id': _get_period_default,
        'type_commission': 'invoiced',
    }
    
    def action_redirect_invoice(self, cr, uid, comm_id, context=None):
        """
            Redirecciona a la comision creada
        """
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_commission', 'sale_commission_commission_form_view')
        return {
            'name':_("Comision"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'sale.commission.commission',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': comm_id
        }
    
    def action_compute_commission(self, cr, uid, ids, context=None):
        """
            Genera la nueva comision sobre el periodo seleccionado
        """
        comm_obj = self.pool.get('sale.commission.commission')
        cline_obj = self.pool.get('sale.commission.line')
        
        # Obtiene el periodo del wizard
        period_id = self.browse(cr, uid, ids[0], context=context).period_id.id or False
        # Obtiene la version para calcular la comision
        version_id = comm_obj.get_version(cr, uid, period_id, context=context)
        
        # Crea la nueva comision
        comm_id = comm_obj.create_commission(cr, uid, period_id, context=context)
        
        # Obtiene la lista de vendedores sobre los que se va a calcular la comision
        line_ids = cline_obj.search(cr, uid, [('commission_id','=', comm_id)], context=context)
        # Recorre las lineas de la comision
        for line in cline_obj.browse(cr, uid, line_ids, context=context):
            # Obtiene los objetivos del vendedor respecto a la línea de versiones
            comm_obj._get_commission_sale(cr, uid, version_id, line, period_id, context=context)
            
        # Actualiza la comision para que se apliquen los cambios
        cline_obj.write(cr, uid, line_ids, {}, context=context)
        comm_obj.write(cr, uid, [comm_id], {}, context=context)
        return self.action_redirect_invoice(cr, uid, comm_id, context=context)

sale_commission_compute_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
