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

from openerp.osv import osv, fields
from tools.translate import _
import base64
import pooler
from time import strftime
from string import upper
from string import join
import datetime
import tempfile
import os
from dateutil.relativedelta import *
import csv

class wizard_account_diot_mx(osv.osv_memory):
    _name = 'account.diot.report'
    _description = 'Account - DIOT Report for Mexico'

    _columns = {
        'name': fields.char('Nombre del archivo', readonly=True),
        'company_id': fields.many2one('res.company', 'Compañia', required=True),
        'period_id': fields.many2one('account.period', 'Periodo', help='Seleccionar peridoo', required=True),
        'filename': fields.char('Nombre del archivo', size=128, readonly=True, help='Este es el nombre del archivo'),
        'file': fields.binary('Archivo', readonly=True),
        'state': fields.selection([('choose', 'Escojer'), ('get', 'Obtener'), ('not_file', 'Sin archivo')]),
    }

    _defaults = {
        'state': 'choose',
    }
 
    def default_get(self, cr, uid, fields, context=None):
        """
            Obtiene la compañia del usuario y el periodo anterior al actual
        """
        data = super(wizard_account_diot_mx, self).default_get(cr, uid,
            fields, context=context)
        time_now = datetime.date.today()+relativedelta(months=-1)
        company_id = self.pool.get('res.company')._company_default_get(cr, uid,
            'account.diot.report', context=context)
        period_id = self.pool.get('account.period').search(cr, uid,
            [('date_start', '<=', time_now),
            ('date_stop', '>=', time_now),
            ('company_id', '=', company_id)])
        if period_id:
            data.update({'company_id': company_id,
                        'period_id': period_id[0]})
        return data
    
    def get_config_diot(self, cr, uid, context=None):
        """
            Obtiene la configuracion de los codigos fiscales que afectan la perdida/utilidad
        """
        config_id = False
        res = {
            'diot_account_id1': False,
            'diot_account_id2': False,
            'diot_account_id3': False,
            'diot_account_id4': False,
            'diot_account_id5': False,
            'diot_account_id6': False,
            'diot_account_id7': False,
            'diot_account_id8': False,
            'diot_account_id9': False,
            'diot_account_id10': False,
            'diot_account_id11': False,
            'diot_account_id12': False,
            'diot_account_id13': False,
            'diot_account_id14': False,
            'diot_account_id15': False,
        }
        cr.execute(
            """ select max(id) as id
                from account_diot_config_settings 
                limit 1 """)
        dat = cr.dictfetchall()
        config_id = dat and dat[0]['id'] or False

        # Obtiene la configuracion de la utilidad
        if config_id:
            config = self.pool.get('account.diot.config.settings').browse(cr, uid, config_id, context=context)
            res['diot_account_id1'] = config.diot_account_id1.id or False
            res['diot_account_id2'] = config.diot_account_id2.id or False
            res['diot_account_id3'] = config.diot_account_id3.id or False
            res['diot_account_id4'] = config.diot_account_id4.id or False
            res['diot_account_id5'] = config.diot_account_id5.id or False
            res['diot_account_id6'] = config.diot_account_id6.id or False
            res['diot_account_id7'] = config.diot_account_id7.id or False
            res['diot_account_id8'] = config.diot_account_id8.id or False
            res['diot_account_id9'] = config.diot_account_id9.id or False
            res['diot_account_id10'] = config.diot_account_id10.id or False
            res['diot_account_id11'] = config.diot_account_id11.id or False
            res['diot_account_id12'] = config.diot_account_id12.id or False
            res['diot_account_id13'] = config.diot_account_id13.id or False
            res['diot_account_id14'] = config.diot_account_id14.id or False
            res['diot_account_id15'] = config.diot_account_id15.id or False
        return res
    
    def create_diot(self, cr, uid, ids, context=None):
        """
            Generacion del archivo del reporte DIOT
        """
        if context is None:
            context = {}
        acc_move_line_obj = self.pool.get('account.move.line')
        acc_tax_obj = self.pool.get('account.tax')
        acc_tax_category_obj = self.pool.get('account.tax.category')
        code_obj = self.pool.get('account.tax.code')
        this = self.browse(cr, uid, ids[0], context=context)
        period = this.period_id
        
        # Obtiene los codigos de impuesto de la configuracion, con los que se va a calcular el resultado
        config = self.get_config_diot(cr, uid, context=context)
        
        #print******************** configuracion diot **************** ", config
        
        # Recorre los registros de los codigos configurados para obtener un resultado de los codigos a utilizar sobre los 
        config_ids = []
        config_res = {}
        for conf in config:
            #print********************** config *********** ", conf
            # Agrupa y ordena la informacion de las cuentas configuradas para la DIOT
            if config[conf]:
                config_ids.append(config[conf])
                
                if not config_res.get(config[conf], False):
                    config_res[config[conf]] = []
                
                # Valida si no tiene hijos relacionados
                code_ids = code_obj.search(cr, uid, [('parent_id','=', config[conf])], context=context)
                if code_ids:
                    for code in code_ids:
                        config_ids.append(code)
                        if not config_res.get(code, False):
                            config_res[code] = []
                        config_res[code].append(conf)
                
                # Invierte el valor de las cuentas
                config_res[config[conf]].append(conf)
        
        # Obtiene los impuestos que son para las compras
        #tax_purchase_ids = acc_tax_obj.search(cr, uid, [('type_tax_use', '=', 'purchase'),], context=context)
        #tax_purchase = ",".join(tax_purchase_ids)
        
        # Consulta para obtener la base de los movmientos registrados sobre el sistema
        #cr.execute('SELECT line.tax_code_id, line.base, line.partner_id \
        #            FROM account_move_line AS line, \
        #            account_move AS move, \
        #            account_tax_code AS code \
        #            WHERE code.id IN (%s) '+where+' \
        #            AND move.id = line.move_id',
        #               (tax_purchase,))
        #res=dict(cr.fetchall())
        ##print************************ res ***************** ", res
        
        matrix_row = []
        amount_exe = 0
        
        move_lines_diot = acc_move_line_obj.search(cr, uid, [
            ('period_id', '=', period.id),
            ('tax_code_id', 'in', config_ids)])
        dic_move_line = {}
        partner_ids_to_fix = []
        moves_without_partner = []
        partner_ids_tax_0 = []
        #print***************** movimientos de impuestos ********************** ", move_lines_diot
        
        # Recorre los registros y valida que no haya movimientos sin un proveedor asignado
        for items in acc_move_line_obj.browse(cr, uid, move_lines_diot, context=context):
            if not items.partner_id:
                moves_without_partner.append(items.id)
                
        #print***************** movimientos sin proveedor ****************** ", moves_without_partner
        if moves_without_partner:
            return {
                'name': 'Moves without supplier',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move.line',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', moves_without_partner), ],
            }
        
        # Recorrre los movimientos disponibles
        for line in acc_move_line_obj.browse(cr, uid, move_lines_diot, context=context):
            partner_id = line.partner_id
            partner_vat = upper((partner_id.rfc or '').replace('-', '')
                                .replace('_', '').replace(' ', ''))
            
            # Valida que el proveedor tenga la informacion completa
            if not partner_vat \
                or not partner_id.type_of_third \
                or not partner_id.type_of_operation \
                or (partner_id.type_of_third == '05' and not partner_id.country_of_residence) \
                or (partner_id.type_of_third == '04' and not self.pool.get('res.partner').check_vat_mx(partner_vat)):
                partner_ids_to_fix.append(partner_id.id)
            if partner_ids_to_fix:
                continue
            
            # Si no se a registrado al proveedor en la lista del archivo resultante se inicializan valores
            if not dic_move_line.get(partner_id.id, False) and partner_id.type_of_third != '15':
                dic_move_line[partner_id.id] = {
                       'type_of_third': partner_id.type_of_third,
                       'type_of_operation': partner_id.type_of_operation,
                       'vat': partner_vat if partner_id.type_of_third != '05' else '',
                       'number_id_fiscal': str(partner_id.number_fiscal_id) if partner_id.type_of_third == '05' else '',
                       'foreign_name': str(partner_id.foreign_name) if partner_id.type_of_third == '05' else '',
                       'country_of_residence': str(partner_id.country_of_residence) if partner_id.type_of_third == '05' else '',
                       'nationality': str(partner_id.nationality) if partner_id.type_of_third == '05' else '',
                       'diot_account_id1': 0.0,
                       'diot_account_id2': 0.0,
                       'diot_account_id3': 0.0,
                       'diot_account_id4': 0.0,
                       'diot_account_id5': 0.0,
                       'diot_account_id6': 0.0,
                       'diot_account_id7': 0.0,
                       'diot_account_id8': 0.0,
                       'diot_account_id9': 0.0,
                       'diot_account_id10': 0.0,
                       'diot_account_id11': 0.0,
                       'diot_account_id12': 0.0,
                       'diot_account_id13': 0.0,
                       'diot_account_id14': 0.0,
                       'diot_account_id15': 0.0,
               }
            # Valida que no sea una validacion de un tercero
            elif partner_id.type_of_third == '15' and not dic_move_line.get(0, False):
                dic_move_line[0] = {
                       'type_of_third': partner_id.type_of_third,
                       'type_of_operation': partner_id.type_of_operation,
                       'vat': '',
                       'number_id_fiscal': '',
                       'foreign_name': '',
                       'country_of_residence': '',
                       'nationality': '',
                       'diot_account_id1': 0.0,
                       'diot_account_id2': 0.0,
                       'diot_account_id3': 0.0,
                       'diot_account_id4': 0.0,
                       'diot_account_id5': 0.0,
                       'diot_account_id6': 0.0,
                       'diot_account_id7': 0.0,
                       'diot_account_id8': 0.0,
                       'diot_account_id9': 0.0,
                       'diot_account_id10': 0.0,
                       'diot_account_id11': 0.0,
                       'diot_account_id12': 0.0,
                       'diot_account_id13': 0.0,
                       'diot_account_id14': 0.0,
                       'diot_account_id15': 0.0,
               }
            
            # Valida que la fecha del movimiento coincida con las fechas del periodo
            if line.date >= period.date_start and line.date <= period.date_stop:
                # Valida si el proveedor es global
                if partner_id.type_of_third == '15':
                    #print********* proveedor ************ ", dic_move_line[0]
                    #print********* codigo impuesto id ************ ", line.tax_code_id.id
                    
                    # Actualiza la informacion del proveedor en base a lo capturado para proveedores globales
                    for reg in config_res[line.tax_code_id.id]:
                        # Valida que el proveedor no agregue registros sobre los campos que no requiere para proveedores globales
                        if reg in ['diot_account_id7','diot_account_id8','diot_account_id9','diot_account_id10','diot_account_id11']:
                            continue
                        dic_move_line[0][reg] += line.base
                elif partner_id.type_of_third == '05':
                    #print********* proveedor ************ ", dic_move_line[partner_id.id]
                    #print********* codigo impuesto id ************ ", line.tax_code_id.id
                    
                    # Actualiza la informacion del proveedor en base a lo capturado
                    for reg in config_res[line.tax_code_id.id]:
                        # Valida que el proveedor no agregue registros sobre los campos que no requiere para proveedores extranjeros
                        if reg in ['diot_account_id1','diot_account_id2','diot_account_id3','diot_account_id4','diot_account_id5','diot_account_id6','diot_account_id13']:
                            continue
                        dic_move_line[partner_id.id][reg] += line.base
                else:
                    #print********* proveedor ************ ", dic_move_line[partner_id.id]
                    #print********* codigo impuesto id ************ ", line.tax_code_id.id
                    
                    # Actualiza la informacion del proveedor en base a lo capturado
                    for reg in config_res[line.tax_code_id.id]:
                        # Valida que el proveedor no agregue registros sobre los campos que no requiere para proveedores nacionales
                        if reg in ['diot_account_id7','diot_account_id8','diot_account_id9','diot_account_id10','diot_account_id11']:
                            continue
                        dic_move_line[partner_id.id][reg] += line.base
        #print********** proveedores sin la informacion completa ************ ", partner_ids_to_fix
        # Valida que no haya contactos por reparar
        if partner_ids_to_fix:
            return {
                'name': 'Proveedores que no tienen la informacion necesaria '
                'para la DIOT',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'res.partner',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', partner_ids_to_fix), '|', ('active', '=', False), ('active', '=', True)],
            }
        
        #print************ informacion diot ***************** ", dic_move_line
        
        # Genera el nuevo archivo con la informacion de la diot
        (fileno, fname) = tempfile.mkstemp('.csv', 'tmp')
        os.close(fileno)
        f_write = open(fname, 'wb')
        fcsv = csv.DictWriter(f_write, [
            'type_of_third', 
            'type_of_operation',
            'vat', 
            'number_id_fiscal', 
            'foreign_name',
            'country_of_residence', 
            'nationality',
            'valor_de_actos_o_actividades_pagadas_a_la_tasa_del_15_o_16_de_iva',
            'valor_de_actos_o_actividades_pagadas_a_la_tasa_del_15_de_iva',
            'monto_del_iva_pagado_no_acreditable_a_la_tasa_del_15_o_16',
            'valor_de_actos_o_actividades_pagados_a_la_tasa_del_10_u_11_de_iva',
            'valor_de_actos_o_actividades_pagados_a_la_tasa_del_10_de_iva',
            'monto_del_iva_pagado_no_acreditable_a_la_tasa_del_10_u_11',
            'valor_de_los_actos_o_actividades_pagadas_en_la_importacion_de_bienes_y_servicios_a_la_tasa_del_15_o_16_del_iva',
            'monto_del_iva_pagado_no_acreditable_por_la_importacion_de_bienes_y_servicios_a_la_tasa_de_15_o_16_de_iva',
            'valor_de_los_actos_o_actividades_pagados_en_la_importacion_de_bienes_y_servicios_a_la_tasa_del_10_u_11_de_iva',
            'monto_del_iva_pagado_no_acreditable_por_la_importacion_a_la_tasa_del_10_u_11',
            'valor_de_los_actos_o_actividades_pagadas_en_la_importacion_de_bienes_y_servicios_por_los_que_no_se_pagara_el_iva',
            'valor_de_los_demas_actos_o_actividades_pagados_a_la_tasa_de_0_de_iva',
            'valor_de_los_actos_o_actividades_pagados_por_los_que_no_se_pagara_iva',
            'iva_retenido_por_el_contribuyente',
            'iva_correspondiente_a_las_devoluciones_descuentos_y_bonificaciones_sobre_compras',
            'no_aplica',], delimiter='|')
        
        def get_value_result(value):
            if value == 0:
                return ''
            else:
                return value
        
        # Recorre los registros y los agrega al archivo
        for diot in dic_move_line:
            remnant = 0
            values_diot = dic_move_line.get(diot, False)
            
            # Valida que el saldo del iva pagado no sea negativo, de ser negativo pasa el valor a cancelaciones y descuentos
            iva_account1 = int(round((values_diot['diot_account_id1']), 0))
            if iva_account1 < 0:
                remnant += (iva_account1 * -1)
                iva_account1 = 0
            # Valida que el saldo del iva de importaciones no sea negativo, de ser negativo pasa el valor a cancelaciones y descuentos
            iva_account7 = int(round((values_diot['diot_account_id7']), 0))
            if iva_account7 < 0:
                remnant += (iva_account7 * -1)
                iva_account7 = 0
            
            fcsv.writerow(
                {
                   'type_of_third': values_diot['type_of_third'],
                   'type_of_operation': values_diot['type_of_operation'],
                   'vat': values_diot['vat'],
                   'number_id_fiscal': values_diot['number_id_fiscal'],
                   'foreign_name': values_diot['foreign_name'],
                   'country_of_residence': values_diot['country_of_residence'],
                   'nationality': values_diot['nationality'],
                   'valor_de_actos_o_actividades_pagadas_a_la_tasa_del_15_o_16_de_iva': get_value_result(iva_account1),
                   'valor_de_actos_o_actividades_pagadas_a_la_tasa_del_15_de_iva': get_value_result(int(round((values_diot['diot_account_id2']), 0))),
                   'monto_del_iva_pagado_no_acreditable_a_la_tasa_del_15_o_16': get_value_result(int(round((values_diot['diot_account_id3']), 0))),
                   'valor_de_actos_o_actividades_pagados_a_la_tasa_del_10_u_11_de_iva': get_value_result(int(round((values_diot['diot_account_id4']), 0))),
                   'valor_de_actos_o_actividades_pagados_a_la_tasa_del_10_de_iva': get_value_result(int(round((values_diot['diot_account_id5']), 0))),
                   'monto_del_iva_pagado_no_acreditable_a_la_tasa_del_10_u_11': get_value_result(int(round((values_diot['diot_account_id6']), 0))),
                   'valor_de_los_actos_o_actividades_pagadas_en_la_importacion_de_bienes_y_servicios_a_la_tasa_del_15_o_16_del_iva': get_value_result(iva_account7),
                   'monto_del_iva_pagado_no_acreditable_por_la_importacion_de_bienes_y_servicios_a_la_tasa_de_15_o_16_de_iva': get_value_result(int(round((values_diot['diot_account_id8']), 0))),
                   'valor_de_los_actos_o_actividades_pagados_en_la_importacion_de_bienes_y_servicios_a_la_tasa_del_10_u_11_de_iva': get_value_result(int(round((values_diot['diot_account_id9']), 0))),
                   'monto_del_iva_pagado_no_acreditable_por_la_importacion_a_la_tasa_del_10_u_11': get_value_result(int(round((values_diot['diot_account_id10']), 0))),
                   'valor_de_los_actos_o_actividades_pagadas_en_la_importacion_de_bienes_y_servicios_por_los_que_no_se_pagara_el_iva': get_value_result(int(round((values_diot['diot_account_id11']), 0))),
                   'valor_de_los_demas_actos_o_actividades_pagados_a_la_tasa_de_0_de_iva': get_value_result(int(round((values_diot['diot_account_id12']), 0))),
                   'valor_de_los_actos_o_actividades_pagados_por_los_que_no_se_pagara_iva': get_value_result(int(round((values_diot['diot_account_id13']), 0))),
                   'iva_retenido_por_el_contribuyente': get_value_result(int(round((values_diot['diot_account_id14']), 0))),
                   'iva_correspondiente_a_las_devoluciones_descuentos_y_bonificaciones_sobre_compras': get_value_result(int(round((values_diot['diot_account_id15']), 0)) + remnant),
                   'no_aplica': ''
               })
        f_write.close()
        f_read = file(fname, "rb")
        fdata = f_read.read()
        #print********* archivo nombre ************ ", fname
        #print********* informacion de csv ******** ", fdata
        out = base64.encodestring(fdata)
        name = "%s-%s-%s.txt" % ("OPENERP-DIOT", this.company_id.name, strftime('%Y-%m-%d'))
        #print********** name ************ ", name
        f_read.close()
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['time_unit', 'measure_unit'])
        res = res and res[0] or {}
        datas['form'] = res
        if out:
            state = 'get'
        else:
            state = 'not_file'
        #print*********** out *********** ", out
        #print******** state ******** ", state
        self.write(cr, uid, ids, {'state': state,
                                'file': out,
                                'filename': name
                                }, context=context)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'res_model': 'account.diot.report',
            'target': 'new',
        }

wizard_account_diot_mx()