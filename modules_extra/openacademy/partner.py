# -*- encoding: utf-8 -*-
from osv import osv
from osv import fields
from tools.translate import _

class res_partner(osv.osv):
    """
    res_partner
    """
    _inherit = 'res.partner'
    _columns = {
        'is_instructor':fields.boolean('Is Instructor', required=False),
        'session_ids': fields.many2many('openacademy.session',
                                        'openacademy_attendee',
                                        'partner_id','session_id','Sessions'),
    }
res_partner()
