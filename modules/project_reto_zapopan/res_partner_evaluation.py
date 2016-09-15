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

from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

class res_partner_evaluation_category(osv.Model):
    _name = "res.partner.evaluation.category"
    
    _columns = {
        'name': fields.char('Nombre', required=True),
        'description': fields.text('Descripcion'),
    }
    
res_partner_evaluation_category()

class res_partner_evaluation_template(osv.Model):
    _name = "res.partner.evaluation.template"
    
    _columns = {
        'name': fields.char('Area', required=True),
        'category_id': fields.many2one('res.partner.evaluation.category', 'Categoria', ondelete="cascade", required=True),
        'priority': fields.integer('Secuencia'),
        'active': fields.boolean('Activo')
    }
    
    _order = 'category_id,priority'
    
    _defaults = {
        'active': True
    }
    
res_partner_evaluation_template()

class res_partner_evaluation_evaluation(osv.Model):
    _name = "res.partner.evaluation.evaluation"

    def action_redirect_partner(self, cr, uid, ids, context=None):
        """
            Redirecciona al formulario del consultor
        """
        # Obtiene el id del contacto a redireccionar
        partner_id = self.browse(cr, uid, ids[0], context=context).partner_id.id
        # Obtiene la vista formulario de contactos
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'project_reto_zapopan', 'res_partner_view_inherit')
        res_id = res and res[1] or False
        #~ Redirecciona al formulario de solicitud
        return {
            'name':_("Consultor"),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'res.partner.read', # object name
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id' : partner_id, # id of the object to which to redirected
        }
    
    def _get_date_string(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el valor de la fecha con texto
        """
        res = {}
        for log in self.browse(cr, uid, ids, context=context):
            res[log.id] = 'False'
            
            mes_texto = {
                '01': ' de Enero ',
                '02': ' de Febrero ',
                '03': ' de Marzo ',
                '04': ' de Abril ',
                '05': ' de Mayo ',
                '06': ' de Junio ',
                '07': ' de Julio ',
                '08': ' de Agosto ',
                '09': ' de Septiembre ',
                '10': ' de Octubre ',
                '11': ' de Noviembre ',
                '12': ' de Diciembre ',
            }
            
            if log.date:
                (anio, mes, dia) = log.date.split("-")
                res[log.id] = dia + mes_texto[mes] + anio
        return res
    
    def _get_user(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa el usuario activo
        """
        res = {}
        for id in ids:
            res[id] = uid
        return res
    
    def _get_date(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa la fecha actual
        """
        res = {}
        for id in ids:
            res[id] = time.strftime('%Y-%m-%d')
        return res
    
    _columns = {
        'name': fields.char('Area', required=True, readonly=True),
        'category_id': fields.many2one('res.partner.evaluation.category', 'Categoria', ondelete="set null", required=True, readonly=True),
        'notes': fields.text('Notas'),
        'experience': fields.integer('Años Experiencia', help="Indique años de experiencia (comprobable)"),
        'sector_ids': fields.many2many('project.sector', 'res_partner_evaluation_sector_rel', 'evaluation_id', 'sector_id', 'Sectores', help="Marque (X) el sector o contexto de mayor experiencia, en el area de consultoria. "),
        'partner_id': fields.many2one('res.partner', 'Consultor', ondelete="set null", required=True, readonly=True),
        'user_id': fields.function(_get_user, method=True, store=True, string='Evaluador', readonly=True, relation="res.users", type='many2one'),
        'date': fields.function(_get_date, method=True, store=True, string='Fecha', readonly=True, type='date'),
        'date_string': fields.function(_get_date_string, store=True, string='Fecha', readonly=True, type='char', size=40, help="Fecha."),
    }

res_partner_evaluation_evaluation()
