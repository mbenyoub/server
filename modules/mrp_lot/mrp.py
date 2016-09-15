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
# ----MODIFICACION 16/04/2015-----
#   Colocaion de validacion 'cr.fetchone()' en el metodo '_get_lot' de 'mrp.production'

# ---MODIFICACION 17/04/2015-----
#   Eliminacion de la clase 'mrp_lot_conf' para pasarla al archivo 'res_config.py'

from openerp.osv import osv, fields
from openerp import pooler, tools
from openerp.tools.translate import _
from datetime import datetime, time


class mrp_lot(osv.Model):
    _name = 'mrp.lot'
    
    def _lot_day(self, cr, uid, context=None):
        """
            Generador del nombre del lote
        """
        lot = ''
        config_obj = self.pool.get('mrp.lot.config.settings')
        config = config_obj.get_config_lot(cr, uid, context=context)
        
        date_now = datetime.now()
        date = date_now.strftime("%Y-%m-%d")
        if config:
            lot = config['name'] + '/' + date + "/" + config['ref']
            
        return lot
            
    _columns = {
        'name': fields.char('Lote'),
        'mrp_ids': fields.one2many('mrp.production', 'mrp_lot_id', 'Ordenes de produccion'),
        'active': fields.boolean('Activo'),
    }
    
    _defaults = {
        'name': _lot_day,
        'active': False,
    }
    
    def create(self, cr, uid, ids, context=None):
        """
            Metodo para crear lotes de manufactura
        """
        lot_srch = self.search(cr, uid, [('active', '=', True)], context=context)
        
        if lot_srch:
            raise osv.except_osv(_('Error!'), _('No puede haber dos lotes de manufactura activos'))
        else:
            return super(mrp_lot,self).create(cr, uid, ids, context=context)
    
    
mrp_lot()

class mrp_production(osv.Model):
    _inherit = 'mrp.production'
    
    def _get_lot(self, cr, uid, context=None):
        """
            Metodo para obtener el lote de produccion
        """
        lot_obj = self.pool.get('mrp.lot')
        lot_id = False
        
        # Obteniendo el lote de manufactura activo
        lot_srch = lot_obj.search(cr, uid, [('active', '=', True)], context=context)
        if lot_srch:
            lot_id = lot_obj.browse(cr, uid, lot_srch[0], context=context)['id']
        
        if lot_id:
            return lot_id
        
        return False
    
    _columns = {
        'mrp_lot_id': fields.many2one('mrp.lot', 'Lote de produccion')
    }
    
    _defaults = {
        'mrp_lot_id': _get_lot
    }

