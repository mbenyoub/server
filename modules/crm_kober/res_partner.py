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
from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.Model):
    """ Inherits partner and add extra information kober """
    _inherit = 'res.partner'
    
    def onchange_user_id(self, cr, uid, ids, user_id, context=None):
        """
            Actualiza el equipo de ventas en base al vendedor
        """
        values = {}
        user_id = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
        if user_id.default_section_id:
            values['section_id'] = user_id.default_section_id.id
        return {'value':values}
        
    def onchange_parent(self, cr, uid, ids, parent_id, is_company, context=None):
        """
            Actualiza el vendedor por medio del parent_id
        """
        values = {}
        #~ Si el padre tiene un usuario lo agrega
        if parent_id and is_company == False:
            user = self.pool.get('res.partner').browse(cr, uid, parent_id, context=context).user_id
            if user:
                values['user_id'] = user.id or False
                values['notify'] = False
            else:
                #~ Pone por default al usuario que modifica
                values['user_id'] = uid
                values['notify'] = False
        return {'value':values}
    
    def onchange_type(self, cr, uid, ids, is_company, context=None):
        """
            Limpia los campos que no usa la compañia
        """
        res = super(res_partner, self).onchange_type(cr, uid, ids, is_company, context=context)
        
        #print "************************* res ***************** ", res
        
        if not res['value']:
            res['value'] = {}
        
        if is_company:
            res['value']['parent_id'] = False
            res['value']['attention'] = False
            res['value']['sex'] = False
        else:
            res['value']['spin'] = ''
            res['value']['notify'] = False
        return res
    
    def button_check_vat(self, cr, uid, ids, context=None):
        """
            Deja funcionando el boton de validar RFC
        """
        if not self.check_vat2(cr, uid, ids, context=context):
            msg = self._construct_constraint_msg(cr, uid, ids, context=context)
            raise osv.except_osv(_('Error!'), msg)
        return True
    
    def _construct_constraint_msg(self, cr, uid, ids, context=None):
        #print " *************** valida RFC ******************* "
        return ""

    def check_vat2(self, cr, uid, ids, context=None):
        """
            Funcion original de check_vat
        """
        return super(res_partner, self).check_vat(cr, uid, ids, context=context)
    
    def check_vat(self, cr, uid, ids, context=None):
        """
            Elimina funcionalidad de check vat
        """
        #print "************** check vat *********** "
        return True
    
    def _update_date_notify(self, cr, uid, partner_id, context=None):
        """
            Agrega al context el parametro webservice para que no se actualice
        """
        # Agrega al context el parametro de webservice para que no actualice el webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        return super(res_partner, self)._update_date_notify(cr, uid, partner_id, context=context)
    
    def _reset_date_notify(self, cr, uid, partner_id, context=None):
        """
            Agrega al context el parametro webservice para que no se actualice
        """
        # Agrega al context el parametro de webservice para que no actualice el webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        return super(res_partner, self)._reset_date_notify(cr, uid, partner_id, context=context)
    
    def _next_notify_scale(self, cr, uid, partner_id, context=None):
        """
            Agrega al context el parametro webservice para que no se actualice
        """
        # Agrega al context el parametro de webservice para que no actualice el webservice
        if context is None:
            context = {}
        context['webservice'] = True
        
        return super(res_partner, self)._next_notify_scale(cr, uid, partner_id, context=context)
    
    def _have_ws_id(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa verdadero si ya tiene el registro el id del ws
        """
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = False
            if partner.ws_id:
                res[partner.id] = True
        return res
    
    def _have_spin(self, cr, uid, ids, name, arg, context=None):
        """
            Regresa verdadero si tiene la pregunta spin
        """
        res = {}
        #Recorre los contactos
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = False
            if partner.spin:
                #print "**************** tiene spin *************** "
                if len(partner.spin) > 50:
                    #print "**************** spin mayor a 50 ", len(partner.spin)
                    res[partner.id] = True
        return res
    
    def _agree_count(self, cr, uid, ids, field_name, arg, context=None):
        """
            Regresa la cantidad de acuerdos de cobranza pendientes
        """
        res = dict.fromkeys(ids, 0)
        agree_ids = self.pool.get('res.partner.agreement').search(cr, uid, [('partner_id', 'in', ids),('state','in',['to_comply','not_complied'])])
        for agree in self.pool.get('res.partner.agreement').browse(cr, uid, agree_ids, context):
            res[agree.partner_id.id] += 1
        return res
        
    def _get_related_parent(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene los clientes que fueron recomendados por el cliente
        """
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            # Obtiene a los partners que se les tiene que enviar la notificacion
            cr.execute("""
             select id
             from res_partner
             where
                parent_id2=%s and status='ALTA' """%(partner.id,))
            
            partner_ids = [x[0] for x in cr.fetchall()]
            #print "************************** partner_ids ************************ ", partner_ids
            res[partner.id] = partner_ids
        return res
    
    _constraints = [[6, False, [(check_vat, "", ["vat"])]]]
    
    def _display_name_compute(self, cr, uid, ids, name, args, context=None):
        res = dict(self.name_get(cr, uid, ids, context=context))
        #print "*********** display_name ************** ", res
        return res

    _display_name_store_triggers = {
        'res.partner': (lambda self,cr,uid,ids,context=None: self.search(cr, uid, ['|',('id','child_of',ids),('display_name','ilike',self)]),
                        ['parent_id', 'is_company', 'name', 'client'], 10)
    }
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_id.name, name)
            if record.client:
                name = "[" + record.client + "] " + name
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
                name = name.replace('\n\n','\n')
                name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]
            query_args = {'name': search_name}
            limit_str = ''
            if limit:
                limit_str = ' limit %(limit)s'
                query_args['limit'] = limit
            # TODO: simplify this in trunk with _rec_name='display_name', once display_name
            # becomes a stored field
            cr.execute('''SELECT partner.id FROM res_partner partner
                          LEFT JOIN res_partner company ON partner.parent_id = company.id
                          WHERE partner.email ''' + operator +''' %(name)s OR partner.client ''' + operator +''' %(name)s OR
                             CASE WHEN company.id IS NULL OR partner.is_company 
                                      THEN partner.name
                                  ELSE
                                      company.name || ', ' || partner.name
                             END
                          ''' + operator + ' %(name)s ' + limit_str, query_args)
            ids = map(lambda x: x[0], cr.fetchall())
            ids = self.search(cr, uid, [('id', 'in', ids)] + args, limit=limit, context=context)
            if ids:
                return self.name_get(cr, uid, ids, context)
        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
    
    # indirection to avoid passing a copy of the overridable method when declaring the function field
    _display_name = lambda self, *args, **kwargs: self._display_name_compute(*args, **kwargs)
    
    _columns = {
        'display_name': fields.function(_display_name, type='char', string='Name', store=_display_name_store_triggers),
        'name': fields.char('Name', size=128, required=True, select=True, traslate=False),
        'street3': fields.char('Numero', size=64),
        'delegation': fields.char('Delegacion', size=128),
        'category': fields.selection([
                                    ('ACTIVOS', 'Activos'),
                                    ('INACTIVOS', 'Inactivos'),
                                    ('EN LEGAL', 'Legal')], 'Categoria'),
        'family': fields.selection([
                                    ('REGIONALES', 'Regionales'),
                                    ('NACIONALES', 'Nacionales'),
                                    ('INTERNACIONALES', 'Internacionales')], 'Familia'),
        'credit': fields.char('Credito', size=128, help="Politicas"),
        'partial_order': fields.boolean('Pedidos Parciales'),
        'type_client': fields.selection([
                                    ('Cliente', 'Cliente'),
                                    ('Deudor', 'Deudor'),
                                    ('Estructura', 'Estructura'),
                                    ('Bancario', 'Bancario')], 'Tipo'),
        'discount': fields.float('Descuento', readonly=True),
        'condition': fields.char('Condicion', size=128, help="Condiciones de venta"),
        'currency_id': fields.many2one('res.currency', 'Moneda', readonly=True),
        'status': fields.selection([
                                    (u'ALTA', 'Alta'),
                                    (u'BLOQUEADO', 'Bloqueado'),
                                    (u'BAJA', 'Baja'),], 'Estatus'),
        'date_create': fields.date('Fecha Alta', select=1, help="Fecha de creacion", readonly=True),
        'block_morosos': fields.char('Bloquear Morosos', size=128, help="Definido desde intelisis", readonly=True),
        'have_mov': fields.boolean('Tiene Movimientos', readonly=1),
        'branch_id': fields.many2one('crm.access.branch', 'Sucursal'),
        #'branch_customer_id': fields.many2one('crm.access.branch', 'Sucursal Empresa'),
        # Campos para CteCto
        'extension': fields.char('Extension', size=128, help="Numero de extension del telefono"),
        'attention': fields.selection([
                                    ('Estimado', 'Estimado'),
                                    ('Estimada', 'Estimada')], 'Atencion'),
        'type_contact': fields.char('Tipo', size=64, help="Tipo de contacto"),
        'sex': fields.selection([
                                ('Masculino', 'Masculino'),
                                ('Femenino', 'Femenino')], 'Sexo'),
        # Campos ClienteEnviarA (Direcciones)
        'region': fields.char('Zona', size=128),
        'price_list_esp': fields.char('Lista de precio Especial', size=128),
        'is_address': fields.boolean('Es sucursal?'),
        # Relacion hijos con la tabla padre Contactos y Direcciones
        'address_ids': fields.one2many('res.partner', 'parent_id', 'Direcciones', domain=[('active','=',True),('is_address','=',True),('is_company','=',False)]), 
        'child_ids': fields.one2many('res.partner', 'parent_id', 'Direcciones', domain=[('active','=',True),('is_address','=',False),('is_company','=',False)]), 
        # Campos para webservice
        'ws_id': fields.char('Id webservice', size=64),
        'have_ws_id': fields.function(_have_ws_id, method=True, store=True, string='Tiene ws_id', readonly=True, type='boolean'),
        # SPIN Cliente
        'spin_required': fields.boolean('Spin Obligatorio'),
        'spin': fields.text('CUALES SON LOS BENEFICIOS DE KOBER, QUE MAS LE INTERESARON A ESTE CLIENTE? Y QUE PREGUNTA TE LLEVO A DETECTARLOS?'),
        'have_spin': fields.function(_have_spin, method=True, string='Tiene spin?', readonly=True, store=True, type='boolean', help="Indica si tiene la pregunta spin."),
        'competence': fields.boolean('Es competencia?'),
        'swot_id': fields.many2one('crm.swot', 'Foda'),
        # Campo para acuerdos de cobranza
        'agree_count': fields.function(_agree_count, type='integer', string="Acuerdos Pendientes"),
        # Cambiar a que solo haya un solo grupo
        'category_id': fields.many2one('res.partner.category', 'Grupo'),
        'phone': fields.char('Telefono', size=256),
        # Se agrega vat2 para omitir problemas de validacion
        'vat2': fields.char('RFC', size=128),
        # Se agrega la rama y el id del cliente
        'client': fields.char('Cliente', size=64, readonly=True),
        'bunch': fields.char('Rama', size=64),
        'parent_id2': fields.many2one('res.partner', 'Recomendado por', domain=[('is_company','=',True)]),
        'parent_ids2':fields.function(_get_related_parent, type='one2many', relation="res.partner", string="Recomendados"),
    }
    
    _defaults = {
        'category': 'ACTIVOS',
        'family': 'NACIONALES',
        'credit': 'POLITICA 30 DIAS',
        'partial_order': True,
        'type_client': 'Cliente',
        'condition': '30 DIAS',
        'status': 'ALTA',
        'date_create': lambda *a: time.strftime('%Y-%m-%d'),
        'have_mov': False,
        # Default CteCto
        'attention': 'Estimado',
        'sex': 'Masculino',
        'notify': False,
        'price_list_esp': '(Precio Lista)',
        'spin_required': False,
        'active': True
    }
    
    def _check_spin_question(self, cr, uid, ids, context=None):
        """
            Valida que la pregunta SPIN tenga un minimo de 50 caracteres
        """
        for partner in self.browse(cr, uid, ids, context):
            # Valida que sea una compañia
            if partner.is_company == True and partner.spin_required == True:
                # Valida el tamaño de los caracteres de la pregunta spin
                if not partner.spin:
                    return False
                elif len(partner.spin) < 50:
                    return False
        return True
    
    _constraints = [(_check_spin_question, "La pregunta SPIN debe tener un minimo de 50 caracteres !", ['spin']),]    
    
    #####
    #  Metodos agregados para ejecutar webservice
    #####
    
    def create(self, cr, uid, vals, context=None):
        """
            Agrega el nuevo cliente a la base de datos de intelisis
        """
        # Funcion original de crear
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        #print "**************** context create ****************** ", context
        
        if context is None:
            context = {}
        
        # Valida que la insercion no aplique de una modificacion del webservice
        if context.get('webservice'):
            return res
        
        # Valida la pregunta spin
        #if self._check_spin_question(cr, uid, ids, context=context) == False:
        #    raise osv.except_osv(_('Warning!'),_('La pregunta SPIN debe tener un minimo de 50 caracteres!.'))
        
        # Actualiza la informacion en el webservice
        partner = self.browse(cr, uid, res, context=context)
        kober_obj = self.pool.get('crm.kober.ws.control')
        # Valida que el contacto sea un cliente
        if partner.customer == False:
            return res
        # Actualiza el contacto en intelisis
        if partner.is_company == True:
            # Si es compañia actualiza el cliente
            kober_obj.ws_post_cte(cr, uid, [res], context=context)
        elif partner.is_address == True:
            # Si es una direccion actualiza la direccion a enviar
            kober_obj.ws_post_cteenviara(cr, uid, [res], context=context)
        else:
            # Actualiza el contacto
            kober_obj.ws_post_ctecto(cr, uid, [res], context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        """
            Actualiza el campo partner en la base de datos de intelisis (Cliente, contacto o sucursal, segun sea el caso)
        """
        if context is None:
            context = {}
            
        #~ #print "********* ids write **************** ", ids
        #~ #print "********* values write **************** ", vals
        #~ #print "********* values write **************** ", context
        
        webservice = False
        if context.get('webservice', False) == True:
            webservice = context.get('webservice', False)
        #~ #print "********** webservice val *********** ", webservice

        # Inicializa variables y pool's
        kober_obj = self.pool.get('crm.kober.ws.control')
        contacto = []
        # Revisa si tiene contactos para eliminar
        if vals.get('child_ids'):
            for child in vals.get('child_ids'):
                if child[0] == 2:
                    contacto.append(child[1])
        if len(contacto):
            #~ #print "*********** elimnar contactos de write ******* ", contacto
            # Elimina el contacto
            kober_obj.ws_delete_ctecto(cr, uid, contacto, context=context)
            context['webservice'] = False
        # Funcion original de modificar
        super(res_partner, self).write(cr, uid, ids, vals, context=context)
        #~ #print "********** webservice val - after super *********** ", webservice
        #~ #print "********* ids write - after super **************** ", ids

        #~ #print "*********** get context write ************* ", context
        #~ #print "*********** get webservice context ************* ", context.get('webservice')
        #~ #print "*********** vals get write ************* ", vals
        #~ #print "*********** validacion context write ************* ", context.get('webservice', False) == True
        
        # Valida que la actualizacion no aplique de una modificacion del webservice
        if webservice == True:
            return True
        
        # Valida la pregunta spin
        #if self._check_spin_question(cr, uid, ids, context=context) == False:
        #    raise osv.except_osv(_('Warning!'),_('La pregunta SPIN debe tener un minimo de 50 caracteres!.'))
        
        # Inicializa variables y pool's
        cliente = []
        contacto = []
        sucursal = []
        
        #print "*************** ids **************** ", ids
        if type(ids) != list:
            ids = [ids]
        
        # Obtiene los ids de los campos a actualizar y los agrupa por tipo (Cliente, contacto o sucursal)
        for partner in self.browse(cr, uid, ids, context=context):
            #print "********** partner es compañia ********** ", partner.is_company
            if partner.is_company == True:
                # Busca direcciones sin registrar
                address_ids = self.search(cr, uid, [('parent_id','=',partner.id),('is_address','=',True),('have_ws_id','=',False)], context=context)
                #print "********** address_ids *********** ", address_ids
                if address_ids:
                    # Agrega nuevas direcciones
                    kober_obj.ws_post_cteenviara(cr, uid, address_ids, context=context)
            # Valida que el contacto sea un cliente
            if partner.customer == False:
                continue
            #print "************** partner ******************* ", partner.name
            # Valida que exista el id del webservice, sino lo manda a crear
            if not partner.ws_id:
                #print "************** no existe ws_id ******************* ", partner.ws_id
                #print "************** padre contacto ******************* ", partner.parent_id.id
                if partner.is_company == True:
                    # Crea el cliente en intelisis
                    kober_obj.ws_post_cte(cr, uid, [partner.id], context=context)
                elif partner.is_address == True:
                    # Valida que tenga asignado un padre
                    if partner.parent_id.id:
                        # Crea la direccion a enviar en intelisis
                        kober_obj.ws_post_cteenviara(cr, uid, [partner.id], context=context)
                else:
                    # Valida que tenga asignado un padre
                    if partner.parent_id.id:
                        #print "********* Crea contacto ************* ", partner.parent_id.id
                        # Crea el contacto en intelisis
                        kober_obj.ws_post_ctecto(cr, uid, [partner.id], context=context)
            else:
                if partner.is_company == True:
                    cliente.append(partner.id)
                elif partner.is_address == True:
                    # Valida que tenga asignado un padre
                    if partner.parent_id.id:
                        sucursal.append(partner.id)
                else:
                    # Valida que tenga asignado un padre
                    if partner.parent_id.id:
                        contacto.append(partner.id)
        
        # Actualiza la informacion en el webservice
        if len(cliente):
            # Actualiza el cliente
            kober_obj.ws_put_cte(cr, uid, cliente, context=context)
        elif len(sucursal):
            # Actualiza la direccion a enviar
            kober_obj.ws_put_cteenviara(cr, uid, sucursal, context=context)
        elif len(contacto):
            # Actualiza el contacto
            kober_obj.ws_put_ctecto(cr, uid, contacto, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        """
            Elimina el registro del calendario de actividades
        """
        
        if context is None:
            context = {}
        
        #print "*********** delete partner **************** ", ids
        #print "*********** delete context **************** ", context
        
        # Obtiene los ids de los campos a eliminar
        if not context.get('webservice'):
            # Inicializa variables y pool's
            kober_obj = self.pool.get('crm.kober.ws.control')
            cliente = []
            contacto = []
            sucursal = []
            
            # Obtiene los ids de los campos a actualizar y los agrupa por tipo (Cliente, contacto o sucursal)
            for partner in self.browse(cr, uid, ids, context=context):
                # Valida que el contacto sea un cliente
                if partner.customer == False:
                    continue
                
                # Valida que el cliente no tenga movimientos
                if partner.have_mov == True:
                    raise osv.except_osv('Error!', 'No se puede eliminar el cliente porque tiene movimientos.')
                # Identifica que tipo de partner es
                if partner.is_company == True:
                    cliente.append(partner.id)
                elif partner.is_address == True:
                    sucursal.append(partner.id)
                else:
                    contacto.append(partner.id)
            # Actualiza la informacion en el webservice
            if len(cliente):
                # Actualiza el cliente
                kober_obj.ws_delete_cte(cr, uid, ids, context=context)
            elif len(sucursal):
                # Actualiza la direccion a enviar
                kober_obj.ws_delete_cteenviara(cr, uid, ids, context=context)
            elif len(contacto):
                # Actualiza el contacto
                kober_obj.ws_delete_ctecto(cr, uid, ids, context=context)
        
        # Elimina los registros
        res = super(res_partner, self).unlink(cr, uid, ids, context=context)
        return res

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class res_partner_agreement(osv.osv):
    """ Inherits partner and add extra information invoice line"""
    _name = 'res.partner.agreement'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    def action_agree(self, cr, uid, ids, context=None):
        """ 
            Esta funcion cambia el estado a cumplido
        """
        partner_obj = self.pool.get('res.partner')
        for agreement in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, agreement.id, {'state':'complied'}, context=context)
            
            # Actualiza la actividad de los partners
            if agreement.partner_id:
                if agreement.partner_id.is_company == True:
                    partner_obj._reset_date_notify(cr, uid, agreement.partner_id.id, context=context)
                elif agreement.partner_id.parent_id:
                    partner_obj._reset_date_notify(cr, uid, agreement.partner_id.parent_id.id, context=context)
        return True
    
    def action_disagree(self, cr, uid, ids, context=None):
        """ 
            Esta funcion cambia el estado a no cumplido
        """
        partner_obj = self.pool.get('res.partner')
        for agreement in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, agreement.id, {'state':'not_complied'}, context=context)
            
            # Actualiza la actividad de los partners
            if agreement.partner_id:
                if agreement.partner_id.is_company == True:
                    partner_obj._reset_date_notify(cr, uid, agreement.partner_id.id, context=context)
                elif agreement.partner_id.parent_id:
                    partner_obj._reset_date_notify(cr, uid, agreement.partner_id.parent_id.id, context=context)
        return True
    
    def _get_user(self, cr, uid, context=None):
        """
            Regresa el usuario activo
        """
        return uid

    _columns = {
        'name': fields.char('Nombre', size=128, required=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', required=True, domain=[('customer','=',True)]),
        'user_id': fields.many2one('res.users', 'Responsable', help="Vendedor responsable del acuerdo", required=True),
        'date_agree': fields.date('Fecha Acuerdo', required=True),
        'state': fields.selection([
            ('to_comply','Por cumplir'),
            ('complied','Cumplido'),
            ('not_complied','No cumplido')],'Status', select=True),
        'notes': fields.text('Notas'),
        'branch_id': fields.related('partner_id', 'branch_id', type="many2one", relation="crm.access.branch", store=True, string="Sucursal", readonly=True),
    }
    
    _defaults = {
        'state': 'to_comply',
        'user_id': lambda s, cr, uid, c: s._get_user(cr, uid, c)
    }
    
    def create(self, cr, uid, vals, context=None):
        """
            Actualiza la actividad del partner
        """
        # Funcion original de crear
        res = super(res_partner_agreement, self).create(cr, uid, vals, context=context)
        #print "**************** res ****************** ", res
        
        # Actualiza la actividad de los partners
        agree = self.browse(cr, uid, res, context=context)
        if agree.partner_id:
            partner_obj = self.pool.get('res.partner')
            if agree.partner_id.is_company == True:
                partner_obj._reset_date_notify(cr, uid, agree.partner_id.id, context=context)
            elif agree.partner_id.parent_id:
                partner_obj._reset_date_notify(cr, uid, agree.partner_id.parent_id.id, context=context)
        return res
    
    def cron_notify_agreement(self, cr, uid, context=None):
        """
            Envia un recordatorio a un usuario sobre un pedido de venta
        """
        if context is None:
            context = {}
        
        agree_ids = []
        date = time.strftime('%Y-%m-%d')
        
        # Obtiene a los usuarios que se les tiene que enviar la notificacion
        cr.execute("""
         select id
         from res_partner_agreement
         where
            state='to_comply' and
            user_id>0 and
            date_agree<='%s'"""%(date,))
        
        agree_ids = [x[0] for x in cr.fetchall()]
        
        # Envia correo electronico a los usuarios solicitados
        if len(agree_ids):
            self.send_mail(cr, uid, agree_ids, context=context)
        return True
    
    def send_mail(self, cr, uid, ids, context=None):
        """
            Envia un correo al responsable del acuerdo de cobranza
        """
        #print "************************ send mail notify agreement ************************* "
        mail_server_obj = self.pool.get('ir.mail_server')
        mail_message_obj = self.pool.get('mail.message')
        mail_mail_obj = self.pool.get('mail.mail')
        # Obtiene la informacion general para el envio del mensaje
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        user_id = company.user_mail
        # Obtiene la informacion del email
        mail_server_ids = mail_server_obj.search(cr, uid, [], context=context)
        email_from = mail_server_obj.browse(cr, uid, mail_server_ids[0], context=context).smtp_user
        email_from = "%s <%s>" %(company.name, email_from)
        reply_to = "%s <%s>" %(company.name, company.email)
        subject = "Vencimiento acuerdo de cobranza"
        # Obtiene el contenido del mensaje
        body_html = "Revisar Acuerdo de cobranza." 
        
        # Registra el evento en mail.message
        values_message = {
            'subject': subject,
            'body': body_html,
            'email_from': email_from,
            'partner_ids': [],
            'model': 'res.partner.agreement',
            'res_id': 0,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        mail_message_id = mail_message_obj.create(cr, uid, values_message, context=context)
        
        # Recorre los acuerdos para enviar los mensajes
        for agree in self.browse(cr, uid, ids, context=context):
            # Obtiene el mensaje a enviar
            body_mail = """
                        <h3>Seguimiento %s</h3>
                        <div>El Acuerdo de cobranza %s no se a confirmado, la fecha limite para el acuerdo es %s. Se recomienda
                        contactar con el cliente %s para dar por finalizado el proceso.</div>
                        """ %(agree.name, agree.name, agree.date, agree.partner_id.name)
            # Configuracion del correo a enviar
            email_to = "%s <%s>" %(agree.user_id.name, agree.user_id.email)
        
            # Registra documento en mail.mail
            mail_mail_id = mail_mail_obj.create(cr, uid, {
                'mail_message_id': mail_message_id,
                'mail_server_id': mail_server_ids and mail_server_ids[0],
                'state': 'outgoing',
                'email_from': email_from,
                'email_to': email_to,
                'email_cc': '',
                'reply_to': reply_to,
                'body_html': body_mail}, context=context)
            if mail_mail_id:
                # Envia el correo al vendedor
                mail_mail_obj.send(cr, uid, [mail_mail_id], context=context)
                #print "*********************** mensaje enviado ****************** "
        return True
    
res_partner_agreement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

