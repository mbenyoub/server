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

import time
import base64
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class res_partner(osv.Model):
    """ Inherits partner and add extra information DIOT """
    _inherit = 'res.partner'
    
    def onchange_type(self, cr, uid, ids, is_company, context=None):
        """
            Actualiza el tipo de contacto del cliente como para direccion de envio
        """
        # Funcion original
        res = super(res_partner,self).onchange_type(cr, uid, ids, is_company, context=context)
        # Pone en el tipo de contacto factura si es compañia y envio si es contacto
        if is_company:
            res['value']['type'] = 'invoice'
        else:
            res['value']['type'] = 'delivery'
        
        return res
    
    def name_get(self, cr, uid, ids, context=None):
        """
            Obtiene el nombre del registro
        """
        
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            # print "*****RECORD***: ", record
            if record.id:
                
                name = record.name
                
                if record.parent_id and not record.is_company:
                    name = "%s, %s" % (name,record.parent_id.name)
                if context.get('show_address'):
                    name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
                    # print "********NAME*****: ", name
                    name = name.replace('\n\n','\n')
                    name = name.replace('\n\n','\n')
                if context.get('show_email') and record.email:
                    name = "%s <%s>" % (name, record.email)
                res.append((record.id, name))
        return res
    
    def _get_amount_credit(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene el valor del credito disponible sobre el cliente
        """
        res = {}
        # Recorre la informacion del cliente
        for partner in self.browse(cr, uid, ids, context):
            amount = 0.0
            # Valida si el cliente tiene un limite de credito y cuanto es su credito disponible
            if partner.credit_limit > 0 and (partner.credit_limit > partner.credit):
                amount = partner.credit_limit - partner.credit
            # Actualiza el valor sobre el credito disponible
            res[partner.id] = amount
        return res
    
    def onchange_branch_id(self, cr, uid, ids, partner_id, user_id, context=None):
        """
            Actualiza la sucursal y pone la sucursal del padre en el partner
        """
        branch_id = False
        if user_id:
            # Obtiene el valor de la sucursal del usuario
            user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
            branch_id = user.branch_id.id or False
            section_id = user.default_section_id.id or False
        elif partner_id:
            # Obtiene el valor de la sucursal del padre
            partner = self.browse(cr, uid, partner_id, context=context)
            branch_id = partner.branch_id.id or False
            section_id = user.default_section_id.id or False
        
        return {'value':{'branch_id': branch_id, 'section_id': section_id}}
    
    #def onchange_user_id(self, cr, uid, ids, field, context=None):
    #    """
    #        Actualiza el equipo de ventas del vendedor
    #    """
    #    # Obtiene el valor de la sucursal del padre
    #    user = self.browse(cr, uid, field, context=context)
    #    return {'value':{'section_id': user.section_id.id or False}}
    
    def _get_branch_default_id(self, cr, uid, context=None):
        """
            Obtiene la sucursal del usuario y la pone por default para el cliente
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.branch_id.id or False
        
    def _get_default_user_id(self, cr, uid, context=None):
        """
            Retorna el id del usuario activo
        """
        return uid or False
    
    # ---------CAMBIO 24/03/2015-------------
    def onchaged_journal_id(self, cr, uid, ids, journal_id, context=None):
        """
            Funcion para hacer obligatorio la captura del rfc a través de una bandera
        """
        res = {}
        journal_obj = self.pool.get('account.journal')
        
        # Se revisa que exista un diario
        if journal_id:
            journal_srch = journal_obj.search(cr, uid, [('id', '=', journal_id)], context=context)
            
            if journal_srch:
                for journal in journal_obj.browse(cr, uid, journal_srch, context=context):                    
                
                    # Se valida que el diario sea una factura
                    if journal.is_invoice == True:
                        res['invoice_required'] = True
                    else:
                        res['invoice_required'] = False
                
        return {'value': res}
    # ------------------------------------------------
        
     #Israel Cabrera Juarez
    def create( self, cr, uid, vals, context = None ):
        """
        Metodo "create" que se ejecuta justo antes (o al momento) de CREAR un nuevo registro en OpenERP
        * Argumentos OpenERP: [ cr, uid, vals, context ]
        @param
        @return bool
        """
        code = ""
        nuevo_id = None
        code = vals['name']
        c=code[0:3]
        cr.execute('SELECT substring(code from 4 for 1) FROM res_partner order by id desc')
        folio = cr.fetchone()[0]
        if (folio != '0'):
    
            vals['code'] = c+'001'
        else:
            cr.execute('SELECT substring(code from 6 for 1) FROM res_partner order by id desc')
            consecutivo = cr.fetchone()[0]
            consecutivo_aux =int(consecutivo)+1 
            vals['code'] = c+'00'+str(consecutivo_aux)
            
        
        nuevo_id = super( res_partner, self).create( cr, uid, vals, context = context )
        return nuevo_id
    _columns = {
        'credit_available': fields.function(_get_amount_credit, type='float', digits_compute= dp.get_precision('Account'), string="Saldo Disponible"),
        'partner_type_id': fields.many2one('res.partner.type', 'Tipo de cliente'),
        'region': fields.char('Region'),
        'zm': fields.char('ZM'),
        #'zone': fields.char('Zona'),
        'route': fields.char('Ruta'),
        'code': fields.char('Clave'),
        'branch_id': fields.many2one('access.branch', 'Acceso'),
        'journal_id': fields.many2one('account.journal', 'Documento', domain=[('type','in',['sale'])], context={'type': 'sale'}, help="Este diario sera creado automaticamente para la cuenta del cliente activo cuando confirme el pedido"),
        
        # --------CAMBIO 24/03/2015--------
        'invoice_required': fields.boolean('Invoice required'),
        'name_comercial': fields.char('Nombre comercial'),
        # ---------------------------------
    }
    
    _defaults = {
        'branch_id': _get_branch_default_id,
        'user_id': _get_default_user_id,
        'is_company': True
    }

res_partner()

class res_partner_type(osv.osv):
    """ Tipo de cliente """
    _name = 'res.partner.type'
    
    _columns = {
        'name': fields.char('Nombre', size=128),
        'note': fields.text('Descripcion')
    }
    
res_partner_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
