# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
logging.basicConfig(level=logging.INFO)

class crm_make_sale(osv.osv):
    _inherit = 'crm.make.sale'

    def _get_sales(self, cr, uid,context=None):
	res = []
	if 'active_id' in context:
		active = context['active_id']
		if active is not False and active is not None:
			crm_obj = self.pool.get('crm.lead').browse(cr, uid, active, context=context)
			obj=crm_obj.sale_ids
    			obj_sale = self.pool.get('sale.order')
			for ob in obj:
				res.append((str(ob.id),ob.name))
    	return res

    _columns = {
	'use_sale' : fields.boolean('Utilizar Presupuesto de Oportunidad'),
   	'sale_order_id' : fields.selection(_get_sales,'Presupuestos')
    }


    def makeOrder(self, cr, uid, ids, context=None):

        if context is None:
            context = {}
        data = context and context.get('active_ids', []) or []

        for make in self.browse(cr, uid, ids, context=context):
            partner = make.partner_id
	    use = make.use_sale
            order_id = int(make.sale_order_id)
	    close = make.close

	if use:
		if order_id==0:
			raise osv.except_osv(('Error'), ('El campo Presupuestos esta vacio'))
		ref= 'sale.order,'+str(order_id)
		self.pool.get('crm.lead').write(cr, uid, data[0], {'ref': ref}, context=context)
		crm_lead_id='crm.lead,'+str(data[0])
		self.pool.get('sale.order').write(cr, uid, order_id, {'crm_lead_id': crm_lead_id}, context=context)
		#Marcar como ganado
        	if close:
            		self.pool.get('crm.lead').case_close(cr, uid, data)

                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Quotation'),
                    'res_id': order_id
                }
		return value


	else:
		return super(crm_make_sale,self).makeOrder(cr, uid, ids, context=context)	

	return True

crm_make_sale()
