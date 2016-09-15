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

from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_tax_chart(osv.osv_memory):
    """
    For Chart of Accounts
    """
    _inherit = "account.tax.chart"
    
    def onchange_period_id(self, cr, uid, ids, period_id, context=None):
        """
            Actualiza registros cuando se cambia el periodo
        """
        period_reg = False
        if not period_id:
            period_reg = False
        else:
            history_ids = self.pool.get('account.tax.code.history').search(cr, uid, [('period_id','=',period_id)], context=context)
            if history_ids:
                period_reg = True
        return {'value': {'period_reg': period_reg}}
    
    def account_tax_chart_open_window(self, cr, uid, ids, context=None):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_tax_code_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.period_id:
            result['context'] = str({'period_id': data.period_id.id, \
                                     'fiscalyear_id': data.period_id.fiscalyear_id.id, \
                                        'state': data.target_move, \
                                        'search_default_period_id': data.period_id.id})
            period_code = data.period_id.code
            result['name'] += period_code and (':' + period_code) or ''
        else:
            result['context'] = str({'state': data.target_move})

        return result
    
    def update_value_code_history_childs(self, cr, uid, parent_id, history_id, child_ids, period_id, context=None):
        """
            Agrega al historial los hijos y los relaciona
        """
        line_obj = self.pool.get('account.tax.code.history.line')
        balance_obj = self.pool.get('account.fiscal.balance')
        # Recorre los hijos del codigo
        for child in child_ids:
            # Registra el codigo en el historial
            line_id = line_obj.create(cr, uid, {
                'name': child.name,
                'history_id': history_id,
                'code_id': child.id,
                'company_id': child.company_id.id,
                'sequence': child.sequence,
                'percent': child.percent,
                'sum_period': child.sum_period,
                'sum_year': child.sum,
                'base_period': child.base_period,
                'base_year': child.base,
                'parent_id': parent_id}, context=context)
            
            # Revisa si el codigo registra un saldo, si es un saldo
            if child.sum_period < 0 and child.apply_balance == True:
                # Valida si ya existe un saldo sobre ese periodo
                balance_ids = balance_obj.search(cr, uid, [('tax_code_id','=',child.id),('type','=','tax'),('state','=','open'),('period_id','=',period_id)], context=context)
                if balance_ids:
                    raise osv.except_osv(_('Error de Validacion!'),_("Ya existe un saldo, con el impuesto %s en el estado abierto!"%(child.name)))
                
                # Revisa si hay impuestos sobre ese periodo
                balance_ids = balance_obj.search(cr, uid, [('tax_code_id','=',child.id),('type','=','tax'),('period_id','=',period_id)], context=context)
                if balance_ids:
                    balance_obj.unlink(cr, uid, balance_ids, context=context)
                
                # Registra el saldo
                balance_obj.create(cr, uid, {
                    'amount': child.sum_period * -1,
                    'type': 'tax',
                    'tax_code_id': child.id,
                    'state': 'draft',
                    'period_id': period_id
                    }, context=context)
            
            # Valida si tiene hijos el codigo
            if child.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, child.child_ids, period_id, context=context)
        return True
    
    def account_tax_chart_history_create(self, cr, uid, ids, context=None):
        """
            Guarda la informacion de los impuestos en el historial
        """
        code_obj = self.pool.get('account.tax.code')
        history_obj = self.pool.get('account.tax.code.history')
        line_obj = self.pool.get('account.tax.code.history.line')
        period_id = context.get('period_id', False)
        target_move = context.get('state','posted')
        
        # Valida que no se hayan aplicado saldos sobre los impuestos
        cr.execute("""
            select cont
            from account_tax_code_history
            where period_id = %s"""%(period_id))
        num_balance = 0.0
        for value in cr.fetchall():
            num_balance = value[0]
            break
        if num_balance > 0:
            raise osv.except_osv(_('Error de Validacion!'),_("Ya existe un saldo aplicado sobre el historial en el periodo"))
        
        # Valida que no existan registros en el historial para ese periodo
        history_ids = history_obj.search(cr, uid, [('period_id','=',period_id)], context=context)
        if history_ids:
            # Elimina los registros para actualizar el periodo
            history_obj.unlink(cr, uid, history_ids, context=context)
        
        # Genera el nuevo registro para el encabezado del historial
        period = self.pool.get('account.period').read(cr, uid, period_id, ['name'], context=context)
        name = 'HST-POS-' + period['name'] if target_move == 'posted' else 'HST-ALL-' + period['name']
        
        # Registra el encabezado del historial
        history_id = history_obj.create(cr, uid, {
            'name': name,
            'period_id': period_id,
            'target_move': target_move}, context=context)
        
        # Recorre los registros
        code_ids = code_obj.search(cr, uid, [('parent_id','=',False)], context=context)
        for code in code_obj.browse(cr, uid, code_ids, context=context):
            name_hist = code.name + '- ' + period['name']
            # Registra el codigo en el historial
            line_id = line_obj.create(cr, uid, {
                'name': name_hist,
                'history_id': history_id,
                'code_id': code.id,
                'company_id': code.company_id.id,
                'sequence': code.sequence,
                'percent': code.percent,
                'sum_period': code.sum_period,
                'sum_year': code.sum,
                'base_period': code.base_period,
                'base_year': code.base}, context=context)
            # Valida si tiene hijos el codigo
            if code.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, code.child_ids, period_id, context=context)
        return True
    
    def account_tax_chart_save_window(self, cr, uid, ids, context=None):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        ctx = context.copy()
        
        data = self.browse(cr, uid, ids, context=context)[0]
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_tax_code_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.period_id:
            result['context'] = str({'period_id': data.period_id.id, \
                                     'fiscalyear_id': data.period_id.fiscalyear_id.id, \
                                        'state': data.target_move, \
                                        'search_default_period_id': data.period_id.id})
            ctx['period_id'] = data.period_id.id
            ctx['fiscalyear_id'] = data.period_id.fiscalyear_id.id
            ctx['state'] = data.target_move
            period_code = data.period_id.code
            result['name'] += period_code and (':' + period_code) or ''
        else:
            result['context'] = str({'state': data.target_move})
            ctx['state'] = data.target_move
        
        # Valida que haya un periodo seleccionado para 
        if not data.period_id:
            raise osv.except_osv(_('Error de Validacion!'),_("Debes seleccionar un periodo para guardar la informaicon de los impuestos en el historial!"))
        
        # Guarda el resultado en el historial
        self.account_tax_chart_history_create(cr, uid, ids, context=ctx)
        return result
    
    _columns = {
        'period_reg': fields.boolean('Periodo registrado'),
    }

account_tax_chart()

class account_tax_code_chart_history(osv.osv_memory):
    """
        For Chart of taxes
    """
    _name = "account.tax.code.chart.history"
    _description = "Account tax code chart"
    
    def _get_fiscalyear(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        fiscalyear_id = False
        if period_ids:
           period = self.pool.get('account.period').browse(cr, uid, period_ids[0], context=context)
           fiscalyear_id = period.fiscalyear_id.id
        return fiscalyear_id

    _columns = {
       'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio Fiscal', required=True),
    }
    
    _defaults = {
        'fiscalyear_id': _get_fiscalyear,
    }
    
    def account_tax_code_chart_open(self, cr, uid, data, context=None):
        """
            Obtiene el valor del resultado para la carga del sistema
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        
        # Obtiene la informacion para mostrar la vista
        result = mod_obj.get_object_reference(cr, uid, 'account_fiscal', 'action_account_tax_code_chart_history_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.fiscalyear_id:
            result['context'] = str({'fiscalyear_id': data.fiscalyear_id.id, \
                                        #'target_move': data.target_move})
                                        })
            fiscalyear_code = data.fiscalyear_id.code
            result['name'] += fiscalyear_code and (':' + fiscalyear_code) or ''
            result['domain'] = "[('parent_id','=',False),('fiscalyear_id','=',%s)]"%(data.fiscalyear_id.id)
        else:
            result['name'] = 'Historico Anual'
            result['context'] = str({})
            result['domain'] = "[('parent_id','=',False)]"
        return result
    
    def account_tax_code_chart_history_open_window(self, cr, uid, ids, context=None):
        """
            Opens chart of Accounts
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of account chart’s IDs
            @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        data = self.browse(cr, uid, ids, context=context)[0]
        
        # Obtiene la informacion para mostrar la vista
        result = self.account_tax_code_chart_open(cr, uid, data, context=context)
        return result
    
account_tax_code_chart_history()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
