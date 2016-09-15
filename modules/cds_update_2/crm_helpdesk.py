# -*- coding: utf-8 -*-
##############################################################################

from openerp.addons.base_status.base_state import base_state
from openerp.addons.base_status.base_stage import base_stage
from openerp.addons.crm import crm
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext

CRM_HELPDESK_STATES = (
    crm.AVAILABLE_STATES[2][0], # Cancelled
    crm.AVAILABLE_STATES[3][0], # Done
    crm.AVAILABLE_STATES[4][0], # Pending
)
HAVAILABLE_STATES = [
    ('draft', 'New'),
    ('cancel', 'Cancelled'),
    ('open', 'In Progress'),
    ('pending', 'Pending'),
    ('done', 'Closed'),
    ('assigned', 'Asignado'),
    ('invoicing', 'Facturando'),
    ('end', 'Soporte Hecho'),
    ('eval', 'Evaluacion'),
    ('evalued', 'Evaluacion de Servicio')
]
    #code

class cds_help_consecutivos_issue(osv.osv):
    """ Category of Case """
    _name = "crm.helpdesk.consecutive"
    _description = "Consecutive support"
    _columns = {
        'parent_id': fields.many2one('crm.helpdesk.principale','Problema Padre'),
        'name': fields.char('Consecutivos',required=True),
    }
    
class cds_help_principale_issue(osv.osv):
    """ Category of Case """
    _name = "crm.helpdesk.principale"
    _description = "Principale support"
    _columns = {
        'parent_id': fields.many2one('crm.helpdesk.family','Familia Padre'),
        'name': fields.char('Principales',required=True),
        'consecutives': fields.one2many('crm.helpdesk.consecutive','parent_id','Consecutivos')
    }
    
class cds_help_family_issue(osv.osv):
    """ Category of Case """
    _name = "crm.helpdesk.family"
    _description = "Family support"
    _columns = {
        'parent_id': fields.many2one('crm.helpdesk.type','Tipo de Problema'),
        'name': fields.char('Familia',required=True),
        'principale': fields.one2many('crm.helpdesk.principale','parent_id','Principales problemas')
    }
    
class cds_help_type_issue(osv.osv):
    """ Category of Case """
    _name = "crm.helpdesk.type"
    _description = "Type support"
    _columns = {
        'product': fields.many2one('product.product','Producto a Aplicar'),
        'name': fields.char('Tipo de problema',required=True),
        'family': fields.one2many('crm.helpdesk.family','parent_id','Familias')
    }

class crm_helpdesk(base_state, base_stage, osv.osv):
    """ Helpdesk Cases """

    _name = "crm.helpdesk"
    _description = "Helpdesk"
    _order = "id desc"
    _inherit = ['mail.thread']
    
    
    def case_escalate(self, cr, uid, ids, context=None):
        """ Escalates case to parent level """
        cases = self.browse(cr, uid, ids, context=context)
        cases[0].state # fill browse record cache, for _action having old and new values
        data = {'active': True}
        for case in cases:
            parent_id = case.section_id.parent_id
            if parent_id:
                data['section_id'] = parent_id.id
                if parent_id.change_responsible and parent_id.user_id:
                    data['user_id'] = parent_id.user_id.id
            else:
                raise osv.except_osv(_('Error!'), _('You can not escalate, you are already at the top level regarding your sales-team category.'))
            self.write(cr, uid, [case.id], data, context=context)
            case.case_escalate_send_note(parent_id, context=context)
        return True

    def case_open(self, cr, uid, ids, context=None):
        """ Opens case """
        cases = self.browse(cr, uid, ids, context=context)
        for case in cases:
            values = {'active': True}
            if case.state == 'draft':
                values['date_open'] = fields.datetime.now()
            if not case.user_id:
                values['user_id'] = uid
            self.case_set(cr, uid, [case.id], 'open', values, context=context)
        return True

    def case_close(self, cr, uid, ids, context=None):
        """ Closes case """
        return self.case_set(cr, uid, ids, 'done', {'date_closed': fields.datetime.now()}, context=context)

    def case_cancel(self, cr, uid, ids, context=None):
        """ Cancels case """
        return self.case_set(cr, uid, ids, 'cancel', {'active': True}, context=context)

    def case_pending(self, cr, uid, ids, context=None):
        """ Sets case as pending """
        return self.case_set(cr, uid, ids, 'pending', {'active': True}, context=context)

    def case_reset(self, cr, uid, ids, context=None):
        """ Resets case as draft """
        return self.case_set(cr, uid, ids, 'draft', {'active': True}, context=context)

    def case_set(self, cr, uid, ids, state_name, update_values=None, context=None):
        """ Generic method for setting case. This methods wraps the update
            of the record, as well as call to _action and browse_record
            case setting to fill the cache.

            :params: state_name: the new value of the state, such as
                     'draft' or 'close'.
            :params: update_values: values that will be added with the state
                     update when writing values to the record.
        """
        cases = self.browse(cr, uid, ids, context=context)
        cases[0].state # fill browse record cache, for _action having old and new values
        if update_values is None:
            update_values = {}
        update_values['state'] = state_name
        return self.write(cr, uid, ids, update_values, context=context)
    
    def case_asigna(self, cr, uid, ids, context=None):
        """ Assigned case """
        return self.case_set(cr, uid, ids, 'assigned', {'active': True}, context=context)
    
    def case_eval(self, cr, uid, ids, context=None):
        """ Assigned case """
        return self.case_set(cr, uid, ids, 'eval', {'active': True}, context=context)
    
    def case_evalued(self, cr, uid, ids, context=None):
        """ Assigned case """
        return self.case_set(cr, uid, ids, 'evalued', {'active': True}, context=context)

    def case_pending(self, cr, uid, ids, context=None):
        """ Set case as pending """
        return self.case_set(cr, uid, ids, 'pending', {'active': True}, context=context)

    def case_reset(self, cr, uid, ids, context=None):
        """ Resets case as draft """
        return self.case_set(cr, uid, ids, 'draft', {'active': True}, context=context)
    def case_end(self, cr, uid, ids, context=None):
        """ Set Case waiting next step """
        return self.case_set(cr, uid, ids, 'end', {'active': True}, context=context)

    _columns = {
            'id': fields.integer('ID', readonly=True),
            'name': fields.char('Nombre', size=128),
            'active': fields.boolean('Active', required=False),
            'date_action_last': fields.datetime('Ultima Accion', readonly=1),
            'date_action_next': fields.datetime('Proxima Accion', readonly=1),
            'description': fields.text('Descripcion'),
            'create_date': fields.datetime('Fecha de Creacion' , readonly=True),
            'write_date': fields.datetime('Fecha de Actualizacion' , readonly=True),
            'date_deadline': fields.date('Deadline'),
            'user_id': fields.many2one('res.users', 'Responsable'),
            'tec_id': fields.many2one('resource.resource', 'Tecnico Responsable'),
            'section_id': fields.many2one('crm.case.section', 'Equipo de Trabajo', \
                            select=True, help='Responsible sales team. Define Responsible user and Email account for mail gateway.'),
            'company_id': fields.many2one('res.company', 'Compañia'),
            'date_closed': fields.datetime('Fecha de Cierre', readonly=True),
            'partner_id': fields.many2one('res.partner', 'Empresa/Cliente', ondelete='set null', track_visibility='onchange',required=True, domain="[('customer', '=', True)]"),
            'email_cc': fields.text('Watchers Emails', size=252 , help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma"),
            'email_from': fields.char('Email', size=128, help="Destination email for email gateway"),
            'date': fields.datetime('Fecha'),
            'ref' : fields.reference('Referancia de mantenimiento', selection=crm._links_get, size=128),
            'ref2' : fields.reference('Segunda Referencia', selection=crm._links_get, size=128),
            'channel_id': fields.many2one('crm.case.channel', 'Canal', help="Communication channel."),
            'planned_revenue': fields.float('Planned Revenue'),
            'planned_cost': fields.float('Planned Costs'),
            'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority'),
            'probability': fields.float('Probability (%)'),
            'categ_id': fields.many2one('crm.case.categ', 'Category', \
                            domain="['|',('section_id','=',False),('section_id','=',section_id),\
                            ('object_id.model', '=', 'crm.helpdesk')]"),
            'duration': fields.float('Duration', states={'done': [('readonly', True)]}),
            'state': fields.selection(HAVAILABLE_STATES, 'Status', size=16, readonly=True,
                                  help='The status is set to \'Draft\', when a case is created.\
                                  \nIf the case is in progress the status is set to \'Open\'.\
                                  \nWhen the case is over, the status is set to \'Done\'.\
                                  \nIf the case needs to be reviewed then the status is set to \'Pending\'.'),
            'contracts': fields.many2one('account.analytic.account','Contratos'),
            'type_support': fields.many2one('crm.helpdesk.type','Tipo de Falla'),
            'family_support': fields.many2one('crm.helpdesk.family','Familia de Falla'),
            'principale_support': fields.many2one('crm.helpdesk.principale','Principal'),
            'consecutive_support': fields.many2one('crm.helpdesk.consecutive','Consecutivo'),
            'portal': fields.boolean('Portal(?)'),
            'preg1': fields.selection((("si", "Si"), ("no", "No")), "¿Fue resuelta la insidencia?"),
            'preg2': fields.selection((("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10")), "¿Como calificaria el servicio que recbio?"),
            'products_line': fields.one2many('products.order.line.helpdesk.support', 'product_line_id', 'Productos'),
            #'cantract2': fields.related ('partner_id','partner_id',type = "one2many",relation = "account.analytic.account",string = "Contratos",store = True)
            #'cantract': fields.one2many('account.analytic.account','partner_id', 'Contratos del cliente', readonly=True)
    }


    _defaults = {
        'active': lambda *a: 1,
        'user_id': lambda s, cr, uid, c: s._get_default_user(cr, uid, c),
        'partner_id': lambda s, cr, uid, c: s._get_default_partner(cr, uid, c),
        'email_from': lambda s, cr, uid, c: s._get_default_email(cr, uid, c),
        'state': lambda *a: 'draft',
        'date': lambda *a: fields.datetime.now(),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.helpdesk', context=c),
        'priority': lambda *a: crm.AVAILABLE_PRIORITIES[2][0]
    }


    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    
    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'user_id': False,
            'partner_id': msg.get('author_id', False),
        }
        defaults.update(custom_values)
        return super(crm_helpdesk, self).message_new(cr, uid, msg, custom_values=defaults, context=context)
    
    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        result = {}
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            
            values = {
                'partner_name' : partner.name,
                'street' : partner.street,
                'street2' : partner.street2,
                'city' : partner.city,
                'state_id' : partner.state_id and partner.state_id.id or False,
                'country_id' : partner.country_id and partner.country_id.id or False,
                'email_from' : partner.email,
                'phone' : partner.phone,
                'mobile' : partner.mobile,
                'fax' : partner.fax,
            }
        return {'value' : values}
    
class sale_order_line(osv.osv):

    _name = 'products.order.line.helpdesk.support'
    _description = 'Products to Contract'
    _columns = {
        'product_line_id': fields.many2one('crm.helpdesk', 'Soporte de Referencia', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)]),
        'quantity': fields.integer('Cantidad de Productos')
        
    }

    
    
    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: