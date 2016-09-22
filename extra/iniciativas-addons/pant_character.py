from osv import osv, fields
import pooler
import time
import netsvc

class pant_character(osv.osv):
    _name = 'pant.character'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_character()
