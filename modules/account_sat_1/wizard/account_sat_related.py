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

class account_sat_related_wizard(osv.osv_memory):
    """ Relacion plan de cuentas SAT con el plan de cuentas """
    _name = 'account.sat.related.wizard'
    _description = 'Relacionar cuentas SAT'
    
    def onchange_account_sat_id(self, cr, uid, ids, account_sat_id, store, context=None):
        """
            Actualiza la informacion de los movimientos pendientes de relacionar
        """
        acc_obj = self.pool.get('account.account')
        acc_line_rel = []
        acc_line_ids = []
        
        if account_sat_id and store == True:
            # Busca las cuentas pendientes de conciliar
            acc_ids = acc_obj.search(cr, uid, [('account_sat_id','=',False),('type','!=','view')])
            for account_id in acc_ids:
                val = {
                    'account_id': account_id
                }
                acc_line_ids.append(val)
            
            # Busca las cuentas conciliadas con la cuenta
            account_ids = acc_obj.search(cr, uid, [('account_sat_id','=',account_sat_id),('type','!=','view')])
            if account_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for account_id in account_ids:
                    val = {
                        'account_id': account_id,
                    }
                    acc_line_rel.append(val)
                    
        # Actualiza los valores de retorno
        return {'value': {'account_ids': acc_line_ids, 'account_apply_ids': acc_line_rel}}
    
    def action_related_account(self, cr, uid, ids, context=None):
        """
            Hace la aplicacion sobre las cuentas relacionadas
        """
        # Recorre los registros a validar
        for wizard in self.browse(cr, uid, ids, context=context):
            acc_ids = []
            
            # Si no hay una cuenta sat no aplica la relacion
            if not wizard.account_sat_id:
                continue
            
            # Obtiene el total a cargar en las transacciones
            for line in wizard.account_apply_ids:
                # Valida que tenga una cuenta
                if not line.account_id:
                    continue
                
                # Actualiza la lista de cuentas a relacionar
                acc_ids.append(line.account_id.id)
                
            # Actualiza la informacion de las cuentas sobre la cuenta SAT
            self.pool.get('account.account.sat').write(cr, uid, [wizard.account_sat_id.id], {'account_ids': [[6, False, acc_ids]]}, context=context)
        
        # Elimina registros anteriores
        reg_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, reg_ids, context=context)
        
        # Actualiza variable de retorno
        context.update({
            'default_account_sat_id': False
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_sat', 'account_sat_related_wizard_form_view')
        return {
            'name':_("Relacionar Cuentas SAT"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.sat.related.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            #'res_id' : res_id, # id of the object to which to redirected
        }
    
    def action_related_cancel(self, cr, uid, ids, context=None):
        """
            Hace la cancelacion de la relacion de cuentas
        """
        
        # Elimina registros anteriores
        reg_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, reg_ids, context=context)
        
        # Actualiza variable de retorno
        context.update({
            'default_account_sat_id': False
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_sat', 'account_sat_related_wizard_form_view')
        return {
            'name':_("Relacionar Cuentas SAT"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.sat.related.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            #'res_id' : res_id, # id of the object to which to redirected
        }
    
    def button_dummy(self, cr, uid, ids, context=None):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        acc_obj = self.pool.get('account.account')
        line_obj = self.pool.get('account.sat.related.account.wizard')
        line_rel_obj = self.pool.get('account.sat.related.apply.wizard')
        acc_line_rel = []
        acc_line_ids = []
        
        # Obtiene la cuenta sat
        wizard = self.browse(cr, uid, ids[0], context=context)
        account_sat_id = wizard.account_sat_id.id or False
        wizard_id = wizard.id
        
        # Elimina las lineas relacionadas
        line_ids = line_obj.search(cr, uid, [('wizard_id','=',wizard_id)])
        line_obj.unlink(cr, uid, line_ids, context=context)
        line_rel_ids = line_obj.search(cr, uid, [('wizard_id','=',wizard_id)])
        line_rel_obj.unlink(cr, uid, line_rel_ids, context=context)
        
        # Busca las cuentas pendientes de conciliar
        acc_ids = acc_obj.search(cr, uid, [('account_sat_id','=',False),('type','!=','view')])
        for account_id in acc_ids:
            val = {
                'wizard_id': wizard_id,
                'account_id': account_id
            }
            line_obj.create(cr, uid, val, context=context)
            #acc_line_ids.append(val)
        
        if account_sat_id:
            # Busca las cuentas conciliadas con la cuenta
            account_ids = acc_obj.search(cr, uid, [('account_sat_id','=',account_sat_id),('type','!=','view')])
            if account_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for account_id in account_ids:
                    val = {
                        'wizard_id': wizard_id,
                        'account_id': account_id,
                    }
                    line_rel_obj.create(cr, uid, val, context=context)
                    #acc_line_rel.append(val)
                    
        # Actualiza la informacion del wizard
        vals = {
            'store': True
        }
        self.write(cr, uid, ids, vals, context=context)
        return True
    
    _columns = {
        'name': fields.char('Nombre'),
        'account_sat_id': fields.many2one('account.account.sat','Cuenta SAT', domain=[('type','!=','view')], select="1", required=True),
        'account_apply_ids': fields.one2many('account.sat.related.apply.wizard', 'wizard_id', 'Cuentas aplicadas'),
        'account_ids': fields.one2many('account.sat.related.account.wizard', 'wizard_id', 'Plan contable'),
        'store': fields.boolean('Guardado')
    }
    
    _defaults = {
        'name': 'Relacion Cuentas SAT',
        'store': False
    }

account_sat_related_wizard()

class account_sat_related_apply_wizard(osv.osv_memory):
    """ Relacion cuentas sobre cuenta sat """
    _name = 'account.sat.related.apply.wizard'
    
    def action_break_apply(self, cr, uid, ids, context=None):
        """
            Elimina la relacion de la cuenta seleccionada con la cuenta SAT
        """
        if context is None:
            context = {}
        line_obj = self.pool.get('account.sat.related.account.wizard')
        
        # Recorre los registros a apilcar
        line_rel = self.browse(cr, uid, ids[0], context=context)
        wizard_id = line_rel.wizard_id.id
        # Crea el nuevo registro sobre la otra linea
        line_obj.create(cr, uid, {
            'wizard_id': wizard_id,
            'account_id': line_rel.account_id.id
        }, context=context)
        
        # Elimina el registro actual
        self.unlink(cr, uid, ids, context=context)
        
        #print "************** wizard id ************* ", wizard_id
        #return self.pool.get('account.sat.related.wizard').write(cr, uid, [wizard_id], {}, context=context)
        # Informacion de retorno para recargar el wizard
        context.update({
            'default_account_sat_id': line_rel.wizard_id.account_sat_id.id or False
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_sat', 'account_sat_related_wizard_form_view')
        return {
            'name':_("Relacionar Cuentas SAT"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.sat.related.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : wizard_id, # id of the object to which to redirected
        }
    
    _columns = {
        'wizard_id': fields.many2one('account.sat.related.wizard', 'Wizard conciliacion', ondelete="cascade"),
        'account_id' : fields.many2one('account.account', 'Cuenta', domain=[('type','!=','view')], select="1"),
    }

account_sat_related_apply_wizard()

class account_sat_related_account_wizard(osv.osv_memory):
    """ Cuentas no relacionadas con las cuentas sat """
    _name = 'account.sat.related.account.wizard'
    
    def action_apply(self, cr, uid, ids, context=None):
        """
            Relaciona la cuenta seleccionada con la cuenta SAT
        """
        if context is None:
            context = {}
        line_rel_obj = self.pool.get('account.sat.related.apply.wizard')
        
        # Recorre los registros a apilcar
        line = self.browse(cr, uid, ids[0], context=context)
        wizard_id = line.wizard_id.id
        # Crea el nuevo registro sobre la otra linea
        line_rel_obj.create(cr, uid, {
            'wizard_id': wizard_id,
            'account_id': line.account_id.id
        }, context=context)
        
        # Elimina el registro actual
        self.unlink(cr, uid, ids, context=context)
        
        #print "************** wizard id ************* ", wizard_id
        #return self.pool.get('account.sat.related.wizard').write(cr, uid, [wizard_id], {}, context=context)
        # Informacion de retorno para recargar el wizard
        context.update({
            'default_account_sat_id': line.wizard_id.account_sat_id.id or False
        })
        
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_sat', 'account_sat_related_wizard_form_view')
        return {
            'name':_("Relacionar Cuentas SAT"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.sat.related.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : wizard_id, # id of the object to which to redirected
        }
    
    _columns = {
        'wizard_id': fields.many2one('account.sat.related.wizard', 'Wizard conciliacion', ondelete="cascade"),
        'account_id' : fields.many2one('account.account', 'Cuenta', domain=[('type','!=','view')], select="1"),
    }

account_sat_related_account_wizard()

