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
    'name' : "Envio correo de felicitacion de cumpleaños a socios",
    'category' : "Customer Relationship Management",
    'version' : "1.0",
    'depends' : [
        'base_action_rule',
        'process',
        'mail',
        'email_template',
        'fetchmail'
    ],
    'author' : "Akkadian",
    'description' : """\
     Envio automatico de felicitaciones de cumpleaños a los clientes.
    """,
    'data' : [
        'company_view.xml',
        'res_partner_view.xml',
        'birthday_notifier_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
