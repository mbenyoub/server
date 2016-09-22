from osv import osv, fields
import pooler
import time
import netsvc

class pant_treatment(osv.osv):
    _name = 'pant.treatment'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_treatment()
