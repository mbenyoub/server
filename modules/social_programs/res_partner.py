# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Ivan Serrano Saldaña <riss_600@hotmail.com>"
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

from openerp.osv import fields,osv

class res_partner(osv.osv):
    """ Herencia sobre los contactos para agregar informacion de beneficiarios """
    _inherit = 'res.partner'
    
    def onchange_settlement(self, cr, uid, ids, settlement_id, context=None):
        """
            Obtiene la informacion de ciudad, estado, pais, CP, etc... en base a la colonia seleccionada
        """
        if settlement_id:
            settlement = self.pool.get('social.programs.res.settlement').browse(cr, uid, settlement_id, context)
            if settlement.id:
                state = self.pool.get('res.country.state').browse(cr, uid, settlement.city_id.state_id.id, context)
                return {'value':{
                            'country_id': state.country_id.id,
                            'state_id': state.id,
                            'city_id': settlement.city_id.id,
                            'city': settlement.city_id.name,
                            'area_id': settlement.area_id.id,
                            'sector_id': settlement.sector_id.id,
                            'zip': settlement.zip}}
        return {}
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
            Limpia el curp al momento de duplicar el campo
        """
        if default is None:
            default = {}
        default.update({'curp': '', 'copy': True, 'program_ids': {}, 'delivery_ids': {}, 'program_id':None})
        
        # Continua con la funcionalidad original
        return super(res_partner, self).copy(cr, uid, id, default, context)

    def _program_count(self, cr, uid, ids, field_name, arg, context=None):
        """
            Obtiene la cantidad de programas activos en los que se encuentra el beneficiario
        """
        res = {}
        partner_programs = {}
        # Recorre los partner para obtener la cantidad de programas por el beneficiario
        for partner in self.browse(cr, uid, ids, context=context):
            #print "***************** programs ******************************* ", partner.program_ids
            res[partner.id] = {
                'program_count': 0,
                'program_count_total': 0,
            }
            program_id = 0
            # Recorre los programas y cuenta los que no estan terminados
            for program in partner.program_ids:
                res[partner.id]['program_count_total'] += 1
                # Si esta activo el programa contabiliza el valor
                if program.state == 'confirm':
                    res[partner.id]['program_count'] += 1
                    program_id = program.id
            # Agrupa los beneficiaros por programa
            if not partner_programs.get(program_id):
                partner_programs[program_id] = []
            partner_programs[program_id].append(partner.id)
        # Actualiza el campo que indica el programa en el que se encuentra el beneficiario
        for program_id in partner_programs.keys():
            partners_ids = partner_programs[program_id]
            print "***************** update program ********** ", program_id, "  ", partners_ids
            # Actualiza los programas de los beneficiarios
            if int(program_id):
                self.write(cr, uid, partners_ids, {'program_id': int(program_id)}, context=context)
            else:
                # Si no tiene programa deja sin valor
                self.write(cr, uid, partners_ids, {'program_id': None}, context=context)
        return res
    
    def _entry_additional_qty(self, cr, uid, ids, field_name, arg, context=None):
        """
            Calcula el total mensual otorgado en ingresos extra
        """
        res = {}
        # Recorre los partner para obtener la cantidad otorgada
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = 0.0
            # Contabiliza los montos
            if partner.entry_additional_parent:
                res[partner.id] += partner.entry_additional_parent_qty
            if partner.entry_additional_son:
                res[partner.id] += partner.entry_additional_son_qty
            if partner.entry_additional_retirement:
                res[partner.id] += partner.entry_additional_retirement_qty
            if partner.entry_additional_family:
                res[partner.id] += partner.entry_additional_family_qty
            if partner.entry_additional_government:
                res[partner.id] += partner.entry_additional_government_qty
        return res

    _columns = {
        'beneficiary': fields.boolean('Es Beneficiario?'),
        'copy': fields.boolean('Es copia'),
        'curp' : fields.char(string='Curp', size=18, required=True, help="código alfanumérico único de identidad de 18 caracteres utilizado para identificar oficialmente tanto a residentes como a ciudadanos mexicanos de todo el país"),
        
        'city_id': fields.many2one("social.programs.res.city", 'Ciudad'),
        'settlement_id': fields.many2one('social.programs.res.settlement', 'Colonia'),
        'area_id' : fields.related('settlement_id', 'area_id', type="many2one", relation="social.programs.res.area", string="Area", store=True, readonly=True),
        'sector_id' : fields.related('settlement_id', 'sector_id', type="many2one", relation="social.programs.res.sector", string="Sector", store=True, readonly=True),
        
        # Datos personales segun el programa socioeconomico
        'residency_long': fields.float('Tiempo residencia', help="Años que lleva viviendo dentro del municipio"),
        'date_birth' : fields.date(string='Fecha Nac.'),
        'marital_status': fields.selection([
                    ('single', 'Soltero'),
                    ('free', 'Union libre'),
                    ('married', 'Casado'),
                    ('divorced', 'Divorciado'),
                    ('widowed', 'Viudo'),], 'Estado Civil'),
        'family_head': fields.selection([
                    ('me', 'Soy yo'),
                    ('partner', 'Mi pareja'),
                    ('son', 'Mi hijo(a)'),
                    ('parents', 'Mis padres'),
                    ('other', 'Otro'),], 'Jefe Familia', help="Indique quien es el jefe de familia en su hogar"),
        'family_head_other': fields.char('Especifique jefe', size=128, help="Especifique que familiar es el jefe de familia en su hogar"),
        'ocupation': fields.selection([
                    ('housewife', 'Ama de casa'),
                    ('employee', 'Empleado'),
                    ('unemployed', 'Desempleado'),
                    ('sale', 'Comerciante'),
                    ('other', 'Otro'),], 'Ocupacion', help="Especifique a que se dedica actualmente"),
        'ocupation_other': fields.char('Especifique ocupacion', size=128, help="Especifique cual es su ocupacion"),
        'ocupation_shift': fields.selection([
                    ('morning', 'Matutino'),
                    ('evening', 'Vespertino'),
                    ('night', 'Nocturno'),
                    ('rotary', 'Rotativo'),], 'Turno en que labora'),
        'ocupation_entry': fields.float('Ingreso mensual', help="Indique el ingreso mensual por este trabajo"),
        'social_safe': fields.boolean('Tiene seguro medico?'),
        'social_safe_type': fields.selection([
                    ('popular', 'Seguro popular'),
                    ('issste', 'ISSSTE'),
                    ('imss', 'IMSS o Seguro social'),
                    ('private', 'Seguro privado'),
                    ('other', 'Otro'),], 'Tipo seguro'),
        'social_safe_type_other': fields.char('Especifique', size=128, help="Especifique cual es el tipo de seguro con el que cuenta"),
        'support': fields.boolean('Apoyo de gobierno?', help="Indique si usted cuenta con algun apoyo por parte del gobierno"),
        'support_description': fields.text('Tipo de Apoyo', help="Especifique que tipo de apoyo o apoyos recibe"),
        'education': fields.selection([
                    ('nothing', 'Sin estudios concluidos'),
                    ('primary', 'Primaria'),
                    ('secundary', 'Secundaria'),
                    ('preparatory', 'Preparatoria'),
                    ('university', 'Licenciatura'),
                    ('other', 'Otro'),], 'Grado estudios', help="Indique cual es su grado de estudios concluiodos"),
        'education_other': fields.char('Especifique', size=128, help="Especifique cual es su grado de estudios"),
        'education_present': fields.boolean('Sigue estudiando', help="Actualmente asiste a algun curso o sigue estudiando"),
        'education_present_type': fields.char('Que estudia?', size=128, help="Especifique que esta estudiando actualmente"),
        'education_present_new': fields.boolean('Le gustaria seguir estudiando?'),
        'education_present_new_type': fields.char('Especifique', size=128, help="Especifique que le gustaria estudiar"),
        'workshop_reposteria': fields.boolean('Reposteria'),
        'workshop_computation': fields.boolean('Computacion'),
        'workshop_secretary': fields.boolean('Secretariado'),
        'workshop_stylist': fields.boolean('Estilista'),
        'workshop_kitchen': fields.boolean('Cocina'),
        'workshop_makeup': fields.boolean('Maquillista'),
        'workshop_nails': fields.boolean('Uñas'),
        'workshop_hotel': fields.boolean('Hoteleria'),
        'workshop_cuts': fields.boolean('Corte y confeccion'),
        'workshop_business': fields.boolean('Creacion de empresas'),
        'childrens': fields.boolean('Tiene hijos?'),
        'childrens_qty': fields.integer('Cuantos?'),
        'childrens_high': fields.integer('Mayores de 15?'),
        'childrens_less': fields.integer('Menores de 15?'),
        'dependents': fields.boolean('Dependientes', help="Aparte de hijos tiene mas personas que habiten en su vivienda que dependan directamente de usted"),
        'dependents_qty': fields.integer('Cuantos?'),
        'dependents_high': fields.integer('Mayores de 15?'),
        'dependents_less': fields.integer('Menores de 15?'),
        'impairment': fields.boolean('Dependientes discapacitados', help="Indique si alguno de sus dependientes tiene alguna discapacidad"),
        'impairment_qty': fields.integer('Cuantos?'),
        'impairment_high': fields.integer('Mayores de 15?'),
        'impairment_less': fields.integer('Menores de 15?'),
        'impairment_type': fields.selection([
                    ('physical', 'Motriz, Discapacidad Fisica'),
                    ('intellectual', 'Mental'),
                    ('hearing', 'Auditiva'),
                    ('languaje', 'De lenguaje'),
                    ('visually', 'Visual'),
                    ('sensory', 'Sensorial'),], 'Discapacidad', help='Especifique el tipo de discapacidad'),
        'dependents_support': fields.boolean('Alguno de sus dependientes recibe apoyo de gobierno?'),
        'dependents_support_qty': fields.integer('Cuantos?'),
        'dependents_support_description': fields.text('A cuales programas estan inscritos?'),
        'entry_additional_parent': fields.boolean('Por parte de la pareja'),
        'entry_additional_parent_qty': fields.float('Cantidad'),
        'entry_additional_son': fields.boolean('Manutencion de hijos'),
        'entry_additional_son_qty': fields.float('Cantidad'),
        'entry_additional_retirement': fields.boolean('Pension por jubilacion'),
        'entry_additional_retirement_qty': fields.float('Cantidad'),
        'entry_additional_family': fields.boolean('Ayuda de familiares'),
        'entry_additional_family_qty': fields.float('Cantidad'),
        'entry_additional_government': fields.boolean('Por parte del gobierno'),
        'entry_additional_government_qty': fields.float('Cantidad'),
        'entry_additional_qty': fields.function(_entry_additional_qty, type='float', method=True, store=True, string="Total Mensual Otorgado", help="Las cantidades corresponden al total mensual otorgado"),
        # Informacion adicional sobre programas sociales
        'program_ids': fields.many2many('social.programs.program', 'social_programs_rel_partners', 'partner_ids', 'program_ids', 'Programas'),
        'program_count': fields.function(_program_count, type='integer', method=True, string="Programas Activo", multi='program', help="programas en los que se encuentra inscrito"),
        'program_count_total': fields.function(_program_count, type='integer', method=True, string="Programas inscrito", multi='program', help="programas en los que a participado"),
        'delivery_ids': fields.one2many('social.programs.program.delivery', 'partner_id', 'Entregas', readonly=True),
        'program_id': fields.many2one('social.programs.program', 'Programa Actual', readonly=True),
        'category_id': fields.many2many('res.partner.category', id1='partner_id', id2='category_id', string='Tags'),
        'image_ref': fields.binary("Identificacion oficial",
            help="Agregar identificacion oficial con foto visible, limite 1024x1024px"),
    }
    
    _defaults = {
        'beneficiary': False,
        'copy': False,
        'date' : fields.date.today,
    }
    
    def _validate_size_curp(self, cr, uid, ids, context=None):
        """
            Valida que el curp contenga 18 caracteres
        """
        result = True
        # Recorre los partners
        for partner in self.browse(cr, uid, ids, context=context):
            #~ Valida el tamaño del curp
            if partner.beneficiary == True:
                #print "********* partner  ************ ", partner.copy, "   ", partner.curp
                
                # Valida que no sea un elemento duplicado
                if partner.curp == '':
                    if partner.copy == True:
                        break
                #~ Valida el tamaño del curp
                if len(partner.curp) != 18:
                    # Si es duplicado quita el valor de copia y omite la validacion
                    if partner.copy == True:
                        self.write(cr, uid, partner.id, {'copy': False}, context=context)
                    # Valor de retorno que indica que el curp es incorrecto
                    result = False
                    break
        return result
    
    _constraints = [(_validate_size_curp, "El tamaño del curp es invalido!", ['curp']),]
    
    _sql_constraints = [
        ('curp_uniqe', 'unique(curp)', 'Ya esta registrado un beneficiario con el curp ingresado!')
    ]

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
