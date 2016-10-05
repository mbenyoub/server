from osv import osv, fields
import pooler
import time
import netsvc

class op_project(osv.osv):
    _name = 'op.project'
    _columns = {
            'name': fields.char(size=300, string = 'Nombre', required=True),
	    'description': fields.text('Descripcion',required=True),
    }

op_project()
