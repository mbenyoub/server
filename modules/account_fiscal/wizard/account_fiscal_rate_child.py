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

class account_fiscal_rate_child(osv.osv_memory):
    """ Agregar indice fiscal """
    _name = 'account.fiscal.rate.child'
    _description = 'Indice Fiscal nuevo'
    
    def onchange_type_rate(self, cr, uid, ids, type_rate, context=None):
        """
            Cambia el valor a aplicar segun sea el caso
        """
        if not type_rate:
            return {}
        values = {'apply': 'current'}
        if type_rate == 'asset':
            values = {'apply': 'prev', 'code_year': True, 'apply_year':True}
        return {'value': values}
    
    def onchange_code_id(self, cr, uid, ids, code_id, context=None):
        """
            Revisa si es un codigo anual o mensual
        """
        code_year = False
        if code_id:
            history_ids = self.pool.get('account.fiscal.code.history').search(cr, uid, [('period_id','=',period_id),('type','=','period')], context=context)
            # Valida si aplica por año
            code_year = self.pool.get('account.fiscal.code').code_is_year(cr, uid, code_id, context=context)
        return {'value': {'code_year': code_year, 'apply_year': code_year}}
    
    def action_add_rate(self, cr, uid, ids, context=None):
        """
            Agrega el codigo hijo al indice fiscal
        """
        link_obj = self.pool.get('links.get.request')
        rate_obj = self.pool.get('account.fiscal.rate')
        #~ Valida que el objeto account.invoice se encuentre en las referencias
        link_obj.validate_link(cr, uid, 'account.account.category', 'Account Category', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.rate', 'Account fiscal rate', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.code', 'Account fiscal code', context=context)
        link_obj.validate_link(cr, uid, 'account.fiscal.inpc', 'INPC', context=context)
        
        id = 0
        # Recorre los registros
        for rate in self.browse(cr, uid, ids, context=context):
            base = rate.base if rate.type_rate == 'acf_period' or rate.type_rate == 'acf_cumulative' else 'value'
            # Agrega el nuevo registro
            values = {
                'name': rate.name,
                'code': rate.code,
                'description': rate.description,
                'base': base,
                'factor': rate.factor,
                'type_rate': rate.type_rate,
                'parent_id': rate.parent_id.id,
                'apply_year': rate.apply_year,
                'apply': rate.apply,
                'if_apply': rate.if_apply,
                'period_id': rate.period_id.id,
                'sign': 1
            }
            # Obtiene la secuencia para el registro
            cr.execute("""
            select (case when max(sequence) > 0 then (max(sequence) + 1) else 1 end) as sequence
            from account_fiscal_rate
            where parent_id=%s"""%(rate.parent_id.id,))
            sequence = [x[0] for x in cr.fetchall()]
            values['sequence'] = sequence[0]
            
            # Agrega la referencia sobre el registro
            if rate.type_rate == 'acf_cumulative' or rate.type_rate == 'acf_period':
                values['reference'] = 'account.account.category,' + str(rate.category_id.id)
            elif rate.type_rate == 'frate':
                values['reference'] = 'account.fiscal.rate,' + str(rate.rate_id.id)
            elif rate.type_rate == 'code_cumulative' or rate.type_rate == 'code_period':
                values['reference'] = 'account.fiscal.code,' + str(rate.code_id.id)
                values['code_year'] = code.code_year
                if code.code_year == True:
                    values['apply_year'] = code.code_year
            elif rate.type_rate == 'val':
                values['value'] = rate.value
            elif rate.type_rate == 'inpc':
                if rate.apply == 'esp':
                    values['inpc_id'] = rate.inpc_id.id
            elif rate.type_rate == 'asset':
                values['type_asset'] = rate.type_asset
            
            # Agrega la condicion de ser necesario
            if rate.if_apply:
                values['condition'] = rate.condition
                values['condition_res'] = rate.condition_res
                values['operator'] = rate.operator
                values['condition_type'] = rate.condition_type
                values['condition_value'] = rate.condition_value
            
            # Crea el nuevo registro
            rate_id = rate_obj.create(cr, uid, values, context=context)
        return True
        
    _columns = {
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Codigo', size=32),
        'description': fields.text('Descripcion'),
        'parent_id': fields.many2one('account.fiscal.rate', 'Codigo Padre', select=True),
        'type_rate': fields.selection([
                        ('acf_period','Rubro Fiscal'),
                        ('acf_cumulative','Rubro fiscal Acumulable'),
                        ('code_period','Codigo Fiscal'),
                        ('code_cumulative','Codigo fiscal Acumulable'),
                        ('frate','Indice Fiscal'),
                        ('inpc','INPC'),
                        ('asset','Activo Fijo'),
                        ('utility','Perdida Fiscal'),
                        ('per','No. Mes Periodo'),
                        ('val','Valor')], 'Tipo Indice', required=True),
        'factor': fields.selection([
                        ('sum','Suma'),
                        ('res','Resta'),
                        ('mul','Multiplicacion'),
                        ('div','Division')], 'Factor', required=True),
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
        'inpc_id': fields.many2one('account.fiscal.inpc', 'INPC', select=True),
        'apply': fields.selection([
                        ('prev','Anterior'),
                        ('current','Actual'),
                        ('esp','Especifico')], 'Aplicar'),
        'period_id': fields.many2one('account.period','Periodo', select="1"),
        'fiscalyear_id': fields.many2one('account.fiscalyear','Ejercicio Fiscal', select="1"),
        'type_asset': fields.selection([
                        ('sold','Vendido'),
                        ('open','No Vendido'),
                        ('all','Obtener Todo')], 'Obtener Activo'),
        'value': fields.float('Valor', digits=(16,12)),
        # Aplicar condiciones
        'if_apply': fields.boolean('Aplicar condicion'),
        'condition': fields.selection([
                        ('if','Si'),
                        ('else','Sino'),], 'Condicion'),
        'condition_res': fields.selection([
                        ('res','Resultado'),
                        ('cum','Valor acumulado')], 'Condicion'),
        'operator': fields.selection([
                        ('=','Igual'),
                        ('<>','Diferente'),
                        ('>','Mayor'),
                        ('>=','Mayor o Igual'),
                        ('<','Menor'),
                        ('<=','Menor o Igual'),], 'Operador'),
        'condition_type': fields.selection([
                        ('val','Valor'),
                        ('res','Resultado'),
                        ('per','No. Mes periodo'),
                        ('ejer','No. periodos ejercicio'),], 'Condicion'),
        'condition_value': fields.float('Valor'),
    }
    
    _defaults = {
        'type_rate': 'val',
        'factor': 'sum',
        'base': 'debit',
        'apply': 'prev',
        'if_apply': False,
        'condition': 'if',
        'condition_res': 'cum',
        'operator':'=',
        'condition_type':'res',
        'condition_value': 0.0,
        'value': 1.0,
        'type_asset': 'all'
    }

account_fiscal_rate_child()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
