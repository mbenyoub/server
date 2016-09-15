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

class account_period_close(osv.osv_memory):
    """
        close period
    """
    _inherit = "account.period.close"
    
    def get_value_account_period(self, cr, uid, period_id, category_id, context=None):
        """
            Retorna el saldo de los movimientos sobre el periodo con el rubro fiscal seleccionado
        """
        get_asset = " and m.state = 'posted'"
        amount = 0.0
        
        # Ejecuta la consulta que obtiene el resultado del periodo
        cr.execute("""
            select
                case when sum(l.credit) <> 0 then sum(l.credit) else 0.0 end as credit, 
                case when sum(l.debit) <> 0 then sum(l.debit) else 0.0 end as debit 
            from
                account_move_line as l 
                inner join account_account_category_rel as r on l.account_id=r.account_id
                inner join account_move as m on m.id = l.move_id %s
            where l.period_id = %s and r.category_id = %s """%(get_asset,period_id,category_id))
        for credit, debit in cr.fetchall():
            res = {
                'debit': debit,
                'credit': credit
            }
            break;
        
        # Obtiene el saldo del periodo
        amount = res['credit'] - res['debit']
        return amount
    
    def get_period_config_settings(self, cr, uid, context=None):
        """
            Obtiene la configuracion para el fin del periodo
        """
        config_obj = self.pool.get('account.period.config.settings')
        
        res = {}
        cr.execute(
            """ select id as id
                from account_period_config_settings 
                order by id desc limit 1 """)
        dat = cr.dictfetchall()
        reg_id = dat and dat[0].get('id',False)
        if reg_id:
            config = config_obj.browse(cr, uid, reg_id, context=context)
            res = {
                'category_id': config.account_category_id.id or False,
                'journal_id': config.journal_id.id or False,
                'account_credit_id': config.account_credit_id.id or False,
                'account_debit_id': config.account_debit_id.id or False
            }
            
            # Agrega la configuracion de las cuentas del debe y el haber del diario
            if config.journal_id:
                if config.journal_id.default_credit_account_id:
                    res['account_credit_id'] = config.journal_id.default_credit_account_id.id
                if config.journal_id.default_debit_account_id:
                    res['account_debit_id'] = config.journal_id.default_debit_account_id.id
        return res
    
    def data_save(self, cr, uid, ids, context=None):
        """
            Crea la poliza de cierre sobre el periodo
        """
        period_obj = self.pool.get('account.period')
        period_obj = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')
        valid = True
        
        # Obtiene la configuracion para la poliza de cierre
        config = self.get_period_config_settings(cr, uid, context=context)
        
        # Valida que la configuracion este completa para generar
        if not config.get('category_id', False) or not config.get('journal_id', False) or not config.get('account_credit_id', False) or not config.get('account_debit_id', False):
            valid = False
        
        if valid:
            # Recorre los registros de los periodos a cerrar
            for form in self.read(cr, uid, ids, context=context):
                if form['sure']:
                    for id in context['active_ids']:
                        # Valida que el periodo no tenga un movimiento registrado
                        period = period_obj.browse(cr, uid, id, context=context)
                        if period.move_id:
                            continue
                        
                        # Busca los movimientos que tienen el periodo y las cuentas con el rubro fiscal aplicado en la configuracion
                        amount = self.get_value_account_period(cr, uid, id, config.get('category_id', False), context=context)
                        
                        data = {
                            'period_id': id,
                            'journal_id': config.get('journal_id',False),
                            'account_credit_id': config.get('account_credit_id',False),
                            'account_debit_id': config.get('account_debit_id',False)
                        }
                        # Agrega los datos al registro
                        if amount > 0.0:
                            data['credit'] = amount
                            data['debit'] = 0.0
                        else:
                            data['debit'] = amount * -1
                            data['credit'] = 0.0
                        
                        move_id = period_obj.create_move_id_close(cr, uid, data, context=context)
                        
                        # Actualiza el periodo de cierre
                        period_obj.write(cr, uid, [id], {'move_id': move_id}, context=context)
            
        # Ejecuta la funcion original
        return super(account_period_close, self).data_save(cr, uid, ids, context=context)
    
account_period_close()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
