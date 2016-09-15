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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools.translate import _

class account_invoice(osv.Model):
    _inherit = "account.invoice"
    
    def action_view_asset_purchase(self, cr, uid, ids, context=None):
        """
            Redirecciona a la vista lista los activos generados por la compra
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_asset', 'view_account_asset_asset_tree')
        dummyf, viewf_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_asset', 'view_account_asset_asset_form')
        
        #print "*************** ver activos **************** "
        return {
            'name':_("Activos"),
            'view_mode': 'tree,form',
            'view_id': view_id,
            'view_type': 'form',
            'views': [(view_id, 'tree'),(viewf_id, 'form')],
            'res_model': 'account.asset.asset',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('invoice_id','=',%s)]"%(ids[0],),
            'context': {},
        }
    
    def onchange_partner_id_asset(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_payment_term = False
        acc_id = False
        bank_id = False
        fiscal_position = False

        opt = [('uid', str(uid))]
        if partner_id:

            opt.insert(0, ('id', partner_id))
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if company_id:
                if (p.property_account_receivable.company_id and (p.property_account_receivable.company_id.id != company_id)) and (p.property_account_payable.company_id and (p.property_account_payable.company_id.id != company_id)):
                    property_obj = self.pool.get('ir.property')
                    rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    if not rec_pro_id:
                        rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('company_id','=',company_id)])
                    if not pay_pro_id:
                        pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('company_id','=',company_id)])
                    rec_line_data = property_obj.read(cr,uid,rec_pro_id,['name','value_reference','res_id'])
                    pay_line_data = property_obj.read(cr,uid,pay_pro_id,['name','value_reference','res_id'])
                    rec_res_id = rec_line_data and rec_line_data[0].get('value_reference',False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
                    pay_res_id = pay_line_data and pay_line_data[0].get('value_reference',False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
                    if not rec_res_id and not pay_res_id:
                        raise osv.except_osv(_('Configuration Error!'),
                            _('Cannot find a chart of accounts for this company, you should create one.'))
                    account_obj = self.pool.get('account.account')
                    rec_obj_acc = account_obj.browse(cr, uid, [rec_res_id])
                    pay_obj_acc = account_obj.browse(cr, uid, [pay_res_id])
                    p.property_account_receivable = rec_obj_acc[0]
                    p.property_account_payable = pay_obj_acc[0]

            if type in ('out_invoice', 'out_refund'):
                if p.property_account_asset:
                    acc_id = p.property_account_asset.id
                else:
                    acc_id =  p.property_account_receivable.id
                partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
            else:
                acc_id = p.property_account_payable.id
                partner_payment_term = p.property_supplier_payment_term and p.property_supplier_payment_term.id or False
            fiscal_position = p.property_account_position and p.property_account_position.id or False
            if p.bank_ids:
                bank_id = p.bank_ids[0].id

        result = {'value': {
            'account_id': acc_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position
            }
        }

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id

        if payment_term != partner_payment_term:
            if partner_payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr, uid, ids, partner_payment_term, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
            result['value'].update(to_update['value'])
        return result
    
    def invoice_validate(self, cr, uid, ids, context=None):
        """
            Valida si es un activo y genera la venta del activo
        """
        asset_obj = self.pool.get('account.asset.asset')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        link_obj = self.pool.get('links.get.request')
        date = time.strftime('%Y-%m-%d')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.asset.asset se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.asset.asset', 'Asset', context=None)
        
        # Proceso original de facturacion
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        
        # Recorre las facturas
        for inv in self.browse(cr, uid, ids, context=context):
            # Valida si es una factura de activo
            if inv.invoice_asset == True:
                # Recorre los activos a facturar
                for line in inv.invoice_line:
                    # Valida que tenga un activo seleccionado
                    if not line.asset_id:
                        raise osv.except_osv(_('Warning!'),_("Revise que todas las lineas de factura tengan un activo asignado!"))
                    # Valida que la cantidad seleccionada no sea mayor a la disponible sobre el activo
                    if line.asset_id.product_qty < line.quantity:
                        raise osv.except_osv(_('Warning!'),_("La cantidad del activo %s, es mayor a la cantidad disponible (Disponible: %s)!"%(line.asset_id.name, line.asset_id.product_qty)))
                    # Valida que el activo se encuentre en ejecucion
                    if line.asset_id.state != 'open':
                        if line.asset_id.state != 'close':
                            raise osv.except_osv(_('Warning!'),_("Compruebe que el activo %s se encuentra disponible para la venta (Estado actual: %s)!"%(line.asset_id.name, line.asset_id.state)))
                    
                    code_int = ''
                    # Valida que el activo tenga asignado un codigo interno
                    if line.asset_id.code_int:
                        code_int = line.asset_id.code_int
                    else:
                        # Obtiene el valor del codigo interno del activo
                        code_int = obj_seq.next_by_code(cr, uid, 'account.asset.asset.code', context=context)
                    
                    # Obtiene el valor original del activo
                    orig_val = 0.0
                    orig_sal = 0.0
                    if line.asset_id.original_value > 0.0:
                        orig_val = line.asset_id.original_value
                        orig_sal = line.asset_id.original_salvage
                    else:
                        orig_val = line.asset_id.purchase_value / line.asset_id.product_qty
                        orig_sal = line.asset_id.salvage_value / line.asset_id.product_qty
                    
                    # Valida si se esta usando completo el activo o una parte proporcional
                    if line.asset_id.product_qty != line.quantity:
                        # Toma la parte proporcional del activo y obtiene el valor de lo no vendido
                        value = line.asset_id.value_residual / line.asset_id.product_qty
                        product_qty = line.asset_id.product_qty - line.quantity
                        asset_value = value * product_qty
                        # Obtiene la parte proporcional del valor bruto
                        pvalue = line.asset_id.purchase_value / line.asset_id.product_qty
                        purchase_value = pvalue * product_qty
                        # Obtiene la parte proporcional del valor salvaguarda
                        svalue = line.asset_id.salvage_value / line.asset_id.product_qty
                        salvage_value = svalue * product_qty
                        # Obtiene el numero de depreciaciones por aplicar
                        cr.execute("""
                            select count(id) as cantidad
                            from account_asset_depreciation_line
                            where asset_id = %s
                                and move_check=False"""%(line.asset_id.id))
                        dep_to_apply = 0.0
                        for value in cr.fetchall():
                            dep_to_apply = value[0]
                            break
                        # Obtiene la fecha de la ultima compra
                        cr.execute("""
                            select depreciation_date, extract(day from depreciation_date) as dia, 
                                    to_char(depreciation_date, 'mm/YYYY') as periodo
                            from account_asset_depreciation_line
                            where asset_id = %s
                                and move_check=False
                            order by depreciation_date asc
                            limit 1"""%(line.asset_id.id))
                        dep_date = 0.0
                        day = month = ''
                        for value in cr.fetchall():
                            dep_date = value[0]
                            day = value[1]
                            month = value[2]
                            break
                        
                        # Si la fecha no esta sobre el dia primero pone el inicio de depreciacion sobre el dia primero
                        if int(day) != 1:
                            dep_date = '01/%s'%(month,)
                        
                        # Crea el nuevo activo
                        asset_id = asset_obj.create(cr, uid, {
                            'product_id': line.asset_id.product_id.id,
                            'name': line.asset_id.name,
                            'category_id': line.asset_id.category_id.id,
                            'parent_id': line.asset_id.id,
                            'date': line.asset_id.date,
                            'purchase_date': dep_date,
                            'currency_id': line.asset_id.currency_id.id,
                            'product_qty': product_qty,
                            'purchase_value': asset_value + salvage_value,
                            'salvage_value': salvage_value,
                            'value_residual': asset_value,
                            'partner_id': line.asset_id.partner_id.id,
                            'method': line.asset_id.method,
                            'method_time': 'number',
                            'method_number': dep_to_apply,
                            'method_period': line.asset_id.method_period,
                            'note': line.asset_id.note,
                            'state': 'open',
                            'code_int': code_int,
                            'origin': line.asset_id.origin,
                            'original_value': orig_val,
                            'original_salvage': orig_sal
                            }, context=context)
                        
                        # Actualiza las depreciaciones del nuevo activo
                        asset_obj.compute_depreciation_board(cr, uid, [asset_id], context=context)
                    
                    # Obtiene la fecha de la primera depreciacion del activo
                    if line.asset_id.invoice_asset_id or line.asset_id.parent_id:
                        # Si el activo proviene de una venta de activo toma la fecha de depreciacion o de una baja de activo
                        dep_date = line.asset_id.depreciation_date
                    else:
                        # Si el activo no proviene del restante de una venta toma el valor de la primera depreciacion
                        dep_date = asset_obj.get_depreciation_init(cr, uid, line.asset_id.id, context=context)
                    
                    # Cambia el estado del activo a Vendido y relaciona con la factura
                    asset_obj.write(cr, uid, [line.asset_id.id], {
                        'state': 'sold',
                        'sale_date': date,
                        'sale_quantity': line.quantity,
                        'sale_update_factor': line.update_factor,
                        'sale_value_account': line.value_account,
                        'sale_value_fiscal': line.value_fiscal,
                        'depreciation_date': dep_date,
                        'code_int': code_int,
                        'original_value': orig_val,
                        'original_salvage': orig_sal,
                        'invoice_asset_id': inv.id}, context=context)
                    
                    # Elimina de la tabla de amortizacion las amortizaciones que ya no se van a aplicar
                    cr.execute("""
                            delete from account_asset_depreciation_line
                            where asset_id = %s
                                and move_check=False """%(line.asset_id.id))
                    
                    journal_id = line.asset_id.category_id.journal_id.id
                    move_id = inv.move_id.id
                    act_period_id = inv.period_id.id
                    #print "************** amount_currency **************** ", line.asset_id.value_residual
                    
                    # Si el activo se vende de manera proporcional obtiene el valor correspondiente a aplicar
                    if line.asset_id.product_qty > line.quantity:
                        value_residual = line.asset_id.value_residual / line.asset_id.product_qty
                        value_residual = value_residual * line.quantity
                    else:
                        # Obtiene el valor contable del activo
                        value_residual = line.asset_id.value_residual
                    
                    # Valida que haya una cuenta de costo de venta configurada en el activo
                    if not line.asset_id.category_id.account_cost_sale_id:
                        raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de costo de venta de activo se encuentre registrada en las categorias de los activos!'))
                    # Valida que haya una cuenta de amortizacion configurada sobre el activo
                    if not line.asset_id.category_id.account_depreciation_id:
                        raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de Amortizacion de activo se encuentre registrada en las categorias de los activos!'))
                    # Valida que haya una cuenta de activo configurada sobre el activo
                    if not line.asset_id.category_id.account_depreciation_id:
                        raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de activo se encuentre registrada en las categorias de los activos!'))
                    
                    # Actualiza la poliza de la factura agregando el valor del costo de venta de activo
                    move_line = {
                        'journal_id': journal_id,
                        'period_id': act_period_id,
                        'name': line.asset_id.name,
                        'account_id': line.asset_id.category_id.account_cost_sale_id.id or False,
                        'move_id': move_id,
                        'partner_id': inv.partner_id.id or False,
                        #'amount_currency': value_residual,
                        'quantity': line.quantity,
                        'credit': 0.0,
                        'debit': value_residual,
                        'date': date,
                        'ref': line.asset_id.name,
                        'reference': 'account.asset.asset,' + str(line.asset_id.id)
                    }
                    new_id = move_line_obj.create(cr, uid, move_line, context=context)
                    
                    # Actualiza la poliza con los montos del cierre del activo solo si el activo esta en estado de ejecucion
                    if line.asset_id.state == 'open':
                        # Obtiene el numero de la secuencia del movimiento
                        mov_number = obj_seq.next_by_code(cr, uid, 'account.asset.asset.close', context=context)
                        
                        # Si el activo se vende de manera proporcional obtiene el valor correspondiente a aplicar
                        if line.asset_id.product_qty > line.quantity:
                            purchase_value = 0.0
                            # Obtiene el valor original del activo
                            if line.asset_id.original_value:
                                purchase_value = line.asset_id.original_value * line.quantity
                            else:
                                purchase_value = (line.asset_id.purchase_value / line.asset_id.product_qty) * line.quantity
                            
                            value_residual = (line.asset_id.value_residual / line.asset_id.product_qty) * line.quantity
                            #purchase_value = (line.asset_id.purchase_value / line.asset_id.product_qty) * line.quantity
                            value1 = (purchase_value - value_residual)
                            value2 = purchase_value
                        else:
                            # Obtiene el valor depreciado del activo
                            value1 = line.asset_id.purchase_value - line.asset_id.value_residual
                            #value2 = line.asset_id.purchase_value
                            value2 = 0.0
                            # Obtiene el valor original del activo
                            if line.asset_id.original_value:
                                value2 = line.asset_id.original_value * line.asset_id.product_qty
                            else:
                                value2 = line.asset_id.purchase_value
                        
                        # Genera la linea con las amortizaciones del activo
                        move_line = {
                            'journal_id': journal_id,
                            'period_id': act_period_id,
                            'name': line.asset_id.name,
                            'account_id': line.asset_id.category_id.account_depreciation_id.id,
                            'move_id': move_id,
                            'partner_id': inv.partner_id.id or False,
                            #'amount_currency': value1,
                            'quantity': line.quantity,
                            'credit': 0.0,
                            'debit': value1,
                            'date': date,
                            'ref': line.asset_id.name,
                            'reference': 'account.asset.asset,' + str(line.asset_id.id)
                        }
                        new_id = move_line_obj.create(cr, uid, move_line, context=context)
                        
                        # Genera la linea que cancela el activo
                        move_line = {
                            'journal_id': journal_id,
                            'period_id': act_period_id,
                            'name': line.asset_id.name,
                            'account_id': line.asset_id.category_id.account_asset_id.id or False,
                            'move_id': move_id,
                            'partner_id': inv.partner_id.id or False,
                            #'amount_currency': value2,
                            'quantity': line.quantity,
                            'credit': value2,
                            'debit': 0.0,
                            'date': date,
                            'ref': line.asset_id.name,
                            'reference': 'account.asset.asset,' + str(line.asset_id.id),
                            #'asset_id': line.asset_id.id
                        }
                        new_id = move_line_obj.create(cr, uid, move_line, context=context)
                        
                        # Si hay valor salvaguarda genera un apunte para cuadrar los movimientos
                        if line.asset_id.salvage_value:
                            # Si el activo se vende de manera proporcional obtiene el valor correspondiente a aplicar
                            if line.asset_id.product_qty > line.quantity:
                                if line.asset_id.original_salvage:
                                    salvage_value = line.asset_id.original_salvage
                                else:
                                    salvage_value = line.asset_id.salvage_value / line.asset_id.product_qty
                                salvage_value = salvage_value * line.quantity
                            else:
                                # Obtiene el valor contable del activo
                                if line.asset_id.original_salvage:
                                    salvage_value = line.asset_id.original_salvage * line.asset_id.product_qty
                                else:
                                    salvage_value = line.asset_id.salvage_value
                            
                            # Genera la linea que cancela el activo
                            move_line = {
                                'journal_id': journal_id,
                                'period_id': act_period_id,
                                'name': line.asset_id.name,
                                'account_id': line.asset_id.category_id.account_cost_sale_id.id or False,
                                'move_id': move_id,
                                'partner_id': inv.partner_id.id or False,
                                #'amount_currency': salvage_value,
                                'quantity': line.quantity,
                                'credit': 0.0,
                                'debit': salvage_value,
                                'date': date,
                                'ref': line.asset_id.name,
                                'reference': 'account.asset.asset,' + str(line.asset_id.id),
                                #'asset_id': line.asset_id.id
                            }
                            new_id = move_line_obj.create(cr, uid, move_line, context=context)
        return res
    
    _columns = {
        'invoice_asset': fields.boolean('Factura de Activo')
    }
    
account_invoice()
    
class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"
    
    def onchange_asset_id(self, cr, uid, ids, asset_id, invoice_id, context=None):
        """
            Regresa la informacion disponible del activo seleccionado
        """
        domain = {'asset_id': [('state','in',['open','close'])]}
        
        if not asset_id:
            return {'domain': domain}
        values = {}
        
        #print "************* onchange domain *************** ", invoice_id
        
        # Valida que exista la factura
        if invoice_id:
            # Valida el estado de la factura y si no esta en borrador que deje seleccionar cualquier activo
            invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
            if invoice:
                if invoice.state != 'draft':
                    domain = {'asset_id': []}
            
        # Obtiene la informacion del activo
        asset = self.pool.get('account.asset.asset').browse(cr, uid, asset_id, context=context)
        
        tax_ids = []
        # Obtiene los impuestos del producto
        if asset.product_id:
            # Recorre los impuestos configurados en el producto
            for tax in asset.product_id.taxes_id:
                tax_ids.append(tax.id)
        values['invoice_line_tax_id'] = tax_ids
        values['name'] = asset.name
        values['quantity'] = asset.product_qty
        values['update_factor'] = asset.update_factor
        values['value_account'] = (asset.value_residual/asset.product_qty)
        values['value_fiscal'] = (asset.update_factor * asset.value_residual)/asset.product_qty
        # Agrega la cuenta de la categoria del activo
        if asset.product_id:
            #if asset.product_id:
                #~ values['account_id'] = asset.category_id.account_sale_id.id
            #~ elif asset.product_id:
            if asset.product_id.property_account_income:
                values['account_id'] = asset.product_id.property_account_income.id
            else:
                values['account_id'] = asset.product_id.categ_id.property_account_income_categ.id
        return {'value': values, 'domain': domain}
    
    def action_view_asset(self, cr, uid, ids, context=None):
        """
            Redirecciona a la vista formulario del activo seleccionado
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_asset', 'view_account_asset_asset_form')
        
        # Obtiene el id del activo que se va a mostrar
        asset_id = self.browse(cr, uid, ids[0], context=context).asset_id.id
        
        return {
            'name':_("Activo"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.asset.asset',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': asset_id
        }
    
    def _get_asset_value(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Regresa el valor contable del activo y el valor fiscal
        """
        res = {}
        inpc_obj = self.pool.get('account.fiscal.inpc')

        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'update_factor': 0.0,
                'value_account': 0.0,
                'value_fiscal': 0.0,
                'utility': 0.0
            }
            # Si no es una factura de activo deja los valores en cero
            if line.invoice_id.invoice_asset == False:
                continue
            # Valida que haya seleccionado un activo
            if not line.asset_id:
                continue
            # Informacion del activo
            inpca = str(line.invoice_id.date_invoice)[5:7] + '/' + str(line.invoice_id.date_invoice)[0:4]
            inpcb = str(line.asset_id.date)[5:7] + '/' + str(line.asset_id.date)[0:4]
            inpca_ids = inpc_obj.search(cr, uid, [('name','=',inpca)])
            inpcb_ids = inpc_obj.search(cr, uid, [('name','=',inpcb)])
            if len(inpca_ids) == 0:
                inpca = str(line.invoice_id.date_invoice)[0:4]
                inpca_ids = inpc_obj.search(cr, uid, [('fiscalyear','=',inpca)])

                if len(inpca_ids) == 0:
                    inpca = int(str(line.invoice_id.date_invoice)[0:4])-1
                    inpca_ids = inpc_obj.search(cr, uid, [('fiscalyear','=',inpca)])
            
            for a in inpc_obj.browse(cr, uid, inpcb_ids):
                inpc_actual = a.value
    
            for b in inpc_obj.browse(cr, uid, inpca_ids):
                inpc_anterior = b.value

            #raise osv.except_osv(inpc_actual, inpc_anterior)
            #update_factor = line.asset_id.update_factor
            #raise osv.except_osv('update', update_factor)
            update_factor = inpc_actual/inpc_anterior
            value_fiscal = (line.asset_id.value_residual/line.asset_id.product_qty) * update_factor
            value_account = (line.asset_id.value_residual/line.asset_id.product_qty)
            res[line.id]['update_factor'] = update_factor
            res[line.id]['value_account'] = value_account
            res[line.id]['value_fiscal'] = value_fiscal
            
            # Calcula la utilidad en base al precio aplicado
            total = line.quantity * line.price_unit
            res[line.id]['utility'] = total - (value_account * line.quantity)
            #raise osv.except_osv('res', res)
        return res
    
    def asset_create(self, cr, uid, lines, context=None):
        """
            Genera el nuevo activo
        """
        context = context or {}
        asset_obj = self.pool.get('account.asset.asset')
        # Recorre las lineas de la factura
        for line in lines:
            # Obtiene la fecha de depreciacion del activo
            date_asset = datetime.strptime(line.invoice_id.date_invoice, '%Y-%m-%d')
            day = date_asset.strftime('%d')
            month = date_asset.strftime('%m')
            # Valida si la fecha de compra no es el dia primero del mes
            if int(day) != 1:
                # Calcula para aplicar la depreciacion sobre el 1ro del mes siguiente
                date_asset = date_asset + relativedelta(months=+1)
                days = int(day) - 1
                date_asset = date_asset - timedelta(days=days)
            date_dep = date_asset.strftime('%Y-%m-%d')
            
            # Valida que tenga una categoria de activo
            if line.asset_category_id:
                if line.asset_group:
                    vals = {
                        'name': line.name + '-' + line.product_id.default_code if line.product_id.default_code else line.name,
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'code': line.invoice_id.number or False,
                        'category_id': line.asset_category_id.id,
                        'purchase_value': line.price_subtotal,
                        'period_id': line.invoice_id.period_id.id,
                        'partner_id': line.invoice_id.partner_id.id,
                        'company_id': line.invoice_id.company_id.id,
                        'currency_id': line.invoice_id.currency_id.id,
                        'purchase_date' : line.invoice_id.date_invoice,
                        'invoice_id': line.invoice_id.id,
                        'date': line.invoice_id.date_invoice,
                        'origin': 'purchase'
                    }
                    changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
                    vals.update(changed_vals['value'])
                    asset_id = asset_obj.create(cr, uid, vals, context=context)
                    if line.asset_category_id.open_asset:
                        asset_obj.validate(cr, uid, [asset_id], context=context)
                # Agrega un activo por cantidad
                else:
                    # Inicializa variables
                    name = line.name + '-' + line.product_id.default_code if line.product_id.default_code else line.name
                    i = 1
                    # Recorre la factura por la cantidad de productos
                    while (i <= line.quantity):
                        vals = {
                            'name':  name + ' (' + str(i) +')',
                            'product_id': line.product_id.id,
                            'product_qty': 1,
                            'code': line.invoice_id.number or False,
                            'category_id': line.asset_category_id.id,
                            'purchase_value': line.price_unit,
                            'period_id': line.invoice_id.period_id.id,
                            'partner_id': line.invoice_id.partner_id.id,
                            'company_id': line.invoice_id.company_id.id,
                            'currency_id': line.invoice_id.currency_id.id,
                            'purchase_date' : line.invoice_id.date_invoice,
                            'invoice_id': line.invoice_id.id,
                            'date': line.invoice_id.date_invoice
                        }
                        changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
                        vals.update(changed_vals['value'])
                        asset_id = asset_obj.create(cr, uid, vals, context=context)
                        if line.asset_category_id.open_asset:
                            asset_obj.validate(cr, uid, [asset_id], context=context)
                        # Incrementa el contador
                        i += 1
        return True
    
    _columns = {
        'asset_group': fields.boolean('Agrupar activo'),
        'asset_id': fields.many2one('account.asset.asset', 'Activo'),
        'update_factor': fields.function(_get_asset_value, string='Factor de Actualizacion', type="float", multi="assetvalue", store=True, digits=(16,4)),
        'value_account': fields.function(_get_asset_value, string='Valor contable', type="float", multi="assetvalue", store=True, digits_compute= dp.get_precision('Account')),
        'value_fiscal': fields.function(_get_asset_value, string='Costo fiscal', type="float", multi="assetvalue", store=True, digits_compute= dp.get_precision('Account')),
        'utility': fields.function(_get_asset_value, string='Utilidad/Perdida', type="float", multi="assetvalue", store=True, digits_compute= dp.get_precision('Account'))
    }
    
    _defaults = {
        'asset_group': False
    }

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        """
            Cuando se selecciona un producto de una compra pone la categoria del activo
        """
        if context is None:
            context = {}
        
        # Si no hay producto no hace modificaciones al registro
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain':{'product_uom':[]}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain':{'product_uom':[]}}
        
        # Funcion super de product_id_change
        result = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
        #print "*********************** result **************** ", result
        
        # Si la factura es de una compra revisa si el producto es un activo y pone la categoria
        if type in ('in_invoice', 'in_refund'):
            res = self.pool.get('product.product').browse(cr, uid, product, context=context)
            if res.is_asset:
                result['value']['asset_category_id'] = res.default_asset_category_id.id or False
        
        return result
    
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
