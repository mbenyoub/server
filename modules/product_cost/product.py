# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
#
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields
import openerp.addons.decimal_precision as dp


class product_product(osv.osv):
    _inherit = 'product.product'
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
    def _query_last_cost(self, cr, uid, product_id, context=None):
        """
            Realiza el query para obtener el precio unitario de la última compra del producto
        """
        cost_last = 0.0
        string_query = """
            SELECT
                al.price_unit as price_unit
            FROM
                account_invoice as a
                INNER JOIN account_invoice_line as al ON a.id = al.invoice_id
                INNER JOIN product_product as p ON al.product_id = p.id
            WHERE
                a.type = 'in_invoice' and
                al.product_id = %s and
                (a.state = 'open' or
                    a.state = 'paid') and
                a.id = (SELECT MAX(a2.id) as maximum_id 
                        FROM 
                            account_invoice as a2
                            INNER JOIN account_invoice_line as al2 ON a2.id = al2.invoice_id
                            INNER JOIN product_product as p2 ON al2.product_id = p2.id
                        WHERE 
                            al2.product_id = %s and
                            (a2.state = 'open' or
                                a2.state = 'paid'))
            GROUP BY
                al.price_unit
            """%(product_id, product_id)
        # Se realiza la consulta hacia la tabla factura de compra para obtener el ultimo costo de compra del producto
        cr.execute(string_query)
        
        # Se realiza el recorrido de la consulta
        for i in cr.fetchall():
            cost_last = i[0]        
        #print "****COST_LAST******: ", cost_last
        return cost_last
    
    def _query_medium_cost(self, cr, uid, product_id, context=None):
        """
            Se realiza query para obtener el precio medio del producto comprado
        """
        medium_cost = 0.0
        quantity = 0.0
        amount = 0.0
        
        string_query = """
                SELECT
                        SUM(al.price_subtotal) as amount,
                        SUM(al.quantity) as quantity
                FROM
                        account_invoice as a
                        INNER JOIN account_invoice_line as al ON al.invoice_id = a.id
                        INNER JOIN product_product as p ON al.product_id = p.id
                WHERE
                        a.type = 'in_invoice' AND
                        (a.state = 'open' or a.state = 'paid') AND
                        al.product_id = %s
        """%(product_id)
        
        # Se ejecuta la consulta
        cr.execute(string_query)
        # Se obtienen los datos de la consulta
        for i in cr.fetchall():
            amount = i[0] 
            quantity = i[1]
            
            if amount == None:
                amount = 0.0
            if quantity == None:
                quantity = 0.0
            
        print "****AMOUNT****: ", amount
        print "****QUANTITY****: ", quantity
            
        # Se obtiene el precio medio del producto
        if quantity != 0.0 and amount != 0.0:
            medium_cost = amount / quantity
        print "*****MEDIUM_COST****: ", medium_cost
        
        #print "*****PRECIO COSTE*****: ", self.browse(cr, uid, product_id, context=context).standard_price
        return medium_cost
        
    def _get_cost(self, cr, uid, ids, fields_name, args, context=None):
        """
            Se obtiene el precio unitario de la ultima compra del producto
        """
        res = {}
        # Se obtiene el producto del cual se obtendra su último costo de compra
        for id in ids:
            res[id] = {
                'cost_last': 0.0,
                'standard_price': 0.0
            }
            
            p = self.read(cr, uid, id, ['cost_method','standard_cost_price'])
            print "************** product ************* ", p
            
            # Se manda a realizar una consulta para obtener el ultimo costo de compra
            res[id]['cost_last'] = self._query_last_cost(cr, uid, id, context=context)
            
            # Se valida si el método de costo es 'Precio medio'
            if p['cost_method'] == 'average':
                # Se manda a realizar una consulta para obtener el costo medio del producto
                res[id]['standard_price']= self._query_medium_cost(cr, uid, id, context=context)
            else:
                # Se actualiza el campo standard_price del producto con el precio medio
                res[id]['standard_price'] = p['standard_cost_price']
                #print "******RES******: ", res[product.id]
        return res
    
    _columns = {
        'cost_last': fields.function(_get_cost, type='float', digits_compute=dp.get_precision('Product'),
            string="Ultimo costo", store=False, method=False, multi='cost'),
        'standard_price': fields.function(_get_cost, type='float', digits_compute=dp.get_precision('Product'),
            string="Precio coste", store=False, method=False, multi='cost'),
        'standard_cost_price': fields.float('Precio coste', digits_compute=dp.get_precision('Product')),
    }