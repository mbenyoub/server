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
    'name' : "Planificacion de proyectos y distribucion de tiempos - Reto Zapopan",
    'category' : "Project Management",
    'version' : "1.0",
    'depends' : [
        'base',
        'project',
        'project_issue',
        'project_long_term',
        'crm',
        'hr',
        'contacts',
        'project_evaluation',
        #'document'
    ],
    'author' : "Akkadian",
    'description' : """\
Herramientas para la administracion de proyectos y tareas
=======================================================================

Este modulo contiene herramientas que nos permiten dar seguimiento a los proyectos y tareas,
designar a un responsable, asignacion de tareas a un equipo de trabajo y bitacorizacion.
    """,
    'data' : [
        'security/project_reto_zapopan_security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_phonecall_to_phonecall_view.xml',
        'res_partner_view.xml',
        'res_partner_evaluation_view.xml',
        'project_long_term_view.xml',
        'project_view.xml',
        'project_log_view.xml',
        'res_users_view.xml',
        'crm_meeting_view.xml',
        'crm_phonecall_view.xml',
        'crm_phonecall_menu.xml',
        'crm_custom_view.xml',
        'project_reto_zapopan_view.xml',
        'project_reto_zapopan_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
