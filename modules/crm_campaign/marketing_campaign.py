# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Saldaña (riss_600@hotmail.com)
#              Ivan Macias (ivanfallen@gmail.com)
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

import time
import base64
import itertools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from traceback import format_exception
from sys import exc_info
from openerp.tools.safe_eval import safe_eval as eval
import re
from openerp.addons.decimal_precision import decimal_precision as dp

from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _

class marketing_campaign(osv.Model):
    _inherit = "marketing.campaign"
    
    _defaults = {
        'mode': lambda *a: 'active',
        'object_id': 61,
        'unique_field_id': 459,
    }
    
class marketing_campaign_activity(osv.Model):
    _inherit = "marketing.campaign.activity"
    
    def onchange_condition_activity(self, cr, uid, ids, condition_activity, context=None):
        """
            Obtiene la condicion que se va a aplicar en la campaña
        """
        # Obtiene el valor del registro y lo agrega en el campo de condicion
        condition_config_obj = self.pool.get('marketing.campaign.config.activity')
        condition = condition_config_obj.browse(cr, uid, condition_activity, context=context).condition
        return {'value':{'condition': condition or 'True'}}
    
    _columns = {
        'condition_activity': fields.many2one('marketing.campaign.config.activity', 'Plantilla Condicion', ondelete='set Null', select=1),
    }
    
    _defaults = {
        
    }
    