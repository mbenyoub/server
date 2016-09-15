# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    code by Roberto Ivan Serrano Saldaña <riss_600@hotmail.com>
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

import base

import datetime
from lxml import etree
import math
import pytz
import re

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.tools.yaml_import import is_comment

class social_programs_direction(osv.osv):
    _description="Direcciones de programas sociales"
    _name = 'social.programs.direction'
    
    def onchange_state(self, cr, uid, ids, state_id, context=None):
        """
            Obtiene la informacion del pais en base a el estado seleccioando
        """
        if state_id:
            country_id = self.pool.get('res.country.state').browse(cr, uid, state_id, context).country_id.id
            return {'value':{'country_id':country_id}}
        return {}
    
    def onchange_settlement(self, cr, uid, ids, settlement_id, context=None):
        """
            Obtiene la informacion de ciudad, estado, pais, CP, etc... en base a la colonia seleccionada
        """
        if settlement_id:
            settlement = self.pool.get('social.programs.res.settlement').browse(cr, uid, settlement_id, context)
            if settlement.id:
                state = self.pool.get('res.country.state').browse(cr, uid, settlement.city_id.state_id.id, context)
                return {'value':{
                            'country_id': state.country_id.id,
                            'state_id': state.id,
                            'city_id': settlement.city_id.id,
                            'city': settlement.city_id.name,
                            'area_id': settlement.area_id.id,
                            'sector_id': settlement.sector_id.id,
                            'zip': settlement.zip}}
        return {}
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True, select=True),
        # Datos de ubicacion
        'state_id' : fields.many2one('res.country.state','Estado'),
        'country_id' : fields.related('state_id', 'country_id', type="many2one", relation="res.country", string="Country", store=True),
        'city_id': fields.many2one("social.programs.res.city", 'Ciudad'),
        'settlement_id': fields.many2one('social.programs.res.settlement', 'Colonia'),
        'area_id' : fields.related('settlement_id', 'area_id', type="many2one", relation="social.programs.res.area", string="Area", readonly=True),
        'sector_id' : fields.related('settlement_id', 'sector_id', type="many2one", relation="social.programs.res.sector", string="Sector", readonly=True),
        'street': fields.char('Calle', size=128),
        'zip': fields.char('C.P.', change_default=True, size=24),
        'email': fields.char('Email', size=240),
        'phone': fields.char('Phone', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Mobile', size=64),
        # Datos complemento
        'user_id': fields.many2one('res.users', 'Director', help='Encargado de la direccion.'),
        'comment': fields.text('Notas'),
        'active': fields.boolean('Active'),
        
    }
    _order = 'name'

class social_programs_category(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        """Return the categories' display name, including their direct
           parent by default.

        :param dict context: the ``partner_category_display`` key can be
                             used to select the short version of the
                             category name (without the direct parent),
                             when set to ``'short'``. The default is
                             the long version."""
        if context is None:
            context = {}
        if context.get('partner_category_display') == 'short':
            return super(res_partner_category, self).name_get(cr, uid, ids, context=context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1] + ' / ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _description = 'Programas Categorias'
    _name = 'social.programs.category'
    _columns = {
        'name': fields.char('Nombre de Categoria', required=True, size=64, translate=True),
        'parent_id': fields.many2one('social.programs.category', 'Categoria Padre', select=True, ondelete='cascade'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'child_ids': fields.one2many('social.programs.category', 'parent_id', 'Child Categories'),
        'active': fields.boolean('Active', help="El campo activo permite ocultar la categoria sin tener que eliminarla."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
        'program_ids': fields.many2many('social.programs.program', id1='category_id', id2='program_id', string='Programas'),
    }
    _constraints = [
        (osv.osv._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    
    _defaults = {
        'active': 1,
    }
    
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

class social_programs_program(osv.osv):
    _description="Programas sociales"
    _name = 'social.programs.program'
    
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Confirma el programa
        """
        print "************* funcion confirm ****************"
        # date = fields.date.context_today(self,cr,uid,context=context)
        self.write(cr, uid, ids, {'state':'confirm'}, context=context)
        
        delivery_obj = self.pool.get('social.programs.program.delivery')
        
        # Genera las entregas a beneficiarios
        for program in self.browse(cr, uid, ids, context=context):
            for product in program.products:
                for partner in program.partner_ids:
                    delivery_obj.create(cr, uid, {
                        'program_id': program.id,
                        'partner_id': partner.id,
                        'product_id': product.product_id.id,
                        'qty': product.qty,
                        'delivery':False}, context=context)
        return True
    
    _columns = {
        'name': fields.char('Nombre', size=128, required=True, select=True),
        'code': fields.char('Codigo', size=15, help='Codigo identificador del programa', required=True),
        'direction_id': fields.many2one('social.programs.direction', 'Direccion', required=True, select=True),
        'ref': fields.char('Reference', size=64, select=1),
        'parent_id': fields.many2one('social.programs.program', 'Programa Padre'),
        'user_id': fields.many2one('res.users', 'Responsable', help='Responsable del programa.'),
        'date_start': fields.date('Fecha', select=1),
        'date_end': fields.date('Date', select=1),
        'category_id': fields.many2many('social.programs.category', 'social_programs_rel_category', id1='partner_id', id2='category_id', string='Etiquetas'),
        'program_ids': fields.many2many('social.programs.program', 'social_programs_rel_program', 'program_parent_id', 'program_child_id', 'Programas relacionados'),
        'partner_ids': fields.many2many('res.partner', 'social_programs_rel_partners', 'program_ids', 'partner_ids', 'Beneficiarios', domain=[('beneficiary','=',True)]),
        'products': fields.one2many('social.programs.program.product.qty', 'program_id', 'Productos'),
        'state': fields.selection([
                    ('draft', 'Borrador'),
                    ('confirm', 'Confirmado'),
                    ('done', 'Terminado'),
                    ('cancel', 'Cancelado'),], 'Status', readonly=True, help="Indica el estado en el que se encuentra nuestro programa.", select=True),
        'description': fields.text('Descripcion', help='Descripcion del programa.'),
        'delivery_ids': fields.one2many('social.programs.program.delivery', 'program_id', 'Entregas', readonly=True),
    }
    _order = 'name'
    
    _defaults = {
        'state': 'draft',
    }

class social_programs_program_product_qty(osv.osv):
    _description="Programas sociales"
    _name = 'social.programs.program.product.qty'
    
    _columns = {
        'program_id': fields.many2one('social.programs.program', 'Programa', invisible=True),
        'product_id': fields.many2one('product.product', 'Producto', required=True),
        'qty': fields.float('Cantidad por beneficiario', required=True, select=True),
    }

class format_address(object):
    def fields_view_get_address(self, cr, uid, arch, context={}):
        user_obj = self.pool.get('res.users')
        fmt = user_obj.browse(cr, SUPERUSER_ID, uid, context).company_id.country_id
        fmt = fmt and fmt.address_format
        layouts = {
            '%(city)s %(state_code)s\n%(zip)s': """
                <div class="address_format">
                    <field name="city" placeholder="City" style="width: 50%%"/>
                    <field name="state_id" class="oe_no_button" placeholder="State" style="width: 47%%" options='{"no_open": true}'/>
                    <br/>
                    <field name="zip" placeholder="ZIP"/>
                </div>
            """,
            '%(zip)s %(city)s': """
                <div class="address_format">
                    <field name="zip" placeholder="ZIP" style="width: 40%%"/>
                    <field name="city" placeholder="City" style="width: 57%%"/>
                    <br/>
                    <field name="state_id" class="oe_no_button" placeholder="State" options='{"no_open": true}'/>
                </div>
            """,
            '%(city)s\n%(state_name)s\n%(zip)s': """
                <div class="address_format">
                    <field name="city" placeholder="City"/>
                    <field name="state_id" class="oe_no_button" placeholder="State" options='{"no_open": true}'/>
                    <field name="zip" placeholder="ZIP"/>
                </div>
            """
        }
        for k,v in layouts.items():
            if fmt and (k in fmt):
                doc = etree.fromstring(arch)
                for node in doc.xpath("//div[@class='address_format']"):
                    tree = etree.fromstring(v)
                    node.getparent().replace(node, tree)
                arch = etree.tostring(doc)
                break
        return arch

class social_programs_program_delivery(osv.osv, format_address):
    _description="Entrega Programas sociales"
    _name = 'social.programs.program.delivery'

    def action_delivery_product(self, cr, uid, ids, context=None):
        """
            Muestra una ventana con la informacion del documento a entregar
        """

        partner_id = self.browse(cr, uid, ids[0], context=context).partner_id.id

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'social_programs', 'view_social_programs_program_delivery_form')
        res_id = res and res[1] or False

        #~ Redirecciona al formulario de Entrega
        return {
            'name':"Entrega",
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'social.programs.program.delivery', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id' : ids[0], # id of the object to which to redirected
        }
    
    def action_delivery(self, cr, uid, ids, context=None):
        """
            Pone el documento como entregado
        """
        date = fields.date.context_today(self,cr,uid,context=context)
        self.write(cr, uid, ids, {'delivery':True, 'date': date}, context=context)
        print "*************** cambio de estado **************** "

        #~ Cierra la ventana
        return {'type': 'ir.actions.act_window_close'}
    
    def action_delivery_and_print(self, cr, uid, ids, context=None):
        """
            Entrega el documento e imprime el reporte
        """
        self.action_delivery(cr, uid, ids, context=context)
        res = self.action_print_report(cr, uid, ids, context=context)
        return res
    
    def action_print_report(self, cr, uid, ids, context=None):
        datas = {}
        if context is None:
            context = {}
        print "************** active_ids ************* ", context.get('active_ids',[])
            
        data = self.read(cr, uid, ids)[0]
        datas = {
             'ids': ids,
             'model': 'social.programs.program.delivery',
             'form': data
                 }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'report.social.programs.program.delivery.webkit',
            'datas': datas,
            }
    
    def onchange_delivery(self, cr, uid, ids, delivery, context=None):
        """
            Cierra la ventana si cambia el estado a entregado
        """
        if delivery == True:
            return {'type': 'ir.actions.act_window_close'}
        return True
    
    _columns = {
        'program_id': fields.many2one('social.programs.program', 'Programa', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Beneficiario', readonly=True),
        'product_id': fields.many2one('product.product', 'Producto', readonly=True),
        'qty': fields.float('Cantidad a entregar', readonly=True),
        'date': fields.date('Entregado', readonly=True),
        'delivery': fields.boolean('Entregado', readonly=True),
        # Campos relacionados con el beneficiario
        'name' : fields.related('partner_id', 'name', type="char", string="Nombre", readonly=True),
        'curp' : fields.related('partner_id', 'curp', type="char", string="curp", readonly=True),
        'image' : fields.related('partner_id', 'image', type="binary", string="Image", readonly=True),
        'image_medium' : fields.related('partner_id', 'image_medium', type="binary", string="Image medium", readonly=True),
        'category_id' : fields.many2many("res.partner.category", 'partner_id', 'category_id', string="Etiquetas", readonly=True),
        'street' : fields.related('partner_id', 'street', type="char", string="Calle", readonly=True),
        'settlement_id': fields.related('partner_id', 'settlement_id', type='many2one', relation='social.programs.res.settlement', string='Colonia', readonly=True),
        'city_id': fields.related('partner_id', 'city_id', type='many2one', relation='social.programs.res.city', string='Ciudad', readonly=True),
        'state_id': fields.related('partner_id', 'state_id', type='many2one', relation='res.country.state', string='Estado', readonly=True),
        'zip' : fields.related('partner_id', 'zip', type="char", string="C.P.", readonly=True),
        'sector_id': fields.related('partner_id', 'sector_id', type='many2one', relation='social.programs.res.sector', string='Sector', readonly=True),
        'area_id': fields.related('partner_id', 'area_id', type='many2one', relation='social.programs.res.area', string='Area', readonly=True),
        'country_id': fields.related('partner_id', 'country_id', type='many2one', relation='res.country', string='Estado', readonly=True),
        'phone' : fields.related('partner_id', 'phone', type="char", string="Telefono", readonly=True),
        'mobile' : fields.related('partner_id', 'mobile', type="char", string="Celular", readonly=True),
        'email' : fields.related('partner_id', 'email', type="char", string="Correo", readonly=True),
    }
    
    _defaults = {
        'delivery': False
    }
    
    _order = 'delivery,program_id,partner_id,product_id,qty'
