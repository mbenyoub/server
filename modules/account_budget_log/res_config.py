# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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
from openerp import pooler
from openerp.tools.translate import _

class account_budget_log_settings(osv.osv_memory):
    _name = 'account.budget.log.settings'
    #~ _inherit = 'res.config.settings'

    def execute(self, cr, uid, ids, context=None):

        config = self.browse(cr, uid, ids[0], context)
        print "************* configuracion id ************** ", ids
        print "************* configuracion ************** ", config
        print "************* configuracion diario ************** ", config.journal_budget_id

        budget = {
            'id': 1,
            'config_active': True,
            'journal_budget_id': config.journal_budget_id.id,
            'account_approve': config.account_approve.id,
            'account_modify': config.account_modify.id,
            'account_to_exercised': config.account_to_exercised.id,
            'account_committed': config.account_committed.id,
            'account_accrued': config.account_accrued.id,
            'account_exercised': config.account_exercised.id,
            'account_paid': config.account_paid.id,
        }
        print "************** budget ******************* ", budget

        budget_settings = self.browse(cr, uid, 1, context=context)

        args = [('config_active', '=' , True)]
        budget_ids = self.search(cr, uid, args, context=context)

        print "******************* ids ***************** ", ids
        print "******************* budget ids ***************** ", budget_ids
        print "******************* budget settings ***************** ", budget_settings.id
        if budget_ids:
            print "************ modificando configuracion **************** "
            self.write(cr, uid, budget_ids[0], budget)
            self.unlink(cr, uid, ids[0], budget)
        else:
            print "************ creando configuracion **************** "
            self.write(cr, uid, ids[0], budget)
            #~ self.create(cr, uid, budget)

        # force client-side reload (update user menu and current view)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    _columns = {
        'config_active': fields.boolean("Configuracion Activa"),
        'journal_budget_id': fields.many2one('account.journal', 'Diario', ondelete="set null"),
        'account_approve': fields.many2one('account.account', 'P.E. Aprobado', ondelete="set null"),
        'account_modify': fields.many2one('account.account', 'P.E. Modificado', ondelete="set null"),
        'account_to_exercised': fields.many2one('account.account', 'P.E. Por Ejercer', ondelete="set null"),
        'account_committed': fields.many2one('account.account', 'P.E. Comprometido', ondelete="set null"),
        'account_accrued': fields.many2one('account.account', 'P.E. Devengado', ondelete="set null"),
        'account_exercised': fields.many2one('account.account', 'P.E. Ejercido', ondelete="set null"),
        'account_paid': fields.many2one('account.account', 'P.E. Pagado', ondelete="set null"),
    }

    def _get_journal_budget(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default journal ************ ", budget_settings
                print "********** journal budget ************ ", budget_settings.journal_budget_id
                if not budget_settings.id:
                    return None
                return budget_settings.journal_budget_id.id
            else:
                return None
        except:
            return None

    def _get_account_approve(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default approve ************ ", budget_settings
                print "********** approve budget ************ ", budget_settings.journal_budget_id
                if not budget_settings.id:
                    return None
                return budget_settings.account_approve.id
            else:
                return None
        except:
            return None

    def _get_account_modify(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default modify ************ ", budget_settings
                if not budget_settings.id:
                    return None
                return budget_settings.account_modify.id
            else:
                return None
        except:
            return None

    def _get_account_to_exercised(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default to exercised ************ ", budget_settings
                if not budget_settings.id:
                    return None
                return budget_settings.account_to_exercised.id
            else:
                return None
        except:
            return None

    def _get_account_committed(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default committed ************ ", budget_settings
                if not budget_settings.id:
                    return None
                return budget_settings.account_committed.id
            else:
                return None
        except:
            return None

    def _get_account_accrued(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default accrued ************ ", budget_settings
                print "********** id ************ ", budget_settings.id
                print "********** accrued ************ ", budget_settings.account_accrued
                if not budget_settings.id:
                    return None
                return budget_settings.account_accrued.id
            else:
                return None
        except:
            return None

    def _get_account_exercised(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default exercised ************ ", budget_settings
                if not budget_settings.id:
                    return None
                return budget_settings.account_exercised.id
            else:
                return None
        except:
            return None

    def _get_account_paid(self, cr, uid, context=None):
        try:
            args = [('config_active', '=' , True)]
            ids = self.search(cr, uid, args, context=context)
            if ids:
                budget_settings = self.browse(cr, uid, ids[0], context=context)
                print "********** default paid ************ ", budget_settings
                if not budget_settings.id:
                    return None
                return budget_settings.account_paid.id
            else:
                return None
        except:
            return None

    _defaults = {
        'config_active': False,
        'journal_budget_id': _get_journal_budget,
        'account_approve': _get_account_approve,
        'account_modify': _get_account_modify,
        'account_to_exercised': _get_account_to_exercised,
        'account_committed': _get_account_committed,
        'account_accrued': _get_account_accrued,
        'account_exercised': _get_account_exercised,
        'account_paid': _get_account_paid,
    }

account_budget_log_settings()
