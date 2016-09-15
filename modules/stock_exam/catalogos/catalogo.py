# -*- coding: utf-8 -*-

######################################################################################################################################################
#  @version     : 1.0                                                                                                                                #
#  @autor       : Israel Cabera Juarez                                                                                                               #
#  @creacion    : 17/febrero/2015(aaaa/mm/dd)                                                                                                        #
#  @linea       : Maximo 150 chars                                                                                                                   #
######################################################################################################################################################

#OpenERP imports
from osv import fields, osv
import time
import datetime
from datetime import date

#Modulo :: Vuelo
class catalogo_producto( osv.osv ) :

    ####################################################################################################################################################
    #                                                                                                                                                  #
    #                                         Variables Privadas y Publicas (No variables del API de OPENERP)                                          #
    #                                                                                                                                                  #
    ####################################################################################################################################################    
    
    ####################################################################################################################################################
    #                                                                                                                                                  #
    #                                                 Metodos Privados (No metodos del API de OPENERP)                                                 #
    #                                                                                                                                                  #
    ####################################################################################################################################################
    
    ####################################################################################################################################################
    #                                                                                                                                                  #
    #                                                 Metodos Publicos (No metodos del API de OPENERP)                                                 #
    #                                                                                                                                                  #
    ####################################################################################################################################################
    
    ####################################################################################################################################################
    #                                                                                                                                                  #
    #                                          Metodos OPENERP de Procesos Publicos (No metodos para reportes)                                         #
    #                                                                                                                                                  #
    ####################################################################################################################################################
    
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                                          OPENERP Metodos ORM                                                                 ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    #---------------------------------------------------------------------------------------------------------------------------------------------------
    

    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                                            Metodos OnChange                                                                 ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                                      Metodos para campos "function"                                                          ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                                  Atributos basicos de un modelo OPENERP                                                      ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    
    #Nombre del modelo
    _name = 'catalogo.producto'
    
    #Nombre de la tabla
    #_table = '_saas_catalogo_producto'
    
    #Nombre de la descripcion al usuario en las relaciones m2o hacia este módulo
    #_rec_name = 'nombre_analisis'
    
    #Cláusula SQL "ORDER BY"
    #_order = 'nombre_analisis DESC'

    #Columnas y/o campos Tree & Form
    #La relación [one2one](o2o) está obsoleta
    #En el nombre de los campos [many2one](m2o) el sufijo '_m2o_id' es requerido por normalización de código
    #En el nombre de los campos [one2many](o2m) el sufijo '_o2m' es requerido por normalización de código
    #En el nombre de los campos [many2many](m2m) el sufijo '_m2m' es requerido por normalización de código
    _columns = {
        
        # =========================================  OpenERP Campos Basicos (integer, char, text, float, etc...)  ====================================== #
        'name' : fields.char( 'Nombre del analisis', size = 254, required = True ),
        'fecha_analisis' : fields.date( 'Fecha' ),
        'laboratorio' :fields.char( 'Laboratorio de verificación' ),
        
        'proteina' : fields.float( 'Proteina Cruda', required = False, readonly = True),
        'liminf1':fields.float('Limite Inferior',required=False),
        'limsup1':fields.float('Limite Superior',required=False),
        'used1':fields.boolean('Requerido(?)',required=False),
        
        'proteina_sol' : fields.float( 'Proteina Soluble', required = False, readonly = True),
        'liminf2':fields.float('Limite Inferior',required=False),
        'limsup2':fields.float('Limite Superior',required=False),
        'used2':fields.boolean('Requerido(?) ',required=False),
        
        'grasa' : fields.float( 'Grasa Cruda', required = False, readonly = True ),
        'liminf3':fields.float('Limite Inferior',required=False),
        'limsup3':fields.float('Limite Superior',required=False),
        'used3':fields.boolean('Requerido(?)',required=False),
        
        'ceniza' : fields.float( 'Cenizas', required = False, readonly = True),
        'liminf4':fields.float('Limite Inferior',required=False),
        'limsup4':fields.float('Limite Superior',required=False),
        'used4':fields.boolean('Requerido(?)',required=False),
        
        'bvt' : fields.float( 'Bases Volatiles Totales (mg/kg)', required = False, readonly = True ),
        'liminf5':fields.float('Limite Inferior',required=False),
        'limsup5':fields.float('Limite Superior',required=False),
        'used5':fields.boolean('Requerido(?)',required=False),
        
        'aflatox' : fields.float( 'Aflatoxinas', required = False, readonly = True ),
        'liminf6':fields.float('Limite Inferior',required=False),
        'limsup6':fields.float('Limite Superior',required=False),
        'used6':fields.boolean('Requerido(?)',required=False),
        
        'humedad' : fields.float( 'Humedad', required = False, readonly = True ),
        'liminf7':fields.float('Limite Inferior',required=False),
        'limsup7':fields.float('Limite Superior',required=False),
        'used7':fields.boolean('Requerido(?)',required=False),
        
        'impurezas' : fields.float( 'Impurezas', required = False, readonly = True ),
        'liminf8':fields.float('Limite Inferior',required=False),
        'limsup8':fields.float('Limite Superior',required=False),
        'used8':fields.boolean('Requerido(?)',required=False),
        
        'agl' : fields.float( 'Acidos Grasos Libres', required = False, readonly = True ),
        'liminf9':fields.float('Limite Inferior',required=False),
        'limsup9':fields.float('Limite Superior',required=False),
        'used9':fields.boolean('Requerido(?)',required=False),
        
        'fibra' : fields.float( 'Fibra Cruda', readonly = True ),
        'liminf11':fields.float('Limite Inferior',required=False),
        'limsup11':fields.float('Limite Superior',required=False),
        'used11':fields.boolean('Requerido(?)',required=False),
        
        'peroxidos' : fields.float( 'Indice de peroxidos', readonly = True ),
        'liminf12':fields.float('Limite Inferior',required=False),
        'limsup12':fields.float('Limite Superior',required=False),
        'used12':fields.boolean('Requerido(?)',required=False),
        
        'bromato' : fields.float( 'Bromatologico Completo', readonly = True),
        'liminf13':fields.float('Limite Inferior',required=False),
        'limsup13':fields.float('Limite Superior',required=False),
        'used13':fields.boolean('Requerido(?)',required=False),
        
        'indi_putre' : fields.float( 'Indice de Putrefaccion ', required = False, readonly = True ),
        'liminf14':fields.float('Limite Inferior',required=False),
        'limsup14':fields.float('Limite Superior',required=False),
        'used14':fields.boolean('Requerido(?)',required=False),
        
        'calcio' : fields.float( 'Calcio', required = False, readonly = True ),
        'liminf15':fields.float('Limite Inferior',required=False),
        'limsup15':fields.float('Limite Superior',required=False),
        'used15':fields.boolean('Requerido(?)',required=False),
        
        'peso_es' : fields.float( 'Peso Especifico', required = False, readonly = True ),
        'liminf16':fields.float('Limite Inferior',required=False),
        'limsup16':fields.float('Limite Superior',required=False),
        'used16':fields.boolean('Requerido(?)',required=False),
        
        'grano_da' : fields.float( 'Grano Dañado', required = False, readonly = True ),
        'liminf17':fields.float('Limite Inferior',required=False),
        'limsup17':fields.float('Limite Superior',required=False),
        'used17':fields.boolean('Requerido(?)',required=False),
        
        'plaga' : fields.float( 'Plaga', required = False, readonly = True ),
        'liminf18':fields.float('Limite Inferior',required=False),
        'limsup18':fields.float('Limite Superior',required=False),
        'used18':fields.boolean('Requerido(?)',required=False),
        
        'temperatura' : fields.float( 'Temperatura', required = False, readonly = True ),
        'liminf19':fields.float('Limite Inferior',required=False),
        'limsup19':fields.float('Limite Superior',required=False),
        'used19':fields.boolean('Requerido(?)',required=False),
        
        'digest' : fields.float( 'Digestibilidad en Pepsina', required = False, readonly = True ),
        'liminf20':fields.float('Limite Inferior',required=False),
        'limsup20':fields.float('Limite Superior',required=False),
        'used20':fields.boolean('Requerido(?)',required=False),
        
        'act_ure' : fields.float( 'Actividad Ureasica', required = False, readonly = True ),
        'liminf21':fields.float('Limite Inferior',required=False),
        'limsup21':fields.float('Limite Superior',required=False),
        'used21':fields.boolean('Requerido(?)',required=False),
        
        'grasa_hidro' : fields.float( 'Grasa Hidrolisis acida', required = False, readonly = True ),
        'liminf22':fields.float('Limite Inferior',required=False),
        'limsup22':fields.float('Limite Superior',required=False),
        'used22':fields.boolean('Requerido(?)',required=False),
        
        'bacteri' : fields.float( 'Analisis Bacteriologico', required = False, readonly = True ),
        'liminf23':fields.float('Limite Inferior',required=False),
        'limsup23':fields.float('Limite Superior',required=False),
        'used23':fields.boolean('Requerido(?)',required=False),
        
        'taninos' : fields.float( 'Taninos', required = False, readonly = True ),
        'liminf24':fields.float('Limite Inferior',required=False),
        'limsup24':fields.float('Limite Superior',required=False),
        'used24':fields.boolean('Requerido(?)',required=False),
        
        
        'type': fields.selection([('config', 'Configuracion'), ('bitaco', 'Bitacora')],'Tipo de registro', required=True, select=True, readonly = True),
    }
    
    #Valores por defecto de los campos del diccionario [_columns]
    _defaults = {
          'fecha_analisis': lambda *a: time.strftime('%Y-%m-%d'),
          'type': 'config',
    }
    #Restricciones de BD (constraints)
    _sql_constraints = [
    
    ]
    
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                              Metodos para validacion de la lista: [_constraints]                                             ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    
    #Restricciones desde codigo
    _constraints = [ ]
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    ###                                                                                                                                              ###
    ###                                                            Metodos para reportes                                                             ###
    ###                                                                                                                                              ###
    ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
    


catalogo_producto()

