# -*- coding: utf-8 -*-

######################################################################################################################################################
#  @version     : 1.0                                                                                                                                #
#  @autor       : ICJ                                                                                                                              #
#  @creacion    :11-03-2015 (aaaa/mm/dd)                                                                                                            #
#  @linea       : Maximo 150 chars                                                                                                                   #
######################################################################################################################################################

#OpenERP imports
#from openerp.osv import fields, osv
from openerp.osv import osv, fields
import time
import datetime
from datetime import date
# Class wizard_tonto(osv.memory):
class catalogo_bitacora_new(osv.osv) :
  _name='nueva.tabla'
  _columns={
        'name' : fields.char( 'Nombre del analisis', size = 254, required = True ),
        'fecha_analisis' : fields.date( 'Fecha', required = True ),
        'laboratorio' :fields.char( 'Laboratorio de verificación' ),
        'mov' : fields.many2one('stock.picking','Entrada', readonly=True),
        
        'proteina' : fields.float( 'Proteina Cruda', required = False, readonly = False),
        'liminf1':fields.float('Limite Inferior',required=False),
        'limsup1':fields.float('Limite Superior',required=False),
        'used1':fields.boolean('Requerido(?)',required=False),
        
        'proteina_sol' : fields.float( 'Proteina Soluble', required = False, readonly = False),
        'liminf2':fields.float('Limite Inferior',required=False),
        'limsup2':fields.float('Limite Superior',required=False),
        'used2':fields.boolean('Requerido(?) ',required=False),
        
        'grasa' : fields.float( 'Grasa Cruda', required = False, readonly = False ),
        'liminf3':fields.float('Limite Inferior',required=False),
        'limsup3':fields.float('Limite Superior',required=False),
        'used3':fields.boolean('Requerido(?)',required=False),
        
        'ceniza' : fields.float( 'Cenizas', required = False, readonly = False),
        'liminf4':fields.float('Limite Inferior',required=False),
        'limsup4':fields.float('Limite Superior',required=False),
        'used4':fields.boolean('Requerido(?)',required=False),
        
        'bvt' : fields.float( 'Bases Volatiles Totales (mg/kg)', required = False, readonly = False ),
        'liminf5':fields.float('Limite Inferior',required=False),
        'limsup5':fields.float('Limite Superior',required=False),
        'used5':fields.boolean('Requerido(?)',required=False),
        
        'aflatox' : fields.float( 'Aflatoxinas', required = False, readonly = False ),
        'liminf6':fields.float('Limite Inferior',required=False),
        'limsup6':fields.float('Limite Superior',required=False),
        'used6':fields.boolean('Requerido(?)',required=False),
        
        'humedad' : fields.float( 'Humedad', required = False, readonly = False ),
        'liminf7':fields.float('Limite Inferior',required=False),
        'limsup7':fields.float('Limite Superior',required=False),
        'used7':fields.boolean('Requerido(?)',required=False),
        
        'impurezas' : fields.float( 'Impurezas', required = False, readonly = False ),
        'liminf8':fields.float('Limite Inferior',required=False),
        'limsup8':fields.float('Limite Superior',required=False),
        'used8':fields.boolean('Requerido(?)',required=False),
        
        'agl' : fields.float( 'Acidos Grasos Libres', required = False, readonly = False ),
        'liminf9':fields.float('Limite Inferior',required=False),
        'limsup9':fields.float('Limite Superior',required=False),
        'used9':fields.boolean('Requerido(?)',required=False),
        
        'fibra' : fields.float( 'Fibra Cruda', readonly = False ),
        'liminf11':fields.float('Limite Inferior',required=False),
        'limsup11':fields.float('Limite Superior',required=False),
        'used11':fields.boolean('Requerido(?)',required=False),
        
        'peroxidos' : fields.float( 'Indice de peroxidos', readonly = False ),
        'liminf12':fields.float('Limite Inferior',required=False),
        'limsup12':fields.float('Limite Superior',required=False),
        'used12':fields.boolean('Requerido(?)',required=False),
        
        'bromato' : fields.float( 'Bromatologico Completo', readonly = False),
        'liminf13':fields.float('Limite Inferior',required=False),
        'limsup13':fields.float('Limite Superior',required=False),
        'used13':fields.boolean('Requerido(?)',required=False),
        
        'indi_putre' : fields.float( 'Indice de Putrefaccion ', required = False, readonly = False ),
        'liminf14':fields.float('Limite Inferior',required=False),
        'limsup14':fields.float('Limite Superior',required=False),
        'used14':fields.boolean('Requerido(?)',required=False),
        
        'calcio' : fields.float( 'Calcio', required = False, readonly = False ),
        'liminf15':fields.float('Limite Inferior',required=False),
        'limsup15':fields.float('Limite Superior',required=False),
        'used15':fields.boolean('Requerido(?)',required=False),
        
        'peso_es' : fields.float( 'Peso Especifico', required = False, readonly = False ),
        'liminf16':fields.float('Limite Inferior',required=False),
        'limsup16':fields.float('Limite Superior',required=False),
        'used16':fields.boolean('Requerido(?)',required=False),
        
        'grano_da' : fields.float( 'Grano Dañado', required = False, readonly = False ),
        'liminf17':fields.float('Limite Inferior',required=False),
        'limsup17':fields.float('Limite Superior',required=False),
        'used17':fields.boolean('Requerido(?)',required=False),
        
        'plaga' : fields.float( 'Plaga', required = False, readonly = False ),
        'liminf18':fields.float('Limite Inferior',required=False),
        'limsup18':fields.float('Limite Superior',required=False),
        'used18':fields.boolean('Requerido(?)',required=False),
        
        'temperatura' : fields.float( 'Temperatura', required = False, readonly = False ),
        'liminf19':fields.float('Limite Inferior',required=False),
        'limsup19':fields.float('Limite Superior',required=False),
        'used19':fields.boolean('Requerido(?)',required=False),
        
        'digest' : fields.float( 'Digestibilidad en Pepsina', required = False, readonly = False ),
        'liminf20':fields.float('Limite Inferior',required=False),
        'limsup20':fields.float('Limite Superior',required=False),
        'used20':fields.boolean('Requerido(?)',required=False),
        
        'act_ure' : fields.float( 'Actividad Ureasica', required = False, readonly = False ),
        'liminf21':fields.float('Limite Inferior',required=False),
        'limsup21':fields.float('Limite Superior',required=False),
        'used21':fields.boolean('Requerido(?)',required=False),
        
        'grasa_hidro' : fields.float( 'Grasa Hidrolisis acida', required = False, readonly = False ),
        'liminf22':fields.float('Limite Inferior',required=False),
        'limsup22':fields.float('Limite Superior',required=False),
        'used22':fields.boolean('Requerido(?)',required=False),
        
        'bacteri' : fields.float( 'Analisis Bacteriologico', required = False, readonly = False ),
        'liminf23':fields.float('Limite Inferior',required=False),
        'limsup23':fields.float('Limite Superior',required=False),
        'used23':fields.boolean('Requerido(?)',required=False),
        
        'taninos' : fields.float( 'Taninos', required = False, readonly = False ),
        'liminf24':fields.float('Limite Inferior',required=False),
        'limsup24':fields.float('Limite Superior',required=False),
        'used24':fields.boolean('Requerido(?)',required=False),
        
        'type': fields.selection([('config', 'Configuracion'), ('bitaco', 'Bitacora')],'Tipo de registro', required=True, select=True, readonly = True),

        
   }
  _defaults = {
          'fecha_analisis': lambda *a: time.strftime('%Y-%m-%d'),
          'type': 'bitaco',
    }
  def guardar(self, cr, uid, data, context=None):
            move_obj = self.pool.get('nueva.tabla')
            self.write(cr, uid, ids, {'state': 'step1',}, context=context)
  
catalogo_bitacora_new()


