# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
import datetime
logging.basicConfig(level=logging.INFO)

class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    def create(self, cr, uid, vals, context=None):
	product = vals.get('product_id')
	if product:
		condicion=[('product_id','=',product)]
		ids=self.pool.get('ma.serie').search(cr, uid,condicion,context=None)
		if len(ids)>0:
			obj=self.pool.get('ma.serie').browse(cr,uid,ids[0])
			rule = obj.rule
			now = datetime.datetime.now()
			year = now.strftime("%Y")
			y = now.strftime("%y")
			day = now.strftime("%d")
			month = now.strftime("%m")
			rule= rule.replace("(year)", year)
                        rule= rule.replace("(y)", y)
                        rule= rule.replace("(month)", month)
                        rule= rule.replace("(day)", day)
			vals['x_serie']= rule
		
	return super(mrp_production,self).create(cr, uid, vals, context=context)

mrp_production()

