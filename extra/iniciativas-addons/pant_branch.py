from osv import osv, fields
import pooler
import time
import netsvc

class pant_branch(osv.osv):
    _name = 'pant.branch'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre'),
    }

pant_branch()
