# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Roberto Ivan Serrano Saldaña (riss_600@hotmail.com)
#              Juan Manuel Oropeza (joropeza@akkadian.com.mx)
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
# ----MODIFICACION 21/04/2015----
#   Agregacion del metodo 'confirm' en 'sale_commission_commission' donde se crea el archivo que utilizara
#   la aplicacion de calculo de nomina de Canis

from osv import osv, fields
from openerp.tools.translate import _
import codecs
from datetime import datetime, timedelta
import time
import calendar
import openerp.addons.decimal_precision as dp
import sys
class sale_commission_objective(osv.Model):

    _name = 'sale.commission.objective'

    def onchange_product_ids(self, cr, uid, ids, product_ids):
        """
            Valida que los productos de la lista tengan el mismo tipo de unidad de medida
        """
        #print " ******* Entrando onchange_product_ids **** ", product_ids
        res = {}
        war = ""
        p_ids = []
        type = False
        if product_ids[0][2]:
            for product in self.pool.get('product.product').browse(cr, uid, product_ids[0][2]):
                # Valida el tipo del producto
                if type == False:
                    # Si el tipo no esta asignado asigna el del primer producto en la lista
                    type = product.uom_id.id
                    p_ids.append(product.id)
                # Valida si el tipo de producto es distinto
                elif type != product.uom_id.id:
                    # Agrega el producto a la lista de productos invalidos
                    if war == "":
                        war = product.name
                    else:
                        war = "%s, %s"%(war,product.name)
                else:
                    # Pone el id del producto sobre la lista valida
                    p_ids.append(product.id)

        # Valida si hay productos invalidos
        if war != "":
            warning = {
                'title': _('Tipo de producto Invalido!'),
                'message' : _('No se pueden agregar productos a la lista con diferente tipo de unidad de medida (%s)')%(war,)
            }
            res = {
                'warning': warning,
                'value': {'product_ids': p_ids}
            }
        return res
    
    def onchange_type(self, cr, uid, ids, type_comm, context=None):
        """
            Cambia 'commission_type' a '%' en caso de seleccionar 'PAGADO'
        """
        res = {}
        
        if type_comm == 'paid':
            res = {
                'commission_type': 'percent'
            }
            
        return {'value': res}

    def onchange_type_commission(self, cr, uid, ids, type_commission,
        context=None):
        res = {}

        if type_commission:
            res = {
                'resp_commission_type': type_commission,
            }

        return {'value': res}

    def _check_commission_value(self, cr, uid, ids, context=None):
        """
            Valida que una comisión no se pague en ceros
        """
        for move in self.browse(cr, uid, ids, context):
            # Es verdadero si commission_value es mayor a cero
            if move.commission_value > 0:
                return True
            else:
                return False

    def _check_data_invoiced(self, cr, uid, ids, context=None):
        """
            Valida que al menos un dato de validación por factura sea mayor a cero
        """
        for move in self.browse(cr, uid, ids, context):
            if move.type == 'invoiced':
                # Se valida que monto, cantidad, o peso sean mayor a cero
                if (move.amount > 0) or (move.quantity_min > 0) or (move.weight > 0):
                    return True
                else:
                    return False
            else:
                return True

    def _check_data_paid(self, cr, uid, ids, context=None):
        """
            Valida que algún límite de días su comisión no sea cero
        """
        for move in self.browse(cr, uid, ids, context):
            # Se valida que el tipo de comisión sea "Pagado"
            if move.type == 'paid':
                # Se recorre la lína de los límites de pago (días)
                for line in move.paid_ids:
                    if move.paid_ids is not None:
                        for line in move.paid_ids:
                            # Se valida que cada límite de pago su porcentaje de validación sea mayor a cero
                            if line.percent > 0:
                                return True
                            else:
                                return False
            else:
                return True
    
    def _check_proportion_max(self, cr, uid, ids, context=None):
        """
            Verifica que la propoción máxima sea mayor a la mínima
        """
        for move in self.browse(cr, uid, ids, context=context):
            if move.commission_proportion_min < move.commission_proportion_max:
                return True
            else:
                return False
            
    def _check_proportion_min(self, cr, uid, ids, context=None):
        """
            Verifica que la proporción mínima no sea mayor a 100
        """
        for move in self.browse(cr, uid, ids, context=context):
            if move.commission_proportion_min > 100:
                return False
            else:
                return True

    def _get_commission_type(self, cr, uid, ids, field_name, args, context=None):
        """
            Obtiene el valor del campo 'commission_type'
        """
        res = {}
        for commission in self.browse(cr, uid, ids, context=context):
            res[commission.id] = commission.commission_type
        return res

    _columns = {
        'name': fields.char('Nombre de objetivo', required=True),
        'type': fields.selection([('invoiced', 'Facturado'),
            ('paid', 'Pagado')], 'Tipo', required=True),
        'active': fields.boolean('Activo'),
        # Produto
        'product_ids': fields.many2many('product.product', 'product_rel', 'objective_id', 'product_rel_id', 'Productos'),
        'pricelist_ids': fields.many2many('product.pricelist', 'pricelist_rel', 'pricelist_id', 'pricelist_rel_id', 'Tarifas'),
        'product_category_id': fields.many2one('product.category', 'Categoría'),
        'quantity_min': fields.float('Cantidad', digits=(2, 3)),
        'weight': fields.float('Peso'),
        'amount': fields.float('Monto'),
        'pricelist_id': fields.many2one('product.pricelist', 'Lista de precios'),
        # comision
        'commission_type': fields.selection([
            ('currency', '$'),
            ('percent', '%')], 'Comisión en:'),
        'commission_value': fields.float('Comisión vendedor'),
        'commission_value_ext': fields.float('Excedente'),
        'commission_proportion': fields.boolean('Pagar proporcional'),
        'commission_proportion_min': fields.float('Porcentaje mínimo'),
        'commission_proportion_max':fields.float('Porcentaje máximo'),
        'resp_commission_type': fields.function(_get_commission_type, type="selection", selection=[
            ('currency', '$'),
            ('percent', '%')], string='Comisión en:', readonly=True),
        'resp_commission_value': fields.float('Comisión supervisor'),
        'paid_ids': fields.one2many('sale.commission.objective.paid', 'objective_id', 'Detalle Pagos'),
        'note': fields.text('Notas'),
    }

    _defaults = {
        'type': 'invoiced',
        'commission_type': 'percent',
        'resp_commission_type': 'percent',
        'commission_proportion_min': 100,
        'active': True,
        'commission_value': float(),
        'commission_proportion_max': 110
    }

    _constraints = [
        (_check_commission_value, 'Error!, No se puede dejar en ceros',
            ['commission_value']),
        (_check_data_invoiced,
            'Error!, Debe ser mayor a cero al menos uno de los datos de validación para factura',
            ['amunt', 'quantity_min', 'weight']),
        (_check_data_paid, 'Error!, Debe ser mayor a cero el porcentaje a pagar', ['paid_ids']),
        (_check_proportion_max, 'Error!, La proporción máxima debe ser mayor a la mínima',
            ['commission_proportion_max']),
        (_check_proportion_min, 'Error!, La proporción mínima debe ser menor o igual a 100',
            ['commission_proportion_min'])
    ]

sale_commission_objective()

class sale_commission_objective_paid(osv.Model):
    _name = 'sale.commission.objective.paid'
    _order = 'days,percent'
    
    _columns = {
        'name': fields.char('Nombre de comisión por pago'),
        'days': fields.integer('Días'),
        'percent': fields.float('Porcentaje'),
        'objective_id': fields.many2one('sale.commission.objective',
            'Objetivo'),
    }

sale_commission_objective_paid()

class sale_commission_objective_version(osv.Model):
    _name = 'sale.commission.objective.version'
    _order = 'period_id'
    
    def _validate_active_version(self, cr, uid, ids, context=None):
        """
            Valida si hay una version sobre el mismo periodo o ejercicio
        """
        # Recorre las versiones a validar
        for version in self.browse(cr, uid, ids, context=context):
            # Valida si la version es por periodo o por ejercicio
            if version.fiscalyear_bol == True:
                # Busca y valida que no haya una versión en el mísmo ejercicio
                fiscalyear_ids = self.search(cr, uid, [('fiscalyear_id', '=', version.fiscalyear_id.id or False),
                    ('active', '=', True), ('id', '!=', version.id)])
                if fiscalyear_ids:
                    return False
            else:
                # Busca y valida que no haya una versión en el mísmo periodo
                version_ids = self.search(cr, uid, [('period_id', '=', version.period_id.id or False),
                    ('active','=',True),('id','!=',version.id)])
                if version_ids:
                    return False
            
        return True
    
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Función para duplicar las versiones
        """
        # Diccionario donde se almacenan los datos a duṕlicar
        res = {
            'name': '',
            'period_id': None,
            'active': False,
        }
        
        # Se obtienen los datos a duplicar
        version = self.browse(cr, uid, id, context=context)
        res['name'] = version.name + "(Copia " + version.period_id.name + ")"
        res['active'] = version.active
        print "*******RES******: ", res
        
        return super(sale_commission_objective_version, self).copy(cr, uid, id, res, context)
        
    
    _columns = {
        'name': fields.char('Nombre'),
        'period_id': fields.many2one('account.period', 'Periodo contable'),
        'active': fields.boolean('Activo'),
        'fiscalyear_bol': fields.boolean('Por ejercicio'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio fiscal'),
        'line_ids': fields.one2many('sale.commission.objective.version.line',
            'version_id', 'Línea de versión de comisión'),
    }

    _defaults = {
        'active': True,
    }
    
    _constraints = [
        (_validate_active_version, 'No puede haber dos o más versiones activas en el mismo periodo o ejercicio', ['active'])
    ]

sale_commission_objective_version()

class sale_commission_objective_version_line(osv.Model):
    _name = 'sale.commission.objective.version.line'
    _order = 'sequence'
    
    def onchange_user_id(self, cr, uid, ids, user_id, context=None):
        """
            Obtiene el equipo del vendedor
        """
        res = {}
        usr_obj = self.pool.get('res.users')
        
        #print "***********USER*********: ", user_id
        if user_id:
            # Retorna el id del equipo de ventas asignado al usuario
            usr = usr_obj.browse(cr, uid, user_id, context=context)
            res['section_id'] = usr.default_section_id.id or False
        return {'value': res}

    def onchange_section_id(self, cr, uid, ids, section_id, context=None):
        """
            Obtiene el equipo del vendedor
        """
        res = []
        if section_id:
            # Actualiza el valor del dominio del usuario
            res = [('default_section_id','=',section_id)]
        return {'domain': {'user_id': res}}

    _columns = {
        'name': fields.char('Nombre'),
        'user_id': fields.many2one('res.users', 'Vendedor'),
        'section_id': fields.many2one('crm.case.section', 'Equipo de ventas'),
        'sequence': fields.integer('Secuencia'),
        'version_id': fields.many2one('sale.commission.objective.version', 'Versión de comisión'),
        'objective_parent_id': fields.many2one('sale.commission.objective', 'Objetivo padre'),
        'objective_id': fields.many2one('sale.commission.objective', 'Objetivo'),
    }
    
    _defaults = {
        'sequence': 10,
    }

sale_commission_objective_version_line()

# Estado de comision
state_commission = [
            ('draft', 'Borrador'),
            ('open', 'Abierto'),
            ('paid', 'Pagado'),
            ('cancel', 'Cancelado')]

class sale_commission_commission(osv.Model):
    _name = 'sale.commission.commission'
    
    def _get_filter_invoiced(self, cr, uid, objective,context=None):
        """
            Genera la cadena para realizar el filtrado en el query donde se realizarán los calculos
        """
        cat_ids = []
        product_ids = []
        pricelist_ids = []
        
        categ_obj = self.pool.get('product.category')
        
        # Valida si el objetivo valida la categoria
        if objective.product_category_id:            
            # Busca todas las categorias relacionadas a la categoria padre
            categ_srch = categ_obj.search(cr, uid, ['|',('id','=',objective.product_category_id.id or False),('parent_id','=',objective.product_category_id.id or False)])
            # Recorremos los ids de las categorias y creamos una lista con los ids
            for cat in categ_srch:
                cat_ids.append(str(cat))
            # Crea una lista separados por comas en un string
            
            
        # Valida si hay que buscar el objetivo por algun producto especifico
        if objective.product_ids:
            # Recorremos los productos y creamos una lista con los ids
            for product in objective.product_ids:
                product_ids.append(str(product.id))
            
            
        # Valida si hay que buscar en una tarifa en especifico
        if objective.pricelist_ids:            
            # Se recorren las tarifas generando una lista con los ids
            for pricelist in objective.pricelist_ids:
                pricelist_ids.append(str(pricelist.id))            
        
        return cat_ids, product_ids, pricelist_ids
    
    def _get_data_invoiced(self, cr, uid, period_id, user_id, categ_ids=False, product_ids=False, pricelist_ids=False, context=None):
        """
            Ejecuta el query
        """
        amount = 0
        quantity = 0
        weight = 0
        
        string_query = " "
        
        if categ_ids:
            cat_list = ",".join(categ_ids)
            # Agrega validacion sobre categoria principal y la categoria padre
            string_query = "%s and t.categ_id in (%s)"%(string_query,cat_list)
        
        if product_ids:
            # Agregamos la lista de productos al where
            product_list = " or p.id = ".join(product_ids)
            string_query = "%s and (p.id = %s) "%(string_query,product_list)
        
        if pricelist_ids:
            # Se agrega la lista de tarifas al where
            pricelist_list = " or pl.id = ".join(pricelist_ids)
            string_query = "%s and (l.pricelist_id = %s)"%(string_query, pricelist_list)
            
        # Crea la consulta 
        string_query = """
                    SELECT
                        sum(l.price_subtotal) as subtotal,
                        sum(l.quantity) as quantity_product,
                        sum(t.weight * l.quantity) as product_weight
                    FROM
                        account_invoice_line as l
                        INNER JOIN product_product as p on p.id = l.product_id
                        INNER JOIN product_template as t on t.id = p.product_tmpl_id
                    WHERE
                        l.type = 'out_invoice' and l.user_id = %s and l.period_id = %s 
                        %s
            """%(user_id,period_id,string_query)
            
        print "************ consulta *************** ", string_query
        # Ejecuta el query para obtener los productos
        cr.execute(string_query)
        
        # Obtiene el resultado de la consulta
        for i in cr.fetchall():
            amount = i[0] if i[0] is not None else 0.0
            quantity = i[1] if i[1] is not None  else 0.0
            weight = i[2] if i[2] is not None  else 0.0
            break
        
        return amount, quantity, weight
    
    def _compute_invoiced(self, cr, uid , objective, user_id, period_id, context=None):
        """
            Realiza la validación del objetivo por factura, regresa verdadero su el objetivo se ha cumplido
            y el porcentaje de comisión correspondiente
        """
        str_where = ""
        categ_ids = []
        product_ids = []
        pricelist_ids = []
        
        result = {
            'weight': 0.0,
            'amount': 0.0,
            'quantity': 0.0,
            'percent': 0.0,
            'commission_amount': 0.0,
            'resp_amount': 0.0,
            'objective_complete': False
        }
        
        # Crea la cadena para realizar el filtrado en el query
        categ_ids, product_ids, pricelist_ids = self._get_filter_invoiced(cr, uid, objective, context=context)
        
        # Se genera la consulta
        result['amount'], result['quantity'], result['weight'] = self._get_data_invoiced(cr, uid, period_id, user_id,
                categ_ids, product_ids, pricelist_ids, context=context)
        
        # Obtiene las proporciones sobre cantidad, peso y monto
        quantity = (result['quantity'] * 100)/objective.quantity_min if objective.quantity_min > 0 else 100
        amount = (result['amount'] * 100)/objective.amount if objective.amount > 0 else 100
        weight = (result['weight'] * 100)/objective.weight if objective.weight > 0 else 100
        
        print "*******QUANTITY**********: ", quantity
        print "*******AMOUNT**********: ", amount
        print "*******WEIGTH**********: ", weight

        # Valida si el porcentaje es mayor o igual a las cantidades obtenidas
        if (quantity >= objective.commission_proportion_min or objective.quantity_min == 0.0) and (amount >= objective.commission_proportion_min or objective.amount == 0.0) and (weight >= objective.commission_proportion_min or objective.weight == 0.0):
            result['objective_complete'] = True
            # Obtiene el monto a pagar sobre la comision
            if objective.commission_type == 'currency':
                result['commission_amount'] = objective.commission_value
                result['resp_amount'] = objective.resp_commission_value
            else:
                # Paga comision en base a porcentaje
                result['commission_amount'] =  result['amount'] * (objective.commission_value / 100)
                # Comision a pagar a responsable de equipo sobre vendeor
                result['resp_amount'] =  result['amount'] * (objective.resp_commission_value / 100)
                
            print "*********COMMISSION_PROPORTION*****: ", objective.commission_proportion
            print "****COMMISSION_AMOUNT********: ", result['commission_amount']
            
            # Valida si el objetivo se paga proporcional al valor obtenido
            if objective.commission_proportion:
                prom = 0.0
                n = 0
                # Obtiene promedio en base a los criterios registrados
                if objective.weight > 0:
                    prom += weight
                    n += 1
                if objective.amount > 0:
                    prom += amount
                    n += 1
                if objective.quantity_min > 0:
                    prom += quantity
                    n += 1
                prom = prom/n if n > 0 else 0.0
                
                print "*******PROM********:", prom
                print "*******COMMISSION_TYPE******: ", objective.commission_type
                
                # Valida que el promedio no exceda el 100 porciento
                if (prom < 100) or (objective.commission_type == 'currency'):
                    # Calcula la proporcion de la comision a pagar
                    result['commission_amount'] = (result['commission_amount'] * prom)/100
                    result['resp_amount'] = (result['commission_amount'] * prom)/100
                    
                    print "****COMMISSION_AMOUNT_PROP********: ", result['commission_amount']
            
            # Validar si el objetivo se paga por porcentaje
            if objective.commission_type == 'percent':
                # Valida si el porcentaje es mayor o igual al porcentaje maximo del excedente
                if (quantity >= objective.commission_proportion_max or objective.quantity_min == 0.0) and (amount >= objective.commission_proportion_max or objective.amount == 0.0) and (weight >= objective.commission_proportion_max or objective.weight == 0.0):
                    # Paga comision en base a porcentaje sobre excedente
                    result['commission_amount'] +=  result['amount'] * (objective.commission_value_ext / 100)
                    print "****COMMISSION_AMOUNT_ext********: ", result['commission_amount']
        
        # Obtiene el porcentamje del monto a pagar
        result['percent'] = (result['commission_amount'] * 100)/ result['amount'] if result['amount'] else 0.0
        return result
    
    def _get_data_paid(self, cr, uid, period_id, user_id, paid_ids, context=None):
        """
            Ejecuta el query para el pago
        """
        string_query = ""
        amount = 0.0
        commission_amount = 0.0
        objective_complete = False
        line_paid = []
        
        paid_obj = self.pool.get('sale.commission.line.objective.paid')
        
        string_query = """
                    SELECT
                        sum(v.amount) as monto, (v.date - i.date_due) as dif_date
                    FROM
                        account_voucher as v
                        inner join account_voucher_line as vl on vl.voucher_id=v.id and vl.type='cr' and vl.amount>0.0
                        inner join account_move_line as ml on vl.move_line_id=ml.id
                        inner join account_move as m on m.id=ml.move_id
                        inner join account_invoice as i on i.move_id=m.id
                        inner join res_users as u on u.id=i.user_id
                    WHERE
                        v.type='receipt' 
                        and  v.period_id = %s
                        and u.id = %s
                    group by 
                        (v.date - i.date_due)
                    order by
                        (v.date - i.date_due)"""%(period_id,user_id)
        
        #print "*******CALCULANDO COMISION SOBRE PAGO***********", string_query
        # Se realiza el query para obtener el monto de los pagos y la diferencia de días entre el pago
        cr.execute(string_query)
        
        # Recorriendo la consulta
        for i in cr.fetchall():
            sale_amount = i[0] if i[0] is not None else 0.0
            diference_days = i[1] if i[0] is not None else 0.0
            
            # Valida que el monto sea mayor que cero
            if sale_amount == 0:
                continue
            
            res_paid = {
                'days': diference_days,
                'percent': 0.0,
                'amount': sale_amount,
                'amount_paid': 0.0,
            }
            
            # Obtiene monto total cobrado
            amount += sale_amount
            
            # Recorriendo la l?nea donde se encuentran los datos de validaci?n por pago
            for data_paid in paid_ids:
                # Se obtienen los datos de validaci?n para objetivo por pago
                day_percent = data_paid.percent
                # Se valida que la diferencia de días se encuentre dentro de los límites establecidos en el
                if diference_days <= data_paid.days and sale_amount > 0.0:
                    # Especifica el valor del descuento aplicado sobre la linea
                    res_paid['percent'] = day_percent
                    # Se obtiene el porcentaje sobre el porcentaje de la comisión
                    res_paid['amount_paid'] = (sale_amount * day_percent)/100
                    commission_amount += res_paid['amount_paid']
                    # Esto indica "objetivo cumplido"
                    objective_complete = True
                    break
                else:
                    # Elimina el registro que no se ocupa
                    if len(paid_ids) > 0:
                        paid_ids = paid_ids[1:]
            
            # Crea el nuevo registro del pago
            #paid_id = paid_obj.create(cr, uid, res_paid, context=context)
            #line_paid.append(paid_id)
            line_paid.append(res_paid)
        return line_paid, commission_amount, objective_complete, amount
    
    def _compute_paid(self, cr, uid, objective, user_id, period_id, context=None):
        """
            Realiza la validación del objetivo por pago. Regresará verdadero si el objetivo fué cumplido y el
            porcentaje de comisión correspondiente
        """
        line_paid = []
        paid_ids = objective.paid_ids
        
        result = {
                'weight': 0.0,
                'quantity': 0.0,
                'amount': 0.0,
                'percent': 0.0,
                'commission_amount': 0.0,
                'resp_amount': 0.0,
                'objective_complete': False,
                'paid_ids': 0
            }
        
        line_paid, result['commission_amount'], result['objective_complete'], result['amount'] = self._get_data_paid(cr,
                uid, period_id, user_id, paid_ids, context=context)
        #print "****LINE_PAID****: ", line_paid
        # Calcula el porcentaje a pagar de la comision al vendedor y al supervisor
        result['resp_amount'] = (result['commission_amount'] * objective.resp_commission_value)/100
        
        #print"*****commission_amount******: ", result['commission_amount']
        #print"******commission_value******: ", objective.commission_value
        
        result['commission_amount'] = (result['commission_amount'] * objective.commission_value)/100
        # Obtiene porcentaje sobre la comision 
        result['percent'] = (result['commission_amount'] * 100)/ result['amount'] if result['amount'] else 0.0
        
        # Se agrega la línea de dias de pago al diccionario
        result['paid_ids'] = [(0, 0, x) for x in line_paid]
        #print "****RESULT****: ", result
        return result
    
    def _compute_total(self, cr, uid, ids, field_name, args, context=None):
        """
            Calcula el total de todas las comisiones de los vendedores
        """
        total_commission = 0.0
        res = {}
        
        for commission in self.browse(cr, uid, ids, context=context):
            total_commission = 0.0
            if commission.line_ids:
                for line in commission.line_objective_ids:
                    total_commission += line.commission_amount
                res[commission.id] = total_commission
        return res
    
    def _calculate_commission(self, cr, uid, objective, parent_id, line, period_id, context=None):
        """
            Realiza el calculo de las comisiones
        """
        user_obj = self.pool.get('res.users')
        line_obj = self.pool.get('sale.commission.line')
        line_objective_obj = self.pool.get('sale.commission.line.objective')
        res = {}
        
        # Valida si hay un objetivo padre
        if parent_id:
            # Validar que cumpla con el objetivo padre
            line_objective_ids = line_objective_obj.search(cr, uid, [('objective_id','=',parent_id),('objective_complete','=',True)], context=context)
            if not line_objective_ids:
                return True
        
        
        # Revisamos el tipo de objetivo
        if objective.type == 'paid':
            # Calcula el objetivo sobre el pago
            res = self._compute_paid(cr, uid, objective, line.user_id.id or False, period_id, context=context)
        else:
            # Calcula el objetivo sobre lo facturado
            res = self._compute_invoiced(cr, uid, objective, line.user_id.id or False, period_id, context=context)
        #print "********** res ********** ", res
        
        # Crea un diccionario con la informacion calculada
        vals = {
           'name': objective.name,
           'objective_id': objective.id,
           'type': objective.type,
           'user_id': line.user_id.id or False,
           'commission_line_id': line.id,
           'commission_id': line.commission_id.id or False,
           'commission_type': objective.commission_type,
           'commission_value': objective.commission_value
        }
        # Agrega resultado sobre el objetivo
        vals.update(res)
        print "************* objetivo a crear *********** ", vals
        # Crea el nuevo registro del objetivo para el usuario
        line_objective_id = line_objective_obj.create(cr, uid, vals, context=context)
        
        
        # Si cumple con la condicion agrega al supervisor la comision
        if res.get('objective_complete', False) and line.section_id:
            # Valida que el equipo de ventas tenga un responsable
            resp_id = line.section_id.user_id.id or False
            #print "******* responsable ********** ", resp_id
            rline_ids = line_obj.search(cr, uid, [('user_id','=',resp_id),('commission_id','=',line.commission_id.id or False)])
            #print "********** lineas ************* ", rline_ids
            if rline_ids:
                vals['name'] = user_obj.browse(cr, uid, resp_id, context=context).name
                # Agrega la informacion del objetivo cumplido sobre la comision para el supervisor
                vals['commission_amount'] = vals.get('resp_amount',0.0)
                vals['commission_value'] = objective.resp_commission_value
                vals['commission_line_id'] = rline_ids[0]
                vals['type'] = 'response'
                #print "************* objetivo a crear (supervisor)*********** ", vals
                line_objective_id = line_objective_obj.create(cr, uid, vals, context=context)
                #print "*********** linea obj creado (supervisor) ******** ", line_objective_id
        return True
    
    def _split_period(self, period_name):
        month, year = period_name[:2].lower(), period_name[2:].replace('/', '')
        return month, year
    
    def get_version(self, cr, uid, period_id, context=None):
        """
            Se valida y se obtiene la version sobre el cual se van a calcular las versiones
        """
        version_obj = self.pool.get('sale.commission.objective.version')
        
        # Obtiene la version para generar el calculo por periodo
        version_ids = version_obj.search(cr, uid, [('period_id', '=', period_id),('active','=',True)])
        
        # Valida que haya una version activa
        if not version_ids:
            # Buscamos si hay una version por ejercicio fiscal
            fiscalyear_id = self.pool.get('account.period').read(cr, uid, period_id, ['fiscalyear_id'])['fiscalyear_id']
            version_ids = version_obj.search(cr, uid, [('fiscalyear_id', '=', fiscalyear_id),('active', '=', True)])
        # Valida que haya alguna version para calcular la comision
        if not version_ids:
            raise osv.except_osv(_('Error!'),_("No hay versiones activas para calcular la comision, para continuar genere una nueva version de objetivo desde la parte de configuracion."))
        return version_ids[0]
    
    def create_commission(self, cr, uid, period_id, context=None):
        """
            Crea la nueva comision sobre el periodo seleccionado
        """
        line_obj = self.pool.get('sale.commission.line')
        user_obj = self.pool.get('res.users')
        line_ids = []
        res = {}
        
        # Valida que no haya comisiones abiertas sobre el periodo
        comm_ids = self.search(cr, uid, [('period_id', '=', period_id),('state','in',['open','paid'])])
        if comm_ids:
            raise osv.except_osv(_('Error!'),_("No se puede calcular la comision, porque ya existen comisiones confirmadas para este periodo."))
        
        # Valida si hay comisiones en borrador
        comm_ids = self.search(cr, uid, [('period_id','=',period_id),('state','=','draft')])
        if comm_ids:
            # Elimina las comisiones en borrador
            self.unlink(cr, uid, comm_ids, context=context)
        
        result = {
            'period_id': period_id,
        }
        comm_id = self.create(cr, uid, result, context=context)
        
        # Obtiene a los vendedores que aplican en comision
        user_ids =  user_obj.search(cr, uid, [('commission_apply', '=', True)], context=context)
        #print "************ user_ids ********* ", user_ids
        # Crea una linea por vendedor sobre la comision
        for user in self.pool.get('res.users').browse(cr, uid, user_ids, context=context):
            vals = {
                'name': user.name,
                'user_id': user.id,
                'commission_id': comm_id
            }
            #print "************** vals ********** ", vals
            line_id = line_obj.create(cr, uid, vals, context=context)
            line_ids.append(line_id)
            
        #print "*********LINE_IDS**********: ", line_ids
        #print "*********COMM_ID**********: ", comm_id
        return comm_id
    
    def confirm(self, cr, uid, ids, context=None):
        """
            Se confirma la comision y crea el archivo con el cual se realiza la conexion con el
            programa que calcula la nomina
        """
        print "****CONFIRMANDO LA COMISION*****"
        for commission in self.browse(cr, uid, ids, context=context):
            name = commission.name
            period_name = commission.period_id.name
            date = commission.date
            
            month, year = self._split_period(period_name)
            print "*****MONTH*****: ", month
            print "*****YEAR******: ", year
            # Creando archivo que leera el programa que calcula la nomina
            with codecs.open("/home/open/openerp/comision_%s_%s.txt"%(month, year,), 'w',
                encoding='utf-8') as file_commission:
                file_commission.write("""
                                       Nombre:  %s  Periodo: %s  Fecha: %s
                                      """%(name, period_name, date,))
            file_commission.close()
            # Obteniendo la linea de las comision calculada
            for line in commission.line_ids:
                user_name = line.user_id.name
                amount_paid = line.amount_paid
                amount_invoiced = line.amount_invoiced
                total = line.total
                
                # print "*****USER_NAME***: ", user_name
                
                with codecs.open("/home/open/openerp/comision_%s_%s.txt"%(month, year,),
                    'a', encoding='utf-8') as file_commission:
                    string_writting = """
                                           %s    |   %s   |   %s   |   %s
                                          """%(user_name, amount_paid, amount_invoiced, total)
                    # print "****STRING_WRITING***: ", string_writting
                    # string_decode = unicode(string_writing)
                    file_commission.write(string_writting)
                file_commission.close()
            
        
        return True
    
    
    def _get_commission_sale(self, cr, uid, version_id, line, period_id, context=None):
        """
            Obtiene la comision del vendedor en base a los objetivos que aplican sobre la version
        """
        # Hace referencia a los objetivos generales
        object_obj = self.pool.get('sale.commission.objective')
        # Hace referencia a la línea de versiones de la comision
        vline_obj = self.pool.get('sale.commission.objective.version.line')
        
        # Busca los objetivos que aplican sobre el vendedor en la version
        vobj_id = vline_obj.search(cr, uid, [('version_id','=',version_id),('section_id','=',line.section_id.id or False),'|',
            ('user_id','=',line.user_id.id or False),('user_id','=',False)])
        
        # Recorre los objetivos
        for vline in vline_obj.browse(cr, uid, vobj_id, context=context):
            #print "************* valida secuencia **************** ", vline.sequence
            # Calcula el objetivo y registra los resultados
            self._calculate_commission(cr, uid, vline.objective_id, vline.objective_parent_id.id or False, line, period_id, context=context)
        return True
    
    def _update_after_commission_line_objective_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Busca las comisiones relacionadas a los objetivos modificados
        """
        if type(ids) != type([]):
            ids = [ids]
        list_ids = []
        res = []
        for id in ids:
            list_ids.append(str(id))
        # Obtiene la lista de ids relacionados a los objetivos modificados
        string_query = """
                    SELECT
                        commission_id
                    FROM
                        sale_commission_line_objective
                    WHERE
                        id in (%s)
                    group by 
                        commission_id"""%(",".join(list_ids))
        cr.execute(string_query)
        # Recorriendo la consulta
        for i in cr.fetchall():
            res.append(i[0])
        return res
    
    _store_line = {
        'sale.commission': (lambda self,cr,uid,ids,context: ids,['line_objective_ids','line_ids'],10), 
        'sale.commission.line.objective': (_update_after_commission_line_objective_change, ['apply','commission_amount','commission_complete','commision_id','commission_line_id'], 10),
    }
    
    _columns = {
        'name': fields.char('Nombre', required=True),
        'date': fields.datetime('Fecha'),
        'period_id': fields.many2one('account.period', 'Periodo', required=True),
        'total': fields.function(_compute_total, type='float', digits_compute=dp.get_precision('Account'), string='Total', store=_store_line, method=True),
        'state': fields.selection(state_commission, 'Estado'),
        'line_ids': fields.one2many('sale.commission.line', 'commission_id', 'Vendedores'),
        'line_objective_ids': fields.one2many('sale.commission.line.objective', 'commission_id', 'Objetivos'),
        'active': fields.boolean('Activo'),
        'note': fields.text('Nota')
    }
    
    _defaults = {
        'state': 'draft',
        'date': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        'active': True,
        'name': lambda x, y, z, c: x.pool.get('ir.sequence').get(y, z, 'sale.commission.commission') or '/'
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Referencia unica al nombre')
    ]

sale_commission_commission()

class sale_commission_line(osv.Model):
    _name = 'sale.commission.line'    
    
    def _compute_all(self, cr, uid, ids, fields_name, args, context=None):
        """
            Calcula el total de todas las comisiones
        """
        res = {}
        # Recorre las lineas de comision
        for commission in self.browse(cr, uid, ids, context=context):
            # Inicializa variables
            total_complete = total_incomplete = 0
            total_paid = total_invoiced = total = 0.0
            #print "******** detalles comision ******** ", commission.line_objective_ids
            # Valida si hay detalles de comision
            if commission.line_objective_ids:
                for line in commission.line_objective_ids:
                    # Si el objetivo no aplica se descarta
                    if line.apply == False:
                        continue
                    # Se contabilizan los objetivos cumplidos
                    if line.objective_complete is True:
                        total_complete += 1
                    # Se contabilizan los objetivos no cumplidos
                    if line.objective_complete is False:
                        total_incomplete += 1
                    if line.type == 'paid':
                        # Suma de la cantidad pagada
                        total_paid += line.commission_amount
                    else:
                        # Suma de la cantidad vendida
                        total_invoiced += line.amount
                    # Total comission
                    total += line.commission_amount
                
            # Actualiza resultados obtenidos
            res[commission.id] = {
                'objective_complete': total_complete,
                'objective_not_complete': total_incomplete,
                'amount_invoiced': total_invoiced,
                'amount_paid': total_paid,
                'total': total
            }
        return res

    def _update_after_commission_line_objective_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Busca las comisiones relacionadas a los objetivos modificados
        """
        if type(ids) != type([]):
            ids = [ids]
        list_ids = []
        res = []
        for id in ids:
            list_ids.append(str(id))
        # Obtiene la lista de ids relacionados a los objetivos modificados
        string_query = """
                    SELECT
                        commission_line_id
                    FROM
                        sale_commission_line_objective
                    WHERE
                        id in (%s)
                    group by 
                        commission_line_id"""%(",".join(list_ids))
        cr.execute(string_query)
        # Recorriendo la consulta
        for i in cr.fetchall():
            res.append(i[0])
        return res
    
    _store_line = {
        'sale.commission.line': (lambda self,cr,uid,ids,context: ids,['line_objective_ids'],10), 
        'sale.commission.line.objective': (_update_after_commission_line_objective_change, ['apply','commission_amount','commission_complete','commision_line_id'], 10),
    }
    
    _columns = {
        'name': fields.char('Vendedor'),
        'user_id': fields.many2one('res.users', 'Vendedor', required=True),
        'section_id': fields.related('user_id', 'default_section_id', relation="crm.case.section", type='many2one',  string='Equipo de ventas', store=True),
        'amount_paid': fields.function(_compute_all, type='float', digits_compute=dp.get_precision('Account'), string='Monto Cobrado', store=_store_line, method=True, multi='comm'),
        'amount_invoiced': fields.function(_compute_all, type='float', digits_compute=dp.get_precision('Account'), string='Monto vendido', store=_store_line, method=True, multi='comm'),
        'total': fields.function(_compute_all, type='float', digits_compute=dp.get_precision('Account'), string='Total a Pagar', store=_store_line, method=True, multi='comm'),
        'objective_complete': fields.function(_compute_all, type='integer', string='Objetivos cumplidos', store=_store_line, multi='comm'),
        'objective_not_complete': fields.function(_compute_all, type='integer', string='Objetivos no cumplidos', store=_store_line, multi='comm'),
        'commission_id': fields.many2one('sale.commission.commission', 'Comisión calculada', ondelete="cascade"),
        'period_id': fields.related('commission_id', 'period_id', relation="account.period", type='many2one', string='Periodo', store=True),
        'line_objective_ids': fields.one2many('sale.commission.line.objective', 'commission_line_id', 'Detalle de objetivos'),
        'note': fields.text('Nota')
    }

sale_commission_line()

class sale_commission_line_objective(osv.Model):
    _name = 'sale.commission.line.objective'

    def action_apply(self, cr, uid, ids, context=None):
        """
            Pone el estado como aplicado
        """
        return self.write(cr, uid, ids, {'apply': True}, context=context)
    
    def action_not_apply(self, cr, uid, ids, context=None):
        """
            Pone el estado como no aplicado
        """
        return self.write(cr, uid, ids, {'apply': False}, context=context)

    def _update_after_commission_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        """
            Obtiene los ids relacionados con la comision
        """
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('sale.commission.line.objective').search(cr, uid, [('commission_id','in',ids)]) or []
    
    _store_state = {
        'sale.commission.line.objective': (lambda self,cr,uid,ids,context: ids,['commission_id','commission_line_id'],10), 
        'sale.commission.commission': (_update_after_commission_change, ['state'], 10),
    }
    
    def action_redirect_objective(self, cr, uid, ids, context=None):
        """
            Redirecciona al objetivo general de donde se obtuvo el registro
        """
        # Obtiene el objeto a cargar
        line_objective_ids = self.browse(cr, uid, ids[0], context=context)
        
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_commission',
                'sale_commission_objective_form_view')
        
        return {
            'name':_("Objetivo"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'sale.commission.objective',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {'not_edit': True},
            'res_id': line_objective_ids.objective_id.id or False
        }
    

    _columns = {
        'name': fields.char('Objetivo'),
        'objective_id': fields.many2one('sale.commission.objective', 'Objetivo'),
        'type': fields.selection([
            ('response', 'Comision Supervisor'),
            ('invoiced', 'Facturado'),
            ('paid', 'Pagado')], 'Tipo'),
        'objective_complete': fields.boolean('Cumplido'),
        'commission_type': fields.selection([
            ('currency', '$'),
            ('percent', '%')], 'Comisión en:'),
        'commission_value': fields.float('Comisión vendedor'),
        'amount': fields.float('Monto'),
        'percent': fields.float('Porcentaje pagado'),
        'weight': fields.float('Peso'),
        'quantity': fields.float('Cantidad'),
        'commission_amount': fields.float('Comision a pagar'),
        'commission_line_id': fields.many2one('sale.commission.line', 'Linea de calculo de comisión', ondelete="cascade"),
        'commission_id': fields.many2one('sale.commission.commission', 'Comision', ondelete="cascade"),
        'user_id': fields.many2one('res.users', 'Vendedor'),
        'apply': fields.boolean('Aplicar'),
        'state': fields.related('state', 'commission_id', selection=state_commission, type="selection", string="Estado comision", store=_store_state),
        'paid_ids': fields.one2many('sale.commission.line.objective.paid', 'objective_id', 'Pagos'),
    }
    
    _defaults = {
        'apply': True,
        'type': 'response',
        'objective_complete': False
    }

sale_commission_line_objective()

class sale_commission_line_obective_paid(osv.Model):
    _name = 'sale.commission.line.objective.paid'
    
    _columns = {
        'objective_id': fields.many2one('sale.commission.line.objective', 'Detalle de objetivo'),
        'days': fields.integer('Días'),
        'percent': fields.float('Porcentaje', digits=(2, 3)),
        'amount': fields.float('Monto cobrado'),
        'amount_paid': fields.float('Monto pagado'),
    }
    
sale_commission_line_obective_paid()