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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
import xml.dom.minidom
import base64

class upload_file_task(osv.osv_memory):
    _name = 'upload.file.task.wizard'
    _description = 'Valida XML Factura'
    
    def onchange_file(self, cr, uid, ids, file_data, context=None):
        """
            Agrega al retorno el domain sobre las fases del proyecto y asigna la fase activa
        """
        if context is None:
            context={}
        res = {}
        
        print "**************** context *********** ", context
        return res
    
    def onchange_task(self, cr, uid, ids, task_id, context=None):
        """
            Valida si ya se agrego alguna tarea
        """
        file_obj = self.pool.get('project.phase.file.task')
        task_obj = self.pool.get('project.task')
        if context is None:
            context={}
        res = False
        fname = ''
        if task_id:
            file_ids = file_obj.search(cr, uid, [('task_id','=',task_id or False)])
            if file_ids:
                res = True
            # Obtiene el nombre del archivo
            task = task_obj.browse(cr, uid, task_id, context=context)
            fname="%s-%s.pdf"%(task.name,task.project_id.code)
        
        return {'value': {'check_files': res, 'file_name': fname}}
    
    def import_file(self, cr, uid, ids, context=None):
        """
            Sube el archivo para dar por completado el entregable
        """
        file_obj = self.pool.get('project.phase.file.task')
        task_obj = self.pool.get('project.task')
        log_eval_obj = self.pool.get('project.log.evaluation.task')
        
        # Obtiene la informacion del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)
        
        # Elimina archivos ya adjuntados sobre el sistema
        file_ids = file_obj.search(cr, uid, [('task_id','=',wizard.task_id.id or False)])
        if file_ids:
            file_obj.unlink(cr, uid, file_ids)
        
        # Crea el nuevo registro
        file_id = file_obj.create(cr, uid, {
            'file_name': wizard.file_name,
            'file': wizard.file,
            'task_id': wizard.task_id.id or False,
            'phase_id': wizard.phase_id.id or False
        }, context=context)
        
        # Da por finalizada la tarea
        task_obj.action_close(cr, uid, [wizard.task_id.id], context=context)
        
        # Actualiza el archivo sobre la tarea
        task_obj.write(cr, uid, [wizard.task_id.id], {
            'file_upload': True,
            'file_name': wizard.file_name,
            'file': wizard.file,
        }, context=context)
        
        # Registra sobre el entregable el avance al 100 porciento
        log_eval_obj.create(cr, uid, {
            'phase_id': wizard.phase_id.id or False,
            'user_id': uid,
            'project_id': wizard.phase_id.project_id.id or False,
            'task_id': wizard.task_id.id or False,
            'result': 100.00,
            'note': 'Tarea finalizada al cargar archivo entregable'
        }, context=context)
        
        return True
    
    _columns = {
        'task_id': fields.many2one('project.task', 'Entregable', readonly=True, select=1, ondelete='cascade'),
        'phase_id': fields.many2one('project.phase', 'Fase', readonly=True, select=1, ondelete='cascade'),
        'file_name': fields.char('Nombre Archivo'),
        'file': fields.binary('Archivo', required=True, help='Archivo a actualizar', filters="*.pdf"),
        'check_files': fields.boolean('Ya adjuntado')
    }
    
    _defaults = {
        'file_name': 'entregable.pdf',
        'check_files': False
    }
    
upload_file_task()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
