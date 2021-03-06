# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _


class invite_wizard(osv.osv_memory):
    """ Wizard to invite partners and make them followers. """
    _inherit = 'mail.wizard.invite'
    _description = 'Invite wizard'

    def default_get(self, cr, uid, fields, context=None):
        '''
        Overwrite the original model to add model for the context in the at
        time use and add in the message all documents to follow
        '''

        result = super(invite_wizard, self).default_get(
            cr, uid, fields, context=context)
        model_obj = self.pool.get(result.get('res_model', False) or
                                  context.get('active_model'))

        if len(context.get('active_ids', [])) > 1:
            result.update({'res_model': context.get('active_model')})
            message = _('<div>You have been invited to follow are '
                        'documents: </div>')
            for ids in context.get('active_ids', []):
                document_name = model_obj.name_get(cr, uid, [ids],
                                                   context=context)[0][1]
                message = message + '\n<div>' + document_name + '</div>'

            result['message'] = message
        elif 'message' in fields and result.get('res_model') and \
                result.get('res_id'):
            document_name = self.pool.get(result.get('res_model')).name_get(
                cr, uid, [result.get('res_id')], context=context)[0][1]
            message = _(
                '<div>You have been invited to follow %s.</div>' %
                document_name)
            result['message'] = message

        return result

    _columns = {

        'groups': fields.boolean('Groups', help='Used to add a followers '
                                 'group from mail group '
                                 'and not for Users '
                                 'directly'),
        'partners': fields.boolean('Partners', help='Used to add a follower '
                                                    'group by users'),
        'remove': fields.boolean('Remove Partners', help='Used to remove followers'),
        'p_a_g': fields.boolean('Group and Partner', help='Used to add a '
                                'followers for partner '
                                'and group at the same '
                                'time'),


        'mail_groups': fields.many2many('mail.group', string='Mail Groups',
                                        help='Select the mail.groups that you '
                                        'want add with followers'),

    }

    def add_followers(self, cr, uid, ids, context=None):
        '''
        Overwrite the original model work with many documents at the same time
        and add followers in eech.

        Each id is get by context field
        '''
        res = {'type': 'ir.actions.act_window_close'}
        for wizard in self.browse(cr, uid, ids, context=context):
            if context.get('second', False):
                for res_id in context.get('active_ids', []):
                    model_obj = self.pool.get(wizard.res_model)
                    document = model_obj.browse(cr, uid, res_id,
                                                context=context)
                    new_follower_ids = [p.id for p in wizard.partner_ids
                                        if p.id not in
                                        document.message_follower_ids]

                    # filter partner_ids to get the new followers, to avoid
                    # sending email to already following partners
                    model_obj.message_subscribe(cr, uid, [res_id],
                                                new_follower_ids,
                                                context=context)

                    # send an email only if a personal message exists
                    # when deleting the message, cleditor keeps a <br>
                    # add signature
                    if wizard.message and not wizard.message == '<br>':
                        user_id = self.pool.get("res.users").\
                            read(cr, uid, [uid],
                                 fields=["signature"],
                                 context=context)[0]

                        signature = user_id and user_id["signature"] or ''
                        if signature:
                            wizard.message = \
                                tools.append_content_to_html(wizard.message,
                                                             signature,
                                                             plaintext=True,
                                                             container_tag=
                                                             'div')
                        # FIXME 8.0: use notification_email_send, send a wall
                        # message and let mail handle email notification +
                        # message box
                        for follower_id in new_follower_ids:
                            mail_mail = self.pool.get('mail.mail')
                            # the invite wizard should create a private message
                            # not related to any object -> no model, no res_id
                            mail_id = mail_mail.create(cr, uid, {
                                'model': wizard.res_model,
                                'res_id': res_id,
                                'subject': 'Invitation to follow %s' %
                                                       document.name_get()[
                                                       0][1],
                                'body_html': '%s' % wizard.message,
                                'auto_delete': True,
                                                       }, context=context)
                            mail_mail.send(cr, uid, [mail_id],
                                           recipient_ids=[follower_id],
                                           context=context)
            else:
                res = super(invite_wizard, self).add_followers(cr, uid, ids,
                                                               context=context)

        return res

    def remove_followers(self, cr, uid, ids, context=None):
        '''
        Overwrite the original model work with many documents at the same time
        and add followers in eech.

        Each id is get by context field
        '''
        res = {'type': 'ir.actions.act_window_close'}
        for wizard in self.browse(cr, uid, ids, context=context):
            for res_id in context.get('active_ids', []):
                model_obj = self.pool.get(wizard.res_model)
                document = model_obj.browse(cr, uid, res_id,
                                            context=context)
                new_follower_ids = [p.id for p in wizard.partner_ids]
                follower_ids = [i.id for i in  document.message_follower_ids]
                remove_ids = list(set(follower_ids) -  set(new_follower_ids))
                document.write({'message_follower_ids':[(6, 0, remove_ids)]})
                    
        return res

    def load_partners(self, cr, uid, ids, mail_groups, check, check2,
                      context=None):
        ''' Used to add all partnes in mail.group selected in the view and
            return it
        '''
        if context is None:
            context = {}
        res = {'value': {}}
        mail_obj = self.pool.get('mail.group')
        partner_ids = []

        if check or check2:
            for group in mail_groups:
                group_ids = group and len(group) == 3 and group[2] or []
                for groups in mail_obj.read(cr, uid,
                                            group_ids,
                                            ['message_follower_ids'],
                                            context):
                    partner_ids += groups.get('message_follower_ids', [])

        partner_ids and res['value'].update({'partner_ids': partner_ids})
        return res
