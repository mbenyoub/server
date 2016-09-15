# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Author: Yannick Gouin <yannick.gouin@elico-corp.com>
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
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from openerp.tools.translate import _
from pytz import timezone
import openerp.addons.decimal_precision as dp

class delivery_priority(osv.osv):
    """
        Prioridades de entrega disponibles
    """
    _name = "delivery.priority"
    _description = "Delivery Priority"
    
    _columns = {
        'name': fields.char('Nombre', required=True, size=64),
        'value': fields.char('Valor', size=32)
    }
    
delivery_priority()
    
class delivery_term(osv.osv):
    """
        Plazos de entrega
    """
    _inherit = "delivery.term"
    _description = "Delivery Term"
    
    def get_week_next(self, cr, uid, num_week=1, context=None):
        """
            Obtiene el numero siguiente de la semana contando de 1-7
        """
        if num_week == 7:
            num_week = 1
        else:
            num_week += 1
        
        return num_week
    
    def get_date_next(self, cr, uid, date, value=0, unit='hours', context=None):
        """
            Valida dias inhabiles para calcular la fecha siguiente
        """
        config_obj = self.pool.get('delivery.config.settings')
        # Obtiene la configuracion de dias inhabiles sobre los dias de la semana
        config_week = config_obj.get_config_settings_week(cr, uid, context=context)
        hours_date = 24
        next_value = 0
        validate_hours = 0
        # Obtiene la zona horaria configurada
        tz_utc = pytz.utc
        tz = self.get_timezone(cr, uid, context=context)
        
        if unit != 'minutes':
            # Valida el dia de semana de la fecha actual
            datet = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
            if tz != 'UTC':
                datet = datet.astimezone(timezone(tz))
            num_week = datetime.isoweekday(datet)
            #print "*********** numero dia de la semana (actual) ********* ", num_week, ' - ', datet
            
            # Obtiene el total de dias en horas
            total_hours = value
            if unit == 'days':
                total_hours = total_hours * hours_date
            #print "********************** total horas *********** ", total_hours
            
            validate_week = 'week%s'%(num_week,)
            
            # Valida si hay dias inhabiles entre las entregas
            while validate_hours != total_hours:
                # Valida si es un dia inhabil el dia de la semana
                if config_week.get(validate_week,False) == False:
                    #print "************** dia inhabil ********* ", validate_week
                    # Dias inhabiles a recorrer
                    next_value += hours_date
                else:
                    # Si son menos de 24 horas agrega el tiempo sobre el dia de la entrega
                    if (total_hours - validate_hours) < hours_date:
                        #print "************* menor a 24 horas ****************** ", total_hours - validate_hours 
                        validate_hours = total_hours
                    else:
                        # Si es un dia habil descuenta 24 horas del tiempo de entrega
                        validate_hours += hours_date
                        #print "************** dia habil ********* ", validate_week
                    #print "************************ horas validadas ************ ", validate_hours
                # Recorre a la siguiente semana
                num_week = self.get_week_next(cr, uid, num_week, context=context)
                validate_week = 'week%s'%(num_week,)
            
            #print "************** horas dias inhabiles ********* ", next_value
            
            # Funcion original de obtener fecha
            res = super(delivery_term, self).get_date_next(cr, uid, date, value=(total_hours+next_value), unit='hours', context=context)
        else:
            # Funcion original de obtener fecha
            res = super(delivery_term, self).get_date_next(cr, uid, date, value=value, unit=unit, context=context)
        
        #print "************************ resultado fecha ************** ", res
        
        # Valida el dia de la fecha obtenida
        datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc)
        if tz != 'UTC':
            datet = datet.astimezone(timezone(tz))
        #datet = datetime.strptime(res, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_utc).astimezone(timezone(tz))
        num_week = datetime.isoweekday(datet)
        next_value = 0
        #print "*********** fecha formato Mexico ******************* ", datet
        #print "*********** numero dia de la semana ********* ", num_week
        
        validate_week = 'week%s'%(num_week,)
        
        # Valida si el dia de la entrega es un dia inhabil
        while config_week.get(validate_week,False) == False:
            #print "************** fec nueva dia inhabil ********* ", validate_week
            next_value += hours_date
            # Recorre a la siguiente semana
            num_week = self.get_week_next(cr, uid, num_week, context=context)
            validate_week = 'week%s'%(num_week,)
        #print "************** fec nueva dia habil ********* ", validate_week
        # Incrementa la fecha de entrega con los dias dela semana inhabiles
        if next_value > 0:
            #print "************** fec nueva - incrementar horas ********* ", next_value
            datet = datet + timedelta(hours=next_value)
        
        datet = datet.astimezone(tz_utc)
        res = datet.strftime('%Y-%m-%d %H:%M:%S')
        
        #print "********* Fecha final ************* ", res
        return res

delivery_term()

class delivery_route(osv.osv):
    _inherit = 'delivery.route'
    
    _columns = {
        'paid_log_ids': fields.one2many('delivery.route.paid.log', 'route_id', 'Pagos realizados')
    }

class delivery_route_line(osv.osv):
    _inherit = 'delivery.route.line'
    
    def _get_sign_paid(self, cr, uid, ids, fields_name, args, context=None):
        """
            Indica si el cliente debe pagar el pedido en caso de no contar con credito y
            muestra el botón de 'pago' si el estado de la factura es 'abierto
        """
        res = {}
        date = time.strftime('%Y-%m-%d')
        # Obtiene la configuracion
        config_obj = self.pool.get('delivery.config.settings')
        config = config_obj.get_setting_payment(cr, uid, context=context)
        
        # Recorremos los ids
        for id in ids:
            res[id] = {
                'paid_button_show': False,
                'paid_all_sign': False,
                'paid_cash_sign': False,
            }
            
            # Valida que apliquen condiciones sobre pago
            if not config['payments_enable']:
                continue
            
            delivery = self.read(cr, uid, id, ['credit_available', 'date_due', 'invoice_state', 'residual'])
            print "*****DATE_DUE*****: ", delivery['date_due']
            print "*****DATE*****: ", date
            # Se valida que el cliente disponga del credito para pagar y la factura no este vencida
            if delivery['credit_available'] == 0.0 and delivery['date_due'] <= date and delivery['credit_available'] < delivery['residual']:
                res[id]['paid_all_sign'] = True
                
            #if type_payment_term == 'cash':
            #    res[id]['paid_cash_sign'] = True
            
            
        #if type_payment_term == 'cash':
        #    self.write(cr, uid, ids, {'state': 'pending_paid'}, context=context)
        #    # Registra el log sobre la actualizacion sobre la transicion de estado
        #    self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='pending_paid', context=context)
            
            
            # Se valida si existe un pago pendiente
            if delivery['residual'] > 0.0:
                res[id]['paid_button_show'] = True
        return res
        
    _columns = {
        'residual': fields.related('invoice_id', 'residual', type='float',
            digits_compute=dp.get_precision('Delivery'), string="Monto a pagar"),
        'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string="Fecha factura"),
        'date_due': fields.related('invoice_id', 'date_due', type='date', string="Fecha vencimiento"),
        'payment_term': fields.related('invoice_id', 'payment_term', type='many2one', relation='account.payment.term',
            string="Plazo de pago" ),
        'state': fields.selection([
                            ('draft','No planeado'),
                            ('planned','Planeado'),
                            ('open','Por surtir'),
                            ('pending_paid', 'Esperando pago'),
                            ('arrived','Arribado'),
                            ('delivered', 'En entrega'),
                            ('delivered_carrier', 'En entrega transportista'),
                            ('exeption', 'Excepcion entrega'),
                            ('done', 'Entregado'),
                            ('pending_paid_delivered', 'Esperando pago de entrega'),
                            ('pending_credit', 'Autorizacion credito'),
                            ('paid', 'pagado'),
                            ('not_found', 'No encontrado'),
                            ('return', 'Devuelto'),
                            ('picking', 'Entregado Almacen'),
                            ('cancel','Cancelado')], string='Estado entrega', store=True, readonly=True),
        'credit_available': fields.related('address_id', 'credit_available', type="float",
            string="Credito disponible", digits_compute=dp.get_precision('Delivery')),
        'paid_button_show': fields.function(_get_sign_paid, type='boolean', string="Mostrar boton pago", store=False,
            multi='paid'),
        'paid_all_sign': fields.function(_get_sign_paid, type='boolean', string="Pagar todo", store=False,
            multi='paid'),
        'pending_credit': fields.boolean('solicito credito?')
    }
    
    def action_paid(self, cr, uid, ids, context=None):
        """
            Abre el wizard para realizar el pago además de pasar el pedido al estado 'En entrega'
        """
        #paid_obj = self.pool.get('paid.manager.wizard')
        move = self.browse(cr, uid, ids[0], context=context)
        invoice = move.invoice_id
        residual = move.residual
        route_id = move.route_id.id or False
           
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'delivery_plan',
            'paid_manager_wizard')
        return {
            'name': 'Pagar factura',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'paid.manager.wizard',
            'target' : 'new',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            #'res_id': paid_id
            'context': {
                #'payment_expected_currency': invoice.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(invoice.partner_id).id,
                'default_amount': invoice.type in ('out_refund', 'in_refund') and -residual or residual,
                'default_reference': invoice.name,
                #'close_after_process': True,
                #'invoice_type': invoice.type,
                'default_invoice_id': invoice.id,
                'default_route_id': route_id,
                #'default_type': invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                #'type': invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }
    
    def action_arrived(self, cr, uid, ids, context=None):
        """
            Pasa la entrega a estado arrivado validando que el tipo de pago no sea de contado
        """
        type_payment_term = self.browse(cr, uid, ids[0], context=context).payment_term.type
        #print "******TYPE_PAYMENT_TERM*****: ", type_payment_term
        
        super(delivery_route_line, self).action_arrived(cr, uid, ids, context=context)
        return True
        
    #def action_done(self, cr, uid, ids, context=None):
    #    """
    #        Valida si hay algun adedudo una vez entregado el producto, en caso de haberlo se realiza el cobro
    #    """
    #    super(delivery_route_line, self). action_done(cr, uid, ids, context=context)
    #    
    #    move = self.browse(cr, uid, ids[0], context=context)
    #    if move.residual > 0:
    #        self.write(cr, uid, ids, {'state': 'pending_paid_delivered'}, context=context)
    #        # Registra el log sobre la actualizacion sobre la transicion de estado
    #        self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='pending_paid_delivered', context=context)
    #        return True
    #    else:
    #        return True
        
    def action_requisition_credit_new(self, cr, uid, ids, context=None):
        """
            Permite realizar una solicitud de credito
        """
        if context is None:
            context = {}
            
        #if self.browse(cr,uid,ids[0], context=context).pending_credit == False:
        #    self.write(cr, uid, ids, {'state': 'pending_credit', 'pending_credit': True}, context=context)
        #    # Registra el log sobre la actualizacion sobre la transicion de estado
        #    self.pool.get('delivery.route.line.log').add_log_route_line(cr, uid, ids, state='pending_credit', context=context)
            
        
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'requisition_credit', 'requisition_credit_credit_new_form_view')
        
        route_line = self.browse(cr, uid, ids[0], context=context)
        
        # Obtiene los parametros que van por default
        context['default_partner_id'] = route_line.invoice_id.partner_id.id or False
        context['default_rfc'] = route_line.invoice_id.partner_id.rfc
        context['default_current_credit'] = route_line.invoice_id.partner_id.credit_limit
        context['default_user_id'] = uid
        context['default_state'] = 'open'
        
        return {
            'name':_("Solicitud de credito"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'requisition.credit.credit',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context
        }
    
delivery_route_line()

class delivery_route_paid_log(osv.Model):
    _name = 'delivery.route.paid.log'
    
    _description = 'Realiza el log de los pagos en la ruta'
    
    _rec_name = 'invoice_id'
    
    
    def _get_route_line(self, cr, uid, ids, field_name, args, context=None):
        """
            Se obtiene la entrega del pago
        """
        res = {}
        line_obj = self.pool.get('delivery.route.line')
        
        for paid in self.browse(cr, uid, ids, context=context):
            invoice_id = paid.invoice_id.id or False
            
            line_srch = line_obj.search(cr, uid, [('invoice_id', '=', invoice_id)], context=context)
            # Obtencion de la entrega de la factura
            for line in line_obj.browse(cr, uid, line_srch, context=context):
                res[paid.id] = line.id or False
            
        return res
            
        
    
    _columns = {
        'route_id': fields.many2one('delivery.route', 'Ruta'),
        'date': fields.date('Fecha'),
        'amount': fields.float('Cantidad', digits_compute=dp.get_precision('Delivery')),
        'invoice_id': fields.many2one('account.invoice', 'Factura'),
        'journal_id': fields.many2one('account.journal', 'Metodo de pago'),
        'r_line_id': fields.function(_get_route_line, type="many2one",
            relation='delivery.route.line', string='Entrega'),
        # 'r_line_id': fields.many2one('delivery.route.line', 'Pagos')
    }

delivery_route_paid_log()
    
class delivery_route_line_log(osv.Model):
    _inherit = 'delivery.route.line.log'
    
    _columns = {
        'state': fields.selection([
            ('draft','No planeado'),
            ('planned','Planeado'),
            ('open','Por surtir'),
            ('pending_paid', 'Esperando pago'),
            ('arrived','Arribado'),
            ('delivered', 'En entrega'),
            ('delivered_carrier', 'En entrega transportista'),
            ('exeption', 'Excepcion entrega'),
            ('done', 'Entregado'),
            ('pending_paid_delivered', 'Esperando pago de entrega'),
            ('pending_credit', 'Autorizacion credito'),
            ('paid', 'pagado'),
            ('not_found', 'No encontrado'),
            ('return', 'Devuelto'),
            ('picking', 'Entregado Almacen'),
            ('cancel','Cancelado')],'Estado',readonly=True),
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
