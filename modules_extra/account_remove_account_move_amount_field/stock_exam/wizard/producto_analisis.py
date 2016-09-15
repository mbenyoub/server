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
# Class wizard_tonto(osv.memory):
class producto_analisis( osv.osv ) :
  
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
  def get_analisis(self, cr, uid, ids, context=None):
        """ Obtiene la lista de analisis que se han echo a los productos"""
        product_id = self.browse(cr, uid, ids[0], context)['product_id']
        analisis_id = self.browse(cr, uid, ids[0], context)['catalogo_producto_m2o_id']
        picking_id = self.browse(cr, uid, ids[0], context)['picking_id']
        
        catalogo_product_obj = self.pool.get('catalogo.bitacora')
        catalogo_product_src = catalogo_product_obj.search(cr, uid, [('picking_id', '=', picking_id.id),('name', '=', product_id.name)])
        
        var = {
            'name': product_id.name,
            'analisis_id': analisis_id.id,
            'picking_id': picking_id.id,
        }
        
        if not catalogo_product_src:
            catalogo_product_obj.create(cr, uid, var, context)
        else:
            catalogo_product_get = catalogo_product_obj.browse(cr, uid, catalogo_product_src[0], context)['id']
            catalogo_product_obj.write(cr, uid, catalogo_product_get, var, context)
                 
        return True
        '''
        test_product = []
        vals = {}
            
                    
        catalogo_id = catalogo_product_obj.create(cr, uid, var, context=context)
        
        test_product.append(catalogo_id)
        
        stock_picking_srch = stock_picking_obj.search(cr, uid, [('id', '=', picking_id)])
        stock_picking_id = stock_picking_obj.browse(cr, uid, stock_picking_srch[0], context=context)['id']
        print "*****STOCK_PICKING_ID*****: ", stock_picking_id
        
        #for picking in stock_picking_obj.browse(cr, uid, stock_picking_srch, context=context):
        #    name = picking.name
        #    print "*****NAME*****: ", name
        vals['catalogo_bitacora_ids'] = (6, False, test_product)
        
        stock_picking_obj.write(cr, uid, stock_picking_id, vals, context=context)
        return True
        '''
  #---------------------------------------------------------------------------------------------------------------------------------------------------
  #def suma( self, cr, uid, ids, context = None ) :
  #  """
  #  Metodo que suma dos campos
  #  """
  #  x = self.browse( cr, uid, ids, context = context )
  #  z = 0
  #  for y in x:
  #    z = y.campo1 + y.campo2
  #  raise osv.except_osv( 'Resultado', z )
  #
  #def suma_total_precios_productos( self, cr, uid, ids, context = None ) :
  #  """
  #  Metodo que suma el total de los precios de todos los productos
  #  """
  #  cr.execute (
  #    """
  #    SELECT
  #      id
  #    FROM _cap_producto
  #    ORDER BY id
  #    """
  #  )
  #  registros = cr.fetchall()
  #  ids_todos = []
  #  if type( registros ) in ( list, tuple ) :
  #    if len( registros ) != 0 :
  #      for registro in registros :
  #        ids_todos.append( registro[0] )
  #  suma_total_precios = 0
  #  for r in self.pool.get( '_cap_producto' ).read( cr, uid, ids_todos, [ 'id', 'precio' ] ) :
  #    suma_total_precios = suma_total_precios + r[ 'precio' ]
  #  raise osv.except_osv( 'Total precios productos', suma_total_precios )
  #  
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
  
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  ###                                                                                                                                              ###
  ###                                                            Metodos OnChange                                                                  ###
  ###                                                                                                                                              ###
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  ###                                                                                                                                              ###
  ###                                                      Metodos para campos "function"                                                          ###
  ###                                                                                                                                              ###
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  def _get_entrada(self, cr, uid, ids, context=None ):
        result = {}
        try:
            for id in ids:
              cr.execute('SELECT id FROM stock_picking where id=70')
              entrada= cr.fetchone()[0]
            
        except Exception:
            return result
        return entrada
      
      
  def _get_analisis(self, cr, uid, context=None ):
        result = {}
        record_id = context and context.get('active_id', False) or False
        picking_obj = self.pool.get('stock.picking')
        picking = picking_obj.browse(cr, uid, record_id, context=context)
        print "****PICKING****: ", picking.id
        print "****MOVE__LINES****: ", picking.move_lines
        print "****jajajajajjaja****", picking.analisis
        #print "****CATALOGO_BITACORA_IDS****: ", picking.catalogo_bitacora_ids
     
        if picking.catalogo_bitacora_ids:
          for pick in picking.catalogo_bitacora_ids:
            product_id = pick.product_id.id or False
            print "*****PRODUCT_ID*****: ", product_id
          return True
        else:
          return False
        
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  ###                                                                                                                                              ###
  ###                                                  Atributos basicos de un modelo OPENERP                                                      ###
  ###                                                                                                                                              ###
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  
  # Nombre del modelo
  _name= 'producto.analisis'
  
  # Nombre de la tabla
  _table = 'producto_analisis'
  #Nombre de la descripcion al usuario en las relaciones m2o hacia este módulo

  #Clausula SQL "ORDER BY"

  _columns= {

    # =========================================  OpenERP Campos Basicos (integer, char, text, float, etc...)  ====================================== #
    'campo1' : fields.float( 'Primer número' ),
    'campo2' : fields.float( 'Segundo número' ),
   
    # ========================================================  Relaciones [many2one](m2o) ========================================================= #
    'stock_picking_in_id' : fields.many2one('stock.picking.in','Entrada de almacen'),
    # ========================================================  Relaciones [one2many](o2m) ========================================================= #
    'catalogo_bitacora_ids':fields.one2many('catalogo.bitacora', 'producto_analisis_id',
                                             'Analisis Realizados'),
                                              
     
     #'bitacoraa' :fields.many2one('catalogo.bitacora'),
    # ========================================================  Relaciones [many2many](m2m) ======================================================== #
    
    # ======================================================== Campos "function" (function) ======================================================== #
    
  }
  
  #Valores por defecto de los campos del diccionario [_columns]
  _defaults = {
    'campo1' : lambda self, cr, uid, context : 2.0,
    'campo2' : lambda self, cr, uid, context : 3.0,
    'stock_picking_in_id': _get_entrada,
    'catalogo_bitacora_ids':_get_analisis,
  }
  
  #Restricciones de BD (constraints)
  
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  ###                                                                                                                                              ###
  ###                                              Metodos para validacion de la lista: [_constraints]                                             ###
  ###                                                                                                                                              ###
  ### //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// ###
  
  #Restricciones desde codigo
  

producto_analisis()


