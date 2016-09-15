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
from openerp import pooler
from openerp.tools.translate import _

# Paletas de colores disponibles
colors = [
    (0,'Blanco'),
    (1,'Negro'),
    (2,'Rojo'),
    (3,'Amarillo'),
    (4,'Verde'),
    (5,'Esmeralda'),
    (6,'Cian'),
    (7,'Azul'),
    (8,'Morado'),
    (0,'Rosa'),
]

#class delivery_config_settings(osv.TransientModel):
class delivery_config_settings(osv.Model):
    _name = 'delivery.config.settings'
    _inherit = 'res.config.settings'
    _order = "id desc"
    
    def get_config_settings(self, cr, uid, context=None):
        """
            Obtiene la configuracion de los registros
        """
        config_id = False
        res = {
            'delivery_term_id': False,
            'color1': 0,
            'color2': 0,
            'color3': 0,
            'color4': 0,
            'color5': 0,
        }
        # Obtiene el ultimo registro generado sobre la configuracion
        cr.execute(
            """ select id as id
                from delivery_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        config_id = dat and dat[0]['id'] or False
        
        # Obtiene la informacion de los registros
        if config_id:
            config = self.browse(cr, uid, config_id, context=context)
            res['delivery_term_id'] =  config.delivery_term_id and config.delivery_term_id.id or False
            res['color1'] = config.color1 or 0
            res['color2'] = config.color2 or 0
            res['color3'] = config.color3 or 0
            res['color4'] = config.color4 or 0
            res['color5'] = config.color5 or 0
        return res
    
    def get_config_settings_week(self, cr, uid, context=None):
        """
            Obtiene la configuracion de los registros sobre dias habiles de la semana
        """
        res = {
            'week1': True,
            'week2': True,
            'week3': True,
            'week4': True,
            'week5': True,
            'week6': True,
            'week7': True,
        }
        # Obtiene el ultimo registro generado sobre la configuracion
        cr.execute(
            """ select id as id
                from delivery_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        config_id = dat and dat[0]['id'] or False
        
        # Obtiene la informacion de los registros
        if config_id:
            config = self.browse(cr, uid, config_id, context=context)
            res['week1'] = config.week1 or False
            res['week2'] = config.week2 or False
            res['week3'] = config.week3 or False
            res['week4'] = config.week4 or False
            res['week5'] = config.week5 or False
            res['week6'] = config.week6 or False
            res['week7'] = config.week7 or False
        
        val = False
        # Valida que haya al menos un dia habil
        for conf in res:
            #print "********** conf ******* ", conf
            if res.get(conf,False):
                val = True
                break
        # Si no hay dias habiles
        if val == False:
            raise osv.except_osv(_('Error!'),_("No hay dias habiles para las entregas, Contacte con el Administrador de Logistica!"))
        
        return res
    
    _columns = {
        'delivery_term_id': fields.many2one('delivery.term', 'Plazo base entrega', ondelete="restrict", help="Este plazo se utilizara para seccionar las fechas sobre los indicadores en las entregas de almacen"),
        'color1': fields.selection(colors, string="En tiempo (Color)", required=True),
        'color2': fields.selection(colors, string="Por Surtir (Color)", required=True),
        'color3': fields.selection(colors, string="Urgente (Color)", required=True),
        'color4': fields.selection(colors, string="Vencido (Color)", required=True),
        'color5': fields.selection(colors, string="Programado (Color)", required=True),
        # Dias habiles para entregas
        'week1': fields.boolean('Lun'),
        'week2': fields.boolean('Mar'),
        'week3': fields.boolean('Mie'),
        'week4': fields.boolean('Jue'),
        'week5': fields.boolean('Vie'),
        'week6': fields.boolean('Sab'),
        'week7': fields.boolean('Dom'),
    }
    
    def get_default_delivery_term_id(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del plazo de entrega
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg_id = self.browse(cr, uid, data).delivery_term_id
        return {'delivery_term_id': reg_id and reg_id.id or False}
    
    def get_default_color1(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).color1
        return {'color1': reg or False}
    
    def get_default_color2(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).color2
        return {'color2': reg or False}
    
    def get_default_color3(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).color3
        return {'color3': reg or False}
    
    def get_default_color4(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).color4
        return {'color4': reg or False}
    
    def get_default_color5(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).color5
        return {'color5': reg or False}
    
    def get_default_week1(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week1
        return {'week1': reg or False}
    
    def get_default_week2(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week2
        return {'week2': reg or False}
    
    def get_default_week3(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week3
        return {'week3': reg or False}
    
    def get_default_week4(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week4
        return {'week4': reg or False}
    
    def get_default_week5(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week5
        return {'week5': reg or False}
    
    def get_default_week6(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week6
        return {'week6': reg or False}
    
    def get_default_week7(self, cr, uid, fields, context=None):
        """
            Obtiene el valor por default del registro
        """
        reg_id = False
        cr.execute(
            """ select max(id) as conf_id from delivery_config_settings """)
        dat = cr.dictfetchall()
        data = dat and dat[0]['conf_id'] or False
        if data:
            reg = self.browse(cr, uid, data).week7
        return {'week7': reg or False}
    
delivery_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
