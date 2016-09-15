# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Ivan Macias <ivanfallen@gmail.com>"
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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class crm_make_sale(osv.osv_memory):
    """ Inherit Make sale  order for crm """

    _inherit = "crm.make.sale"

    def makeOrder(self, cr, uid, ids, context=None):
        """
            Inherit makeOrder - Agregar la relacion entre el documento oportinidad con venta.
        """
        #print "**************** context ****************** ", context
        if context is None:
            context = {}

        #print "*******************Funcion makeOrder*************"
        #valor = super(crm_make_sale, self).makeOrder(cr, uid, ids, context=context)
        valor = self.makeOrder_reply(cr, uid, ids, context=context)
        #print "*********  Valor funcion super *******", valor
        
        #~ Valida que el objeto crm.lead se encuentre en las referencias en solicitudes
        request_obj = self.pool.get('res.request.link')
        request_ids = request_obj.search(cr, uid, [('object', '=', 'crm.lead'),])
        #print "************* busca la referencia ***************** ", request_ids
        if not request_ids:
            #print "*************** agrega referencia ***************** "
            #~ Si no esta en las referencias agrega el registro
            request_obj.create(cr, uid, {'name': 'Oportunidad', 'object': 'crm.lead', })
        
        #~ Relaciona el documento origen con la venta 
        sale_obj = self.pool.get('sale.order')
        data = context and context.get('active_ids', []) or []
        #print "+++++++++++++++++ data es igual a ", data 
        sale_obj.write(cr, uid, valor['res_id'], {'crm_lead_id': 'crm.lead,' + str(data[0])})
        return valor
        
    def makeOrder_reply(self, cr, uid, ids, context=None):
        """
        This function  create Quotation on given case.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created sales order.
        """
        if context is None:
            context = {}
        # update context: if come from phonecall, default state values can make the quote crash lp:1017353
        context.pop('default_state', False)        
        
        case_obj = self.pool.get('crm.lead')
        sale_obj = self.pool.get('sale.order')
        partner_obj = self.pool.get('res.partner')
        data = context and context.get('active_ids', []) or []

        for make in self.browse(cr, uid, ids, context=context):
            partner = make.partner_id
            partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                    ['default', 'invoice', 'delivery', 'contact'])
            pricelist = partner.property_product_pricelist.id
            fpos = partner.property_account_position and partner.property_account_position.id or False
            payment_term = partner.property_payment_term and partner.property_payment_term.id or False
            new_ids = []
            for case in case_obj.browse(cr, uid, data, context=context):
                if not partner and case.partner_id:
                    partner = case.partner_id
                    fpos = partner.property_account_position and partner.property_account_position.id or False
                    payment_term = partner.property_payment_term and partner.property_payment_term.id or False
                    partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                            ['default', 'invoice', 'delivery', 'contact'])
                    pricelist = partner.property_product_pricelist.id
                if False in partner_addr.values():
                    raise osv.except_osv(_('Insufficient Data!'), _('No address(es) defined for this customer.'))

                vals = {
                    'origin': _('Opportunity: %s') % str(case.id),
                    'section_id': case.section_id and case.section_id.id or False,
                    'categ_ids': [(6, 0, [categ_id.id for categ_id in case.categ_ids])],
                    'shop_id': make.shop_id.id,
                    'partner_id': partner.id,
                    'pricelist_id': pricelist,
                    'partner_invoice_id': partner_addr['invoice'],
                    'partner_shipping_id': partner_addr['delivery'],
                    'date_order': fields.date.context_today(self,cr,uid,context=context),
                    'fiscal_position': fpos,
                    'payment_term':payment_term,
                    'user_id': case.user_id.id
                }
                #print "***************** vals sale ***************** ", vals
                #~ if partner.id:
                    #~ vals['user_id'] = partner.user_id and partner.user_id.id or uid
                new_id = sale_obj.create(cr, uid, vals, context=context)
                sale_order = sale_obj.browse(cr, uid, new_id, context=context)
                #print "******************** sale order ************** ", sale_order.user_id
                case_obj.write(cr, uid, [case.id], {'ref': 'sale.order,%s' % new_id})
                new_ids.append(new_id)
                message = _("Opportunity has been <b>converted</b> to the quotation <em>%s</em>.") % (sale_order.name)
                case.message_post(body=message)
            if make.close:
                case_obj.case_close(cr, uid, data)
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            if len(new_ids)<=1:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Quotation'),
                    'res_id': new_ids and new_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name' : _('Quotation'),
                    'res_id': new_ids
                }
            return value
    
    def _get_ref_crm_lead(self, cr, uid, context=None):
        """
            Retorna verdadero si el campo referencia no esta vacio
        """
        res = False
        # Obtiene el id de las oportunidades a validar
        data = context and context.get('active_ids', []) or []
        case_obj = self.pool.get('crm.lead')
        # Recorre las oportunidades
        for crm in case_obj.browse(cr, uid, data, context=context):
            #print "************** Referencia ************* ", crm.ref
            # Si el campo contiene referencia cambia el valor de retorno a True y termina recorrido
            if crm.ref:
                res = True
                break;
        return res
    
    _columns = {
        'have_ref': fields.boolean('Tiene referencia', readonly=True, select=True),
    }
    
    _defaults = {
        'close': True,
        'have_ref': _get_ref_crm_lead
    }

crm_make_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
