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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_fiscal_code_child(osv.osv_memory):
    """ Agregar codigo fiscal """
    _name = 'account.fiscal.code.child'
    _description = 'Codigo Fiscal nuevo'
    
    def onchange_code_id(self, cr, uid, ids, code_id, context=None):
        """
            Revisa si es un codigo anual o mensual
        """
        code_year = False
        if code_id:
            # Valida si aplica por año
            code_year = self.pool.get('account.fiscal.code').code_is_year(cr, uid, code_id, context=context)
        return {'value': {'code_year': code_year, 'apply_year': code_year}}
    
    def action_add_code(self, cr, uid, ids, context=None):
        """
            Agrega el codigo hijo al codigo fiscal
        """
        link_obj = self.pool.get('links.get.request')
        code_obj = self.pool.get('account.fiscal.code')
        com_obj = self.pool.get('account.fiscal.code.compute')
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.account.category', 'Account Category', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.rate', 'Account fiscal rate', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.code', 'Account fiscal code', context=context)
        
        id = 0
        # Recorre los registros
        for code in self.browse(cr, uid, ids, context=context):
            base = 'value' if code.type_code == 'frate' or code.type_code == 'code_cumulative' or code.type_code == 'code_period' else code.base
            # Agrega el nuevo registro
            values = {
                'name': code.name,
                'info': code.info,
                'base': base,
                'factor': code.factor,
                'type_code': code.type_code,
                'parent_id': code.parent_id.id,
                'apply_year': code.apply_year,
                'compute': code.compute,
                'apply': code.apply,
                'apply_balance': code.apply_balance,
                'sign': 1,
                'if_apply2': code.if_apply2,
                'condition2': code.condition2,
                'condition_res2': code.condition_res2,
                'operator2': code.operator2,
                'condition_value2': code.condition_value2,
                'type_move': code.type_move
            }
            # Obtiene la secuencia para el registro
            cr.execute("""
            select (case when max(sequence) > 0 then (max(sequence) + 1) else 1 end) as sequence
            from account_fiscal_code
            where parent_id=%s"""%(code.parent_id.id,))
            sequence = [x[0] for x in cr.fetchall()]
            values['sequence'] = sequence[0]
            
            # Agrega la referencia sobre el registro
            if code.type_code == 'acf_cumulative' or code.type_code == 'acf_period':
                values['reference'] = 'account.account.category,' + str(code.category_id.id)
            elif code.type_code == 'frate':
                values['reference'] = 'account.fiscal.rate,' + str(code.rate_id.id)
            elif code.type_code == 'code_cumulative' or code.type_code == 'code_period':
                values['reference'] = 'account.fiscal.code,' + str(code.code_id.id)
                values['code_year'] = code.code_year
                if code.code_year == True:
                    values['apply_year'] = code.code_year
            
            # Crea el nuevo registro
            code_id = code_obj.create(cr, uid, values, context=context)
            # Valida si agrega calculos extra al codigo
            if code.compute:
                for com in code.compute_ids:
                    # Agrega el nuevo registro
                    values = {
                        'code_id': code_id,
                        'factor': com.factor,
                        'type': com.type,
                        'value': com.value
                    }
                    # Obtiene la secuencia para el registro
                    cr.execute("""
                    select (case when max(sequence) > 0 then (max(sequence) + 1) else 1 end) as sequence
                    from account_fiscal_code_compute
                    where code_id=%s"""%(code_id,))
                    sequence = [x[0] for x in cr.fetchall()]
                    values['sequence'] = sequence[0]
                    # Crea el nuevo registro
                    com_id = com_obj.create(cr, uid, values, context=context)
        return True
        
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32),
        'info': fields.text('Descripcion'),
        'parent_id': fields.many2one('account.fiscal.code', 'Codigo Padre', select=True),
        'type_code': fields.selection([
                        ('acf_period','Rubro Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_period','Codigo Fiscal'),
                        ('code_cumulative','Codigo fiscal Acumulable'),
                        ('frate','Indice Fiscal')], 'Tipo Codigo', required=True),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division'),
                        ('none','Nulo')], 'Factor', required=True),
        'base': fields.selection([
                        ('debit','Debe'),
                        ('credit','Haber'),
                        ('dif','Debe - Haber'),
                        ('dif2','Haber - Debe')], 'Calculo base', required=True),
        'category_id': fields.many2one('account.account.category','Rubro fiscal', select="1"),
        'rate_id': fields.many2one('account.fiscal.rate','Indice Fiscal', select="1"),
        'apply_year': fields.boolean('Obtener por Ejercicio Fiscal'),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal', select=True),
        'code_year': fields.boolean('Codigo anual'),
        'compute_ids': fields.one2many('account.fiscal.code.child.compute', 'code_id', 'Calculos Extra', ondelete='cascade'),
        'compute': fields.boolean('Agregar Calculos extra'),
        'apply': fields.selection([
                        ('prev','Anterior'),
                        ('current','Actual')], 'Aplicar'),
        'if': fields.boolean('Aplicar condicion'),
        'is_year': fields.boolean('Aplica por año'),
        # Aplicar condiciones sobre acumulador
        'if_apply2': fields.boolean('Aplicar condicion sobre acumulacion'),
        'condition2': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'condition_res2': fields.selection([
                        ('res','Resultado'),
                        ('cum','Valor acumulado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], 'condicion valor'),
        'operator2': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_value2': fields.float('Valor'),
        'apply_balance': fields.boolean('Aplica en Saldos Fiscales'),
        'type_move': fields.selection([
                        ('reconciled','Conciliado'),
                        ('not_reconciled','No conciliado'),
                        ('all','Todo')], 'Tipo Movimiento'),
    }
    
    _defaults = {
        'type_code': 'acf_period',
        'factor': 'sum',
        'base': 'debit',
        'apply': 'prev',
        
        'if_apply2': False,
        'condition_res2': 'res',
        'condition2': 'if',
        'operator2': '=',
        'condition_value2': 0.0,
        'type_move': 'all'
    }

account_fiscal_code_child()

class account_fiscal_code_child_compute(osv.osv_memory):
    _name = 'account.fiscal.code.child.compute'
    
    _columns = {
        'code_id': fields.many2one('account.fiscal.code.child', 'Codigo', select=True, ondelete='cascade'),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division')], 'Factor'),
        'type': fields.selection([
                        ('val','Valor Fijo'),
                        ('anio','No. año fiscal'),
                        ('per','No. Mes periodo')], 'Tipo'),
        'value': fields.float('Valor', digits=(16,4))
    }
    
    _defaults = {
        'type': 'val',
        'factor': 'sum',
        'value': 0.0
    }
    
account_fiscal_code_child_compute()

class account_fiscal_code_child_condition(osv.osv_memory):
    """ Agregar condicion sobre codigo fiscal """
    _name = 'account.fiscal.code.child.condition'
    _description = 'Condicion sobre Codigo Fiscal nuevo'
    
    def action_add_code(self, cr, uid, ids, context=None):
        """
            Agrega la condicion al codigo fiscal
        """
        link_obj = self.pool.get('links.get.request')
        code_obj = self.pool.get('account.fiscal.code')
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.account.category', 'Account Category', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.rate', 'Account fiscal rate', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.code', 'Account fiscal code', context=context)
        
        id = 0
        # Recorre los registros
        for code in self.browse(cr, uid, ids, context=context):
            base = 'value' if code.type_code == 'frate' or code.type_code == 'code_cumulative' or code.type_code == 'code_period' else code.base
            # Agrega el nuevo registro
            values = {
                'name': code.name,
                'code': code.code,
                'info': code.info,
                'base': base,
                'factor': code.factor,
                'type_code': code.type_code,
                'parent_id': code.parent_id.id,
                'apply_year': code.apply_year,
                'apply': code.apply,
                'if_value': True,
                'condition': code.condition,
                'operator': code.operator,
                'condition_value': code.condition_value,
                'sign': 1
            }
            # Obtiene la secuencia para el registro
            cr.execute("""
            select (case when max(sequence) > 0 then (max(sequence) + 1) else 1 end) as sequence
            from account_fiscal_code
            where parent_id=%s"""%(code.parent_id.id,))
            sequence = [x[0] for x in cr.fetchall()]
            values['sequence'] = sequence[0]
            
            # Agrega la referencia sobre el registro
            if code.type_code == 'acf_cumulative' or code.type_code == 'acf_period':
                values['reference'] = 'account.account.category,' + str(code.category_id.id)
            elif code.type_code == 'frate':
                values['reference'] = 'account.fiscal.rate,' + str(code.rate_id.id)
            elif code.type_code == 'code_cumulative' or code.type_code == 'code_period':
                values['reference'] = 'account.fiscal.code,' + str(code.code_id.id)
            
            # Crea el nuevo registro
            code_id = code_obj.create(cr, uid, values, context=context)
        return True
        
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32),
        'info': fields.text('Descripcion'),
        'parent_id': fields.many2one('account.fiscal.code', 'Codigo Padre', select=True),
        'type_code': fields.selection([
                        ('acf_period','Rubro Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_period','Codigo Fiscal'),
                        ('code_cumulative','Codigo fiscal Acumulable'),
                        ('frate','Indice Fiscal')], 'Tipo Codigo', required=True),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division'),
                        ('none','Nulo')], 'Factor', required=True),
        'base': fields.selection([
                        ('debit','Debe'),
                        ('credit','Haber'),
                        ('dif','Debe - Haber'),
                        ('dif2','Haber - Debe')], 'Calculo base', required=True),
        'category_id': fields.many2one('account.account.category','Rubro fiscal', select="1"),
        'rate_id': fields.many2one('account.fiscal.rate','Indice Fiscal', select="1"),
        'apply_year': fields.boolean('Obtener por Ejercicio Fiscal'),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal', select=True),
        'apply': fields.selection([
                        ('prev','Anterior'),
                        ('current','Actual')], 'Aplicar'),
        'condition': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'operator': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_value': fields.float('Valor')
    }
    
    _defaults = {
        'type_code': 'acf_period',
        'factor': 'sum',
        'base': 'debit',
        'apply': 'current',
        'condition': 'if',
        'operator': '=',
        'condition_value': 0.0
    }

account_fiscal_code_child_condition()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
