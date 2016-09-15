# -*- coding: utf-8 -*-

######################################################################################################################################################
#  @version     : 1.0                                                                                                                                #
#  @autor       : ICJ                                                                                                                              #
#  @creacion    :25-03-2015 (aaaa/mm/dd)                                                                                                            #
#  @linea       : Maximo 150 chars                                                                                                                   #
######################################################################################################################################################
# ---------MODIFICACION 18/04/2015----------
#   Modificacion en la funcion 'onchange_actualiza_monto', se realiza una validacion en caso de recibir
#     un valor 'null' de la variable 'config_id'

#OpenERP imports
#from openerp.osv import fields, osv
from openerp.osv import osv, fields

class canis_configuracion( osv.osv ) :
  
  
  def insertar_configuracion(self, cr, uid, ids, context=None ):
        """
        Actualiza la configuracion de el monto permitido ques de puede
        hacer en un pedido de compra
        """
        return True
  
  def _get_name_config(self, cr, uid, context=None ):
        """
            Obtiene el ultimo prefijo registrado en la configuracion
        """
        # Obtiene el ultimo de 'name' registrado
        cr.execute('SELECT name FROM mrp_lot_config_settings order by id desc')
        return cr.fetchone()[0]
    
  def _get_config_id(self, cr, uid, context=None ):
      """
          Obtiene la ultima referencia interna registrada para la configuracion
      """
      # Obtiene el ultimo valor de 'ref' registrado
      cr.execute('SELECT config_id FROM canis_configuracion order by id desc')
      return cr.fetchone()[0] or iuds
      
  def _actualiza_ultimo_monto(self, cr, uid, context=None ):
        """
        Actualiza el campo ultimo_monto de todas las ordenes de compra
        a False, y pone el ultimo en True, para tomarlo como el ultimo monto
        """
        cr.execute('UPDATE canis_config SET ultimo_monto=False')
        return True
  
  def onchange_actualiza_monto( self, cr, uid, ids, config_id) :
      """
      Actualiza el ultimo monto creado o guardado como el activo.
      """
      # try:
        
      if config_id :
            cr.execute('''UPDATE canis_config 
                          SET ultimo_monto = True 
                          WHERE id=%s''',(config_id,))
            return	{
                'value' :	{},
           }
      if config_id == False or config_id == '' or config_id==None:
        return	{
            'value': {'config_id': 0},
              }
  
  # Nombre del modelo
  _name= 'canis.configuracion'
  _inherit = 'res.config.settings'
  _order = 'id desc'
  

  _columns= {

    # =========================================  OpenERP Campos Basicos (integer, char, text, float, etc...)  ====================================== #
    'config_id' : fields.many2one( 'canis.config', 'Monto Permitido', required=True),
    'ultimo_monto': fields.boolean('ultimo'),
    # 'ultimo_monto_aux': fields.char('SI NO', size=254),
    
    
  }
  
  #Valores por defecto de los campos del diccionario [_columns]
  _defaults = {
             'ultimo_monto': _actualiza_ultimo_monto,
             'config_id': _get_config_id,
                }
  

canis_configuracion()


