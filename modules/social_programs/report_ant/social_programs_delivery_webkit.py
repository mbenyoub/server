# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Ivan Serrano Salda?a <riss_600@hotmail.com>"
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
from openerp.report import report_sxw

class social_programs_delivery(report_sxw.rml_parse):

    def __init__(self, cr, uid, name,context=None):
        super(social_programs_delivery, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.social.programs.program.delivery.webkit',
                      'social.programs.program.delivery',
                      'addons/social_programs/report/social_programs_program_delivery_webkit.mako',
                      parser=social_programs_delivery,
                      header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: