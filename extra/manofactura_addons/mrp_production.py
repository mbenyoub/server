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
	# Si la orden de produccion tiene producto se buscar el numero de serie
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
		#Se crea traspaso interno
		if vals.get('origin') is False:
			ori=''
		else:
			ori=vals.get('origin')
		doc=vals.get('name')+':'+ori
		obj_picking=self.pool.get('stock.picking')
		#Busco la lista de materiales de producto
		bom_obj=self.pool.get('mrp.bom')
		bom_id = bom_obj._bom_find(cr, uid, product,'')
		#Buscar los productos con el bom_id, despues llamar el metodo children y quitar los productos que son fabricados
		condicion=[('bom_id','=',bom_id)]
		res = bom_obj.search(cr, uid, condicion, context=context)
 		res2 = bom_obj.browse(cr, uid, res, context=context)
		res3 = self.get_children(res2)
		for r in res3:
			logging.info(r)
		#obj_picking.create(cr, uid, {'origin':doc,'date':datetime.now(),'min_date':datetime.now(),'invoice_state': 'none','stock_journal_id':1,'state': 'assigned'}, context=context)

	return super(mrp_production,self).create(cr, uid, vals, context=context)


    def get_children(self, object, level=0):
        result = []

        def _get_rec(object, level):
            for l in object:
                res = {}
		res['id'] = l.product_id.id 
                res['name'] = l.name
                res['pname'] = l.product_id.name
                res['pcode'] = l.product_id.default_code
                res['pqty'] = l.product_qty
                res['uname'] = l.product_uom.name
                res['code'] = l.code
		#res['supply_method'] = l.product_id.product_tmpl_id.supply_method
                res['level'] = level
		if l.product_id.product_tmpl_id.supply_method <> 'produce':
                	result.append(res)
                if l.child_complete_ids:
                    if level<6:
                        level += 1
                    _get_rec(l.child_complete_ids,level)
                    if level>0 and level<6:
                        level -= 1
            return result

        children = _get_rec(object,level)

        return children



    """def _needaction_domain_get(self, cr, uid, context=None):
       	d=datetime.now()
       	n_format = '%Y-%m-%d'
       	fecha = d.strftime(n_format)
       	fecha = fecha+ ' 00:00:00'

        return [ '&', ('state','=','confirmed'), ('date_planned','>=',fecha)]"""


mrp_production()

