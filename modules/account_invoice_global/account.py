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

from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
# ---------------------------------------------------------
# Account journal - Diarios contables
# ---------------------------------------------------------

class account_journal(osv.Model):
    """
        Modificacion series sobre creacion de diarios
    """
    _inherit='account.journal'
    
    _columns = {
        'note_sale': fields.boolean('Generar nota de venta', help="Maque esta opcion para que al momento de la facturacion con este diario se le de un trato de nota de venta en base a la gestion de las cuentas"),
        'paid_invoice_global': fields.boolean('Aplicacion de Nota de Venta sobre Factura Global')
    }
    
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
