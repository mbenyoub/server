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

class account_fiscal_utility_validate(osv.osv_memory):
    """ Aplicar Perdida/Utilidad """
    _name = 'account.fiscal.utility.validate'
    _description = 'Aplicar Perdida/Utilidad'
    
    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id, remnant_before, context=None):
        """
            Actualiza la informacion de la perdida 
        """
        util_obj = self.pool.get('account.fiscal.utility')
        # Obtiene el codigo fiscal del que se va a obtener la utilidad del ejercicio fiscal
        #code_id = util_obj.get_config_code_id(cr, uid, context=context)
        config = util_obj.get_config_utility(cr, uid, context=context)
        
        # Valida que este registrado el codigo fiscal en la configuracion
        if config['code_id'] == False or config['result_code_id'] == False or config['balance_code_id'] == False:
            raise osv.except_osv('Error Validacion', u'Para continuar con la aplicacion, debe tener completa la configuracion de Perdida/Utilidad Fiscal. Revisar en configuracion de Codigos Fiscales ')
        
        # Obtiene la utilidad del ejercicio fiscal
        utility = util_obj.get_value_code(cr, uid, config['code_id'], fiscalyear_id, context=context)
        result = util_obj.get_value_code(cr, uid, config['result_code_id'], fiscalyear_id, context=context)
        balance = util_obj.get_value_code(cr, uid, config['balance_code_id'], fiscalyear_id, context=context)
        balance2 = util_obj.get_value_code(cr, uid, config['balance_code_id2'], fiscalyear_id, context=context)
        lost = 0.0
        #print "******** utilidad ejercicio ********* ", utility
        #print "******** total ejercicio ********* ", result
        # Obtiene cuanto se va a aplicar de remanente y el total a pagar
        if utility < 0.0:
            # Pone total a pagar en cero y el remanente
            total = 0.0
            remnant = 0.0
            lost = utility * -1
            utility = 0.0
            balance = 0.0
        else:
            if remnant_before >= utility:
                remnant = utility
                total = 0.0
            else:
                total = utility - remnant_before
                remnant = remnant_before
            balance2 = 0.0
        
        values = {
            'utility': utility,
            'utility2': utility,
            'lost': lost,
            'balance': balance,
            'balance2': balance2,
            'remnant': remnant,
            'total': result,
            'code_id': config['code_id'],
            'result_code_id': config['result_code_id'],
            'balance_code_id': config['balance_code_id'],
            'balance_code_id2': config['balance_code_id2']
        }
        return {'value': values}
    
    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        #print "************* get period **************"
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False
    
    def action_utility_validate(self, cr, uid, ids, context=None):
        """
            Valida la utilidad de los movimientos
        """
        util_obj = self.pool.get('account.fiscal.utility')
        line_obj = self.pool.get('account.fiscal.utility.line')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        util_id = False
        
        # Recorre los registros
        for valid in self.browse(cr, uid, ids, context=context):
            # Obtiene el año del ejercicio fiscal
            year = fiscalyear_obj.get_year(cr, uid, valid.fiscalyear_id.id, context=context)
            
            # Valida que este registrado el codigo fiscal en la configuracion
            hist_ids = self.pool.get('account.fiscal.code.history.line').search(cr, uid, [('code_id','=',valid.code_id.id),('fiscalyear_id','=',valid.fiscalyear_id.id)], context=context)
            #print "*********** historial ********* ", hist_ids, " code ", valid.code_id.id, " fy ", valid.fiscalyear_id.id
            if not hist_ids:
                raise osv.except_osv('Error Validacion', u'No se a guardado en el historial de codigos fiscales el Ejercicio %s. Para continuar calcular y guardar la utilidad fiscal del ejercicio en los codigos fiscales.'%(year,))
            
            # Valida que haya registros del año anterior en las perdidas fiscales
            cr.execute("""
            select u.fiscalyear, l.fiscalyear_amortized
            from account_fiscal_utility as u
            left join account_fiscal_utility_line as l on u.id=l.utility_id and l.fiscalyear_amortized= %s
            where u.state = 'open' and l.fiscalyear_amortized is null and u.utility < 0 """%(year-1,))
            years = []
            for value in cr.fetchall():
                years.append(str(value[0]))
            #print "*********** years ******** ", years
            # Si hay ejercicios pendientes por aplicar el año anterior, se debe actualizar
            if years:
                fy = year-1
                vals = ", ".join(years)
                raise osv.except_osv('Error Validacion', u'El año "%s" no esta actualizado en los ejercicios "%s". Debe actualizar los ejercicios para continuar'%(fy, vals,))
            
            # Busca que no se encuentre otro documento para el mismo ejercicio fiscal 
            util_ids = util_obj.search(cr, uid, [('state','in',['open','close']),('fiscalyear', '=', year)], context=context)
            # Valida si encontro documentos para ese ejercicio fiscal
            if util_ids:
                raise osv.except_osv('Error Validacion', 'El documento de Perdida Fiscal con el periodo %s ya fue cerrado.'%(year))
            
            # Actualiza la perdida fiscal en los ejercicios
            util_id = util_obj.update_utility(cr, uid, year, valid.fiscalyear_id.id, valid.close, context=context)
            
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_fiscal', 'view_account_fiscal_utility_form')
        
        return {
            'name':_("Perdida Fiscal"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.fiscal.utility',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : util_id, # id of the object to which to redirected
        }
    
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio Fiscal', select=True, required=True),
        'utility': fields.float('Utilidad', digits=(16,4), help="Utilidad o perdida registrada sobre el ejercicio fiscal"),
        'utility2': fields.float('Utilidad', digits=(16,4), readonly=True, help="Utilidad registrada sobre el ejercicio fiscal"),
        'lost': fields.float('Perdida', digits=(16,4), help="Perdida registrada sobre el ejercicio fiscal"),
        'balance': fields.float('Saldo', digits=(16,4), help="Saldo registrado sobre el ejercicio"),
        'balance2': fields.float('Saldo', digits=(16,4), help="Saldo registrado sobre el ejercicio por pagos provisionales"),
        'remnant_before': fields.float('Remanente Anterior', digits=(16,4), readonly=True, help="Remanente Disponible para utililzar"),
        'remnant': fields.float('Remanente Aplicado', digits=(16,4), readonly=True, help="Remanente utilizado sobre el ejercicio fiscal"),
        'total': fields.float('Total a Pagar en el Ejercicio fiscal', digits=(16,4), readonly=True, help="Total a pagar sobre el Ejercicio Fiscal"),
        'close': fields.boolean('Cerrar Ejercicio', help="Si pone como cerrado el ejercicio ya no podra reemplazar el resultado"),
        'code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal Utilidad'),
        'result_code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal Total a pagar'),
        'balance_code_id': fields.many2one('account.fiscal.code', 'Codigo Fiscal Saldo fiscal'),
        'balance_code_id2': fields.many2one('account.fiscal.code', 'Codigo Fiscal Saldo fiscal')
    }
    
    def _get_remnant_before(self, cr, uid, context=None):
        """
            Obtiene el remanente disponible
        """
        remnant = self.pool.get('account.fiscal.utility').get_remnant(cr, uid, context=context)
        return remnant
    
    def _get_fiscalyear_default(self, cr, uid, context=None):
        """
            Obtiene el ejercicio fiscal ya sea del año anterior
        """
        # Obtiene el periodo actual
        period_id = self._get_period(cr, uid, context=context)
        # Obtiene el Ejercicio fiscal del año anterior
        fiscalyear_id = 0
        cr.execute("""
            select
                    id
                from
                    account_fiscalyear
                where extract(year from date_start) = (select extract(year from (date_start - interval '1 year')) from account_period where id = %s)"""%(period_id))
        for value in cr.fetchall():
            fiscalyear_id = value[0]
            break
        return fiscalyear_id
    
    _defaults = {
        'fiscalyear_id': _get_fiscalyear_default,
        'remnant_before': _get_remnant_before,
        'utility': 0.0,
        'total': 0.0,
    }

account_fiscal_utility_validate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
