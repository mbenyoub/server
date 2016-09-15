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

{
    'name' : "Administracion de Programas Sociales",
    'category' : "GRP",
    'version' : "1.0",
    'depends' : ['base', 'board', 'report_webkit', 'product'],
    'author' : "Akkadian",
    'description' : """\
        Administracion de programas sociales:
            - Creacion de Beneficiarios
            - Crear programas sociales
            - Entrega de Beneficios
    """,
    'data' : [
        'security/social_programs_security.xml',
        #'security/ir.model.access.csv',
        'report/social_programs_delivery_webkit.xml',
        'social_programs_view.xml',
        'social_programs_menu.xml',
        'res_partner_view.xml',
        'res_country_view.xml'
    ],
    'css' : [
        'static/src/css/social_programs.css',
    ],
    'installable': True,
    'auto_install': False,
}
