# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _

import time

class planning_project_phonecall2phonecall(osv.osv_memory):
    _name = 'planning.project.phonecall2phonecall'
    _description = 'Phonecall To Phonecall project'

    _columns = {
        'name' : fields.char('Resumen de Llamada', size=64, required=True, select=1),
        'user_id' : fields.many2one('res.users','Asignar a', select="1", help='Quien atiende la llamda'),
        'contact_name':fields.char('Nombre contacto', size=64),
        'phone':fields.char('Telefono', size=64),
        'categ_id': fields.many2one('crm.case.categ', 'Categoria', \
                domain="[('object_id.model', '=', 'crm.phonecall')]"), 
        'date': fields.datetime('Fecha Prevista'),
        'action': fields.selection([('schedule','Planificar llamada'), ('log','Registrar llamada')], 'Acción', required=True),
        'partner_id' : fields.many2one('res.partner', "Contacto", select="1", help='Con quien se comunica'),
        'duration': fields.float('Duracion', help="Duracion en Minutos"),
        'note':fields.text('Nota'),
    }

    _defaults = {
        'date': fields.datetime.now,
    }

    def action_cancel(self, cr, uid, ids, context=None):
        """
        Closes Phonecall to Phonecall form
        """
        return {'type':'ir.actions.act_window_close'}

    def redirect_planning_project_phonecall_view(self, cr, uid, phonecall_id, context=None):
        model_data = self.pool.get('ir.model.data')
        # Select the view
        tree_view = model_data.get_object_reference(cr, uid, 'planning_project', 'planning_project_crm_case_phone_tree_view')
        form_view = model_data.get_object_reference(cr, uid, 'planning_project', 'planning_project_crm_case_phone_form_view')
        search_view = model_data.get_object_reference(cr, uid, 'planning_project', 'view_planning_project_crm_case_phonecalls_filter')

        #print "******************** view redirect **************** ", tree_view, form_view, search_view
        
        value = {
                'name': _('Phone Call'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'crm.phonecall',
                'res_id' : int(phonecall_id),
                'views': [(form_view and form_view[1] or False, 'form'), (tree_view and tree_view[1] or False, 'tree'), (False, 'calendar')],
                'type': 'ir.actions.act_window',
                'search_view_id': search_view and search_view[1] or False,
        }

        #print "************** valores *********************** ", value
        return value

    def action_log_call(self, cr, uid, ids, context=None):
        """
            Registra una nueva llamada telefonica para proyectos
        """
        phonecall_obj = self.pool.get('crm.phonecall')
        #print "****************************** context ******************** ", context

        #~ Recorre el registro de las llamadas
        for phonecall in self.browse(cr, uid, ids, context=context):
            #~ Genera un nuevo arreglo con la informacion de la llamada
            vals = {
                'name': phonecall.name,
                'date': phonecall.date,
                'user_id': phonecall.user_id.id,
                'partner_id': phonecall.partner_id.id,
                'duration': phonecall.duration,
                'state': context['state'],
                'is_project': True,
            }

            if phonecall.action == 'log':
                vals['date'] = fields.date.context_today(self,cr,uid,context=context)
            else:
                vals['duration'] = 0.0
            #print "************ llamada *************** ", vals

            #~ Registra la nueva llamda
            phonecall_id = phonecall_obj.create(cr, uid, vals, context=context)
            #print "**************** id llamda ************** ", phonecall_id
        return self.redirect_planning_project_phonecall_view(cr, uid, phonecall_id, context=context)

    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        
        """
        res = super(planning_project_phonecall2phonecall, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        res.update({'action': 'schedule', 'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        if record_id:
            phonecall = self.pool.get('crm.phonecall').browse(cr, uid, record_id, context=context)

            categ_id = False
            data_obj = self.pool.get('ir.model.data')
            res_id = data_obj._get_id(cr, uid, 'crm', 'categ_phone2')
            if res_id:
                categ_id = data_obj.browse(cr, uid, res_id, context=context).res_id

            if 'name' in fields:
                res.update({'name': phonecall.name})
            if 'user_id' in fields:
                res.update({'user_id': phonecall.user_id and phonecall.user_id.id or False})
            if 'date' in fields:
                res.update({'date': False})
            if 'section_id' in fields:
                res.update({'section_id': phonecall.section_id and phonecall.section_id.id or False})
            if 'categ_id' in fields:
                res.update({'categ_id': categ_id})
            if 'partner_id' in fields:
                res.update({'partner_id': phonecall.partner_id and phonecall.partner_id.id or False})
        return res

planning_project_phonecall2phonecall()
