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
from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_users(osv.osv):
    """ Inherits partner and add extra information kober """
    _inherit = 'res.users'
    
    _columns = {
        'branch_id': fields.many2one('crm.access.branch', 'Mi Sucursal'),
        'branch_ids': fields.many2many('crm.access.branch', 'user_branch_rel', 'user_id', 'branch_id', 'Acceso a sucursales'),
    }
    
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
