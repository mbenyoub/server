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

from openerp.osv import fields, osv

class links_get(osv.Model):
    _name = "links.get.request"
    
    def _links_get(self, cr, uid, context=None):
        """
            Gets links value for reference field
        """
        obj = self.pool.get('res.request.link')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['object', 'name'], context)
        
        return [(r['object'], r['name']) for r in res]
    
    def validate_link(self, cr, uid, object, name, context=None):
        """
            Valida si el objeto referenciado existe
        """
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', object),])
        if not request_ids:
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': name, 'object': object, })
        return True

links_get()