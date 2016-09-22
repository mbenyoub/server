from osv import osv, fields
import pooler
import time
import netsvc

class pant_title(osv.osv):
    _name = 'pant.title'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_title()
