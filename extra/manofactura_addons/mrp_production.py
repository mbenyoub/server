# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.tools.translate import _
import logging
from datetime import datetime, timedelta, date, time
logging.basicConfig(level=logging.INFO)

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _order = "date_planned desc"

    def create(self, cr, uid, vals, context=None):
	product = vals.get('product_id')
	if product:
		condicion=[('product_id','=',product)]
		ids=self.pool.get('ma.serie').search(cr, uid,condicion,context=None)
		if len(ids)>0:
			obj=self.pool.get('ma.serie').browse(cr,uid,ids[0])
			rule = obj.rule
			now = datetime.now()
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


    def _needaction_domain_get(self, cr, uid, context=None):
       	d=datetime.now()
       	n_format = '%Y-%m-%d'
       	fecha = d.strftime(n_format)
       	fecha = fecha+ ' 00:00:00'

        return [ '&', ('state','=','confirmed'), ('date_planned','>=',fecha)]


mrp_production()

