# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Author: Yannick Gouin <yannick.gouin@elico-corp.com>
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

from osv import osv, fields
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from openerp import netsvc
from openerp.tools.translate import _
from pytz import timezone

class delivery_priority(osv.osv):
    """
        Prioridades de entrega disponibles
    """
    _name = "delivery.priority"
    _description = "Delivery Priority"
    
    _columns = {
        'name': fields.char('Nombre', required=True, size=64),
        'value': fields.char('Valor', size=32)
    }
    
delivery_priority()
    
class delivery_term(osv.osv):
    """
        Plazos de entrega
    """
    _inherit = "delivery.term"
    _description = "Delivery Term"
    
    def get_week_next(self, cr, uid, num_week=1, context=None):
        """
            Obtiene el numero siguiente de la semana contando de 1-7
        """
        if num_week == 7:
            num_week = 1
        else:
            num_week += 1
        
        return num_week
    
    def get_date_next(self, cr, uid, date, value=0, unit='hours', context=None):
        """
            Valida dias inhabiles para calcular la fecha siguiente
        """
        config_obj = self.pool.get('delivery.config.settings')
        # Obtiene la configuracion de dias inhabiles sobre los dias de la semana
        config_week = config_obj.get_config_settings_week(cr, uid, context=context)
        hours_date = 24
        next_value = 0
        validate_hours = 0
        # Obtiene la zona horaria configurada
        tz_utc = pytz.utc
        tz = self.get_timezone(cr, uid, context=context)
        
        if unit != 'minutes':
            # Valida el dia de semana de la fecha actual
            datet = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
            if tz != 'UTC':
                datet = datet.astimezone(timezone(tz))
            num_week = datetime.isoweekday(datet)
            #print "*********** numero dia de la semana (actual) ********* ", num_week, ' - ', datet
            
            # Obtiene el total de dias en horas
            total_hours = value
            if unit == 'days':
                total_hours = total_hours * hours_date
            #print "********************** total horas *********** ", total_hours
            
            validate_week = 'week%s'%(num_week,)
            
            # Valida si hay dias inhabiles entre las entregas
            while validate_hours != total_hours:
                # Valida si es un dia inhabil el dia de la semana
                if config_week.get(validate_week,False) == False:
                    #print "************** dia inhabil ********* ", validate_week
                    # Dias inhabiles a recorrer
                    next_value += hours_date
                else:
                    # Si son menos de 24 horas agrega el tiempo sobre el dia de la entrega
                    if (total_hours - validate_hours) < hours_date:
                        #print "************* menor a 24 horas ****************** ", total_hours - validate_hours 
                        validate_hours = total_hours
                    else:
                        # Si es un dia habil descuenta 24 horas del tiempo de entrega
                        validate_hours += hours_date
                        #print "************** dia habil ********* ", validate_week
                    #print "************************ horas validadas ************ ", validate_hours
                # Recorre a la siguiente semana
                num_week = self.get_week_next(cr, uid, num_week, context=context)
                validate_week = 'week%s'%(num_week,)
            
            #print "************** horas dias inhabiles ********* ", next_value
            
            # Funcion original de obtener fecha
            res = super(delivery_term, self).get_date_next(cr, uid, date, value=(total_hours+next_value), unit='hours', context=context)
        else:
            # Funcion original de obtener fecha
            res = super(delivery_term, self).get_date_next(cr, uid, date, value=value, unit=unit, context=context)
        
        #print "************************ resultado fecha ************** ", res
        
        # Valida el dia de la fecha obtenida
        datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
        if tz != 'UTC':
            datet = datet.astimezone(timezone(tz))
        #datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc).astimezone(timezone(tz))
        num_week = datetime.isoweekday(datet)
        next_value = 0
        #print "*********** fecha formato Mexico ******************* ", datet
        #print "*********** numero dia de la semana ********* ", num_week
        
        validate_week = 'week%s'%(num_week,)
        
        # Valida si el dia de la entrega es un dia inhabil
        while config_week.get(validate_week,False) == False:
            #print "************** fec nueva dia inhabil ********* ", validate_week
            next_value += hours_date
            # Recorre a la siguiente semana
            num_week = self.get_week_next(cr, uid, num_week, context=context)
            validate_week = 'week%s'%(num_week,)
        #print "************** fec nueva dia habil ********* ", validate_week
        # Incrementa la fecha de entrega con los dias dela semana inhabiles
        if next_value > 0:
            #print "************** fec nueva - incrementar horas ********* ", next_value
            datet = datet + timedelta(hours=next_value)
        
        datet = datet.astimezone(tz_utc)
        res = datet.strftime('%Y-%m-%d %H:%M:%S')
        
        #print "********* Fecha final ************* ", res
        return res

delivery_term()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
