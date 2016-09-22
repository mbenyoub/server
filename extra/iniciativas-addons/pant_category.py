from osv import osv, fields
import pooler
import time
import netsvc

class pant_category(osv.osv):
    _name = 'pant.category'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_category()
