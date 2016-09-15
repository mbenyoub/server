# -*- coding: utf-8 -*-
##############################################################################

from openerp.addons.base_status.base_state import base_state
from openerp.addons.base_status.base_stage import base_stage
from openerp.addons.crm import crm
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext
import time

CRM_HELPDESK_STATES = (
    crm.AVAILABLE_STATES[2][0], # Cancelled
    crm.AVAILABLE_STATES[3][0], # Done
    crm.AVAILABLE_STATES[4][0], # Pending
)
HAVAILABLE_STATES = [
    ('draft', 'New'),
    ('open', 'In Progress'),
    ('pending', 'Pending'),
    ('assing', 'Por Asignar'),
    ('assigned', 'Asignado'),
    ('toinvoice', 'Esperando Facturacion'),
    ('invoicing', 'Facturado'),
    ('end', 'Soporte Hecho'),
    ('eval', 'Evaluacion'),
    ('evalued', 'Evaluacion de Servicio'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled'),
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
        """ To Assign case """
        return self.case_set(cr, uid, ids, 'assing', {'active': True}, context=context)
    
    def case_asignad(self, cr, uid, ids, context=None):
        """ Assigned case """
        return self.case_set(cr, uid, ids, 'assigned', {'active': True}, context=context)
    
    def case_eval(self, cr, uid, ids, context=None):
        """ Assigned case """
        return self.case_set(cr, uid, ids, 'eval', {'active': True}, context=context)
    
    def case_invoicing(self, cr, uid, ids, context=None):
        """ Invoice case """
        return self.case_set(cr, uid, ids, 'invoicing', {'active': True}, context=context)
    
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
            'date_deadline': fields.datetime('Deadline', readonly=True),
            'user_id': fields.many2one('res.users', 'Responsable'),
            'tec_id': fields.many2one('resource.resource', 'Tecnico Responsable',track_visibility='always'),
            'section_id': fields.many2one('crm.case.section', 'Equipo de Trabajo', \
                            select=True, help='Responsible sales team. Define Responsible user and Email account for mail gateway.'),
            'company_id': fields.many2one('res.company', 'Compañia'),
            'date_closed': fields.datetime('Fecha de Cierre', readonly=True),
            'partner_id': fields.many2one('res.partner', 'Empresa/Cliente', ondelete='set null',track_visibility='always',required=True, domain="[('customer', '=', True)]"),
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
            'contracts': fields.many2one('account.analytic.account','Contratos',track_visibility='onchange'),
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
    
    
    
    
    
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        obj_helpdesk_products_line = self.pool.get('products.order.line.helpdesk.support')
        date_invoice= False
        invoices = {}
        if context is None:
            context = {}
        # If date was specified, use it as date invoiced, usefull when invoices are generated this month and put the
        # last day of the last month as invoice date
        if date_invoice:
            context['date_invoice'] = date_invoice
        for o in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in o.products_line:
                if line.invoiced:
                    continue
                elif line:
                    lines.append(line.id)
            created_lines = obj_helpdesk_products_line.invoice_line_create(cr, uid, lines)
            if created_lines:
                invoices.setdefault(o.partner_id.id, []).append((o, created_lines))
        if not invoices:
            for o in self.browse(cr, uid, ids, context=context):
                for i in o.invoice_ids:
                    if i.state == 'draft':
                        return i.id
        for val in invoices.values():
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    #self.write(cr, uid, [order.id], {'state': 'toinvoice'})
                    #cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (order.id, res))
        return self.case_set(cr, uid, ids, 'toinvoice', {'active': True}, context=context)
    
    def _inv_get(self, cr, uid, order, context=None):
        return {}
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        today = time.strftime('%Y-%m-%d')
        invoice_vals = {
            'name': order.name or '',
            'origin': order.name+'/Helpdesk-'+str(order.id),
            'type': 'out_invoice',
            'reference': order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'comment': order.description,
            'fiscal_position': order.partner_id.property_account_position.id,
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'date_invoice': today,
            'helpdesk':order.id
        }
        
        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals
        
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}
        invoiced_sale_line_ids = self.pool.get('products.order.line.helpdesk.support').search(cr, uid, [('product_line_id', '=', order.id)], context=context)
        from_line_invoice_ids = []
        
        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        #data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        #if data.get('value', False):
        #    inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id
    
class sale_order_line(osv.osv):
    _name = 'products.order.line.helpdesk.support'
    _description = 'Products to Contract'
    _columns = {
        'product_line_id': fields.many2one('crm.helpdesk', 'Soporte de Referencia', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)]),
        'quantity': fields.integer('Cantidad de Productos'),
        'invoiced': fields.boolean('Facturado')
        
    }
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_('Error!'),
                                _('Please define income account for this product: "%s" (id:%d).') % \
                                    (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uosuom = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
           # if uosqty:
             #   pu = round(line.price_unit * line.product_uom_qty / uosqty,
             #           self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            fiscal_position= False
            fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
            taxes = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, line.product_id.taxes_id)
            res = {
                'name':line.product_id.name,
                'origin': line.product_line_id.name+' Helpdesk No. '+ str(line.product_line_id.id),
                'account_id': account_id,
                'quantity': uosqty,
                'uos_id':uosuom,
                'invoice_line_tax_id': taxes,
                'product_id': line.product_id.id or False,
                'account_analytic_id': line.product_line_id.contracts and line.product_line_id.contracts.id or False,
                'discount': line.product_line_id.contracts.discount_ref
            }

        return res
    
    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        create_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line, False, context)
            if vals:
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                #self.write(cr, uid, [line.id], {'invoice_lines': [(4, inv_id)]}, context=context)
                create_ids.append(inv_id)
        return create_ids
        
    def _get_line_qty(self, cr, uid, line, context=None):
        return line.quantity
    
    def _get_line_uom(self, cr, uid, line, context=None):
        return line.product_id.uom_id.id

    
    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: