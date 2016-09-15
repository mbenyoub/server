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

import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import pytz

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_invoice(osv.Model):
    _inherit='account.invoice'
    
    def create_ir_attachment_facturae(self, cr, uid, ids, context=None):
        """
            Proceso para timbrado factura electronica automatico
        """
        seq_obj = self.pool.get('ir.sequence')
        ir_attach_obj = self.pool.get('ir.attachment.facturae.mx')
        try:
            # Proceso original para timbrado de facturas
            res = super(account_invoice, self).create_ir_attachment_facturae(cr, uid, ids, context=context)
            if not res:
                res = {}
            attach = res.get('res_id',False)
            if attach:
                #print "************* factura electronica *********** ", attach
                # Finaliza el proceso del timbrado sobre la factura
                ir_attach_obj.action_create_ir_attachment_facturae(cr, uid, [attach], context=context)
                return self.write(cr, uid, ids, {}, context=context)
        except Exception as inst:
            # Hace que si falla el proceso al validar la factura regrese al numero anterior de la serie
            inv = self.browse(cr, uid, ids[0], context=context)
            last = seq_obj.last_by_id(cr, uid, inv.journal_id.sequence_id.id, context=context)
            #print "*********** ids *********** ", ids
            #print "*********** regresar secuencia de ", inv.id, " ****** ", last
            
            #print "********** exepcion inst ************** ", inst
            
            title = 'Error! '
            value = ''
            
            # Regresa de nuevo la exepcion
            if type(inst) == list:
                title, value = inst.args
            else:
                value = inst
            raise osv.except_osv(title, value)
        return True
    
    def _check_stock(self, cr, uid, ids, field_names, args, context=None, query='', query_params=()):
        """
            Checa si hay un inventario relacionado por otro documento o por el mismo
        """
        res = {}
        picking_obj = self.pool.get('stock.picking')
        # Recorre los registros
        for inv in self.browse(cr, uid, ids, context=context):
            stock = True
            shipped = False
            picking_ids = []
            # Valida que el estado no este en borrador o una nota de debito
            if inv.state == 'draft' or inv.debit_note == True:
                stock = False
            else:
                # Valida si tiene una relacion sobre la factura
                if inv.ref:
                    #print "*********** Entro porque hay referencia ********* ", inv.ref
                    stock = False
                    # Identifica si la relacion es sobre la compra o la venta
                    if inv.type == 'out_invoice':
                        #print "****************************** es factura de venta ****************** "
                        # Busca compras relacionadas con el ingreso
                        reference = 'sale.order,%s'%(inv.ref.id,)
                        picking_ids = picking_obj.search(cr, uid, ['|',('sale_id','=', inv.ref.id),('reference','=',reference)], context=context)
                    elif inv.type == 'in_invoice':
                        #print "******************************* es factura de compra ***************** "
                        # Busca compras relacionadas con el ingreso
                        reference = 'purchase.order,%s'%(inv.ref.id,)
                        picking_ids = picking_obj.search(cr, uid, ['|',('purchase_id','=', inv.ref.id),('reference','=',reference)], context=context)
                # Valida si la factura tiene un albaran relacionado con la factura
                pick_inv_ids = picking_obj.search(cr, uid, [('invoice_id','=', inv.id)], context=context)
                if pick_inv_ids:
                    #print "*************** busca albaranes de facturas ************ ", pick_inv_ids
                    stock = False
                    shipped = True
                    # Agrega la informacion de los albaranes relacionados a las facturas
                    for pick_id in pick_inv_ids:
                        # Valida que no se encuentre ya registrado
                        if not (pick_id in picking_ids):
                            picking_ids.append(pick_id)
            
            #print "************* picking_ids *************** ", picking_ids
            if picking_ids and shipped == False:
                #Revisa si hay albaranes que no se hayan entregado
                pick_ids = picking_obj.search(cr, uid, [('id','in', picking_ids),('state','not in',['done','cancel'])], context=context)
                #print "************* pick_ids *************** ", pick_ids
                shipped = False if pick_ids else True
            
            # Valida que si el stock es automatico haya productos que se puedan inventariar
            if stock == True:
                stock = False
                # Recorre las lineas de factura
                for line in inv.invoice_line:
                    # Revisa si hay un producto asignado en la linea
                    if line.product_id:
                        if line.product_id.type == 'consu' or line.product_id.type == 'product':
                            stock = True
                            break
            
            res[inv.id] = {
                'apply_stock': stock,
                'picking_ids': picking_ids,
                'shipped': shipped
            }
            #print "****************** resultado factura  ", inv.id, " ********* ", res[inv.id]
        return res
    
    def _check_apply_deduction(self, cr, uid, ids, field_names, arg, context=None, query='', query_params=()):
        """
            Checa si se debe aplicar la deduccion sobre la factura
        """
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            apply = False
            apply_sale = False
            title = 'title_2'
            # Valida que el estado no este en borrador y que sea factura de proveedor
            if inv.state != 'draft' and inv.type == 'in_invoice':
                # Valida si el contacto tiene el regimen fiscal
                if inv.partner_id.regimen_fiscal_id:
                    # Actualiza el valor de la deduccion del pago sobre el cliente
                    apply = inv.partner_id.regimen_fiscal_id.apply_deduction
                # Obtiene el titulo de la compañia
                if inv.company_id:
                    #print "********** busca compañia *************** ", inv.company_id
                    if inv.company_id.partner_id and inv.company_id.partner_id.regimen_title:
                        title = inv.company_id.partner_id.regimen_title
            # Valida que el estado no este en borrador y que sea factura de cliente
            elif inv.state != 'draft' and inv.type == 'out_invoice':
                # Obtiene el titulo de la compañia
                if inv.company_id:
                    if inv.company_id.partner_id and inv.company_id.partner_id.regimen_title:
                        apply_sale = inv.company_id.partner_id.regimen_fiscal_id.apply_deduction_sale
            res[inv.id] = {
                'apply_deduction': apply,
                'apply_deduction_sale': apply_sale,
                'title': title
            }
        return res
    
    def _get_date_cancel(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la fecha de cancelacion
        """
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            date_cancel = False
            if inv.date_invoice_cancel:
                date_cancel = inv.date_invoice_cancel[:10]
            res[inv.id] = date_cancel
        return res
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """
            Actualiza la informacion del cliente sobre la factura
        """
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids,
            type, partner_id, date_invoice, payment_term, partner_bank_id,
            company_id)
        data_obj = self.pool.get('ir.model.data')
        
        # Si no esta el metodo de pago relacionado con el cliente pone el metodo de no identificado
        if res['value'].get('pay_method_id',False) == False:
            pay_method_id = False
            try:
                pay_method_id = data_obj.get_object(cr, uid, 'l10n_mx_payment_method', 'pay_method_none').id
            except:
                pass
            res['value']['pay_method_id'] = pay_method_id
        return res
    
    _columns = {
        'move_id_cancel': fields.many2one('account.move', 'Asiento Cancelacion', readonly=True, select=1, ondelete='restrict', help="Link to the automatically generated Journal Items."),
        'invoice_id': fields.many2one('account.invoice', 'Factura origen', readonly=True, select=1, ondelete='restrict', help="Referencia sobre factura"),
        'deduction_ids': fields.one2many('account.fiscal.deduction', 'invoice_id', 'Deducciones'),
        'apply_deduction': fields.function(_check_apply_deduction, string='Aplicar deduccion al pago', type='boolean', multi="regimen", store=True),
        'apply_deduction_sale': fields.function(_check_apply_deduction, string='Aplicar deduccion al cobro', type='boolean', multi="regimen", store=True),
        'title': fields.function(_check_apply_deduction, type='selection', multi="regimen", selection=[
                        ('title_2','Titulo 2'),
                        ('title_4','Titulo 4')], string='Titulo Empresa', readonly=True),
        'ref_invoice_cancel': fields.text('Motivo de cancelacion'),
        # 'apply_stock': fields.boolean('Inventario automatico'),
        'apply_stock': fields.function(_check_stock, string="Inventario automatico", multi="stock", readonly=True, type="boolean"),
        #'picking_id': fields.many2one('stock.picking.out', 'Salida Almacen', readonly=True),
        'picking_ids': fields.function(_check_stock, string="Inventario relacionado", multi="stock", readonly=True, relation="stock.picking", type="many2many"),
        #'picking_ids': fields.one2many('stock.picking.out', 'sale_id', 'Related Picking', readonly=True, help="This is a list of delivery orders that has been generated for this sales order."),
        'shipped': fields.function(_check_stock, string="Producto Entregado", multi="stock", readonly=True, type="boolean"),
        'date_cancel': fields.function(_get_date_cancel, string="Fecha cancelacion", readonly=True, type="date", store=True),
        #'date_cancel': fields.date('Fecha Cancelacion')
    }
    
    def _get_pay_method_default(self, cr, uid, context=None):
        """
            Obtiene no identificado por default
        """
        data_obj = self.pool.get('ir.model.data')
        res = False
        try:
            res = data_obj.get_object(cr, uid, 'l10n_mx_payment_method', 'pay_method_none').id
        except:
            pass
        return res
    
    _defaults = {
        'pay_method_id': _get_pay_method_default,
    }
    
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        """
            Relaciona el pago con la factura
        """
        # Funcionalidad original
        res = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
        
        inv = self.browse(cr, uid, ids[0], context=context)
        
        # Agrega relacion de pago con factura
        res['context']['default_invoice_id'] = res['context']['invoice_id']
        # Agrega la relacion del contacto al pago
        res['context']['default_partner_id'] = inv.partner_id.id
        return res
    
    #def invoice_validate(self, cr, uid, ids, context=None):
    #    """
    #        Si es una factura de reintegro se agrega la informacion a la factura de origen
    #    """
    #    for inv in self.browse(cr, uid, ids, context=context):
    #        # Valida si es una factura de reintegro y que proviene de una factura
    #        if (inv.type == 'out_refund' or inv.type == 'in_refund') and inv.invoice_id:
    #            #Ejecuta la cancelacion del timbrado de la factura
    #            self.sf_cancel_invoice(cr, uid, [inv.invoice_id.id], context=context)
    #            # Cancela la factura origen de la factura de reintegro y relaciona con la factura de reintegro
    #            self.write(cr, uid, [inv.invoice_id.id], {'invoice_id': inv.id}, context=context)
    #
    #    return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
    
    def invoice_validate(self, cr, uid, ids, context=None):
        """
            Valida el estado al que debe transicionar la factura, si es una nota de credito para el cliente pone a la factura relacionada como transicionada
        """
        #print "************ invoice_validate **************** "
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        inv_line_obj = self.pool.get('account.invoice.line')
        picking_m_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')
        delete_lines = []
        
        # Revisa si alguna factura es de nota de credito y ve si tiene que aplicar una modificacion sobre la factura origen
        for inv in self.browse(cr, uid, ids, context=context):
            # Valida que el monto total de la nota de credito no sea cero
            if inv.type in ['out_refund','in_refund']:
                if inv.amount_total == 0.0:
                    raise osv.except_osv(_('Error!'),_("No puede validar notas de credito en cero: '%s'!")%(inv.number,))
            
            # Valida que sea una nota de credito generada para el cliente
            if inv.type in ['out_refund','in_refund']:
                # Valida si tiene una factura origen
                if inv.invoice_id:
                    # valida que se tenga que generar la salida del almacen
                    if inv.apply_stock:
                        # Valida que no haya albaranes 
                        if not inv.picking_ids:
                            # Valida si va a ser una entrada o una salida de inventario
                            type = 'out'
                            if inv.type in ['out_refund','in_invoice']:
                                type = 'in'
                            # Genera el albaran con lo facturado
                            self._apply_picking(cr, uid, inv, inv.invoice_line, type, context=context)
        return super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
    
    def button_reset_taxes(self, cr, uid, ids, context=None):
        """
            Actualiza los detalles de las facturas
        """
        inv_tax_obj = self.pool.get('account.invoice.tax')
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['reset_tax'] = True
        ait_obj = self.pool.get('account.invoice.tax')
        
        # Funcion original de modificar
        #super(account_invoice, self).button_reset_taxes(cr, uid, ids, context=ctx)
        
        # Recorre las facturas
        for id in ids:
            # Elimina los impuestos de las facturas que no esten como manual
            cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
            # Obtiene el lenguaje del cliente de la factura
            partner = self.browse(cr, uid, id, context=ctx).partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})
            # Agrega los impuestos
            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
                # Valida que el impuesto a agregar no este cargado
                print "************ impuesto ************ ", taxe
                tax_code_id = taxe.get('tax_code_id',False)
                ait_ids = ait_obj.search(cr, uid, [('tax_code_id','=',tax_code_id),('invoice_id','=',id)])
                print "************ impuesto ************ ", ait_ids, " - ", tax_code_id
                
                if len(ait_ids) < 1:
                    print "*********** crea impuesto ************* "
                    # Agrega el impuesto a la lista
                    ait_obj.create(cr, uid, taxe)
        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
        return True
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Limpia los movimientos y facturas relacionadas al documento factura
        """
        if default is None:
            default = {}
        default.update({
            'state':'draft',
            'number':'',
            'move_id':False,
            'move_name':False,
            'internal_number': False,
            'period_id': False,
            'sent': False,
            'invoice_id': None,
            'move_id_cancel':None,
            'move_id': None,
            'name': None
        })
        if 'date_invoice' not in default:
            default.update({
                'date_invoice':False
            })
        if 'date_due' not in default:
            default.update({
                'date_due':False
            })
        # Continua con la funcionalidad original
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza los detalles de las facturas
        """
        # Funcion original de modificar
        super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        if context is None:
            context = {}
        ctx = context.copy()
        #print "******************** ctx ********** ", ctx.get('reset_tax'), "  - ", ctx
        
        # Actualiza los detalles
        if context.get('reset_tax',False) != True:
            ctx['reset_tax'] = True
            if type(ids) == int:
                ids = [ids]
            self.button_reset_taxes(cr, uid, ids, context=ctx)
            
        line_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id','in',ids)], context=context)
        if line_ids:
            self.pool.get('account.invoice.line').write(cr, uid, line_ids, {}, context=context)
        return True
    
    def create(self, cr, uid, vals, context=None):
        """
            Actualiza los datos de facturacion del cliente
        """
        if context is None:
            context = {}
        
        # Funcion original de crear
        res = super(account_invoice, self).create(cr, uid, vals, context=context)
        
        # Actualiza los impuestos sobre la factura
        ctx = context.copy()
        ctx['reset_tax'] = True
        # Funcion original de modificar
        self.button_reset_taxes(cr, uid, [res], context=ctx)
        return res
    
    def _get_period(self, cr, uid, context=None):
        """
            Obtiene el periodo actual
        """
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    
    def create_move_id_cancel(self, cr, uid, inv_id, move_id, context=None):
        """ 
            Esta funcion Genera los asiento inverso al de la factura
        """
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        link_obj = self.pool.get('links.get.request')
        date = time.strftime('%Y-%m-%d')
        if context is None:
            context = {}
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.invoice', 'Invoice', context=None)
        # Obtiene el periodo actual
        act_period_id = self._get_period(cr, uid, context=context)
        # Obtiene el movimiento
        move = move_obj.browse(cr, uid, move_id, context=context)
        ctx = context.copy()
        # Inicializa las variables para generar el movimiento
        mov_lines = []
        # Obtiene el numero de la secuencia del movimiento
        mov_number = 'CAN/' + move.name
        
        # Genera el asiento contable
        new_move = {
            'name': mov_number,
            'ref': move.name,
            'journal_id': move.journal_id.id,
            'period_id': act_period_id,
            'date': date,
            'narration': move.narration,
            'company_id': move.company_id.id,
            'to_check': move.to_check,
            'reference': 'account.invoice,' + str(inv_id),
            'state': 'posted'
        }
        move_id_cancel = move_obj.create(cr, uid, new_move, context=context)
        #print "*************** crea movimiento de cancelacion ************** ", move_id_cancel
        
        invoice = self.browse(cr, uid, inv_id, context=context)
        tax_apply = {}
        payment_advance = False
        # Aplica la cancelacion de impuestos sobre los pagos aplicados en la factura
        if invoice.payment_ids:
            advance_account_id = False
            # Obtiene la cuenta de los anticipos
            if invoice.type in ('out_invoice','out_refund'):
                if invoice.partner_id.property_account_advance_customer:
                    advance_account_id = invoice.partner_id.property_account_advance_customer.id
                else:
                    advance_account_id = invoice.partner_id.property_account_receivable.id
            else:
                if invoice.partner_id.property_account_advance_supplier:
                    advance_account_id = invoice.partner_id.property_account_advance_supplier.id
                else:
                    advance_account_id = invoice.partner_id.property_account_payable.id
            
            # Recorre los pagos
            for payment_line in invoice.payment_ids:
                # Guarda la lista de los ids de los pagos
                mov_lines.append(payment_line.id)
                
                if not payment_advance:
                    # Crea la linea de movimiento para registrar el anticipo sobre lo pagado en la factura a cancelar
                    payment_advance = {
                        'journal_id': move.journal_id.id,
                        'period_id': act_period_id,
                        'name': mov_number,
                        'account_id': advance_account_id,
                        'move_id': move_id_cancel,
                        'partner_id': invoice.partner_id.id or False,
                        'amount_currency': payment_line.amount_currency,
                        'credit': payment_line.credit,
                        'debit': payment_line.debit,
                        'date': date,
                        'ref': invoice.number,
                        'reference': 'account.invoice,' + str(inv_id),
                    }
                else:
                    payment_advance['credit'] += payment_line.credit
                    payment_advance['debit'] += payment_line.debit
                
                # Recorre los movimientos de la poliza
                for line in payment_line.move_id.line_id:
                    if line.reference.id == invoice.id and line.tax_code_id:
                        account_rec_id = False
                        #Obtiene la cuenta con la que realiza la conciliacion
                        for rec in line.reconcile_id.line_id:
                            if rec.account_id.id != line.account_id.id:
                                account_rec_id = rec.account_id.id
                                continue
                        
                        # Si ya esta registrado el apunte actualiza el valor del monto
                        if tax_apply.get(account_rec_id, False):
                            tax_apply[account_rec_id]['debit'] += line.credit
                            tax_apply[account_rec_id]['credit'] += line.debit
                            tax_apply[account_rec_id]['tax_amount'] += line.tax_amount
                            tax_apply[account_rec_id]['base'] += line.credit
                        else:
                            # Crea el nuevo registro
                            tax_apply[account_rec_id] = {
                                'journal_id': move.journal_id.id,
                                'period_id': act_period_id,
                                'name': line.name,
                                'account_id': line.account_id.id,
                                'move_id': move_id_cancel,
                                'partner_id': line.partner_id.id or False,
                                'amount_currency': line.amount_currency,
                                'quantity': line.quantity,
                                'credit': line.debit,
                                'debit': line.credit,
                                'date': date,
                                'ref': line.name,
                                'tax_code_id': line.tax_code_id.id or False,
                                'tax_amount': line.tax_amount * -1,
                                'base': line.base * -1,
                                'reference': 'account.invoice,' + str(inv_id),
                            }
        
        #print "*************** impuestos aplicados ******** ", tax_apply
        
        # Recorre las lineas del movimiento
        for line in move.line_id:
            debit = 0.0
            credit = 0.0
            add_move = False
            # Obtiene el valor del impuesto aplicado si esta sobre la cuenta
            if tax_apply.get(line.account_id.id, False):
                debit = tax_apply[line.account_id.id]['debit']
                credit = tax_apply[line.account_id.id]['credit']
                # Crea el nuevo registro sobre los impuestos aplicados
                new_id = move_line_obj.create(cr, uid, tax_apply[line.account_id.id], context=context)
                #mov_lines.append(new_id)
            # Valida si la linea de movimiento es la del movimiento pr
            elif (invoice.account_id.id == line.account_id.id):
                add_move = True
                if payment_advance:
                    debit = payment_advance['debit']
                    credit = payment_advance['credit']
                    # Crea un nuevo apunte registrando los pagos de anticipo
                    new_id = move_line_obj.create(cr, uid, payment_advance, context=context)
            
            # Genera las lineas de movimiento sobre el ingreso con el efecto contrario a la factura original
            move_line = {
                'journal_id': move.journal_id.id,
                'period_id': act_period_id,
                'name': line.name,
                'account_id': line.account_id.id,
                'move_id': move_id_cancel,
                'partner_id': line.partner_id.id or False,
                'amount_currency': line.amount_currency,
                'quantity': line.quantity,
                'credit': (line.debit - credit),
                'debit': (line.credit - debit),
                'date': date,
                'ref': line.name,
                'reference': 'account.invoice,' + str(inv_id),
            }
            #print "***************** create move line ************* ", move_line
            new_id = move_line_obj.create(cr, uid, move_line, context=context)
            if add_move:
                mov_lines.append(new_id)
            #print "*************************** new_id cancel ******** ", new_id
        return move_id_cancel, mov_lines
    
    def sf_cancel_invoice(self, cr, uid, invoice_id, context=None):
        """
            Ejecuta la funcionalidad de cancelar para los timbrados de facturacion electronica
        """
        if context is None:
            context = {}
        #print "***************** cancelar sf agregado a account_fiscal ************* ", invoice_id, " - ", type(invoice_id)
        # Funcionalidad cancelar l10n_mx_ir_attachment_facturae/invoice
        ir_attach_obj = self.pool.get('ir.attachment.facturae.mx')
        id_attach = ir_attach_obj.search(cr, uid, [('invoice_id', '=', invoice_id)], context=context)
        wf_service = netsvc.LocalService("workflow")
        inv_type_facturae = {
            'out_invoice': True,
            'out_refund': True,
            'in_invoice': False,
            'in_refund': False}
        inv = self.browse(cr, uid, invoice_id)
        if inv_type_facturae.get(inv.type, False):
            for attachment in ir_attach_obj.browse(cr, uid, id_attach, context=context):
                if attachment.state == 'done':
                    wf_service.trg_validate(
                        uid, 'ir.attachment.facturae.mx',
                        attachment.id, 'action_cancel', cr)
        return True
    
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        """
            Quita la referencia a el codigo de impuestos para crear el movimimento de la factura
        """
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            #'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }
    
    def action_move_create(self, cr, uid, ids, context=None):
        """
            Agrega al asiento contable la informacion de los impuestos
        """
        #print "******************* context **************** ", context
        if context is None:
            context = {}
        
        # Funcionalidad original de create
        res = super(account_invoice, self).action_move_create(cr, uid, ids, context)
        
        ait_obj = self.pool.get('account.invoice.tax')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        move_tax_obj = self.pool.get('account.move.tax')
        link_obj = self.pool.get('links.get.request')
        
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.invoice', 'Invoice', context=None)
        
        # Recorre las facturas
        for inv in self.browse(cr, uid, ids, context=context):
            move_tax_ids = []
            
            # Obtiene el movimiento a aplicar en el asiento
            ml_ids = move_line_obj.search(cr, uid, [('state','=','valid'), '|',('account_id.type', '=', 'payable'),('account_id.type', '=', 'receivable'), ('reconcile_id', '=', False), ('move_id', '=', inv.move_id.id)], context=context)
            # Valida que se haya encontrado el apunte
            if not len(ml_ids):
                raise osv.except_osv('Error Validacion', 'Ocurrio un error al tratar de obtener los apuntes del Asiento creado.')
            
            # Valida que haya un monto a pagar
            if inv.amount_total:
                # Obtiene los impuestos de la factura
                for tax_line in inv.tax_line:
                    # Si es nota de venta no agrega referencia de impuestos a trasladar
                    if inv.note_sale:
                        continue
                    
                    # Valida que tenga valor en la base del monto
                    if tax_line.base:
                        account_id = False
                        # Actualiza el valor de la cuenta a aplicar para los impuestos
                        if inv.type in ('out_invoice','in_invoice'):
                            account_id = tax_line.account_tax_id.account_collected_id_apply.id or False
                        else:
                            account_id = tax_line.account_tax_id.account_paid_id_apply.id or False
                        # Si la factura no hay un registro por acreditar se aplica el impuesto en ese momento
                        if not account_id:
                            # Busca en el movimiento donde se aplica el impuesto 
                            ml_ids = move_line_obj.search(cr, uid, [('account_id','=',tax_line.account_id.id),('move_id', '=', inv.move_id.id)], context=context)
                            # Valida que se haya encontrado el apunte
                            if ml_ids:
                                # Si es nota de venta no pone el codigo de impuesto
                                tax_code_id = False
                                # Valida que el diario de la factura no sea de nota de venta
                                if not inv.note_sale:
                                    tax_code_id = tax_line.tax_code_id.id or False
                                
                                # Agrega los valores del codigo de impuesto
                                move_line_obj.write(cr, uid, ml_ids, {
                                        'tax_amount': tax_line.amount,
                                        'base': tax_line.base,
                                        'tax_code_id': tax_code_id}, context=context)
                                # Continua con el siguiente impuesto
                                continue
                        # Valida que no sea una factura global
                        if inv.global_invoice:
                            continue
                        
                        # Obtiene el porcentaje aplicado sobre el impuesto
                        percent = tax_line.amount/inv.amount_total
                        # Crea el nuevo movimiento de referencia para trasladar impuestos
                        mt_id = move_tax_obj.create(cr, uid, {
                                                    'move_line_id':ml_ids[0],
                                                    'name': tax_line.name,
                                                    'tax_id': tax_line.account_tax_id.id or False,
                                                    'invoice_total': inv.amount_total,
                                                    'base': tax_line.base,
                                                    'base_tax': tax_line.amount,
                                                    'tax_code_id': tax_line.tax_code_id.id or False,
                                                    'amount': 0.0,
                                                    'percent': percent,
                                                    'account_id': account_id or False}, context=context)
                        move_tax_ids.append(mt_id)
            percent = 0
            if inv.amount_total > 0:
                percent = inv.amount_untaxed/inv.amount_total
            # Actualiza el movimiento de cuentas por pagar
            # move_line_obj.write(cr, uid, ml_ids, {'base': inv.amount_untaxed, 'percent': percent}, context=context)
            
            # Obtiene los apuntes del movimiento
            ml_ids = move_line_obj.search(cr, uid, [('move_id', '=', inv.move_id.id)], context=context)
            move_line_obj.write(cr, uid, ml_ids, {'reference': 'account.invoice,' + str(inv.id), 'partner_id': inv.partner_id.id}, context=context)
            
            #~ Relaciona el documento movimiento con la factura 
            move_obj.write(cr, uid, [inv.move_id.id], {'reference': 'account.invoice,' + str(inv.id)})
        return res
    
    def action_cancel_wizard(self, cr, uid, ids, context=None):
        """
            Muestra la venta con la funcionalidad para cancelar la factura
        """
        if context is None:
            context = {}
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_invoice_cancel_wizard')
        
        # Obtiene la informacion de la factura a cancelar
        inv = self.browse(cr, uid, ids[0], context=context)
        
        # Valida que la factura no se encuentre en estado borrador
        if inv.state == 'draft':
            raise osv.except_osv(_('Error!'), _('No se pueden cancelar facturas en estado borrador.'))
        
        # Valida que no haya notas de credito aplicadas sobre la factura
        if inv.refund_ids:
            raise osv.except_osv(_('Error!'), _('No se pueden cancelar facturas que contienen notas de credito aplicadas.'))
        
        # Obtiene los parametros que van por default
        context['default_invoice_id'] = inv.id
        context['type_invoice'] = inv.type
        
        return {
            'name':_("Cancelacion de Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice.cancel.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
    
    def action_cancel(self, cr, uid, ids, context=None):
        """
            Cancela la factura
        """
        return True
        
    def action_invoice_cancel(self, cr, uid, invoice_id, context=None):
        """
            Cancela la factura
        """
        account_move_line_obj = self.pool.get('account.move.line')
        # Ejecuta la funcionalidad de cancelar el timbrado
        self.sf_cancel_invoice(cr, uid, invoice_id, context=context)
        #print "**************** funcion cancel fiscal ***************** "
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        #invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids','state','account_id'])
        move_ids = [] # ones that we will need to remove
        invoice = self.browse(cr, uid, invoice_id, context=context)
        if invoice.state == 'draft':
            return True
        
        if invoice.move_id:
            move_ids.append(invoice.move_id.id)
        
        # Proceso validacion de pagos en factura omitido
        #if invoice.payment_ids:
        #    p_ids = []
        #    for move_line in invoice.payment_ids:
        #        if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
        #            raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))
        to_reconcile_ids = []
        # Genera movimiento inverso para la cancelacion de la factura si tiene un movimiento
        move_id_cancel, to_reconcile_ids = self.create_move_id_cancel(cr, uid, invoice.id, invoice.move_id.id, context=context)
        print "***************** movimiento de cancelacion de factura ************ ", move_id_cancel
        
        # Concilia los movimientos y elimina la relacion con los voucher generados
        movelines = invoice.move_id.line_id
        for line in movelines:
            print "**************** cuenta a conciliar cancelacion ************ ", invoice.account_id.id
            # Si la linea es la principal donde se carga el monto facturado la pasa a los valores a conciliar
            if line.account_id.id == invoice.account_id.id:
                to_reconcile_ids.append(line.id)
                # Si ya hay conciliaciones sobre el movimiento las rompe
                if type(line.reconcile_id) != osv.orm.browse_null:
                    reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
        print "******* movimientos concliados ************ ", to_reconcile_ids
        # Aplica conciliacion en la cancelacion
        account_move_line_obj.reconcile(cr, uid, to_reconcile_ids,
                    writeoff_period_id=invoice.period_id.id,
                    writeoff_journal_id = invoice.journal_id.id,
                    writeoff_acc_id=invoice.account_id.id
                    )
        
        # Concilia los movimientos y elimina la relacion con los voucher generados
        #movelines = invoice.move_id.line_id
        #to_reconcile_ids = {}
        #for line in movelines:
        #    if line.account_id.id == invoice.account_id.id:
        #        to_reconcile_ids[line.account_id.id] = [line.id]
        #    if type(line.reconcile_id) != osv.orm.browse_null:
        #        reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
        #
        #for line in account_move_obj.browse(cr, uid, move_id_cancel, context=context).line_id:
        #    if line.account_id.id == invoice.account_id.id:
        #        to_reconcile_ids[line.account_id.id].append(line.id)
        #
        #for account in to_reconcile_ids:
        #    account_move_line_obj.reconcile(cr, uid, to_reconcile_ids[account],
        #                writeoff_period_id=invoice.period_id.id,
        #                writeoff_journal_id = invoice.journal_id.id,
        #                writeoff_acc_id=invoice.account_id.id
        #                )
        
        # First, set the invoices as cancelled and detach the move ids
        self.write(cr, uid, [invoice.id], {
            'state':'cancel',
            'date_invoice_cancel': time.strftime('%Y-%m-%d %H:%M:%S'),
            #'date_cancel': time.strftime('%Y-%m-%d'),
            'ref_invoice_cancel': context.get('reference',''),
            'move_id_cancel': move_id_cancel})
        
        # if move_ids:
            # second, invalidate the move(s)
            # account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            
            # No eliminar los movimientos
            # account_move_obj.unlink(cr, uid, move_ids, context=context)
        self._log_event(cr, uid, [invoice.id], -1.0, 'Cancel Invoice')
        return True
    
    def check_tax_lines(self, cr, uid, inv, compute_taxes, ait_obj):
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id
        if not inv.tax_line:
            print "********************** compute_taxes ****************** ", compute_taxes
            for tax in compute_taxes.values():
                print "**************** compute tax ***************** ", tax
                ait_obj.create(cr, uid, tax)
        else:
            tax_key = []
            for tax in inv.tax_line:
                if tax.manual:
                    continue
                key = (tax.account_tax_id.id, tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id, tax.account_analytic_id.id)
                print "****************** key ****************** ", key
                tax_key.append(key)
                if not key in compute_taxes:
                    raise osv.except_osv(_('Warning!'), _('Global taxes defined, but they are not in invoice lines !'))
                base = compute_taxes[key]['base']
                print "***************** base **************** ", base
                if abs(base - tax.base) > company_currency.rounding:
                    raise osv.except_osv(_('Warning!'), _('Tax base different!\nClick on compute to update the tax base.'))
            #for key in compute_taxes:
            #    if not key in tax_key:
            #        raise osv.except_osv(_('Warning!'), _('Taxes are missing!\nClick on compute button.'))
    
    def date_to_datetime(self, cr, uid, userdate, context=None):
        """ Convert date values expressed in user's timezone to
        server-side UTC timestamp, assuming a default arbitrary
        time of 12:00 AM - because a time is needed.
    
        :param str userdate: date string in in user time zone
        :return: UTC datetime string for server-side use
        """
        # TODO: move to fields.datetime in server after 7.0
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        """
            Obtiene la informacion principal del documento de albaran a generar por la factura
        """
        pick_name = '/'
        invoice_id = order.id
        if context is None:
            context = {}
        type = context.get('type','out')
        
        # Obtiene el nombre de la entrega segun sea el caso
        if type == 'out':
            pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        else:
            pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
        
        res = {
            'name': pick_name,
            'origin': order.number,
            'invoice_id': invoice_id,
            'date': self.date_to_datetime(cr, uid, order.date_invoice, context),
            'type': type,
            'state': 'auto',
            'move_type': 'one',
            'partner_id': order.partner_id.id,
            'note': order.comment,
            'invoice_state': 'none',
            'company_id': order.company_id.id,
        }
        
        # Si es una nota de credito asigna a la factura origen el albaran y deja una referencia sobre la nota de credito
        if order.type in ['in_refund','out_refund']:
            res['invoice_id'] = order.invoice_id.id
            res['reference'] = 'account.invoice,%s'%(order.id,)
        return res
    
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, type='out', context=None):
        """
            Prepara la informacion de la entrega del producto
        """
        if type == 'out':
            location_id = order.shop_id.warehouse_id.lot_stock_id.id
            output_id = order.shop_id.warehouse_id.lot_output_id.id
        else:
            location_id = order.shop_id.warehouse_id.lot_input_id.id
            output_id = order.partner_id.property_stock_supplier.id
        
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.quantity,
            'product_uom': line.uos_id.id,
            'product_uos_qty': line.quantity,
            'product_uos': line.uos_id.id,
            'partner_id': order.partner_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'tracking_id': False,
            'state': 'draft',
            'type': type,
            'company_id': order.company_id.id,
            'price_unit': line.price_unit or 0.0,
            'invoice_line_id': line.id
        }

    def _apply_picking(self, cr, uid, invoice, invoice_lines, type='out', context=None):
        """
            Aplica la entrada/salida de los productos en el inventario
        """
        todo_moves = []
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        partial_data = {}
        if context is None:
            context = {}
        context['type'] = type
        # Crea la orden de entrega
        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, invoice, context=context))
        # Crea las lineas de los productos a entregar
        for line in invoice_lines:
            date_planned = invoice.date_invoice
            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    # Valida las existencias del producto
                    #if line.product_id.qty_available < line.quantity:
                    #    raise osv.except_osv('Existencias Insuficientes', 'No existencias suficientes para entregar el producto %s'%(line.product_id.name,))
                    
                    # Valida que si es una nota de credito, que el concepto sea por devolucion
                    if invoice.type in ['in_refund','out_refund']:
                        if line.edit_refund != 'dev':
                            continue
                    
                    # Genera la linea del movimiento
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, invoice, line, picking_id, date_planned, type, context=context))
                    # Actualiza informacion para la entraga del producto
                    partial_data['move%s' % (move_id)] = {
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'product_uom': line.uos_id.id,
                    }
                    todo_moves.append(move_id)
        # Genera la entrega del producto
        if picking_id:
            move_obj.action_confirm(cr, uid, todo_moves)
            move_obj.force_assign(cr, uid, todo_moves)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            #picking_obj.draft_validate(cr, uid, [picking_id], context=context)
            #picking_obj.do_partial(cr, uid, [picking_id], partial_data, context=context)
            
        self.write(cr, uid, [invoice.id], {}, context=context)
        return picking_id

    def action_ship_create(self, cr, uid, ids, context=None):
        """
            Genera la entrega de las facturas
        """
        # Recorre los registros
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.apply_stock:
                # Valida que no haya albaranes 
                if not invoice.picking_ids:
                    #print "***************** factura"
                    # Valida si va a ser una entrada o una salida de inventario
                    type = 'out'
                    if invoice.type in ['out_refund','in_invoice']:
                        type = 'in'
                    #print "***************** type ************ ", type
                    # Genera el albaran con lo facturado
                    self._apply_picking(cr, uid, invoice, invoice.invoice_line, type, context=context)
        return True
    
account_invoice()

class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"
    
    def action_redirect_invoice(self, cr, uid, ids, context=None):
        """
            Redirecciona a la factura del registro
        """
        # Obtiene el objeto a cargar
        invoice_line = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
        
        return {
            'name':_("Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': invoice_line.invoice_id.id or False
        }
    
    def action_redirect_invoice_supplier(self, cr, uid, ids, context=None):
        """
            Redirecciona a la factura del registro
        """
        # Obtiene el objeto a cargar
        invoice_line = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        
        return {
            'name':_("Factura"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id': invoice_line.invoice_id.id
        }
    
    def _get_account_tax(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la cuenta del impuesto
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = False
            for tax in line.invoice_line_tax_id:
                res[line.id] = tax.id
                break
        return res
    
    _columns = {
        'journal_id': fields.related('invoice_id', 'journal_id', type='many2one', relation='account.journal', string='Diario', store=True, readonly=True),
        'period_id': fields.related('invoice_id', 'period_id', type='many2one', relation='account.period', string='Periodo', store=True, readonly=True),
        'currency_id': fields.related('invoice_id', 'currency_id', type='many2one', relation='res.currency', string='Moneda', store=True, readonly=True),
        'user_id': fields.related('invoice_id', 'user_id', type='many2one', relation='res.users', string='Comercial', store=True, readonly=True),
        'date_invoice': fields.related('invoice_id','date_invoice', type='date', readonly=True, store=True, string='Fecha factura'),
        'invoice_number': fields.related('invoice_id','number', type='char', readonly=True, store=True, string='Factura'),
        'state': fields.related('invoice_id','state', type='selection', selection=[('draft','Borrador'),('open','Abierto'),('paid','Pagado'),('cancel','Cancelado')], readonly=True, store=True, string='Estado Factura'),
        'type_invoice': fields.related('invoice_id','type', type='selection', selection=[
                                                                            ('out_invoice','Customer Invoice'),
                                                                            ('in_invoice','Supplier Invoice'),
                                                                            ('out_refund','Customer Refund'),
                                                                            ('in_refund','Supplier Refund'),
                                                                            ], readonly=True, store=True, string='Tipo Factura'),
        'account_tax': fields.function(_get_account_tax, type='many2one', relation='account.tax', string='Impuesto', store=True)
    }
    
    _defaults = {
        'account_id': False
    }
    
    def _default_account_id(self, cr, uid, context=None):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        if context is None:
            context = {}
        if context.get('type_invoice') in ('out_invoice','out_refund'):
            #print "*************** categoria ingresos ************ "
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
        else:
            #print "*************** categoria salida ************ "
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category', context=context)
        #print "************ prop ************** ", prop
        return prop and prop.id or False

account_invoice_line()

class account_invoice_tax(osv.Model):
    _inherit = "account.invoice.tax"
    
    def compute(self, cr, uid, invoice_id, context=None):
        """
            Calcula los impuestos de la factura, Agrega parametro de account_tax_id en el key
        """
        tax_grouped = {}
        compute_all = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        for line in inv.invoice_line:
            #if inv.type in ['out_refund','in_refund'] or inv.debit_note == True:
            #    compute_all = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_subtotal), 1, line.product_id, inv.partner_id)['taxes']
            #else:
            #    compute_all = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, line.product_id, inv.partner_id)['taxes']
            #for tax in compute_all:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_subtotal), 1, line.product_id, inv.partner_id)['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
                val['account_tax_id'] = tax['id']
                
                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                    # Si es una nota de venta pone la cuenta de la factura de notas de venta
                    if inv.type == 'out_invoice' and inv.note_sale:
                        # Pone en la cuenta del puesto la cuenta de nota de venta
                        tax_data = tax_obj.browse(cr, uid, tax['id'], context=context)
                        if tax_data.account_collected_note_id:
                            val['account_id'] = tax_data.account_collected_note_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['account_tax_id'], val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                #print "***************** key compute tax **************** ", key
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
        
        #print "**************** tax grouped ************* ", tax_grouped
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
            
        #print "**************** tax grouped ************* ", tax_grouped
        return tax_grouped
    
    _columns = {
        'account_tax_id': fields.many2one('account.tax', 'Tax', select=True)
    }

account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
