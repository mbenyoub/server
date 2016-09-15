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
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
import xml.dom.minidom
import base64
from dateutil.relativedelta import relativedelta

import time
from datetime import datetime, timedelta
import pytz
from pytz import timezone

class upload_file_meeting(osv.osv_memory):
    _name = 'upload.file.meeting.wizard'
    _description = 'Valida XML Factura'
    
    def onchange_meeting(self, cr, uid, ids, meeting_id, context=None):
        """
            Valida si ya se agrego la reunion
        """
        file_obj = self.pool.get('project.phase.file.meeting')
        meeting_obj = self.pool.get('crm.meeting')
        if context is None:
            context={}
        res = False
        fname = ''
        if meeting_id:
            file_ids = file_obj.search(cr, uid, [('meeting_id','=',meeting_id or False)])
            if file_ids:
                res = True
            # Obtiene el nombre del archivo
            meeting = meeting_obj.browse(cr, uid, meeting_id, context=context)
            fname="%s-%s.pdf"%(meeting.name,meeting.project_id.code)
        
        return {'value': {'check_files': res, 'file_name': fname}}
    
    def get_week_next(self, cr, uid, num_week=1, context=None):
        """
            Obtiene el numero siguiente de la semana contando de 1-7
        """
        if num_week == 7:
            num_week = 1
        else:
            num_week += 1
        
        return num_week
    
    def get_timezone(self, cr, uid, context=None):
        """
            Obtiene la zona horaria del context o del usuario
        """
        if context is None:
            context = {}
        tz = 'UTC'
        if context.get('tz',False) != False:
            tz = context.get('tz','UTC')
        print "*********** context tz ************ ", context.get('tz','UTC')
        # Valida si el context trae el dato de la zona horaria
        if tz == 'UTC' or tz == False:
            zone = self.pool.get('res.users').browse(cr, uid, uid, context=context).tz
            # Valida que el usuario tenga una zona horaria
            if zone:
                tz = zone
            print "**************** get tz ************ ", tz
        return tz
    
    def get_date_next(self, cr, uid, date, value=0, unit='hours', context=None):
        """
            Obtiene la fecha siguiente en base a los parametros
        """
        res = date
        # Obtiene la zona horaria configurada
        tz_utc = pytz.utc
        tz = self.get_timezone(cr, uid, context=context)
        
        print "**************** tz **************** ", tz
        if not date:
            date = datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Inicializa la fecha
        datet = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
        if tz != 'UTC':
            datet = datet.astimezone(timezone(tz))
        print "************* datetime get date next ************** ", datet
        
        # Valida si se incrementa por horas
        if unit == 'hours':
            datet = datet + timedelta(hours=value)
        elif unit == 'days':
            datet = datet + timedelta(days=value)
        elif unit == 'minutes':
            datet = datet + timedelta(minutes=value)
        
        # Regresa la fecha al formato de UTC
        datet = datet.astimezone(tz_utc)
        res = datet.strftime('%Y-%m-%d %H:%M:%S')
        return res
    
    def get_config_week(self, cr, uid, context=None):
        """
            Configuracion base para dias trabajados en la semana
        """
        return {
            'week1': True,
            'week2': True,
            'week3': True,
            'week4': True,
            'week5': True,
            'week6': False,
            'week7': False,
        }
    
    def get_date_next_zone(self, cr, uid, date, value=0, unit='hours', context=None):
        """
            Valida dias inhabiles para calcular la fecha siguiente (Considera zona horaria)
        """
        config_obj = self.pool.get('delivery.config.settings')
        # Obtiene la configuracion de dias inhabiles sobre los dias de la semana
        config_week = self.get_config_week(cr, uid, context=context)
        hours_date = 24
        next_value = 0
        validate_hours = 0
        # Obtiene la zona horaria configurada
        tz_utc = pytz.utc
        tz = self.get_timezone(cr, uid, context=context)
        
        if unit != 'minutes':
            print "************** timezone *********** ", tz
            # Valida el dia de semana de la fecha actual
            datet = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
            if tz != 'UTC':
                 # Inicializa la fecha con la zona horaria
                datet = datet.astimezone(timezone(tz))
            print "************* datetime get date next ************** ", datet
            num_week = datetime.isoweekday(datet)
            
            # Obtiene el total de dias en horas
            total_hours = value
            if unit == 'days':
                total_hours = total_hours * hours_date
            print "********************** total horas *********** ", total_hours
            
            validate_week = 'week%s'%(num_week,)
            
            # Valida si hay dias inhabiles entre las entregas
            while validate_hours != total_hours:
                # Valida si es un dia inhabil el dia de la semana
                if config_week.get(validate_week,False) == False:
                    print "************** dia inhabil ********* ", validate_week
                    # Dias inhabiles a recorrer
                    next_value += hours_date
                else:
                    # Si son menos de 24 horas agrega el tiempo sobre el dia de la entrega
                    if (total_hours - validate_hours) < hours_date:
                        print "************* menor a 24 horas ****************** ", total_hours - validate_hours 
                        validate_hours = total_hours
                    else:
                        # Si es un dia habil descuenta 24 horas del tiempo de entrega
                        validate_hours += hours_date
                        print "************** dia habil ********* ", validate_week
                    print "************************ horas validadas ************ ", validate_hours
                # Recorre a la siguiente semana
                num_week = self.get_week_next(cr, uid, num_week, context=context)
                validate_week = 'week%s'%(num_week,)
            
            print "************** horas dias inhabiles ********* ", next_value
            
            # Funcion original de obtener fecha
            res = self.get_date_next(cr, uid, date, value=(total_hours+next_value), unit='hours', context=context)
        else:
            # Funcion original de obtener fecha
            res = self.get_date_next(cr, uid, date, value=value, unit=unit, context=context)
        
        print "************************ resultado fecha ************** ", res
        
        # Valida el dia de la fecha obtenida
        datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
        if tz != 'UTC':
            # Inicializa la fecha con la zona horaria
            datet = datet.astimezone(timezone(tz))
            
        #datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc).astimezone(timezone(tz))
        num_week = datetime.isoweekday(datet)
        next_value = 0
        print "*********** fecha formato Mexico ******************* ", datet
        print "*********** numero dia de la semana ********* ", num_week
        
        validate_week = 'week%s'%(num_week,)
        
        # Valida si el dia de la entrega es un dia inhabil
        while config_week.get(validate_week,False) == False:
            print "************** fec nueva dia inhabil ********* ", validate_week
            next_value += hours_date
            # Recorre a la siguiente semana
            num_week = self.get_week_next(cr, uid, num_week, context=context)
            validate_week = 'week%s'%(num_week,)
        print "************** fec nueva dia habil ********* ", validate_week
        # Incrementa la fecha de entrega con los dias dela semana inhabiles
        if next_value > 0:
            print "************** fec nueva - incrementar horas ********* ", next_value
            datet = datet + timedelta(hours=next_value)
        
        datet = datet.astimezone(tz_utc)
        res = datet.strftime('%Y-%m-%d %H:%M:%S')
        
        print "********* Fecha final ************* ", res
        return res

    def import_file(self, cr, uid, ids, context=None):
        """
            Sube el archivo para dar por completado el entregable
        """
        file_obj = self.pool.get('project.phase.file.meeting')
        meeting_obj = self.pool.get('crm.meeting')
        
        # Obtiene la fecha actual
        cur_date = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Obtiene la informacion del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)
        
        # Valida el tipo de usuario que esta queriendo subir el archivo
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.type_contact == 'emp':
            raise osv.except_osv(_('Error!'),_("No esta autorizado para agregar minutas sobre reuniones!"))
        # Valida que no hayan pasado 48 horas de la reunion
        if user.type_contact == 'con':
            # Obtiene la fecha de la reunion mas 48 horas
            date = self.get_date_next_zone(cr, uid, wizard.meeting_id.date, value=(52 + wizard.meeting_id.duration), unit='hours', context=context)
            print "************* valida fechas ********** ", cur_date, " > ", date
            # Valida que la fecha actual sea menor a la fecha limite
            if cur_date > date:
                raise osv.except_osv(_('Error!'),_("Se ha excedido el tiempo limite para la carga del archivo!"))
            
        # Elimina archivos ya adjuntados sobre el sistema
        file_ids = file_obj.search(cr, uid, [('meeting_id','=',wizard.meeting_id.id or False)])
        if file_ids:
            file_obj.unlink(cr, uid, file_ids)
        
        # Crea el nuevo registro
        file_id = file_obj.create(cr, uid, {
            'name': wizard.file_name,
            'file': wizard.file,
            'meeting_id': wizard.meeting_id.id or False,
            'phase_id': wizard.phase_id.id or False
        }, context=context)
        
        # Actualiza el archivo sobre la reunion
        meeting_obj.write(cr, uid, [wizard.meeting_id.id], {
            'file_name': wizard.file_name,
            'file': wizard.file,
        }, context=context)
        
        # Cierra la reunion 
        meeting_obj.meeting_done(cr, uid, [wizard.meeting_id.id or False], context=context)
        return True
    
    _columns = {
        'meeting_id': fields.many2one('crm.meeting', 'Reunion', readonly=True, select=1, ondelete='cascade'),
        'phase_id': fields.many2one('project.phase', 'Fase', readonly=True, select=1, ondelete='cascade'),
        'file_name': fields.char('Nombre Archivo'),
        'file': fields.binary('Archivo', required=True, help='Archivo a actualizar', filters="*.pdf"),
        'check_files': fields.boolean('Ya adjuntado'),
    }
    
    _defaults = {
        'file_name': 'minuta.pdf',
        'check_files': False
    }
    
upload_file_meeting()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
