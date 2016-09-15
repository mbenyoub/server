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

class marketing_campaign_config_activity(osv.osv):
    #code
    _name = 'marketing.campaign.config.activity'
    _columns = {
        'name' : fields.char('Nombre', size=256, required=True, select=True, help="Nombre de la condicion de la actividad"),
        'condition' : fields.char('Condicion', size=256, required=True,
                                 help="Python expression to decide whether the activity can be executed, otherwise it will be deleted or cancelled."
                                 "The expression may use the following [browsable] variables:\n"
                                 "   - activity: the campaign activity\n"
                                 "   - workitem: the campaign workitem\n"
                                 "   - resource: the resource object this campaign item represents\n"
                                 "   - transitions: list of campaign transitions outgoing from this activity\n"
                                 "...- re: Python regular expression module"),
    }
