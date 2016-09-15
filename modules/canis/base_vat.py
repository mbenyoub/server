# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import string

_ref_vat = {
    'at': 'ATU12345675',
    'be': 'BE0477472701',
    'bg': 'BG1234567892',
    'ch': 'CHE-123.456.788 TVA or CH TVA 123456', #Swiss by Yannick Vaucher @ Camptocamp
    'cy': 'CY12345678F',
    'cz': 'CZ12345679',
    'de': 'DE123456788',
    'dk': 'DK12345674',
    'ee': 'EE123456780',
    'el': 'EL12345670',
    'es': 'ESA12345674',
    'fi': 'FI12345671',
    'fr': 'FR32123456789',
    'gb': 'GB123456782',
    'gr': 'GR12345670',
    'hu': 'HU12345676',
    'hr': 'HR01234567896', # Croatia, contributed by Milan Tribuson 
    'ie': 'IE1234567T',
    'it': 'IT12345670017',
    'lt': 'LT123456715',
    'lu': 'LU12345613',
    'lv': 'LV41234567891',
    'mt': 'MT12345634',
    'mx': 'MXABC123456T1B',
    'nl': 'NL123456782B90',
    'no': 'NO123456785',
    'pl': 'PL1234567883',
    'pt': 'PT123456789',
    'ro': 'RO1234567897',
    'se': 'SE123456789701',
    'si': 'SI12345679',
    'sk': 'SK0012345675',
}


class res_partner(osv.osv):
  _inherit = 'res.partner'
  
  # Se copio el metodo original para ejecutar el constraint, no se realizo ningun cambio de funcionalidad
  def _construct_constraint_msg(self, cr, uid, ids, context=None):
        def default_vat_check(cn, vn):
            # by default, a VAT number is valid if:
            #  it starts with 2 letters
            #  has more than 3 characters
            return cn[0] in string.ascii_lowercase and cn[1] in string.ascii_lowercase
        #print "*****VAT****: ", self.browse(cr, uid, ids)[0].vat
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        if self.browse(cr, uid, ids)[0].vat:
            vat_country, vat_number = self._split_vat(self.browse(cr, uid, ids)[0].vat)
            
            if default_vat_check(vat_country, vat_number):
                vat_no = _ref_vat[vat_country] if vat_country in _ref_vat else vat_no
        return '\n' + _('This VAT number does not seem to be valid.\nNote: the expected format is %s') % vat_no
  
  def check_vat(self, cr, uid, ids, context=None):
        # print "****VERIFICANDO EL RFC******"
        user_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if user_company.vat_check_vies:
            # force full VIES online check
            check_func = self.vies_vat_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_check
        for partner in self.browse(cr, uid, ids, context=context):
            # print "****PARTNER.VAT****: ", partner.vat
            if not partner.vat:
                # print "***CLIENTE SIN RFC****"
                continue
            vat_country, vat_number = self._split_vat(partner.vat)
            # print "*****VAT_NUMBER*****: ", vat_number
            # Validando que 'vat_number' contenga un valor para mandar el mensaje de error
            if vat_number != 'False':
                # print "*****CON RFC****: ", vat_number
                # Validando que el RFC tenga un formato valido dependiendo el pais
                if not check_func(cr, uid, vat_country, vat_number, context=context):
                    return False
        return True
    
  # Se copio el constraint para ejecutar el metodo que se va a modificar
  _constraints = [(check_vat, _construct_constraint_msg, ["vat"])]

  #code
