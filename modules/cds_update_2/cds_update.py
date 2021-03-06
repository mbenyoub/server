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
class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    def invoice_validate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'open'}, context=context)
        partner_id= self.browse(cr, uid, ids[0], context)['partner_id']
        
        product_obj = self.pool.get('res.partner')
        
        product_id = product_obj.search(cr, uid, [('id','=',partner_id.id)])
            
        product_obj.write(cr, uid, partner_id.id, {'is_prospect':False}, context=None)
        
        
        #raise osv.except_osv('Error',[partner.is_prospect,' name ',partner.name])
        #raise osv.except_osv('Error',[partner_id.id,' name '])
        #raise osv.except_osv('Error',[partner_id.is_prospect,' name '])
        return True
account_invoice()
    #code
