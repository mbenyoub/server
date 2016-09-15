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

class sale_order(osv.Model):
    _inherit='sale.order'
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """
            Agrega a la informacion de la factura la tienda de la que proviene la factura
        """
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['shop_id'] = order.shop_id.id
        invoice_vals['journal_id'] = order.shop_id.journal_id.id
        return invoice_vals
    
sale_order()

class sale_shop(osv.Model):
    _inherit='sale.shop'
    
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Diario de ventas', select=1, ondelete='restrict'),
        'prefix': fields.related('journal_id', 'prefix', type='char', size=64, string="Serie"),
        'prefix2': fields.related('journal_id', 'prefix2', type='char', size=64, string="Serie"),
        'cfdi': fields.related('journal_id', 'cfdi', type='boolean', string="Es CFDI"),
        'number_next_actual': fields.related('journal_id', 'number_next_actual', type='integer', required=True, string="Numero Siguiente Factura"),
        'check_journal': fields.boolean('Diario obligatorio')
    }
    
    _defaults = {
        'number_next_actual': 1,
        'check_journal': False,
        'cfdi': False
    }
    
    def create(self, cr, uid, vals, context=None):
        """
            Crea un nuevo diario para la tienda
        """
        #print"*************** vals ******************* ", vals
        seq_obj = self.pool.get('ir.sequence')
        journal_obj = self.pool.get('account.journal')
        obj_seq = self.pool.get('ir.sequence')
        
        if vals is None:
            vals = {}
        
        # Valida que la tienda tenga seleccionado un diario, de no ser asi lo crea
        if not vals.get('journal_id',False):
            # Obtiene el id de la compañia
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            # Obtiene el numero de la tienda a crear
            number = seq_obj.next_by_code(cr, uid, 'sale.shop.journal', context=context)
            # Obtiene el id de la moneda Pesos
            currency_id = self.pool.get('res.currency').search(cr, uid, [('name','=','MXN'),])[0]
            
            # Crea la secuencia del diario
            seq_id = seq_obj.create(cr, uid, {
                'company_id': company.id,
                'name': 'Sequence CFD-I Suc %s'%(number,),
                'active': True,
                'padding': 0,
                'number_next_actual': vals['number_next_actual'],
                'number_next': vals['number_next_actual'],
                'number_increment': 1,
                'implementation': 'standard'}, context=context)
            # Crea la secuencia de aprovacion para el cfdi
            seq_ap_id = self.pool.get('ir.sequence.approval').create(cr, uid, {
                'company_id': company.id,
                'sequence_id': seq_id,
                'approval_number': 12345,
                'serie': vals['prefix'],
                'approval_year': time.strftime('%Y'),
                'number_start': 1,
                'number_end': 9999,
                'type': 'cfdi32'}, context=context)
            # Crea el nuevo diario
            journal_id = journal_obj.create(cr, uid, {
                'company_id': company.id,
                'sequence_id': seq_id,
                'name': 'Diario de CFD-I SF Suc %s'%(number,),
                'code': 'FE-%s'%(number,),
                'type': 'sale',
                'user_id': uid,
                'prefix2': vals.get('prefix',''),
                'company2_id': company.partner_id.id,
                'address_invoice_company_id': company.partner_id.id,
                'update_posted': True,
                'currency': currency_id
                }, context=context)
            
            # Agrega a los valores a generar en la base
            vals['journal_id'] = journal_id
        else:
            prefix = shop.prefix or ''
            journal_obj.write(cr, uid, [shop.journal_id.id], {'prefix2':prefix}, context=context)
        vals['check_journal'] = True
        
        # Funcion original de crear
        res = super(sale_shop, self).create(cr, uid, vals, context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza la serie del diario
        """
        # Funcion original de modificar
        super(sale_shop, self).write(cr, uid, ids, vals, context=context)
        journal_obj = self.pool.get('account.journal')
        
        # Actualiza la actividad de los partners
        for shop in self.browse(cr, uid, ids, context=context):
            prefix = shop.prefix or ''
            journal_obj.write(cr, uid, [shop.journal_id.id], {'prefix2':prefix}, context=context)
        return True
    
    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        """
            Obtiene la serie del diario y el valor si es cfdi o no
        """
        if not journal_id:
            return {'value':{'prefix': '', 'prefix2':'', 'cfdi':False}}
        journal_obj = self.pool.get('account.journal')
        journal = journal_obj.browse(cr, uid, journal_id, context=context)
        return {'value':{'prefix': journal.prefix or '', 'prefix2': journal.prefix2 or '', 'cfdi': journal.cfdi or False}}
    
sale_shop()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
