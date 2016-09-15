# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Helpdesk',
    'category': 'Gestion de Relaciones con el Cliente', 
    'version': '0.9',
    'description': """
Administracion Helpdesk.
====================

Al igual que los registros y procesamiento de reclamaciones, asistencia y de apoyo son buenas herramientas
para trazar sus intervenciones. Este menú se adapta más a la comunicación oral,
que no está necesariamente relacionada con una reclamación. Seleccione un cliente, añadir notas
y clasificar sus intervenciones con un canal y un nivel de prioridad.
    """,
    'author': 'Akkadian',
    'depends': ['base','crm', 'account_analytic_analysis','base_calendar','portal'],
    'data': [
        'crm_helpdesk_view.xml',
        'crm_helpdesk_menu.xml',
        'crm_helpdesk_portal_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/crm_helpdesk_report_view.xml',
        'crm_helpdesk_data.xml',
        'cds_update_view.xml',
        'cds_update_contract_view.xml',
        'res_partner_view.xml',
        'crm_helpdesk_config_view.xml',
        'portal_helpdesk_issue_view.xml',
        'crm_meeting_data.xml',
        'crm_meeting_menu.xml',
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
