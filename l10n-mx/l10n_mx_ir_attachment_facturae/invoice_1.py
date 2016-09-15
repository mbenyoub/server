#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
# Credits######################################################
#    Coded by: Juan Carlos Funes(juan@vauxoo.com)
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler, tools
from openerp import netsvc

import time

class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def action_cancel(self, cr, uid, ids, context=None):
        ir_attach_obj = self.pool.get('ir.attachment.facturae.mx')
        id_attach = ir_attach_obj.search(
            cr, uid, [('invoice_id', '=', ids[0])], context)
        wf_service = netsvc.LocalService("workflow")
        inv_type_facturae = {
            'out_invoice': True,
            'out_refund': True,
            'in_invoice': False,
            'in_refund': False}
        for inv in self.browse(cr, uid, ids):
            if inv_type_facturae.get(inv.type, False):
                for attachment in ir_attach_obj.browse(cr, uid, id_attach,
                                                       context):
                    if attachment.state == 'done':
                        wf_service.trg_validate(
                            uid, 'ir.attachment.facturae.mx',
                            attachment.id, 'action_cancel', cr)
        self.write(cr, uid, ids, {
                   'date_invoice_cancel': time.strftime('%Y-%m-%d %H:%M:%S')})
        return super(account_invoice, self).action_cancel(cr, uid, ids,
                                                          context)

    def create_ir_attachment_facturae(self, cr, uid, ids, context=None):
        ir_attach_obj = self.pool.get('ir.attachment.facturae.mx')
        invoice = self.browse(cr, uid, ids, context=context)[0]
        if invoice.invoice_sequence_id.approval_id:
            if invoice.invoice_sequence_id.approval_id.type == 'cfdi32':
                pac = self.pool.get('params.pac').search(
                    cr, uid, [('active', '=', True)], context)
                # if not pac:
                    # raise osv.except_osv(_('Warning !'),_('Not Params PAC.'))
            attach = ir_attach_obj.create(cr, uid, {
                'name': invoice.fname_invoice, 'invoice_id': ids[0],
                'type': invoice.invoice_sequence_id.approval_id.type},
                context=context)

            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(
                uid, 'ir.attachment.facturae.mx', attach, 'action_confirm', cr)

            ir_model_data = self.pool.get('ir.model.data')

            form_res = ir_model_data.get_object_reference(
                cr, uid, 'l10n_mx_ir_attachment_facturae',
                'view_ir_attachment_facturae_mx_form')
            form_id = form_res and form_res[1] or False

            tree_res = ir_model_data.get_object_reference(
                cr, uid, 'l10n_mx_ir_attachment_facturae',
                'view_ir_attachment_facturae_mx_tree')
            tree_id = tree_res and tree_res[1] or False

            return {
                'name': _('Attachment Factura E MX'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'ir.attachment.facturae.mx',
                'res_id': attach,
                'view_id': False,
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                'type': 'ir.actions.act_window',
            }
    
    def action_invoice_sent2(self, cr, uid, ids, context=None):
        '''
            Envia la informacion del mensaje y los adjuntos a la factura
        '''
        # Funcion original para enviar el mensaje
        # res = super(account_invoice, self).action_invoice_sent(cr, uid, ids, context=context)
        
        # Agrega los adjuntos al documento
        adjuntos = self.pool.get('ir.attachment').search(cr, uid, [(
            'res_model', '=', 'account.invoice'), ('res_id', '=', ids[0])])
        #print"**************** attachment invoice ************* ", adjuntos
        
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_ids = ir_model_data.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')
            #print"********************* template id ********************* ", template_ids
            template_id = template_ids[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'account.invoice',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': adjuntos,
            'mark_so_as_sent': True
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    def invoice_print(self, cr, uid, ids, context=None):
        '''
            Esta funcion imprime la factura
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        invoice = self.browse(cr, uid, ids[0], context=context)
        if invoice.invoice_sequence_id.approval_id:
            if invoice.invoice_sequence_id.approval_id.type == 'cfdi32':
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'account.invoice.facturae.webkit',
                    'datas': datas,
                    'nodestroy' : True
                }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice',
            'datas': datas,
            'nodestroy' : True
        }
