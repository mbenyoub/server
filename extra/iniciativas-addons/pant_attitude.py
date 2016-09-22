from osv import osv, fields
import pooler
import time
import netsvc

class pant_attitude(osv.osv):
    _name = 'pant.attitude'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_attitude()
