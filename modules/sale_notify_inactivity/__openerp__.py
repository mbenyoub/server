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
    'name' : "Notificacion a vendedores que no estan en contacto con los clientes",
    'category' : "Customer Relationship Management",
    'version' : "1.0",
    'depends' : [
        'base_action_rule',
        'process',
        'mail',
        'email_template',
        'fetchmail',
        'sale',
        'crm',
    ],
    'author' : "Akkadian",
    'description' : """\
    Envio de notificaciones para los vendedores que no estan en contacto con los clientes
    
    Notificaicones a los vendedores para avisarles que ha transcurrido un periodo de tiempo sin comunicarse con el cliente.
    Se toman en cuenta, reuniones, llamadas realizadas, iniciativas y ventas.
    
    Si ya se notifico al vendedor, pasa al responsable y despues si sigue sin realizar actividad notifica al padre del equipo de ventas que seria el responsable.
    """,
    'data' : [
        'security/ir.model.access.csv',
        'crm_view.xml',
        'sale_notify_inactivity_data.xml',
        'sale_notify_inactivity_view.xml',
        'res_partner_view.xml',
        'crm_lead_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
