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

from osv import osv, fields
from tools.translate import _

class account_journal(osv.osv):
    _inherit = 'account.journal'
    
    _columns = {
        'have_partner': fields.boolean('Contacto Requerido en Traspasos', help="Solicitar como obligatorio el contacto cuando se apliquen traspasos sobre el diario"),
        'account_transit': fields.many2one('account.account','Cuentra transferencias',help="Cuenta utilizada para la transferencia de efectivo entre bancos"),
    }
    
    _defaults = {
        'have_partner' : False,
    }
    
account_journal()

class account_move(osv.osv):
    _inherit = 'account.move'
    
    _document_type = {
        'sale': 'Sales Receipt',
        'purchase': 'Purchase Receipt',
        'payment': 'Supplier Payment',
        'receipt': 'Customer Payment',
        'transfer': 'Money Transfer',
        'expense': 'Egreso',
        'income': 'Ingreso',
        'out_invoice': 'Factura cliente',
        'in_invoice': 'Facura proveedor',
        False: 'journal',
    }
    
    _columns = {
        'journal_id_transfer': fields.many2one('account.journal','Diario Transferencia', readonly=True, domain=[('type','in',['cash','bank'])], ondelete="restrict"),
        'type':fields.selection([
                             ('sale','Venta'),
                             ('purchase','Compra'),
                             ('payment','Pago'),
                             ('receipt','Cobro'),
                             ('journal','Diario'),
                             ('expense','Egreso'),
                             ('income','Ingreso'),
                             ('out_invoice','Factura cliente'),
                             ('in_invoice','Factura proveedor'),
                             ('transfer','Transferencia'),
                             ],'Tipo', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    _defaults = {
        'type': 'journal'
    }
    
account_move()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def _get_journal(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el diario que aplica segun el movimiento
        """
        
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            #print "************ tipo movimiento ******************** ", line.move_id.journal_id, " **** ", line.move_id.type
            #print "************* diario traspaso ************* ", line.move_id.journal_id_transfer.account_transit
            
            res[line.id] = line.move_id.journal_id.id
            # Valida si es un movimiento de transferencia
            if line.move_id.type == 'transfer':
                # Valida si la cuenta del movimiento es igual a la que se aplica en la del diario de la transferencia
                if line.move_id.journal_id_transfer.account_transit:
                    if line.move_id.journal_id_transfer.account_transit.id == line.account_id.id:
                        res[line.id] = line.move_id.journal_id_transfer.id
        return res
    
    _columns = {
        'move_type':fields.related('move_id', 'type', type='selection', selection=[
                             ('sale','Venta'),
                             ('purchase','Compra'),
                             ('payment','Pago'),
                             ('receipt','Cobro'),
                             ('journal','Diario'),
                             ('transfer','Transferencia'),
                             ], string="Tipo", store=True),
        'journal_id':fields.function(_get_journal, type='many2one', relation="account.journal", string="Diario Transferencia", store=True),
        'type':fields.char('Tipo movimiento'),
    }
    
    _defaults = {
        'type': 'journal'
    }
    
account_move_line()

