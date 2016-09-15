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
    
    _columns = {
        'id': fields.integer('ID'),
        'name': fields.char('Nombre'),
        'account_sat_id': fields.many2one('account.account.sat','Cuenta SAT', domain=[('type','!=','view')], select="1"),
        #'account_apply_ids': fields.one2many('account.sat.related.apply.wizard', 'wizard_id', 'Cuentas aplicadas'),
        'account_apply_ids': fields.many2many('account.account', 'account_sat_related_apply_wizard_rel', 'wizard_id', 'account_id', 'Cuentas aplicadas', domain=[('type','!=','view')]),
        'account_ids': fields.one2many('account.sat.related.account.wizard', 'wizard_id', 'Plan contable'),
        'filter': fields.char('Filtrar cuenta', size=164),
    }
    
    _defaults = {
        'name': 'Relacion Cuentas SAT'
    }
    
    def onchange_account_sat_id(self, cr, uid, ids, account_sat_id, filter, context=None):
        """
            Actualiza la informacion de los movimientos pendientes de relacionar
        """
        acc_obj = self.pool.get('account.account')
        acc_line_rel = []
        acc_line_ids = []
        
        if account_sat_id:
            # Genera filtros para obtener las cuentas
            filter_search = [('account_sat_id','=',False),('type','!=','view')]
            if filter:
                filter_search.append('|')
                filter_search.append(('name','ilike','%' + filter + '%'))
                filter_search.append(('code','ilike','%' + filter + '%'))
            
            # Busca las cuentas pendientes de conciliar
            account_ids = acc_obj.search(cr, uid, filter_search)
            if account_ids:
                # Recorre los movimientos y los agrega en la vista de banco
                for account_id in account_ids:
                    val = {
                        'account_id': account_id,
                    }
                    acc_line_ids.append(val)
            
            # Busca las cuentas conciliadas con la cuenta
            acc_line_rel = acc_obj.search(cr, uid, [('account_sat_id','=',account_sat_id),('type','!=','view')])
            
        # Actualiza los valores de retorno
        return {'value': {'account_ids': acc_line_ids, 'account_apply_ids': acc_line_rel}}
    
    def onchange_filter(self, cr, uid, ids, filter, account_sat_id, account_apply_ids, context=None):
        """
            Filtra la lista de cuentas que estan pendientes de aplicar
        """
        acc_obj = self.pool.get('account.account')
        acc_line_ids = []
        apply_ids = []
        
        # Valida que ya este seleccionada una cuenta sat y este guardado
        if account_sat_id:
            # Descarta las cuentas que estan ya sobre la lista 
            for acc in account_apply_ids:
                print "************* acc ******* ", acc
                if acc[0] == 6:
                    apply_ids = acc[2]
            
            # Genera filtros para obtener las cuentas
            filter_search = ['|',('account_sat_id','=',account_sat_id),('account_sat_id','=',False),('type','!=','view'),('id','not in', apply_ids)]
            if filter:
                filter_search.append('|')
                filter_search.append(('name','ilike','%' + filter + '%'))
                filter_search.append(('code','ilike','%' + filter + '%'))
            
            # Busca las cuentas pendientes de conciliar
            acc_ids = acc_obj.search(cr, uid, filter_search, context=context)
            for account_id in acc_ids:
                val = {
                    'account_id': account_id
                }
                acc_line_ids.append(val)
            
        # Actualiza los valores de retorno
        return {'value': {'account_ids': acc_line_ids}}
    
    def action_related_auto(self, cr, uid, ids, context=None):
        act_obj = self.pool.get('account.account') 
        acc_obj = self.pool.get('account.account.sat') 

        accounts = [
(1111001000,101.01),
(1111002000,101.01),
(1111003000,101.01),
(111302,102.01),
(1114001000,102.02),
(1115001000,103.01),
(1115002000,103.01),
(1115003000,103.01),
(1115004000,103.01),
(1122001000,105.01),
(1122004000,105.01),
(1122005000,105.01),
(1123001000,105.02),
(1124001000,106.01),
(1124002000,106.01),
(1125001000,107.01),
(1125002000,107.01),
(1125003000,107.02),
(1125004000,107.01),
(1125008000,107.01),
(1125009000,107.01),
(1128001000,107.02),
(1129008000,120.01),
(1131001000,115.01),
(1131002000,115.01),
(1131003000,115.01),
(1131009000,115.01),
(1134001000,115.05),
(1151004000,118.01),
(1151005000,119.01),
(1151006000,118.02),
(1151007000,113.08),
(1151008000,113.08),
(1152001000,114.01),
(1152005000,113.06),
(1152006000,113.04),
(1152007000,113.07),
(1152008000,113.08),
(1152009000,113.08),
(1153001000,113.01),
(1153002000,113.02),
(1153003000,113.03),
(1211001000,151.01),
(1211005000,152.01),
(1211007000,153.01),
(1211009000,154.01),
(1211011000,155.01),
(1211013000,156.01),
(1212005000,171.01),
(1212007000,171.02),
(1212009000,171.03),
(1212011000,171.04),
(1212013000,171.05),
(1221001000,103.03),
(1221003000,103.03),
(1221004000,103.03),
(1251001000,185.01),
(1271001000,182.01),
(1271002000,177.01),
(1272001,174.01),
(1272001001,174.01),
(1272001002,174.01),
(1272001003,174.01),
(1272001004,184.02),
(1272001099,183.01),
(1291001000,184.03),
(1291002000,184.03),
(1291004000,184.02),
(2111001000,202.01),
(2122001000,201.01),
(2131001000,206.01),
(214,205.02),
(2141,205.02),
(2151001000,202.11),
(2161005000,205.06),
(2161006000,210.04),
(2161007000,205.06),
(2161008000,216.11),
(2171001000,211.01),
(2171002000,211.02),
(2171003000,211.03),
(2173001000,205.06),
(2173002000,205.06),
(2173003000,205.06),
(2173004000,211.03),
(2175014000,212.01),
(2175017000,210.01),
(2175021000,205.06),
(2191001000,213.03),
(2191002000,213.03),
(2201112000,216.10),
(2201113000,216.01),
(2201114000,216.02),
(2201115000,216.04),
(2201116000,216.03),
(2201117000,216.10),
(2201118000,216.10),
(2201119000,213.01),
(2201121000,213.02),
(2202111000,208.01),
(2202119000,207.01),
(2202120000,216.03),
(2202121000,216.10),
(2202122000,216.04),
(2202123000,216.10),
(2511001000,252.01),
(2581001000,252.05),
(2591001000,252.17),
(3111001000,301.01),
(3131001000,301.02),
(3211001000,304.01),
(3211002000,304.01),
(3311001000,303.01),
(3311002000,301.03),
(3391001000,306.01),
(3391002000,306.01),
(3911002000,304.01),
(3911003000,304.02),
(5111001000,401.01),
(5111002000,401.01),
(5111003000,401.12),
(5112001000,401.01),
(5114001000,402.01),
(6111001000,501.01),
(7111001000,602.72),
(7111002000,602.61),
(7111003000,602.61),
(7111004000,602.61),
(7111005000,602.61),
(7111006000,602.61),
(7111007000,602.61),
(7111008000,602.84),
(7111009000,602.84),
(7111010000,602.72),
(7111011000,602.76),
(7131001000,601.01),
(7131002000,601.01),
(7131003000,601.03),
(7131004000,601.05),
(7131005000,601.02),
(7131006000,601.16),
(7131007000,601.10),
(7131008000,601.10),
(7131009000,601.10),
(7131010000,601.10),
(7131011000,601.10),
(7131012000,601.10),
(7131013000,601.10),
(7131014000,601.26),
(7131015000,601.28),
(7131016000,601.27),
(7131017000,601.23),
(7131019000,601.06),
(7131020000,601.08),
(7131021000,601.29),
(7131025000,601.22),
(7131030000,601.49),
(7131031000,601.31),
(7131033000,601.22),
(7131035000,601.22),
(7131036000,601.22),
(7131037000,601.31),
(7151001000,601.56),
(7151002000,601.56),
(7151003000,601.56),
(7151004000,601.56),
(7151005000,601.56),
(7151006000,601.53),
(7151007000,601.38),
(7151009000,601.84),
(7151010000,601.52),
(7151012000,601.50),
(7151013000,601.51),
(7151014000,601.54),
(7151015000,601.55),
(7151016000,601.54),
(7151017000,601.49),
(7151018000,601.49),
(7151019000,601.49),
(7151021000,601.84),
(7151022000,601.50),
(7151023000,601.84),
(7151024000,601.61),
(7151025000,601.84),
(7151026000,601.46),
(7151027000,601.58),
(7151028000,601.84),
(7151029000,601.84),
(7151030000,601.84),
(7151031000,601.84),
(7151032000,601.72),
(7151033000,601.84),
(7151035000,601.39),
(7151036000,601.64),
(7151039000,601.49),
(7151040000,601.48),
(7151041000,601.84),
(7151043000,601.57),
(7151044000,601.83),
(7151045000,601.38),
(7151046000,601.84),
(7151047000,601.61),
(7151048000,601.58),
(7151060000,601.62),
(7151070000,601.60),
(7151080000,601.46),
(7161002000,613.01),
(7161003000,613.02),
(7161004000,613.03),
(7161005000,613.04),
(7161006000,613.05),
(7161008000,613.05),
(7162001000,614.01),
(7162002000,614.02),
(7162003000,614.10),
(7171001000,611.01),
(7171002000,607.01),
(9111001000,701.04),
(9111002000,701.10),
(9111003000,701.10),
(9111004000,701.08),
(9113002000,701.11),
(9113003000,703.03),
(9113006000,701.01),
(9113008000,601.84),
(9113010000,601.84),
(9113012000,701.01),
(9113013000,703.03),
(9113014000,703.03),
(9113099000,601.59),
(9211001000,702.04),
(9211002000,702.05),
(9211003000,702.10),
(9212001000,704.03),
(9212002000,704.03),
(9212003000,702.01),
(9212004000,702.10),
(9212005000,702.10),
(9212006000,702.10),
(9212007000,702.10),
(9212008000,702.10)]
        
################ Bancos Nacional #################
        
        for cuentas in accounts:
            act_ids = act_obj.search(cr, uid,[('active','=',True)])#cuentas[0])])
            acc_ids = acc_obj.search(cr, uid,[('code','=',cuentas[1])])
            for sat in acc_obj.browse(cr, uid, acc_ids): 
                for act in act_obj.browse(cr, uid, act_ids):
                    if str(cuentas[0]) in act.code:
                        cr.execute("""update account_account set account_sat_id = %s where id = %s""" % (sat.id, act.id))
                        cr.commit()

        # for account in accounts:
        #     act_ids = act_obj.search(cr, uid,[('code','=',account[0])])
        #     acc_ids = acc_obj.search(cr, uid,[('code','=',account[1])])

        #     if len(act_ids) > 0 and len(acc_ids) > 0:
        #         for act_act in act_obj.browse(cr, uid, act_ids):
        #             act = act_act.id
        #         for acc_sat in acc_obj.browse(cr, uid, acc_ids):
        #             acc = acc_sat.id
        #         cr.execute("""update account_account set account_sat_id = %s where id = %s""" % (acc, act))
        #         cr.commit()
                #cuenta = act_obj.write(cr, uid, [act], {'account_sat_id':acc})
            #else:
            #       raise osv.except_osv(account[0], account[1])

            #cr.execute("""update account_account set account_sat_id = %s where id = %s""" % (acc, act))
            #cr.commit()

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
            for account in wizard.account_apply_ids:
                # Actualiza la lista de cuentas a relacionar
                acc_ids.append(account.id)
            
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
            'target': 'inline',
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
            'target': 'inline',
            'domain': '[]',
            'context': context,
            #'res_id' : res_id, # id of the object to which to redirected
        }
    
    def action_remove(self, cr, uid, ids, context=None):
        """
            Quita la relacion de las cuentas relacionadas a la cuenta sat
        """
        if context is None:
            context = {}
        
        self.write(cr, uid, ids, {'account_apply_ids': [[6, False, []]]}, context=context)
        return True

    def action_apply(self, cr, uid, ids, context=None):
        """
            Actualiza el valor del monto aplicado sobre las lineas seleccionadas
        """
        if context is None:
            context = {}
        line_ids = []

        # Recorre las lineas de las cuentas a aplicar
        for wizard in self.browse(cr, uid, ids, context=context):
            # Agrega al arreglo los ids a aplicar a la cuenta sat
            for line in wizard.account_ids:
                if line.account_id:
                    line_ids.append(line.account_id.id)
            # Agrega al arrelog los ids ya aplycados
            for line in wizard.account_apply_ids:
                line_ids.append(line.id)
        
        print "************ line_ids ******* ", line_ids
        
        self.write(cr, uid, ids, {'account_apply_ids': [[6, False, line_ids]], 'account_ids': [[6, False, []]]}, context=context)
        return False

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
        
        self.write(cr, uid, ids, {}, context=context)
        return True

account_sat_related_wizard()

class account_sat_related_account_wizard(osv.osv_memory):
    """ Cuentas no relacionadas con las cuentas sat """
    _name = 'account.sat.related.account.wizard'
    
    _columns = {
        'wizard_id': fields.many2one('account.sat.related.wizard', 'Wizard conciliacion', ondelete="cascade"),
        'account_id' : fields.many2one('account.account', 'Cuenta', domain=[('type','!=','view')], select="1"),
    }

account_sat_related_account_wizard()

#class account_sat_related_apply_wizard(osv.osv_memory):
#    """ Relacion cuentas sobre cuenta sat """
#    _name = 'account.sat.related.apply.wizard'
#    
#    def action_break_apply(self, cr, uid, ids, context=None):
#        """
#            Elimina la relacion de la cuenta seleccionada con la cuenta SAT
#        """
#        if context is None:
#            context = {}
#        line_obj = self.pool.get('account.sat.related.account.wizard')
#        
#        # Recorre los registros a apilcar
#        for line_rel in self.browse(cr, uid, ids, context=context):
#            wizard_id = line_rel.wizard_id.id
#            # Obtiene la cuenta sat y agrega la referencia sobre el context
#            if not context.get('default_account_sat_id',False):
#                # Informacion de retorno para recargar el wizard
#                context.update({
#                    'default_account_sat_id': line_rel.wizard_id.account_sat_id.id or False
#                })
#
#            # Crea el nuevo registro sobre la otra linea
#            line_obj.create(cr, uid, {
#                'wizard_id': wizard_id,
#                'account_id': line_rel.account_id.id
#            }, context=context)
#        
#        # Elimina el registro actual
#        self.unlink(cr, uid, ids, context=context)
#        
#        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_sat', 'account_sat_related_wizard_form_view')
#        return {
#            'name':_("Relacionar Cuentas SAT"),
#            'view_mode': 'form',
#            'view_id': view_id,
#            'view_type': 'form',
#            'res_model': 'account.sat.related.wizard',
#            'type': 'ir.actions.act_window',
#            'nodestroy': True,
#            'target': 'inline',
#            'domain': '[]',
#            'context': context,
#            'res_id' : wizard_id, # id of the object to which to redirected
#        }
#    
#    _columns = {
#        'wizard_id': fields.many2one('account.sat.related.wizard', 'Wizard conciliacion', ondelete="cascade"),
#        'account_id' : fields.many2one('account.account', 'Cuenta', domain=[('type','!=','view')], select="1"),
#    }
#
#account_sat_related_apply_wizard()
