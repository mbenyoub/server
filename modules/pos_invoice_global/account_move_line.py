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
#              Juan Manuel Oropeza (joropeza@akkadian.com.mx)
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


class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def _check_date(self, cr, uid, ids, context=None):
        """
            Valida la fecha de clausura que se encuentre dentro del periodo contable actual
        """
        return super(account_move_line, self)._check_date(cr, uid, ids, context=context)
        
    _constraints = [
        (_check_date, 'La fecha de clausura no se encuentra dentro del periodo actual para poder cerrar la sesion', ['date']),
    ]