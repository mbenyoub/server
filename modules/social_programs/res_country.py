# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    code by Jorge Ivan Macias Olivares <ivanfallen@gmail.com>
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
import base

class City(osv.osv):
    _description="City"
    _name = 'social.programs.res.city'
    _columns = {
        'state_id' : fields.many2one('res.country.state','Estado',required=True),
        'country_id' : fields.related('state_id', 'country_id', type="many2one", relation="res.country", string="Country", store=False, readonly=True),
        'name': fields.char('Nombre de la Ciudad', size=64, required=True),
        'code': fields.char('Codigo de la Ciudad', size=3, help='El codigo solo puede tener 3 caracteres', required=True),
    }
    _order = 'name'

class Area(osv.osv) :
    _description="Area"
    _name = 'social.programs.res.area'
    _columns = {
        'name' : fields.char('Nombre del Área', size=64, required=True),
        'code' : fields.char('Codigo del Área', size = 3, help='El codigo solo puede tener 3 caracteres', required=True),
        'city_id' : fields.many2one('social.programs.res.city','Ciudad',required=True),
    }
    _order = 'name'
    
class Sector(osv.osv) :
    _description="Sector"
    _name = 'social.programs.res.sector'
    _columns = {
        'name' : fields.char('Nombre del Sector', size=64, required=True),
        'code' : fields.char('Codigo del Sector', size = 3, help='El codigo solo puede tener 3 caracteres', required=True),
    }
    _order = 'name'

class Settlement(osv.osv) :
    _description="Settlement"
    _name = 'social.programs.res.settlement'
    _columns = {
        'area_id' : fields.many2one('social.programs.res.area','Area', required=True),
        'city_id' : fields.related('area_id', 'city_id', type="many2one", relation="social.programs.res.city", string="Ciudad", store=False, readonly=True),
        'sector_id' : fields.many2one('social.programs.res.sector','Sector',required=True),
        'name' : fields.char('Nombre de la Colonia', size=64, required=True),
        'code' : fields.char('Codigo de la Colonia', size = 3, help='The settlement code in max. three chars.', required=True),
        'zip' : fields.char('C.P.', size = 5),
    }
    _order = 'name'
