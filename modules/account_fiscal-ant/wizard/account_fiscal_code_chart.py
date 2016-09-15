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

class account_fiscal_code_chart(osv.osv_memory):
    """
        For Chart of taxes
    """
    _name = "account.fiscal.code.chart"
    _description = "Account fiscal code chart"
    
    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def onchange_period_id(self, cr, uid, ids, period_id, context=None):
        """
            Actualiza registros cuando se cambia el diario
        """
        #print "********** onchange_period_id ******** ", period_id
        period_reg = False
        year_reg = False
        if not period_id:
            period_reg = False
            year_reg = False
        else:
            history_ids = self.pool.get('account.fiscal.code.history').search(cr, uid, [('period_id','=',period_id),('type','=','period')], context=context)
            #print "************** history_ids ******* ", history_ids
            if history_ids:
                period_reg = True
            fiscalyear_id = self.pool.get('account.period').browse(cr, uid, period_id, context=context).fiscalyear_id.id
            history_ids = self.pool.get('account.fiscal.code.history').search(cr, uid, [('fiscalyear_id','=',fiscalyear_id),('type','=','year')], context=context)
            #print "************** history_ids ******* ", history_ids
            if history_ids:
                year_reg = True
        return {'value': {'period_reg': period_reg, 'year_reg': year_reg}}
    
    _columns = {
       'period_id': fields.many2one('account.period', 'Periodo', required=True),
       'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                        ('all', 'Todos los asientos'),
                                        ], 'Movimientos', required=True),
        'period_reg': fields.boolean('Periodo registrado'),
        'year_reg': fields.boolean('Año registrado')
    }
    
    _defaults = {
        'period_id': _get_period,
        'target_move': 'posted'
    }
    
    def update_value_code(self, cr, uid, period_id, target_move='all', context=None):
        """
            Actualiza el valor del codigo fiscal
        """
        code_ids = self.pool.get('account.fiscal.code').search(cr, uid, [], context=context)
        self.pool.get('account.fiscal.code').write(cr, uid, code_ids, {'period_id': period_id, 'target_move': target_move}, context=context)
        return True
    
    def update_value_code_history_childs(self, cr, uid, parent_id, history_id, child_ids, context=None):
        """
            Agrega al historial los hijos y los relaciona
        """
        history_line_obj = self.pool.get('account.fiscal.code.history.line')
        # Recorre los hijos del codigo
        for child in child_ids:
            # Registra el codigo en el historial
            line_id = history_line_obj.create(cr, uid, {
                'name': child.name,
                'history_id': history_id,
                'code_id': child.id,
                'value': child.result,
                'sequence': child.sequence,
                'factor': child.factor,
                'parent_id': parent_id}, context=context)
            # Valida si tiene hijos el codigo
            if child.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, child.child_ids, context=context)
        return True
    
    def update_value_code_history(self, cr, uid, period_id, fiscalyear_id, target_move, context=None):
        """
            Actualiza el valor del codigo fiscal
        """
        code_obj = self.pool.get('account.fiscal.code')
        history_obj = self.pool.get('account.fiscal.code.history')
        history_line_obj = self.pool.get('account.fiscal.code.history.line')
        code_ids = code_obj.search(cr, uid, [('parent_id','=',False)], context=context)
        period = self.pool.get('account.period').read(cr, uid, period_id, ['name'], context=context)
        # Valida que no existan registros para ese periodo
        history_ids = history_obj.search(cr, uid, [('period_id','=',period_id),('target_move','=',target_move)], context=context)
        if history_ids:
            # Elimina los registros para actualizar el periodo
            history_obj.unlink(cr, uid, history_ids, context=context)
        name = 'HST-POS-' + period['name'] if target_move == 'posted' else 'HST-ALL-' + period['name']
        # Registra el encabezado del historial
        history_id = history_obj.create(cr, uid, {
            'name': name,
            'period_id': period_id,
            'target_move': target_move}, context=context)
        # Recorre los registros de los codigos fiscales
        for code in code_obj.browse(cr, uid, code_ids, context=context):
            # Registra el codigo en el historial
            line_id = history_line_obj.create(cr, uid, {
                'name': code.name + '- ' + code.period_id.name,
                'history_id': history_id,
                'code_id': code.id,
                'sequence': code.sequence,
                'factor': code.factor,
                'value': code.result}, context=context)
            # Valida si tiene hijos el codigo
            if code.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, code.child_ids, context=context)
        return True
    
    def account_fiscal_code_chart_open(self, cr, uid, data, context=None):
        """
            Obtiene el valor del resultado para la carga del sistema
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        
        # Obtiene la informacion para mostrar la vista
        result = mod_obj.get_object_reference(cr, uid, 'account_fiscal', 'action_account_fiscal_code_chart_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.period_id:
            result['context'] = str({'period_id': data.period_id.id, \
                                        'fiscalyear_id': data.period_id.fiscalyear_id.id, \
                                        'state': data.target_move})
            period_code = data.period_id.code
            result['name'] += period_code and (':' + period_code) or ''
        else:
            result['context'] = str({'state': data.target_move})
        #print "************* resultado reporte ******** ", result
        return result
    
    def account_fiscal_code_chart_open_window(self, cr, uid, ids, context=None):
        """
            Opens chart of Accounts
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of account chart’s IDs
            @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        data = self.browse(cr, uid, ids, context=context)[0]
        # Actualiza el periodo en los codigos fiscales
        self.update_value_code(cr, uid, data.period_id.id, data.target_move, context=context)
        
        # Obtiene la informacion para mostrar la vista
        result = self.account_fiscal_code_chart_open(cr, uid, data, context=context)
        return result
    
    def account_fiscal_code_chart_save_window(self, cr, uid, ids, context=None):
        """
            Ejecuta un wizard con los movimientos posibles a relacionar
        """
        # Obtiene la vista a cargar
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_code_chart_save')
        
        # Obtiene la informacion del registro
        code = self.browse(cr, uid, ids[0], context=context)
        # Envia la informacion del registro en el context
        ctx = context.copy()
        ctx['default_period_id'] = code.period_id.id
        ctx['default_target_move'] = code.target_move
        ctx['default_period_reg'] = code.period_reg
        ctx['default_year_reg'] = code.year_reg
        
        return {
            'name':_("Guardar Calculo de Codigos Fiscales"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.code.chart.save',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': ctx
        }

account_fiscal_code_chart()

class account_fiscal_code_chart_save(osv.osv_memory):
    """
        For Chart of taxes
    """
    _name = "account.fiscal.code.chart.save"
    _description = "Account fiscal code chart"
    
    _columns = {
       'period_id': fields.many2one('account.period', 'Periodo', required=True),
       'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                        ('all', 'Todos los asientos'),
                                        ], 'Movimientos', required=True),
        'period_reg': fields.boolean('Periodo registrado'),
        'year_reg': fields.boolean('Año registrado')
    }
    
    def update_value_code(self, cr, uid, period_id, target_move='all', context=None):
        """
            Actualiza el valor del codigo fiscal
        """
        code_ids = self.pool.get('account.fiscal.code').search(cr, uid, [], context=context)
        self.pool.get('account.fiscal.code').write(cr, uid, code_ids, {'period_id': period_id, 'target_move': target_move}, context=context)
        return True
    
    def update_value_code_history_childs(self, cr, uid, parent_id, history_id, child_ids, period_id, fiscalyear_id, type='period', context=None):
        """
            Agrega al historial los hijos y los relaciona
        """
        balance_obj = self.pool.get('account.fiscal.balance')
        history_line_obj = self.pool.get('account.fiscal.code.history.line')
        # Recorre los hijos del codigo
        for child in child_ids:
            # Registra el codigo en el historial
            line_id = history_line_obj.create(cr, uid, {
                'name': child.name,
                'history_id': history_id,
                'code_id': child.id,
                'value': child.result,
                'sequence': child.sequence,
                'factor': child.factor,
                'parent_id': parent_id}, context=context)
            
            ## Revisa si el codigo registra un saldo, si es un saldo
            #if child.result < 0 and child.apply_balance == True:
            #    balance_ids = False
            #    # Revisa si es un codigo por proceso anual o mensual
            #    if type == 'period':
            #        # Valida si ya existe un saldo sobre ese periodo
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',child.id),('type','=','code'),('state','=','open'),('type_code','=','month'),('period_id','=',period_id)], context=context)
            #    else:
            #        # Valida si ya existe un saldo sobre el ejercicio
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',child.id),('type','=','code'),('state','=','open'),('type_code','=','year'),('fiscalyear_id','=',fiscalyear_id)], context=context)
            #    
            #    if balance_ids:
            #        raise osv.except_osv(_('Error de Validacion!'),_("Ya existe un saldo registrado con el codigo fiscal %s en el estado abierto!"%(child.name)))
            #    
            #    # Revisa si hay impuestos sobre ese periodo
            #    if type == 'period':
            #        # Revisa si hay saldos sobre ese periodo
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',child.id),('type','=','code'),('type_code','=','month'),('period_id','=',period_id)], context=context)
            #    else:
            #        # Revisa si hay saldos sobre el ejercicio
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',child.id),('type','=','code'),('type_code','=','year'),('fiscalyear_id','=',fiscalyear_id)], context=context)
            #    # Elimina los registros sobre el codigo fiscal
            #    if balance_ids:
            #        balance_obj.unlink(cr, uid, balance_ids, context=context)
            #    
            #    # Registra el saldo
            #    balance_obj.create(cr, uid, {
            #        'amount': child.result * -1,
            #        'type': 'code',
            #        'type_code': 'month' if type == 'period' else 'year',
            #        'period_id': period_id,
            #        'fiscalyear_id': fiscalyear_id,
            #        'code_id': child.id,
            #        'state': 'draft'
            #        }, context=context)
            
            # Valida si tiene hijos el codigo
            if child.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, child.child_ids, period_id, fiscalyear_id, type, context=context)
        return True
    
    def update_value_code_history(self, cr, uid, period_id, fiscalyear_id, target_move, type='period', context=None):
        """
            Actualiza el valor del codigo fiscal
        """
        code_obj = self.pool.get('account.fiscal.code')
        balance_obj = self.pool.get('account.fiscal.balance')
        history_obj = self.pool.get('account.fiscal.code.history')
        history_line_obj = self.pool.get('account.fiscal.code.history.line')
        
        # Valida que no se hayan aplicado saldos sobre los impuestos
        if type == 'period':
            cr.execute("""
                select cont
                from account_fiscal_code_history
                where period_id = %s and type = '%s'"""%(period_id,type))
        else:
            cr.execute("""
                select cont
                from account_fiscal_code_history
                where fiscalyear_id = %s and type = '%s'"""%(fiscalyear_id,type))
        num_balance = 0.0
        for value in cr.fetchall():
            num_balance = value[0]
            break
        if num_balance > 0:
            raise osv.except_osv(_('Error de Validacion!'),_("Ya existe un saldo aplicado sobre el historial en el periodo"))
        
        # Valida si debe obtener procesos anuales o mensuales
        apply_year = False if type == 'period' else True
        code_ids = code_obj.search(cr, uid, [('parent_id','=',False),('apply_year','=',apply_year)], context=context)
        if type == 'period':
            # Valida que no existan registros para ese periodo
            history_ids = history_obj.search(cr, uid, [('period_id','=',period_id),('type','=',type)], context=context)
            if history_ids:
                # Elimina los registros para actualizar el periodo
                history_obj.unlink(cr, uid, history_ids, context=context)
        else:
            # Valida que no existan registros para ese periodo
            history_ids = history_obj.search(cr, uid, [('fiscalyear_id','=',fiscalyear_id),('type','=',type)], context=context)
            if history_ids:
                # Elimina los registros para actualizar el periodo
                history_obj.unlink(cr, uid, history_ids, context=context)
        if type == 'period':
            period = self.pool.get('account.period').read(cr, uid, period_id, ['name'], context=context)
            name = 'HST-POS-' + period['name'] if target_move == 'posted' else 'HST-ALL-' + period['name']
        else:
            year = self.pool.get('account.fiscalyear').read(cr, uid, fiscalyear_id, ['name'], context=context)
            name = 'HST-POS-' + year['name'] if target_move == 'posted' else 'HST-ALL-' + year['name']
        # Registra el encabezado del historial
        history_id = history_obj.create(cr, uid, {
            'name': name,
            'period_id': period_id,
            'type': type,
            'target_move': target_move,
            'cont': 0.0}, context=context)
        # Recorre los registros de los codigos fiscales
        for code in code_obj.browse(cr, uid, code_ids, context=context):
            if type == 'period':
                name_hist = code.name + '- ' + code.period_id.name
            else:
                name_hist = code.name + '- ' + code.period_id.fiscalyear_id.name
            
            # Registra el codigo en el historial
            line_id = history_line_obj.create(cr, uid, {
                'name': name_hist,
                'history_id': history_id,
                'code_id': code.id,
                'value': code.result,
                'sequence': code.sequence,
                'factor': code.factor}, context=context)
            
            ## Revisa si el codigo registra un saldo, si es un saldo
            #if code.result < 0 and code.apply_balance == True:
            #    balance_ids = False
            #    # Revisa si es un codigo por proceso anual o mensual
            #    if type == 'period':
            #        # Valida si ya existe un saldo sobre ese periodo
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',code.id),('type','=','code'),('state','=','open'),('type_code','=','month'),('period_id','=',period_id)], context=context)
            #    else:
            #        # Valida si ya existe un saldo sobre el ejercicio
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',code.id),('type','=','code'),('state','=','open'),('type_code','=','year'),('fiscalyear_id','=',fiscalyear_id)], context=context)
            #    
            #    if balance_ids:
            #        raise osv.except_osv(_('Error de Validacion!'),_("Ya existe un saldo registrado con el codigo fiscal %s en el estado abierto!"%(code.name)))
            #    
            #    # Revisa si hay impuestos sobre ese periodo
            #    if type == 'period':
            #        # Revisa si hay saldos sobre ese periodo
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',code.id),('type','=','code'),('type_code','=','month'),('period_id','=',period_id)], context=context)
            #    else:
            #        # Revisa si hay saldos sobre el ejercicio
            #        balance_ids = balance_obj.search(cr, uid, [('code_id','=',code.id),('type','=','code'),('type_code','=','year'),('fiscalyear_id','=',fiscalyear_id)], context=context)
            #    # Elimina los registros sobre el codigo fiscal
            #    if balance_ids:
            #        balance_obj.unlink(cr, uid, balance_ids, context=context)
            #    
            #    # Registra el saldo
            #    balance_obj.create(cr, uid, {
            #        'amount': code.result * -1,
            #        'type': 'code',
            #        'type_code': 'month' if type == 'period' else 'year',
            #        'period_id': period_id,
            #        'fiscalyear_id': fiscalyear_id,
            #        'code_id': code.id,
            #        'state': 'draft'
            #        }, context=context)
            
            # Valida si tiene hijos el codigo
            if code.child_ids:
                self.update_value_code_history_childs(cr, uid, line_id, history_id, code.child_ids, period_id, fiscalyear_id, type, context=context)
        return True
    
    def account_fiscal_code_chart_open(self, cr, uid, data, context=None):
        """
            Obtiene el valor del resultado para la carga del sistema
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        
        # Obtiene la informacion para mostrar la vista
        result = mod_obj.get_object_reference(cr, uid, 'account_fiscal', 'action_account_fiscal_code_chart_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.period_id:
            result['context'] = str({'period_id': data.period_id.id, \
                                        'fiscalyear_id': data.period_id.fiscalyear_id.id, \
                                        'state': data.target_move})
            period_code = data.period_id.code
            result['name'] += period_code and (':' + period_code) or ''
        else:
            result['context'] = str({'state': data.target_move})
        #print "************* resultado reporte ******** ", result
        return result
    
    def account_fiscal_code_chart_save_period_window(self, cr, uid, ids, context=None):
        """
            Opens chart of Accounts
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of account chart’s IDs
            @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        data = self.browse(cr, uid, ids, context=context)[0]
        
        # Valida que el mes a calcular no sea enero
        cr.execute("""
                    select extract(month from p.date_start) as month
                    from account_period as p
                        inner join account_period as p2 on (p.date_start - interval '1 month')=(p2.date_start) and p2.date_start<>p2.date_stop
                    where p.id = %s"""%(data.period_id.id,))
        values = [x[0] for x in cr.fetchall()]
        #print "******************** valores mes ************* ", values
        if values:
            if values > 1:
                # Valida que este registrado el periodo anterior al periodo a guardar sino marca error
                cr.execute("""
                            select p.id 
                            from account_period as p
                                inner join account_fiscal_code_history as h on h.period_id=p.id
                            where extract(year from p.date_start) = (select extract(year from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                                and extract(month from p.date_start) = (select extract(month from (date_start - interval '1 month')) as Fecha from account_period where id = %s)
                                and p.special=False"""%(data.period_id.id,data.period_id.id))
                value = cr.fetchone()
                #print "************ value ************* ", value
                if not value:
                    period_ant_id = self.pool.get('account.fiscal.code')._get_period_ant(cr, uid, data.period_id.id, context=context)
                    period_ant = self.pool.get('account.period').browse(cr, uid, period_ant_id, context=context)
                    
                    raise osv.except_osv(_('Error de Validacion!'),_("Debes registrar el periodo anterior para poder guardar el siguente periodo!. \n (Periodo: %s ). \n\n NOTA. En caso de no utilizar el periodo debe eliminarlo para continuar con el proceso."%(period_ant.name,)))
        
        # Actualiza el periodo en los codigos fiscales para los movimientos con todos los asientos y sin ellos
        #target = 'all' if data.target_move == 'posted' else 'posted'
        #self.update_value_code(cr, uid, data.period_id.id, target, context=context)
        # Guarda la informacion de los codigos fiscales en el historial para el caso contrario al que se mostrara
        #self.update_value_code_history(cr, uid, data.period_id.id, data.period_id.fiscalyear_id.id, target, context=None)
        
        # Guarda la informacion de los codigos fiscales en el historial para el caso que se mostrara
        self.update_value_code(cr, uid, data.period_id.id, data.target_move, context=context)
        self.update_value_code_history(cr, uid, data.period_id.id, data.period_id.fiscalyear_id.id, data.target_move, 'period', context=None)
        
        # Obtiene la informacion para mostrar la vista
        result = self.account_fiscal_code_chart_open(cr, uid, data, context=context)
        return result
    
    def account_fiscal_code_chart_save_year_window(self, cr, uid, ids, context=None):
        """
            Opens chart of Accounts
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of account chart’s IDs
            @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        data = self.browse(cr, uid, ids, context=context)[0]
        
        # Guarda la informacion de los codigos fiscales en el historial para el caso que se mostrara
        self.update_value_code(cr, uid, data.period_id.id, data.target_move, context=context)
        self.update_value_code_history(cr, uid, data.period_id.id, data.period_id.fiscalyear_id.id, data.target_move, 'year', context=None)
        
        # Obtiene la informacion para mostrar la vista
        result = self.account_fiscal_code_chart_open(cr, uid, data, context=context)
        return result

account_fiscal_code_chart_save()

class account_fiscal_code_chart_history(osv.osv_memory):
    """
        For Chart of taxes
    """
    _name = "account.fiscal.code.chart.history"
    _description = "Account fiscal code chart"
    
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
       'get_year': fields.boolean('Obtener Historico anual')
       #'target_move': fields.selection([('posted', 'Todos los asientos asentados'),('all', 'Todos los asientos'),], 'Movimientos', required=True)
    }
    
    _defaults = {
        'fiscalyear_id': _get_fiscalyear,
        #'target_move': 'posted'
    }
    
    def account_fiscal_code_chart_open(self, cr, uid, data, context=None):
        """
            Obtiene el valor del resultado para la carga del sistema
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        
        # Obtiene la informacion para mostrar la vista
        result = mod_obj.get_object_reference(cr, uid, 'account_fiscal', 'action_account_fiscal_code_chart_history_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.fiscalyear_id and data.get_year == False:
            result['context'] = str({'fiscalyear_id': data.fiscalyear_id.id, \
                                        #'target_move': data.target_move})
                                        })
            fiscalyear_code = data.fiscalyear_id.code
            result['name'] += fiscalyear_code and (':' + fiscalyear_code) or ''
            #result['domain'] = "[('parent_id','=',False),('fiscalyear_id','=',%s),('target_move','=','%s')]"%(data.fiscalyear_id.id,data.target_move)
            result['domain'] = "[('parent_id','=',False),('fiscalyear_id','=',%s),('type','=','period')]"%(data.fiscalyear_id.id)
        else:
            #result['context'] = str({'target_move': data.target_move})
            #result['domain'] = "[('parent_id','=',False),('target_move','=','%s')]"%(data.target_move)
            result['name'] = 'Historico Anual'
            result['context'] = str({})
            result['domain'] = "[('parent_id','=',False),('type','=','year')]"
        #print "************* resultado reporte ******** ", result
        return result
    
    def account_fiscal_code_chart_history_open_window(self, cr, uid, ids, context=None):
        """
            Opens chart of Accounts
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of account chart’s IDs
            @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        data = self.browse(cr, uid, ids, context=context)[0]
        
        # Obtiene la informacion para mostrar la vista
        result = self.account_fiscal_code_chart_open(cr, uid, data, context=context)
        return result
    
account_fiscal_code_chart_history()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
