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
# Actualizacion de Impuestos
# ---------------------------------------------------------

class admon_update_journal_data(osv.osv_memory):
    """
        Actualiza la informaicon de las categorias de productos a travez de otra base de datos
    """
    _name = "admon.update.journal.data.wizard"

    def _get_method_db_selection(self, cr, uid, context=None):
        # From module of PAC inherit this function and add new methods
        db_list = []
        result = []
        db = ws()
        res = []
        # Obtiene la lista de 
        db_list = db.exp_list()
        for db in db_list:
            res.append((db,' %s '%(db,)))
        result.extend(
            res
        )
        return result

    _columns = {
        'name': fields.char('Nombre', size=32),
        # Gestiona bases de datos activas sobre el servidor
        'db_list': fields.selection(_get_method_db_selection, "Base de Datos origen", required=True),
        # Configuracion timbrado
        'database_id': fields.many2one('admon.database', 'Base de Datos destino', select=True, ondelete='cascade', required=True),
    }
    
    def update_info_sequence(self, cr1, cr2, sequence_origin_id, sequence_dest_id, context=None):
        """
            Actualiza la informacion de los diarios de la base de datos
        """
        # Inicializa variables
        sequence_obj = self.pool.get('ir.sequence')
        approval_obj = self.pool.get('ir.sequence.approval')
        account_obj = self.pool.get('account.account')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Valida que haya una secuencia de destino a modificar
            if sequence_dest_id:
                # Obtiene la informacion del diario de destino
                seq = sequence_obj.browse(cr1, uid, sequence_origin_id, context=context)
                # Arreglo para actualizacion de datos sobre los impuestos
                vals = {
                    'name': seq.name,
                    'code': seq.code,
                    'active': seq.active,
                    'prefix': seq.prefix,
                    'suffix': seq.suffix,
                    'padding': seq.padding,
                    'number_increment': seq.number_increment,
                    'implementation': seq.implementation,
                }
                
                # Busca las aprovaciones del sat
                if seq.approval_ids:
                    app_list = []
                    for approval in seq.approval_ids:
                        # Crea el nuevo registro
                        val_app = {
                            'type': approval.type,
                            'approval_number': approval.approval_number,
                            'serie': approval.serie,
                            'approval_year': approval.approval_year,
                            'number_start': approval.number_start,
                            'number_end': approval.number_end
                        }
                        approval_id = approval_obj.create(cr2, uid, val_app, context=context)
                        # Agrega el id del registro
                        app_list.append(approval_ids)
                    vals['approval_ids'] = [[6, 0, app_list]]
                
                # Actualiza el registro
                sequence_obj.write(cr2, uid, sequence_dest_id, vals, context=context)
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def update_info_journal(self, db_origin, db_destiny, context=None):
        """
            Actualiza la informacion de los diarios de la base de datos
        """
        # Inicializa variables
        journal_obj = self.pool.get('account.journal')
        sequence_obj = self.pool.get('ir.sequence')
        account_obj = self.pool.get('account.account')
        db_obj = self.pool.get('admon.database')
        context = {}
        uid = 1
        
        # Crea la conexion a la base de datos origen
        cr1 = db_obj.conect_to_db(db_origin)
        # Crea la conexion a la base de datos destino
        cr2 = db_obj.conect_to_db(db_destiny)
        
        try:
            # Recorre los registros de los diarios de la base origen y descarta los que sean de tipo efectivo y banco
            journal_ids = journal_obj.search(cr1, uid, [('type','not in',['bank'])], context=context)
            for journal in journal_obj.browse(cr1, uid, journal_ids, context=context):
                # Arreglo para actualizacion de datos sobre los impuestos
                vals = {
                    'name': journal.name,
                    'code': journal.code,
                    'type': journal.type,
                    'user_id': uid,
                    'centralisation': journal.centralisation,
                    'entry_posted': journal.entry_posted,
                    'allow_check_writing': journal.allow_check_writing,
                    'use_preprint_check': journal.use_preprint_check,
                    'update_posted': journal.update_posted,
                    'allow_date': journal.allow_date,
                    'group_invoice_lines': journal.group_invoice_lines,
                    'with_last_closing_balance': journal.with_last_closing_balance,
                    'balance_bank': journal.balance_bank,
                }
                
                # Busca la cuenta de ganancias
                if journal.profit_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.profit_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['profit_account_id'] = account_ids[0]
                
                # Busca la cuenta de perdidas
                if journal.loss_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.loss_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['loss_account_id'] = account_ids[0]
                
                # Busca la cuenta de perdidas
                if journal.internal_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.internal_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['internal_account_id'] = account_ids[0]
                
                # Busca la cuenta deudora por defecto
                if journal.default_debit_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.default_debit_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['default_debit_account_id'] = account_ids[0]
                
                # Busca la cuenta acreedora por defecto
                if journal.default_credit_account_id:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.default_credit_account_id.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['default_credit_account_id'] = account_ids[0]
                
                # Busca la cuenta de transferenciass
                if journal.account_transit:
                    account_ids = account_obj.search(cr2, uid, [('code', '=', journal.account_transit.code)])
                    if account_ids:
                        # Agrega el id del registro
                        vals['account_transit'] = account_ids[0]
                
                sequence_dest_id = False
                
                # Valida si ya registrado en la base de destino
                journal_ids = journal_obj.search(cr2, uid, [('code','=',journal.code)])
                # Actualiza el registro
                if journal_ids:
                    journal_obj.write(cr2, uid, journal_ids, vals, context=context)
                    
                    journal_dest = journal_obj.browse(cr2, uid, journal_ids[0])
                    sequence_dest_id = journal_dest.sequence_id.id or False
                    
                # Crea el nuevo registro
                else:
                    journal_id = journal_obj.create(cr2, uid, vals, context=context)
                    
                    journal_dest = journal_obj.browse(cr2, uid, journal_id)
                    sequence_dest_id = journal_dest.sequence_id.id or False
                    
                self.update_info_sequence(cr1, cr2, journal.sequence_id.id, journal_dest_id, context=context)
            
        finally:
            cr1.close()
            cr2.close()
        return True
    
    def action_update_data(self, cr, uid, ids, context=None):
        """
            Actualiza la informacion de impuestos
        """
        # Recorre los registros
        for data in self.browse(cr, uid, ids, context=context):
            # Obtiene la base de datos origen
            db_origin = data.db_list
            # Obtiene la base de datos destino
            db_dest = data.database_id.code or False
            
            # Actualiza la informacion de la base
            self.update_info_journal_category(db_origin, db_dest, context=context)
            self.update_info_journal_code(db_origin, db_dest, context=context)
            self.update_info_journal(db_origin, db_dest, context=context)
        # Muestra un mensaje indicando la actualizacion del registro
        return self.pool.get('warning').info(cr, uid, title='Proceso Completo!', message=_("Se completo la actualizacion de los registros de la base origen %s a la base destino %s")%(db_origin,db_dest))
    
admon_update_journal_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
