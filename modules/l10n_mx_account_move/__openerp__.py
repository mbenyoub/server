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

{
    'name' : "Correccion proceso generacion manual de polizas",
    'category' : "Accounting & Finance",
    'version' : "1.0",
    'depends' : ['base', 'account'],
    'author' : "Akkadian",
    'description' : """\
     Se corrige el problema que aparece al querer modificar los apuntes de una poliza
    """,
    'data' : [
        'security/ir.model.access.csv',
        'account_move_view.xml',
        'wizard/wizard_account_move_edit_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
