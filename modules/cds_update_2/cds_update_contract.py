# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from datetime import datetime

from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_analytic_account(osv.osv):
    _inherit ='account.analytic.account'
    _description = 'Update Analytic Account'
    _columns = {
        'visits': fields.integer('Visitas(Anuales)', help="Numero de visitas programadas en el periodo, mientras el contrato\n este vigente."),
        'visits_extra': fields.integer('Visitas Adicionales', help="Numero de visitas adicionales permitidas al cliente"),
        'request_time':fields.selection ((('1', '1 Hora'), ('2', '2 Horas'), ('3', '3 Horas'), ('4', '4 Horas'), ('5', '5 Horas'), ('6', '6 Horas')), 'Tiempo de Respuesta', help="Tiempo de respuesta minimo pactado con el cliente"),
        'attention_days':fields.selection ((('L-V', 'Lunes-Viernes'), ('L-S', 'Lunes-Sabado'), ('L-D', 'Lunes-Domingo')), 'Dias de Atencion'),
        'attention_timeset':fields.selection ((('office', 'Oficina (9:00-18:00)'), ('calendar', 'Calendario (24 Horas)')), 'Horario de Atencion'),
        'attention_time_limit':fields.selection ((('24', '24 Horas'), ('48', '48 Horas'), ('72', '72 Horas')), 'Tiempo limite de Atencion'),
        'discount_ref': fields.float('Descuento de Refacciones(%)', help='Descuento en porcentaje'),
        'discount_han': fields.float('Descuento de mano de Obra(%)'),
        'products_line': fields.one2many('products.order.line.helpdesk', 'product_line_id', 'Productos', readonly=True, states={'draft': [('readonly', False)],'open': [('readonly', False)]}),
        'supports': fields.one2many('crm.helpdesk','contracts','Soportes'),
        'reuniones': fields.one2many('crm.meeting', 'contracts_id', 'Reuniones programadas', readonly=True, states={'draft': [('readonly', False)],'open': [('readonly', False)]}),
    }
    
class sale_order_line(osv.osv):

    _name = 'products.order.line.helpdesk'
    _description = 'Products to Contract'
    _columns = {
        'product_line_id': fields.many2one('account.analytic.account', 'Contrato de referencia', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)]),
        'quantity': fields.integer('Cantidad de Productos')
        
    }

class partner(osv.osv):

    _inherit ='res.partner'
    _description = 'Partners to Contract'
    _columns = {
        'cantract': fields.one2many('account.analytic.account','partner_id', 'Contratos del cliente', readonly=True)
    }
