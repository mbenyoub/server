from osv import osv, fields
import pooler
import time
import netsvc

class pant_feature(osv.osv):
    _name = 'pant.feature'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_feature()
