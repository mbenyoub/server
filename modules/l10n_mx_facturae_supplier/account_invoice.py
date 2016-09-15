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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import base64

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import pytz

class account_invoice(osv.osv):
    _inherit='account.invoice'
    
    _columns = {
        'file_xml': fields.many2one('ir.attachment', 'XML Asociado',
            readonly=True, help='Archivo XML asociado a la factura', ondelete='cascade'),
        'xml_data': fields.related('file_xml', 'datas', type="binary", string="XML Asociado", readonly=True),
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({'file_xml' : False})
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def action_confirm_xml(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard para validar el XML de la factura
        """

        self.read_xml(cr, uid, ids, context)
        # Obtiene el estado de la factura
        state = self.browse(cr, uid, ids[0], context=context).state
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_mx_facturae_supplier', 'wizard_account_invoice_confirm_xml_view')

        return {
            'name':_("Validar XML Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice.confirm.xml',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_invoice_id': ids[0],
                'default_state': state
            }
        }


    def read_xml(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        attach_obj = self.pool.get('ir.attachment')

        for inv_ids in self.browse(cr, uid, ids, context=context):
            inv = inv_ids.id

        attach_ids = attach_obj.search(cr, uid, [('res_id','=',inv_ids.id)], context=context)

        if len(attach_ids) < 1:
            raise osv.except_osv('Error', 'No se ha adjuntado ningun archivo')
        else:
            for attach in attach_obj.browse(cr, uid, attach_ids, context=context):
                xml_file = base64.b64decode(attach.db_datas)#.decode().encode('utf-8')
            #raise osv.except_osv('xml', str(xml_file.split("UUID")[1]).split('"')[1] )
        try:
            self.write(cr, uid, [inv_ids.id],{'cfdi_folio_fiscal':str(xml_file.split("UUID")[1]).split('"')[1]})
        except IndexError:
            raise osv.except_osv('Error', 'Tu archivo no contiene UUID')
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
