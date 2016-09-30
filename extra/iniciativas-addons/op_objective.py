from osv import osv, fields
import pooler
import time
import netsvc

class op_objective(osv.osv):
    _name = 'op.objective'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre', required=True),
    }

op_objective()
