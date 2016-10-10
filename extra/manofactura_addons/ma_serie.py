from osv import osv, fields
import pooler
import time
import netsvc

class ma_serie(osv.osv):
    _name = 'ma.serie'
    _columns = {
	'product_id':  fields.many2one('product.product', string='Producto'),
	'rule': fields.char('Regla',size=300),
    }

ma_serie()
