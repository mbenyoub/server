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
from openerp.osv import fields, osv
from openerp import pooler

import openerp.sql_db as sql_db
from openerp.tools.translate import _
from openerp.service.web_services import db as ws

# ---------------------------------------------------------
# Creacion de Bancos en el sistema
# ---------------------------------------------------------

class create_acount_bank_wizard(osv.osv_memory):
    """
        Actualiza la informaicon de las cuentas bancarias
    """
    _name = "create.account.bank.wizard"
    
    _columns = {
        'name': fields.char('Nombre de la cuenta'),
        'code': fields.char('Codigo', help="Prefijo con el que se va a identificar la secuencia de la cuenta al momento de crear polizas"),
        'number': fields.char('Numero de cuenta'),
        'clabe': fields.char('Cuenta CLABE')
    }
    
    def create_account_bank(self, cr, uid, info, context=None):
        """
            Crea la cuenta bancaria para el cliente
        """
        # Inicializa variables
        data_obj = self.pool.get('ir.model.data')
        journal_obj = self.pool.get('account.journal')
        account_obj = self.pool.get('account.account')
        bank_obj = self.pool.get('res.partner.bank')
        user_obj = self.pool.get('res.users')
        num = 1
        
        # Obtiene la cuenta padre de Bancos
        cr.execute(
            """ select id, code, name, parent_id
                from account_account
                where type = 'liquidity' and code like '1113%'
                order by code desc limit 1
            """)
        dat = cr.dictfetchall()
        
        code = dat and dat[0]['code'] or False
        parent_id = dat and dat[0]['parent_id'] or False
        
        # Genera el nuevo codigo a partir del ultimo codigo registrado
        new_code = str(int(code) + 1)
        
        # Obtiene el id de la compañia
        company = user_obj.browse(cr, uid, uid, context=context).company_id
        company_id = company.id
        
        # Valida que la cuenta no exista y si existe pone el siguiente
        for n in xrange(num, 100):
            acc_ids = account_obj.search(cr, uid, [('code','=', new_code),('company_id','=',company_id)])
            if not acc_ids:
                break
            new_code = str(int(new_code) + 1)
        
        # Crea la cuenta bancaria
        tmp = data_obj.get_object_reference(cr, uid, 'account', 'data_account_type_bank')
        bank_type = tmp and tmp[1] or False
        account_id = account_obj.create(cr, uid, {
                'name': info['name'],
                'currency_id': False,
                'code': new_code,
                'type': 'liquidity',
                'user_type': bank_type,
                'parent_id': parent_id or False,
                'company_id': company_id,
        })
        
        # Obtiene el numero siguiente para el codigo del diario
        cr.execute(
            """ select count(type) + 1 as num
                from account_journal
                where type in ('bank','cash')
            """)
        dat = cr.dictfetchall()
        current_num = dat and dat[0]['num'] or 1
        journal_code = 'BNK'
        
        # Valida si tiene un codigo de diario sino le pone uno predefinido
        if info.get('code',False):
            journal_code = info.get('code')
        # Valida si el codigo se esta usando por otro diario
        journal_ids = journal_obj.search(cr, uid, [('code', '=', code), ('company_id', '=', company_id)], context=context)
        # Valida que si se encontro el registro repetido le agregue 
        if journal_ids:
            # Verifica que no se este usando el numero sobre el diario y si se esta usando lo cambia por el siguiente
            for num in xrange(current_num, 100):
                # journal_code has a maximal size of 5, hence we can enforce the boundary num < 100
                code = journal_code + str(num)
                journal_ids = journal_obj.search(cr, uid, [('code', '=', code), ('company_id', '=', company_id)], context=context)
                # Valida que si se encontro el registro repetido le agregue 
                if not journal_ids:
                    journal_code = code
                    break
        
        # Crea el diario sobre el banco
        journal_id = journal_obj.create(cr, uid, {
                'name': info['name'],
                'code': journal_code,
                'type': 'bank',
                'company_id': company_id,
                'analytic_journal_id': False,
                'currency': False,
                'default_credit_account_id': account_id,
                'default_debit_account_id': account_id,
                'account_transit': account_id,
        })
        
        # Agrega la cuenta bancaria a la compañia
        bank_id = bank_obj.create(cr, uid, {
            'state': 'bank',
            'acc_number': info['number'],
            'bank_name': info['name'],
            'clabe': info['clabe'],
            'partner_id': company.partner_id.id or False,
            'journal_id': journal_id,
            'footer': True,
            'company_id': company_id
        })
        
        return bank_id
    
    def action_create_bank(self, cr, uid, ids, context=None):
        """
            Registra una nueva cuenta bancaria sobre la base de datos
        """
        bank_id = False
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Obtiene los datos de la cuenta a generar
            info_bank = {
                    'name': data.name,
                    'code': data.code,
                    'number': data.number,
                    'clabe': data.clabe
                }
            
            # Crea la nueva cuenta
            bank_id = self.create_account_bank(cr, uid, info_bank, context=context)
            
        # Redirecciona a la cuenta bancaria creada
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base', 'view_partner_bank_form')

        return {
            'name':_("Cuentas bancarias"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'res.partner.bank',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context,
            'res_id' : bank_id, # id of the object to which to redirected
        }
    
    
create_acount_bank_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
