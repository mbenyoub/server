############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
from openerp.osv import osv, fields
from openerp import pooler
from openerp.tools.translate import _

class mrp_lot_config_settings(osv.Model):
    _name = 'mrp.lot.config.settings'
    _inherit = 'res.config.settings'
    _order = 'id desc'
    
        
    def get_config_lot(self, cr, uid, context=None):
        """
            Obtiene la configuracion de lote de produccion
        """
        res = {
            'name': '',
            'ref': '',
        }
        
        # Obteniendo el registro de la ultima configuracion
        cr.execute("""
                   SELECT
                        id
                    FROM
                        mrp_lot_config_settings
                    ORDER BY
                        id DESC limit 1
                   """)
        dat = cr.dictfetchall()
        config_id = dat and dat[0]['id'] or False
        print "******CONFIG_ID******: ", config_id
        
        # Obteniendo la informacion de los registros
        if config_id:
            config = self.browse(cr, uid, config_id, context=context)
            res['name'] = config.name
            res['ref'] = config.ref
            
        if not (res.get('name', False) or res.get('ref', False)):
            
            raise osv.except_osv(_('Error!'), _('Falta un dato en la configuracion'))
        
        return res
        
    def _get_name_config(self, cr, uid, context=None ):
        """
            Obtiene el ultimo prefijo registrado en la configuracion
        """
        # Obtiene el ultimo de 'name' registrado
	name = ""
        cr.execute('SELECT name FROM mrp_lot_config_settings order by id desc')
	for query in cr.fetchall():
		if query[0]:
			name =  query[0]       	
	return name
    
    def _get_ref_config(self, cr, uid, context=None ):
        """
            Obtiene la ultima referencia interna registrada para la configuracion
        """
        # Obtiene el ultimo valor de 'ref' registrado
	ref = ""
        cr.execute('SELECT ref FROM mrp_lot_config_settings order by id desc')
	
	for query in cr.fetchall():
		if query[0]:
			ref =  query[0]       	
	return ref
    
    
    _columns = {
        'name': fields.char('Prefijo'),
        'ref': fields.char('Referencia interna'),
    }
    
    _defaults = {
        'name': _get_name_config,
        'ref': _get_ref_config,
        }
    
    # def get_name(self, cr, uid, field, context=None):
    #     """
    #         Obtiene los datos del registro
    #     """
    #     reg = ''
    #     cr.execute("""
    #             SELECT
    #                 max(id) as config_id
    #             FROM
    #                 mrp_lot_config_settings
    #                """)
    #     dat = cr.dictfetchall()
    #     data = dat and dat[0]['config_id'] or False
    #     # Obteniendo el valor de 'name' del utimo registro
    #     if data:
    #         reg = self.browse(cr, uid, data).name
    #         
    #     return {'name': reg or False}
    # 
    # def get_ref(self, cr, uid, field, context=None):
    #     """
    #         Obtiene los datos del registro
    #     """
    #     reg = ''
    #     cr.execute("""
    #             SELECT
    #                 max(id) as config_id
    #             FROM
    #                 mrp_lot_config_settings
    #                """)
    #     dat = cr.dictfetchall()
    #     data = dat and dat[0]['config_id'] or False
    #     # Obteniendo el valor de 'ref' del utimo registro
    #     if data:
    #         reg = self.browse(cr, uid, data).ref
    #         
    #     return {'ref': reg or False}
        
    

mrp_lot_config_settings()
