from osv import osv, fields
import pooler
import time
import netsvc

class pant_culture(osv.osv):
    _name = 'pant.culture'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_culture()
