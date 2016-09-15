# -*- coding: utf-8 -*-

######################################################################################################################################################
#  @version     : 1.0                                                                                                                                #
#  @autor       : Israel Cabera Juarez                                                                                                               #
#  @creacion    : 17/febrero/2015(aaaa/mm/dd)                                                                                                        #
#  @linea       : Maximo 150 chars                                                                                                                   #
######################################################################################################################################################
# ------MODIFICACION 18/04/2015---------
#   Agregacion de la funcion 'onchange_monto' en la clase 'canis.config'

#OpenERP imports
from osv import fields, osv
import time
import datetime
from datetime import date
import openerp.addons.decimal_precision as dp

#Modulo :: Vuelo
class canis_config(osv.osv):
    def _actualiza_ultimo_monto(self, cr, uid, context=None ):
        """
        Actualiza el campo ultimo_monto de todas las ordenes de compra
        a False, y pone el ultimo en True, para tomarlo como el ultimo monto
        """
        cr.execute('UPDATE canis_config SET ultimo_monto=False')
        return True
    
    def onchange_monto(self, cr, uid, ids, monto, context=None):
        """
            Coloca el nombre de manera automatica utilizando el monto
        """
        res = {
            'name': '',
            }
        if monto != 0.0:
            res['name'] = str(monto)
        return {'value': res}
    
    
    #Nombre del modelo
    _name = 'canis.config'
    # _rec_name = 'monto_maximo'

    _columns = {
        
        # =========================================  OpenERP Campos Basicos (integer, char, text, float, etc...)  ====================================== #
        'fecha_actualizacion': fields.date('Fecha'),
        'monto_maximo' : fields.float('Monto Permitido', digits_compute=dp.get_precision('Config'),
            required=True),
        'name' : fields.char('Monto Permitido', required=True),
        'ultimo_monto': fields.boolean('ultimo'),
        
    }
    
    #Valores por defecto de los campos del diccionario [_columns]
    _defaults = {
          'fecha_actualizacion': lambda *a: time.strftime('%Y-%m-%d'),
          'ultimo_monto': _actualiza_ultimo_monto,

    }
    #Restricciones de BD (constraints)
    _sql_constraints = [
    
    ]
    
   
    
    #Restricciones desde codigo
    _constraints = [ ]

canis_config()

