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
    'name' : "Personalizacion CRM para Kober",
    'category' : "Customer Management Client",
    'version' : "1.0",
    'depends' : [
        'base',
        'board',
        'sale',
        'crm',
        'crm_claim',
        'crm_campaign',
        'crm_access_branch',
        'birthday_notifier',
        'sale_notify_inactivity',
        'crm_todo'
    ],
    'author' : "Akkadian",
    'description' : """\
        Personalizacion de CRM para empresa Kober,
        Envio de mensajes de cumpleaños,
        Comunicacion con intelisis por medio de webservice,
        Notificaciones a vendedores con los clientes que no han tenido contacto en un periodo de tiempo
        
    """,
    'data' : [
        'security/ir.model.access.csv',
        'security/crm_kober_security.xml',
        'crm_lead_view.xml',
        'crm_kober_view.xml',
        'crm_kober_data.xml',
        'crm_kober_cron.xml',
        'crm_swot_view.xml',
        'res_partner_view.xml',
        'res_partner_data.xml',
        'product_view.xml',
        'account_invoice_view.xml',
        'sale_view.xml',
        'project_view.xml',
        'res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
