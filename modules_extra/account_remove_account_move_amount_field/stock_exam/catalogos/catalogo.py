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
        'name' : fields.char( 'Nombre del analisis', size = 254, required = False ),
        'fecha_analisis' : fields.date( 'Fecha' ),
        'laboratorio' :fields.char( 'Laboratorio de verificación' ),
        'ingrediente' :fields.char( 'ingrediente' ),
        'proveedor' :fields.char( 'proveedor' ),
        'c_proteina' : fields.char( ' PROTEINA ', size = 254, required = False ),
        'proteina' : fields.float( 'PROTEINA', required = False ),
        
        'c_grasa' : fields.char( ' GRASA ', size = 254, required = False ),
        'grasa' : fields.float( 'GRASA', required = False ),
        
        'c_ceniza' : fields.char( ' CENIZA ', size = 254, required = False ),
        'ceniza' : fields.float( 'CENIZA', required = False ),
        
        'c_bvt' : fields.char( ' BVT (mg N/100 g ', size = 254, required = False ),
        'bvt' : fields.float( 'BVT (mg N/100 g', required = False ),
        
        'c_aflotox' : fields.char( ' AFLATOX ', size = 254, required = False ),
        'aflotox' : fields.float( 'AFLATOX', required = False ),
        
        'c_humedad' : fields.char( ' HUMEDAD ', size = 254, required = False ),
        'humedad' : fields.float( 'HUMEDAD', required = False ),
        
        'c_ip' : fields.char( ' IP ', size = 254, required = False ),
        'ip' : fields.float( 'IP', required = False ),
        
        'c_agl' : fields.char( ' AGL ', size = 254, required = False ),
        'agl' : fields.float( 'AGL', required = False ),
        
        'c_acidez' : fields.char( ' ACIDEZ ', size = 254, required = False ),
        'acidez' : fields.float( 'ACIDEZ', required = False),
        'size_muestra' : fields.char( 'Tamaño de la muestra', size = 254 ),
        
        # ========================================================  Relaciones [many2one](m2o) ========================================================= 
        'stock_picking_in_m2o_id':fields.many2one('stock.picking.in', '' ),
        'producto_m2o_id':fields.many2one( 'product.product' ,'Producto' ),
        'catalogo_m2o_id':fields.many2one('catalogo.producto', 'Analisis')
        # ========================================================  Relaciones [one2many](o2m) ========================================================= #

        # ========================================================  Relaciones [many2many](m2m) ======================================================== #
        
        # ======================================================== Campos "function" (function) ======================================================== #
        
    }
    
    #Valores por defecto de los campos del diccionario [_columns]
    _defaults = {
          'fecha_analisis': lambda *a: time.strftime('%Y-%m-%d'),
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

