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

from openerp.osv import fields,osv

class crm_case_section(osv.osv):
    """ Inherits partner to notify client"""
    _inherit = 'crm.case.section'

    _columns = {
        'notify_trade' : fields.integer(string='Dias notificacion Vendedor'),
        'notify_boss' : fields.integer(string='Dias notificacion jefe equipo'),
        'user_id': fields.many2one('res.users', 'Lider de Equipo', required=True),
    }
    
    _defaults = {
        'change_responsible' : True,
        'notify_trade' : 30,
        'notify_boss' : 30,
    }

crm_case_section()
