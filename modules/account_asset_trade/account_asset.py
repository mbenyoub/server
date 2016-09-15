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

class account_asset_asset(osv.Model):
    """ Inherits product - Añadir funcionalidad para identificarlo como activo """
    _inherit = 'account.asset.asset'
    
    def validate(self, cr, uid, ids, context=None):
        """
            Asigna un codigo interno antes de validar el registro
        """
        if context is None:
            context = {}
        obj_seq = self.pool.get('ir.sequence')
        
        # Recorre los registros
        for asset_id in ids:
            # Obtiene el valor del codigo interno del activo
            code = obj_seq.next_by_code(cr, uid, 'account.asset.asset.code', context=context)
            # Actualiza la informacion del registro
            self.write(cr, uid, [asset_id], {'code_int': code})
            
            # Actualiza las amortizaciones sobre el activo
            self.compute_depreciation_board(cr, uid, [asset_id], context=context)
        return super(account_asset_asset, self).validate(cr, uid, ids, context=context)
    
    def _get_name(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el nombre del activo
        """
        res = {}
        for asset in self.browse(cr, uid, ids, context=context):
            res[asset.id] = asset.name
        return res
    
    def get_depreciation_init(self, cr, uid, asset_id, context=None):
        """
            Obtiene la fecha de la depreciacion inicial del activo
        """
        cr.execute("""
            select
                d.depreciation_date
            from
                account_asset_depreciation_line as d
            where
                d.asset_id = %s and d.move_check= True
            order by
                d.depreciation_date asc
            limit 1"""%(asset_id))
        date = ''
        for value in cr.fetchall():
            date = value[0]
            break
        # Si la fecha esta vacia toma la fecha de inicio de depreciacion del activo
        if not date:
            date = self.browse(cr, uid, asset_id, context=context).purchase_date
        return date
    
    def cron_create_move(self, cr, uid, context=None):
        """
            Crea los movimientos sobre los Activos que deben ser depreciados
        """
        if context is None:
            context = {}
        
        line_depr = self.pool.get('account.asset.depreciation.line')
        
        # Obtiene las lineas a depreciar
        cr.execute("""
         select l.id
         from account_asset_depreciation_line as l
         inner join account_asset_asset as a on a.id=l.asset_id
         where
            l.move_check = False and a.state='open' and a.active=True and
            l.depreciation_date<=current_timestamp""")
        
        line_ids = [x[0] for x in cr.fetchall()]
        
        # Agrega los movimientos sobre las lineas de depreciacion pendientes
        if len(line_ids):
            line_depr.create_move(cr, uid, line_ids, context=context)
        return True
    
    def cron_create_move_close(self, cr, uid, context=None):
        """
            Crea un movimiento de cierre para los activos que se terminaron de depreciar el mes anterior
        """
        if context is None:
            context = {}
        
        # Obtiene los activos que se terminaron de depreciar el mes anterior
        cr.execute("""
         select a.id
         from account_asset_depreciation_line as l
         inner join account_asset_asset as a on a.id=l.asset_id
         where
            l.move_check = True and a.state='open' and a.active=True and
            l.depreciation_date<=current_timestamp and l.remaining_value=0.0
            and (extract(month from l.depreciation_date) < extract(month from current_date) 
                or extract(year from l.depreciation_date) < extract(year from current_date))""")
        asset_ids = [x[0] for x in cr.fetchall()]
        
        # Cierra los activos que estan pendientes
        if len(asset_ids):
            self.set_to_close(cr, uid, asset_ids, context=context)
        return True
    
    def action_next_month(self, cr, uid, ids, context=None):
        """
            Obtiene la fecha de notificacion
        """
        for asset in self.browse(cr, uid, ids, context=context):
            # Valida que el activo tenga fecha de compra
            if not asset.date:
                raise osv.except_osv(_('Warning!'), _('El activo no tiene la fecha de compra!'))
            # Obtiene la fecha de depreciacion del activo
            date_asset = datetime.strptime(asset.date, '%Y-%m-%d')
            day = date_asset.strftime('%d')
            month = date_asset.strftime('%m')
            # Valida si la fecha de compra no es el dia primero del mes
            if int(day) != 1:
                # Calcula para aplicar la depreciacion sobre el 1ro del mes siguiente
                date_asset = date_asset + relativedelta(months=+1)
                days = int(day) - 1
                date_asset = date_asset - timedelta(days=days)
            date_dep = date_asset.strftime('%Y-%m-%d')
            self.write(cr, uid, [asset.id], {'purchase_date': date_dep}, context=context)
        return {'value':{'purchase_date': date_dep}}
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
           Funcion para duplicar 
        """
        if default is None:
            default = {}
        if context is None:
            context = {}
        #print "******************** duplicar registro activo ************* ", id, " **** ", context
        
        default.update({
            'depreciation_line_ids': [], 
            'account_move_line_ids': [],
            'child_ids': [],
            'code_int': '',
            'invoice_id': False,
            'income_id': False,
            'parent_id': False,
            'original_value': False,
            'original_salvage': False,
            'sale_date': False,
            'sale_quantity': None,
            'sale_update_factor': None,
            'sale_value_account': False,
            'sale_value_fiscal': False,
            'invoice_asset_id': False,
            'move_id_close': False,
            'drop_move_id': False,
            'drop_date': False,
            'drop_quantity': False,
            'drop_ref': False,
            'state': 'draft'})
        
        res = super(account_asset_asset, self).copy(cr, uid, id, default, context=context)
        #print "******************* resultado copy ******************* ", res
        return res
    
    def action_check_invoice(self, cr, uid, ids, context=None):
        """
            Muestra la informacion de la factura de la venta
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_asset_trade', 'invoice_asset_form')
        invoice = self.browse(cr, uid, ids[0], context=context).invoice_asset_id
        invoice_id = invoice.id or False
        
        return {
            'name':_("Factura Activo"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : invoice_id, # id of the object to which to redirected
        }
    
    def create_move_drop(self, cr, uid, asset_id, quantity, context=None):
        """ 
            Esta funcion Genera la poliza de baja del activo
        """
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        link_obj = self.pool.get('links.get.request')
        date = time.strftime('%Y-%m-%d')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.asset.asset se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.asset.asset', 'Asset', context=None)
        
        # Obtiene el periodo actual
        act_period_id = self._get_period(cr, uid, context=context)
        
        # Inicializa las variables para generar el movimiento
        mov_lines = []
        
        # Obtiene el objeto con la informacion del activo
        asset = self.browse(cr, uid, asset_id, context=context)
        
        # Valida que el activo no se encuentre en un estado distinto al de ejecucion o cerrado
        if asset.state not in ['open','close']:
            raise osv.except_osv(_('Warning!'), _('El activo se debe encontrar en Ejecucion o Cerrado para poderlo marcar como baja!'))
        # Valida que haya una cuenta de amortizacion configurada sobre el activo
        if not asset.category_id.account_asset_decline_id:
            raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de Baja de activo se encuentre registrada en las categorias de los activos!'))
        # Valida que haya una cuenta de activo configurada sobre el activo
        if not asset.category_id.account_asset_id:
            raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de activo se encuentre registrada en las categorias de los activos!'))
        # Valida que haya una cuenta de activo configurada sobre el activo
        if not asset.category_id.account_depreciation_id:
            raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de Amortizacion se encuentre registrada en las categorias de los activos!'))
        
        # Obtiene el numero de la secuencia del movimiento
        mov_number = obj_seq.next_by_code(cr, uid, 'account.asset.asset.drop', context=context)
        journal_id = asset.category_id.journal_id.id
        
        # Genera el asiento contable
        new_move = {
            'name': mov_number,
            'ref': asset.name,
            'journal_id': journal_id,
            'period_id': act_period_id,
            'date': date,
            'company_id': asset.company_id.id,
            'to_check': False,
            'reference': 'account.asset.asset,' + str(asset.id),
            'state': 'posted'
        }
        move_id = move_obj.create(cr, uid, new_move, context=context)
        
        orig_val = 0.0
        orig_sal = 0.0
        # Obtiene el valor original sobre 1 activo
        if asset.original_value:
            orig_val = asset.original_value
            orig_sal = asset.original_salvage
        else:
            orig_val = (asset.purchase_value / asset.product_qty)
            orig_sal = (asset.salvage_value / asset.product_qty)
        
        # Si la cantidad es igual al valor total del activo aplica el valor completo sino obtiene el valor proporcional a la cantidad
        if asset.product_qty > quantity:
            # Obtiene el valor proporcional depreciado del activo
            value_residual = (asset.value_residual / asset.product_qty) * quantity
            purchase_value = orig_val * quantity
            value_amortized = purchase_value - value_residual
        else:
            # Obtiene el valor depreciado del activo
            value_residual = asset.value_residual
            purchase_value = orig_val * quantity
            value_amortized = purchase_value - value_residual
        
        # Genera la linea con la baja del activo
        move_line = {
            'journal_id': journal_id,
            'period_id': act_period_id,
            'name': asset.name,
            'account_id': asset.category_id.account_asset_decline_id.id,
            'move_id': move_id,
            'partner_id': asset.partner_id.id or False,
            #'amount_currency': value_residual,
            'quantity': quantity,
            'credit': 0.0,
            'debit': value_residual,
            'date': date,
            'ref': asset.name,
            'reference': 'account.asset.asset,' + str(asset.id),
            'asset_id': False
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        # Genera la linea con las amortizaciones del activo
        move_line = {
            'journal_id': journal_id,
            'period_id': act_period_id,
            'name': asset.name,
            'account_id': asset.category_id.account_depreciation_id.id or False,
            'move_id': move_id,
            'partner_id': asset.partner_id.id or False,
            #'amount_currency': value_amortized,
            'quantity': quantity,
            'credit': 0.0,
            'debit': value_amortized,
            'date': date,
            'ref': asset.name,
            'reference': 'account.asset.asset,' + str(asset.id),
            'asset_id': False
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        # Genera la linea que cancela el activo
        move_line = {
            'journal_id': journal_id,
            'period_id': act_period_id,
            'name': asset.name,
            'account_id': asset.category_id.account_asset_id.id,
            'move_id': move_id,
            'partner_id': asset.partner_id.id or False,
            #'amount_currency': purchase_value,
            'quantity': quantity,
            'credit': purchase_value,
            'debit': 0.0,
            'date': date,
            'ref': asset.name,
            'reference': 'account.asset.asset,' + str(asset.id),
            'asset_id': False
            #'asset_id': asset.id
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        
        # Si hay valor salvaguarda genera un apunte para cuadrar los movimientos
        if asset.salvage_value:
            # Si la cantidad es igual al valor total del activo aplica el valor completo sino obtiene el valor proporcional a la cantidad
            if asset.product_qty > quantity:
                # Obtiene el valor proporcional depreciado del activo
                salvage_value = orig_sal * quantity
            else:
                # Obtiene el valor salvaguarda del activo
                salvage_value = orig_sal * quantity
            
            # Genera la linea que cancela el activo
            move_line = {
                'journal_id': journal_id,
                'period_id': act_period_id,
                'name': asset.name,
                'account_id': asset.category_id.account_asset_decline_id.id or False,
                'move_id': move_id,
                'partner_id': inv.partner_id.id or False,
                #'amount_currency': salvage_value,
                'quantity': quantity,
                'credit': 0.0,
                'debit': salvage_value,
                'date': date,
                'ref': asset.name,
                'reference': 'account.asset.asset,' + str(asset.id),
                'asset_id': False
                #'asset_id': asset.id
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=context)
        
        # Valida que la cantidad seleccionada no sea mayor a la disponible sobre el activo
        if asset.product_qty < quantity:
            raise osv.except_osv(_('Warning!'),_("La cantidad del activo %s, es mayor a la cantidad disponible (Disponible: %s)!"%(asset.name, asset.product_qty)))
        # Valida que el activo se encuentre en ejecucion
        if asset.state != 'open':
            if asset.state != 'close':
                raise osv.except_osv(_('Warning!'),_("Compruebe que el activo %s se encuentra disponible para darlo de baja (Estado actual: %s)!"%(asset.name, asset.state)))
        
        code_int = ''
        # Valida que el activo tenga asignado un codigo interno
        if asset.code_int:
            code_int = asset.code_int
        else:
            # Obtiene el valor del codigo interno del activo
            code_int = obj_seq.next_by_code(cr, uid, 'account.asset.asset.code', context=context)
        
        # Valida si se esta usando completo el activo o una parte proporcional
        if asset.product_qty != quantity:
            # Obtiene la fecha de la primera depreciacion del activo
            if asset.invoice_asset_id:
                # Si el activo proviene de una venta de activo toma la fecha de depreciacion
                dep_date = asset.depreciation_date
            else:
                # Si el activo no proviene del restante de una venta toma el valor de la primera depreciacion
                dep_date = self.get_depreciation_init(cr, uid, asset.id, context=context)
            
            # Toma la parte proporcional del activo y obtiene el valor de lo que no se da de baja
            value = asset.value_residual / asset.product_qty
            product_qty = asset.product_qty - quantity
            asset_value = value * product_qty
            # Obtiene la parte proporcional del valor bruto
            pvalue = asset.purchase_value / asset.product_qty
            purchase_value = pvalue * product_qty
            # Obtiene la parte proporcional del valor salvaguarda
            svalue = asset.salvage_value / asset.product_qty
            salvage_value = svalue * product_qty
            # Obtiene el numero de depreciaciones por aplicar
            cr.execute("""
                select count(id) as cantidad
                from account_asset_depreciation_line
                where asset_id = %s
                    and move_check=False"""%(asset.id))
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
                limit 1"""%(asset.id))
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
            asset_id = self.create(cr, uid, {
                'product_id': asset.product_id.id,
                'name': asset.name,
                'category_id': asset.category_id.id,
                'parent_id': asset.id,
                'date': asset.date,
                'purchase_date': dep_date,
                'currency_id': asset.currency_id.id,
                'product_qty': product_qty,
                'purchase_value': asset_value + salvage_value,
                'salvage_value': salvage_value,
                'value_residual': asset_value,
                'partner_id': asset.partner_id.id,
                'method': asset.method,
                'method_time': 'number',
                'method_number': dep_to_apply,
                'method_period': asset.method_period,
                'note': asset.note,
                'state': 'open',
                'code_int': code_int,
                'origin': asset.origin,
                'original_value': orig_val,
                'original_salvage': orig_sal
                }, context=context)
            
            # Actualiza las depreciaciones del nuevo activo
            self.compute_depreciation_board(cr, uid, [asset.id], context=context)
        
        # Obtiene la fecha de la primera depreciacion del activo
        if asset.invoice_asset_id or asset.parent_id:
            # Si el activo proviene de una venta de activo toma la fecha de depreciacion o de una baja de activo
            dep_date = asset.depreciation_date
        else:
            # Si el activo no proviene del restante de una venta toma el valor de la primera depreciacion
            dep_date = self.get_depreciation_init(cr, uid, asset.id, context=context)
        
        # Cambia el estado del activo a Baja y actualiza los valores
        self.write(cr, uid, [asset.id], {
            'state': 'drop',
            'drop_move_id': move_id,
            'drop_quantity': quantity,
            'drop_date': context.get('date',date),
            'depreciation_date': dep_date,
            'code_int': code_int,
            'original_value': orig_val,
            'original_salvage': orig_sal,
            'drop_ref': context.get('ref','')}, context=context)
        
        # Elimina de la tabla de amortizacion las amortizaciones que ya no se van a aplicar
        cr.execute("""
                delete from account_asset_depreciation_line
                where asset_id = %s
                    and move_check=False """%(asset.id))
        return move_id
    
    def create_move_close(self, cr, uid, asset_id, context=None):
        """ 
            Esta funcion Genera la poliza de cierre del activo
        """
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        obj_seq = self.pool.get('ir.sequence')
        link_obj = self.pool.get('links.get.request')
        date = time.strftime('%Y-%m-%d')
        if context is None:
            context = {}
        
        #~ Valida que el objeto account.asset.asset se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.asset.asset', 'Asset', context=None)
        
        # Obtiene el periodo actual
        act_period_id = self._get_period(cr, uid, context=context)
        
        # Inicializa las variables para generar el movimiento
        mov_lines = []
        
        # Obtiene el objeto con la informacion del activo
        asset = self.browse(cr, uid, asset_id, context=context)
        
        # Valida que el activo no tenga depreciaciones pendientes
        if asset.value_residual != 0.0:
            raise osv.except_osv(_('Warning!'), _('El valor contable del producto debe ser 0.0 para poderlo marcar como cerrado!'))
        # Valida que el activo no se encuentre en un estado distinto al de ejecucion
        if asset.state != 'open':
            raise osv.except_osv(_('Warning!'), _('El activo se debe encontrar en Ejecucion para poderlo marcar como cerrado!'))
        # Valida que haya una cuenta de amortizacion configurada sobre el activo
        if not asset.category_id.account_depreciation_id:
            raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de Amortizacion de activo se encuentre registrada en las categorias de los activos!'))
        # Valida que haya una cuenta de activo configurada sobre el activo
        if not asset.category_id.account_asset_id:
            raise osv.except_osv(_('Warning!'), _('Verifique que la cuenta de activo se encuentre registrada en las categorias de los activos!'))
        
        # Obtiene el numero de la secuencia del movimiento
        mov_number = obj_seq.next_by_code(cr, uid, 'account.asset.asset.close', context=context)
        journal_id = asset.category_id.journal_id.id
        
        # Genera el asiento contable
        new_move = {
            'name': mov_number,
            'ref': asset.name,
            'journal_id': journal_id,
            'period_id': act_period_id,
            'date': date,
            'company_id': asset.company_id.id,
            'to_check': False,
            'reference': 'account.asset.asset,' + str(asset.id),
            'state': 'posted'
        }
        move_id = move_obj.create(cr, uid, new_move, context=context)
        
        # Obtiene el valor depreciado del activo
        if asset.original_value:
            value = (asset.original_value * asset.product_qty) - asset.value_residual
        else:
            value = asset.purchase_value - asset.value_residual
        
        # Genera la linea con las amortizaciones del activo
        move_line = {
            'journal_id': journal_id,
            'period_id': act_period_id,
            'name': asset.name,
            'account_id': asset.category_id.account_depreciation_id.id,
            'move_id': move_id,
            'partner_id': asset.partner_id.id or False,
            #'amount_currency': value,
            'quantity': asset.product_qty,
            'credit': 0.0,
            'debit': value,
            'date': date,
            'ref': asset.name,
            'reference': 'account.asset.asset,' + str(asset.id),
            'asset_id': False
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        # Genera la linea que cancela el activo
        move_line = {
            'journal_id': journal_id,
            'period_id': act_period_id,
            'name': asset.name,
            'account_id': asset.category_id.account_asset_id.id or False,
            'move_id': move_id,
            'partner_id': asset.partner_id.id or False,
            #'amount_currency': asset.purchase_value,
            'quantity': asset.product_qty,
            'credit': asset.purchase_value,
            'debit': 0.0,
            'date': date,
            'ref': asset.name,
            'reference': 'account.asset.asset,' + str(asset.id),
            'asset_id': False,
            #'asset_id': asset.id
        }
        new_id = move_line_obj.create(cr, uid, move_line, context=context)
        mov_lines.append(new_id)
        
        # Si hay valor salvaguarda genera un apunte para cuadrar los movimientos
        if asset.salvage_value:
            # Obtiene el valor salvaguarda original
            if asset.original_salvage:
                salvage_value = asset.original_salvage * product_qty
            else:
                salvage_value = asset.salvage_value
            
            # Genera la linea que cancela el activo
            move_line = {
                'journal_id': journal_id,
                'period_id': act_period_id,
                'name': asset.name,
                'account_id': asset.category_id.account_cost_sale_id.id or False,
                'move_id': move_id,
                'partner_id': inv.partner_id.id or False,
                #'amount_currency': salvage_value,
                'quantity': asset.product_qty,
                'credit': 0.0,
                'debit': salvage_value,
                'date': date,
                'ref': asset.name,
                'reference': 'account.asset.asset,' + str(asset.id),
                'asset_id': False,
                #'asset_id': asset.id
            }
            new_id = move_line_obj.create(cr, uid, move_line, context=context)
        
        # Relaciona el movimiento con el activo
        self.write(cr, uid, [asset.id], {'move_id_close': move_id}, context=context)
        return move_id
    
    def set_to_close(self, cr, uid, ids, context=None):
        """
            Genera una poliza de cierre al momento de cerrar el activo
        """
        # Recorre los activos y genera el proceso de cierre
        for asset_id in ids:
            move_id = self.create_move_close(cr, uid, asset_id, context=context)
        
        # Funcion original
        return super(account_asset_asset, self).set_to_close(cr, uid, ids, context=context)
    
    def action_drop_asset(self, cr, uid, ids, context=None):
        """
            Pone el activo en el status de Baja
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_asset_trade', 'view_account_asset_drop_wizard')
        
        # Obtiene la informacion del activo a dar de baja
        asset = self.browse(cr, uid, ids[0], context=context)
        
        # Obtiene los parametros que van por default
        select_qty = False
        if asset.product_qty > 1:
            select_qty = True
        context['default_asset_id'] = asset.id
        context['default_select_qty'] = select_qty
        context['default_quantity'] = asset.product_qty
        
        return {
            'name':_("Activo"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.asset.drop.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
    
    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """
            Obtiene la categoria del activo
        """
        res = {}
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        
        # Si el producto esta configurado como activo actualiza su informacion
        if product.is_asset:
            res['category_id'] = product.default_asset_category_id.id
            res['purchase_value'] = product.standard_price
            res['product_qty'] = 1
            res['name'] = product.name + '-' + product.default_code if product.default_code else product.name
        return {'value': res}
    
    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        """
            Actualiza la informacion de la categoria del activo
        """
        # Funcion original
        res = super(account_asset_asset, self).onchange_category_id(cr, uid, ids, category_id, context=context)
        # Si recibio la categoria actualiza los campos faltantes
        if category_id:
            category = self.pool.get('account.asset.category').browse(cr, uid, category_id, context=context)
            
            if category.mdv:
                res['value']['mdv'] = category.mdv
        return res
    
    def onchange_product_qty(self, cr, uid, ids, product_id, product_qty, context=None):
        """
            Actualiza el monto del activo
        """
        res = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            
            # Si el producto esta configurado como activo actualiza el monto del activo
            if product.is_asset:
                res['purchase_value'] = product.standard_price * product_qty
        return {'value': res}
    
    def compute_depreciation_board(self, cr, uid, ids, context=None):
        """
            Calculo de Amortizaciones sobre el activo
        """
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        currency_obj = self.pool.get('res.currency')
        for asset in self.browse(cr, uid, ids, context=context):
            # Valida que el activo no este vendido
            if asset.state == 'sold':
                raise osv.except_osv(_('Warning!'),_("No se puede depreciar un activo que ya esta vendido!"))
            
            if asset.value_residual == 0.0:
                continue
            posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)],order='depreciation_date desc')
            old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)
            
            amount_to_depr = residual_amount = asset.value_residual
            #print "****************** amount to depr *************** ", amount_to_depr
            #print "**************** prorata *************** ", asset.prorata
            if asset.prorata:
                depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
                #print "**************** depreciation date prorata ************** ", depreciation_date
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                #print "**************** depreciation date ************** ", purchase_date
                #if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                #print "****************** validacion si hay depr anteriores confirmadas ************* ", len(posted_depreciation_line_ids)
                if (len(posted_depreciation_line_ids)>0):
                    last_depreciation_date = datetime.strptime(depreciation_lin_obj.browse(cr,uid,posted_depreciation_line_ids[0],context=context).depreciation_date, '%Y-%m-%d')
                    depreciation_date = (last_depreciation_date+relativedelta(months=+asset.method_period))
                    #print "********** fecha aplicada sobre periodo iniciado ********** ", depreciation_date
                else:
                    #depreciation_date = datetime(purchase_date.year, 1, 1)
                    day = purchase_date.strftime('%d')
                    month = purchase_date.strftime('%m')
                    # Valida si la fecha de compra no es el dia primero del mes
                    if int(day) != 1:
                        # Calcula para aplicar la depreciacion sobre el 1ro del mes siguiente
                        depreciation_date = purchase_date + relativedelta(months=+1)
                        days = int(day) - 1
                        depreciation_date = depreciation_date - timedelta(days=days)
                    else:
                        depreciation_date = purchase_date
                    #print "************** fecha aplicada **************** ", depreciation_date
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            #print "*************** day ************** ", day
            #print "*************** month ************** ", month
            #print "*************** year ************** ", year
            
            total_days = (year % 4) and 365 or 366
            #print "************ total days ", (year % 4),  " ************ ", total_days

            undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
            #print "************ undone_dotation_number ****************** ", undone_dotation_number
            #print "****************** cantidad de depreciaciones **** ", len(posted_depreciation_line_ids), " *** ", undone_dotation_number, " ********* ", range(len(posted_depreciation_line_ids), undone_dotation_number)
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
                company_currency = asset.company_id.currency_id.id
                current_currency = asset.currency_id.id
                # compute amount into company currency
                amount = currency_obj.compute(cr, uid, current_currency, company_currency, amount, context=context)
                residual_amount -= amount
                dep_date = depreciation_date
                
                if not asset.prorata:
                    dep_date = depreciation_date + relativedelta(months=+1) - timedelta(days=1)
                
                vals = {
                     'amount': amount,
                     'asset_id': asset.id,
                     'sequence': i,
                     'name': str(asset.id) +'/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
                     'depreciation_date': dep_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(cr, uid, vals, context=context)
                # Considering Depr. Period as months
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
                #print "********** new depr date ******** ", depreciation_date
                
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
                #print "*************** new day ************** ", day
                #print "*************** new month ************** ", month
                #print "*************** new year ************** ", year
        return True
    
    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
        #by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                #print "******************* amount depr ****** ", amount_to_depr, " / (", undone_dotation_number, " - ", len(posted_depreciation_line_ids), ") = ", amount 
                if asset.prorata:
                    amount = amount_to_depr / asset.method_number
                    #print "************* amount prorata *********** ", amount
                    days = total_days - float(depreciation_date.strftime('%j'))
                    #print "**************** days *********** ", total_days, " - ", float(depreciation_date.strftime('%j')), " = ", days
                    if i == 1:
                        amount = (amount_to_depr / asset.method_number) / total_days * days
                        #print "************* amount first *********** ", (amount_to_depr / asset.method_number), " / ", total_days, " * ", days, " = ", amount 
                    elif i == undone_dotation_number:
                        amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
                        #print "************** amount next ********** ", (amount_to_depr / asset.method_number), " / ", total_days, " * ", "(", total_days, " - " ,days, ") = ", amount
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                if asset.prorata:
                    days = total_days - float(depreciation_date.strftime('%j'))
                    if i == 1:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * days
                    elif i == undone_dotation_number:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
        return amount
    
    def get_inpc_depreciation_init(self, cr, uid, asset_id, context=None):
        """
            Obtiene el valor del inpc de la primera depreciacion del activo
        """
        cr.execute("""
            select
                count(id) as period
            from
                account_period as p
            where
                fiscalyear_id = %s
                and p.special=False"""%(fiscalyear_id))
        period_id = False
        for value in cr.fetchall():
            period_id = value[0]
            break
        return period_id
    
    def _get_qty(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene la cantidad disponible sobre el activo, si viene de una
        """
        res = {}
        
        # Recorre los registros
        for asset in self.browse(cr, uid, ids, context=context):
            # Valida si el activo no ha sido vendido
            if asset.state == 'sold':
                res[asset.id] = asset.sale_quantity
            elif asset.state == 'drop':
                res[asset.id] = asset.drop_quantity
            else:
                res[asset.id] = asset.product_qty
        return res
    
    def get_value_fiscal(self, cr, uid, asset_id, fiscalyear_id, context=None):
        """
            Obtiene el Costo fiscal de un activo en el año especificado
        """
        # Inicializa variables
        line_depr = self.pool.get('account.asset.depreciation.line')
        fyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        inpc_obj = self.pool.get('account.fiscal.inpc')
        year = 0.0
        month = 0.0
        dep_period = 0.0
        amount = 0.0
        nex_dep = 0.0
        sale_period = 0.0
        depreciation_date = False
        date_init = False
        inpc_val1 = 0.0
        inpc_val2 = 0.0
        result = 0
        mdv = 1.0
        
        # Obtiene la informaicon del activo
        asset = self.browse(cr, uid, asset_id, context=context)
        
        # Obtiene el año del ejercicio fiscal
        year_period = fyear_obj.get_year(cr, uid, fiscalyear_id, context=context)
        #print "***************************** year period *********** ", year_period
        
        # Revisa cual es la ultima depreciacion por aplicar sobre el año
        cr.execute("""
            select
                to_char(d.depreciation_date, 'yyyy'), to_char(d.depreciation_date, 'MM'), to_char(d.depreciation_date, 'yyyyMM'), d.remaining_value, 
                (select count(c.id) from account_asset_depreciation_line as c where c.depreciation_date > d.depreciation_date and c.asset_id=d.asset_id) as depreciation,
                case when to_char(a.sale_date, 'yyyyMM')!='' then to_char(a.sale_date, 'yyyyMM') else '0' end, a.depreciation_date,
                (select sum(amount) from account_asset_depreciation_line as dl where extract(year from d.depreciation_date)= extract(year from dl.depreciation_date) and dl.asset_id=d.asset_id) as amount 
            from
                account_asset_depreciation_line as d
                inner join account_asset_asset as a on a.id=d.asset_id
            where
                d.asset_id = %s and extract(year from d.depreciation_date) <= %s
            order by
                d.depreciation_date desc
            limit 1"""%(asset_id, year_period))
        for value in cr.fetchall():
            year = int(value[0])
            month = int(value[1])
            dep_period = int(value[2])
            next_dep = int(value[4])
            sale_period = int(value[5])
            depreciation_date = value[6]
            amount = value[7]
            break
        
        #print "********** amount ******************* ", amount
        #print "*********** year period ************* ", year_period
        #print "************** mdv ************* ", asset.mdv
        val = asset.purchase_value - asset.salvage_value
        
        # Valida si el activo tiene aplicado un mdv
        if asset.mdv != 0:
            if val > asset.mdv:
                #print "************** purchase_value - salvage_value ************* ", asset.purchase_value, " - ", asset.salvage_value
                if val == 0:
                    # Pone el valor proporcional como cero
                    mdv = 0
                else:
                    # Obtiene el valor proporcional aplicado para el mdv
                    mdv = (asset.mdv/val)
                #print "*********** amount propor ********* ", amount, " * ", mdv 
                # Actualiza el valor del monto
                amount = amount * mdv
                
        #print "*************** amount ************ ", amount
        # Valida si el activo proviene del remanente de una venta
        if depreciation_date:
            # Obtencion del inpc de la compra del articulo
            inpc_id = inpc_obj.get_inpc_to_date(cr, uid, depreciation_date, context=context)
            inpc_val2 = inpc_obj.get_value(cr, uid, inpc_id, context=context)
            date_init = str(depreciation_date)
        else:
            # Obtiene el inpc del periodo donde inicio la depreciacion del activo
            cr.execute("""
                select
                    i.value, d.depreciation_date
                from
                    account_asset_depreciation_line as d
                    left join account_fiscal_inpc as i on to_char(d.depreciation_date, 'mm/yyyy')=i.name
                where
                    d.asset_id = %s and d.move_check= True
                order by
                    d.depreciation_date asc
                limit 1"""%(asset_id))
            for value in cr.fetchall():
                inpc_val2 = value[0]
                date_init = str(value[1])
                break
        
        #print "************** date init ********** ", date_init
        #print "************** inpc_val2 ********** ", inpc_val2
        
        year_init = 0
        month_init = 1
        
        # Obtiene el mes y el año de la fecha
        if date_init:
            init = date_init.split('-')
            year_init = int(init[0])
            month_init = int(init[1])
        #print "************** period ************ ",month_init,'/',year_init
        #print "************** period ************ ",year,' > ',year_init
        
        # Valida si el activo proviene de un año anterior a la venta
        if year > year_init:
            # Si el mes es 1 toma el valor del inpc de diciembre del año anterior
            if month == 1:
                year_period = year -1
                month_period = 12
            # Si el mes es impar le resta 1
            elif month%2 != 0:
                month_period = month - 1
                month_period = month_period / 2
                year_period = year
            # Divide entre 2 el mes
            else: 
                month_period = month / 2
                year_period = year
        else:
            # Valida el mes del calculo considerando la fecha de compra
            month_period = month - month_init + 1
            #print "************** month period *********** ", month, " - ", month_init, " + 1 = ", month_period
            # Si el mes es igual a 1 su valor lo deja en 1
            if month_period == 1:
                month_period = 1
            # Si el mes es impar le resta 1
            elif month_period%2 != 0:
                month_period = month_period - 1
                month_period = month_period / 2
            # Divide entre 2 el mes
            else: 
                month_period = month_period / 2
            # Toma el mes de compra como punto de partida
            month_period = month_period + month_init - 1
            year_period = year
        #print "************** inpc apply val1 ************ ",month_period,'/',year_period
        # Obtiene el inpc
        cr.execute("""
            select
                i.value 
            from
                account_fiscal_inpc as i
            where
                i.period = %s and i.fiscalyear = %s
            limit 1"""%(month_period, year_period))
        inpc_val = 0.0
        for value in cr.fetchall():
            inpc_val1 = value[0]
            break
        
        #print "************** inpc_val1 ********** ", inpc_val1
        #print "************** inpc_val2 ********** ", inpc_val2
        
        update_factor = 0.0
        # Revisa que exista el inpc sobre el periodo
        if inpc_val2:
            # Obtiene el factor de actualizacion
            update_factor = (inpc_val1/inpc_val2)
        
        # Si el factor de actualizacion es cero lo pasa a 1
        if update_factor == 0.0:
            update_factor = 1
        
        # Obtiene el resultado en base al valor fiscal
        result = amount * update_factor
        
        #print "************* result ************* ", amount, " * ", update_factor, " = ", result
        #print "************************************************************"
        return result
    
    def _get_update_factor(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el Factor de actualizacion del Activo
        """
        res = {}
        line_depr = self.pool.get('account.asset.depreciation.line')
        fyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        inpc_obj = self.pool.get('account.fiscal.inpc')
        date_init = ''
        
        #print "********************** obtencion de factor de actualizacion ****************** "
        
        # Obtiene el periodo actual
        period_id = period_obj._get_period_default(cr, uid, context=context)
        # Obtiene el numero del mes del periodo y el año
        month_current = period_obj._get_month_period(cr, uid, period_id, context=context)
        year_current = period_obj._get_year_period(cr, uid, period_id, context=context)
        # Si el mes es 1 toma el valor del inpc de diciembre del año anterior
        if month_current == 1:
            year_period = year_current -1
            month_period = 12
        # Si el mes es impar le resta 1
        elif month_current%2 != 0:
            month_period = month_current - 1
            month_period = month_period / 2
            year_period = year_current
        # Divide entre 2 el mes
        else: 
            month_period = month_current / 2
            year_period = year_current
        
        #print "*********** month period ******** ", month_period
        #print "**********  year period ********* ", year_period
        
        # Obtiene el inpc sobre el mes y el año obtenido
        cr.execute("""
            select
                i.value 
            from
                account_fiscal_inpc as i
            where
                i.period = %s and i.fiscalyear = %s
            limit 1"""%(month_period, year_period))
        inpc_val1 = 0.0
        for value in cr.fetchall():
            inpc_val1 = value[0]
            break
        
        #print "************** inpc_val1 ********** ", inpc_val1
        
        # Recorre los registros
        for asset in self.browse(cr, uid, ids, context=context):
            # Valida si el activo no ha sido vendido
            if asset.state == 'sold':
                res[asset.id] = asset.sale_update_factor
                continue
            
            # Valida si el activo proviene del remanente de una venta
            if asset.invoice_asset_id and asset.depreciation_date:
                # Obtencion del inpc de la compra del articulo
                inpc_id = inpc_obj.get_inpc_to_date(cr, uid, asset.depreciation_date, context=context)
                inpc_val2 = inpc_obj.get_value(cr, uid, inpc_id, context=context)
                date_init = str(asset.depreciation_date)
            else:
                # Obtiene el inpc del periodo donde inicio la depreciacion del activo
                cr.execute("""
                    select
                        i.value, d.depreciation_date
                    from
                        account_asset_depreciation_line as d
                        left join account_fiscal_inpc as i on to_char(d.depreciation_date, 'mm/yyyy')=i.name
                    where
                        d.asset_id = %s and d.move_check= True
                    order by
                        d.depreciation_date asc
                    limit 1"""%(asset.id))
                inpc_val2 = 0.0
                for value in cr.fetchall():
                    inpc_val2 = value[0]
                    date_init = str(value[1])
                    break
            
            #print "************** date init ********** ", date_init
            #print "************** inpc_val2 ********** ", inpc_val2
            
            year_init = 0
            month_init = 1
            
            # Obtiene el mes y el año de la fecha
            if date_init:
                init = date_init.split('-')
                year_init = int(init[0])
                month_init = int(init[1])
                #print "************** periodo compra ************ ",month_init,'/',year_init
            
            # Valida si el activo proviene de un año anterior a la venta
            if (year_current > year_init) or not date_init:
                inpc_val = inpc_val1
                #print "******************* inpc proviene de un año anterior *********** ", inpc_val
            else:
                # Cuando es el mismo año toma el factor de actualizacion con el mes de la compra en los 4 primeros meses
                # Obtiene el inpc de la venta considerando la fecha de compra
                month = month_current - month_init + 1
                # Si el resultado es igual a 1 se queda con el valor
                if month == 1:
                    month = 1
                # Si el mes es impar le resta 1
                elif month%2 != 0:
                    month = month - 1
                    month = month / 2
                # Divide entre 2 el mes
                else: 
                    month = month_period / 2
                # Toma el mes de compra como punto de partida
                month = month + month_init - 1
                #print "************** inpc apply mismo año ************ ",month,'/',year_init
                # Obtiene el inpc
                cr.execute("""
                    select
                        i.value 
                    from
                        account_fiscal_inpc as i
                    where
                        i.period = %s and i.fiscalyear = %s
                    limit 1"""%(month, year_init))
                inpc_val = 0.0
                for value in cr.fetchall():
                    inpc_val = value[0]
                    break
                #print "******************* inpc proviene del mismo año *********** ", inpc_val
            update_factor = 0.0
            # Revisa que exista el inpc sobre el periodo
            if inpc_val2:
                # Obtiene el factor de actualizacion
                update_factor = (inpc_val/inpc_val2)
                #print "*************** resultado activo ************** ", inpc_val, "/", inpc_val2, "= ", update_factor
            
            # Si el valor del factor de actualizacion es cero lo cambia a 1
            if update_factor == 0.0:
                update_factor = 1.0
            # Guarda el valor del factor de actualizacion
            res[asset.id] = update_factor
        return res
    
    def _get_result(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el valor fiscal del activo
        """
        res = {}
        
        for id in ids:
            res[id] = self.get_value_fiscal(cr, uid, id, 1, context=context)
        return res
    
    def _get_num_depreciation(self, cr, uid, ids, field, arg, context=None):
        """
            Obtiene el numero de depreciaciones aplicadas sobre el activo
        """
        res = {}
        # Recorre los ids sobre los que se va a calcular la cantidad de depreciaciones
        for id in ids:
            num = 0.0
            # Obtiene el numero de depreciaciones aplicadas
            cr.execute("""
                select count(move_check) as num_check
                from account_asset_depreciation_line
                where asset_id=%s and move_check=True"""%(id))
            for value in cr.fetchall():
                num = value[0]
                break
            res[id] = num
        return res
    
    #def get_period_on_date(self, cr, uid, date, context=None):
    #    """
    #        Obtiene el periodo en base a una fecha
    #    """
    #    period_obj = self.pool.get('account.period')
    #    period_ids = period_obj.find(cr, uid, date, context=context)
    #    return period_ids and period_ids[0] or False
    def get_period_on_date(self, cr, uid, date, context=None):
        """
            Obtiene el periodo en base a una fecha
        """
        return False
    
    def onchange_date(self, cr, uid, ids, date, context=None):
        """
            Actualiza el periodo de inicio de depreciacion
        """
        period_id = False
        print "************** date ***************** ", date
        if date:
            date_strp = time.strptime(date, "%Y-%m-%d")
            # Obtiene los dias de la fecha  de compra
            day = time.strftime("%d", date_strp)
            month = time.strftime("%m", date_strp)
            year = time.strftime("%Y", date_strp)
            
            print "************* fecha ************ ",day, "/", month, "/", year
            
            print "********** entero dia *** ", int(day), "  mes ", int(month)
            # Valida si la fecha se encuentra dentro de los primeros 10 dias
            if int(day) > 10:
                # Obtiene el valor del mes siguiente
                month = '%s'%(int(month)+1,)
                if int(month) < 10:
                    month = '0%s'%(month,)
                    
                # Obtiene la fecha del mes siguiente
                date = '%s-%s-01'%(year,month)
            
        return {'value': {'purchase_date': date}}
    
    def _get_period_on_date(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el periodo del documento en base a la fecha de inicio de depreciacion
        """
        result = {}
        for asset in self.browse(cr, uid, ids, context=context):
            result[asset.id] = self.get_period_on_date(cr, uid, asset.purchase_date, context=context)
        return result
    
    _columns = {
        'method_progress_factor': fields.float('Degressive Factor', readonly=True, states={'draft':[('readonly',False)]}, digits=(16,4)),
        'product_id': fields.many2one('product.product', 'Activo', domain=[('is_asset','=',True)], required=True),
        'product_qty': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'date': fields.date('fecha de Compra'),
        'invoice_id': fields.many2one('account.invoice', 'Factura de compra'),
        'update_factor': fields.function(_get_update_factor, type='float', digits=(16,4), string="Factor Actualizacion"),
        'state': fields.selection([('draft','Borrador'),('open','En ejecucion'),('close','Cerrado'),('sold','Vendido'),('drop','Baja')], 'Estado', required=True,
                                  help="Indica el estado en el que se encuentra el activo, es estado 'En ejecucion' nos permite aplicar una depreciacion sobre el activo."),
        'qty': fields.function(_get_qty, type='float', string="Cantidad", digits_compute=dp.get_precision('Product Unit of Measure'), store=True),
        'mdv': fields.float('MDV', digits_compute= dp.get_precision('Account'), help="Poner tope sobre el valor Bruto (Activo)"),
        'depreciation_date': fields.date('Inicio depreciacion'),
        'original_value': fields.float('Valor original por cada registro', digits=(16,8)),
        'original_salvage': fields.float('Valor salvaguarda original', digits=(16,8)),
        'code_int': fields.char('Codigo Interno', size=64, readonly=True),
        # Informacion sobre venta de activo
        'sale_date': fields.date('fecha de Venta'),
        'sale_quantity': fields.float('Cantidad', digits_compute= dp.get_precision('Account')),
        'sale_update_factor': fields.float('Factor de Actualizacion', digits=(16,4)),
        'sale_value_account': fields.float('Valor contable', digits_compute= dp.get_precision('Account')),
        'sale_value_fiscal': fields.float('Costo fiscal', digits_compute= dp.get_precision('Account')),
        'invoice_asset_id': fields.many2one('account.invoice', 'Factura de venta de activo', readonly=True),
        # Valor para resultado fiscal
        'result': fields.function(_get_result, type='float', digits=(16,4), string="Valor Fiscal"),
        # Revisar si hay amortizaciones sobre el activo
        'num_dep_line': fields.function(_get_num_depreciation, type='float', digits_compute=dp.get_precision('Account'), string="Numero amortizaciones"),
        'move_id_close': fields.many2one('account.move', 'Asiento de cierre', readonly=True, select=1, ondelete='restrict', help="Ir a Poliza de cierre de activo."),
        # Informacion sobre baja de activo
        'drop_move_id': fields.many2one('account.move', 'Asiento de baja de activo', readonly=True, select=1, ondelete='restrict', help="Ir a Poliza de baja de activo."),
        'drop_date': fields.date('fecha de Baja'),
        'drop_quantity': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure')),
        'drop_ref': fields.text('Motivo de Baja'),
        # Categoria de activo generado en base a su origen
        'origin': fields.selection([('purchase','Compra'),('donation','Donacion'),('income','Aportacion')], 'Origen', required=True, help="Indica cual es el Origen sobre la generacion del activo."),
        'income_id': fields.many2one('account.invoice', 'Factura de venta de activo', readonly=True),
    }
    
    _defaults = {
        'product_qty': 1,
        'date': time.strftime('%Y-%m-%d'),
        'origin': 'purchase'
    }
    
account_asset_asset()

class account_asset_category(osv.Model):
    """ Inherits asset category - Modificacion sobre categoria activos """
    _inherit = 'account.asset.category'
    
    _columns = {
        'code': fields.char('Codigo', size=38, required=True),
        'mdv': fields.float('MDV', digits_compute= dp.get_precision('Account'), help="Poner tope sobre el valor Bruto (Activo)"),
        'account_cost_sale_id': fields.many2one('account.account', 'Costo de Venta de Activo', required=True, help="Cuenta que aplica sobre el costo de venta de activo."),
        'account_asset_decline_id': fields.many2one('account.account', 'Baja de activo', required=True, help="Cuenta que aplica para cuando se da de baja un activo."),
        #'account_sale_id': fields.many2one('account.account', 'Venta de activo', required=True, help="Cuenta que aplica sobre la venta de activo."),
    }
    
    _defaults = {
        'mdv': 0.0
    }
    
account_asset_category()

class account_asset_depreciation_line(osv.Model):
    _inherit = 'account.asset.depreciation.line'
    
    def validate_date(self, cr, uid, date, context=None):
        """
            Valida si la fecha actual es mayor a la fecha recibida
        """
        now = time.strftime('%Y-%m-%d')
        #print "************** now ************** ", now, " < ", date
        #~ Valida que no haya productos repetidos en la solicitud de compra
        cr.execute("""
                select (to_char(to_date('%s','yyyy-mm-dd'),'yyyyMM'))::int as fecha1, (to_char(to_date('%s','yyyy-mm-dd'),'yyyyMM'))::int as fecha2"""%(now,date))
        for value in cr.fetchall():
            date1 = value[0]
            date2 = value[1]
            break
        #print "********************** compara fechas ********** ", date1, " < ", date2
        if date1 < date2:
            return True
        return False
    
    def create_move(self, cr, uid, ids, context=None):
        """
            Valida que el documento no se encuentre vendido
        """
        for dp in self.browse(cr, uid, ids, context=context):
            # Valida que el documento no se encuentre vendido
            if dp.asset_id.state == 'sold':
                raise osv.except_osv(_('Warning!'),_("No se puede depreciar un activo que ya esta vendido!"))
            
            # Valida que la fecha de la depreciacion sea
            check = self.validate_date(cr, uid, dp.depreciation_date, context=context)
            if check == True:
                raise osv.except_osv(_('Warning!'),_("No puedes depreciar activos a un mes mayor al mes en curso!"))
        
        return super(account_asset_depreciation_line, self).create_move(cr, uid, ids, context=context)
    
    def action_skip_depreciation(self, cr, uid, ids, context=None):
        """
            Cambia el registro para que no aplique depreciacion
        """
        return self.write(cr, uid, ids, {'inactive': True}, context=context)
    
    def action_active_depreciation(self, cr, uid, ids, context=None):
        """"
            Habilita la opcion del sistema para que se aplique la depreciacion
        """
        return self.write(cr, uid, ids, {'inactive': False}, context=context)
    
    def action_cancel_depreciation(self, cr, uid, ids, context=None):
        """"
            Cancela la poliza generada sobre la depreciacion del activo
        """
        move_obj = self.pool.get('account.move')
        move_ids = []
        
        # Recorre las lineas de depreciacion a cancelar
        for dep in self.browse(cr, uid, ids, context=context):
            # Obtiene el id de la poliza
            if dep.move_id:
                move_ids.append(dep.move_id.id)
            
        # Elimina la relacion de las polizas con las lineas depreciadas
        self.write(cr, uid, ids, {'move_id': False}, context=context)
        
        # Elimina las polizas
        move_obj.unlink(cr, uid, move_ids, context=context)
        return True
    
    _columns = {
        'inactive': fields.boolean('Inactivado', help="Indica que el registro no genera una poliza")
    }
    
account_asset_depreciation_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
