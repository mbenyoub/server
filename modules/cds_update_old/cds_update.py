from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime, timedelta


class cds_update(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'is_prospect': fields.boolean('Prospecto (?)', help="Este cliente es un prospecto")
        
                
        }
    _defaults = {
        'is_prospect': True,
        'customer': False,
    }
cds_update()
    #code
