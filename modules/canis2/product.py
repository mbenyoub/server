# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Martha Guadalupe Tovar Almaraz (martha.gtovara@hotmail.com)
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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class product_product(osv.osv):
    _inherit = "product.product"
    
    def onchange_weight(self, cr, uid, ids, weight, context=None):
        """
            Llena el campo de "peso neto"
        """
        
        res = {}
        
        if weight:
            res = {
                'weight_net': weight
            }
            
        return {'value': res}
    

    _columns = {
        'protected_price': fields.float('Precio Protegido', help="El producto no debe rebasar este precio y si el precio  protegido es igual a cero va a continuar con la operacion", required=True),
    }

product_product()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
