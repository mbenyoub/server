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

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler, tools
from openerp import netsvc
from openerp import release

class params_pac(osv.Model):
    _inherit = 'params.pac'

    def _get_method_type_selection(self, cr, uid, context=None):
        types = super(params_pac, self)._get_method_type_selection(
            cr, uid, context=context)
        types.extend([
            ('pac_sf_confirmar', _('PAC SF - RecibeCFD')),
        ])
        return types

    _columns = {
        'method_type': fields.selection(_get_method_type_selection,
            "Process to perform", type='char', size=64, required=True,
            help='Type of process to configure in this pac'),
    }
