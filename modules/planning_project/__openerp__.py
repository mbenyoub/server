# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    code by "Roberto Serrano <riss_600@hotmail.com>"
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
    'name' : "Planificacion de proyectos y distribucion de tiempos",
    'category' : "Project Management",
    'version' : "1.0",
    'depends' : ['project', 'project_issue', 'crm', 'hr'],
    'author' : "Riss - Akkadian",
    'description' : """
Herramientas para la administracion de proyectos y tareas
=======================================================================

Este modulo contiene herramientas que nos permiten dar seguimiento a los proyectos y tareas,
designar a un responsable, asignacion de tareas a un equipo de trabajo y bitacorizacion.

""",
    'data' : [
        'security/planning_project_security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_phonecall_to_phonecall_view.xml',
        'project_issue_view.xml',
        'crm_phonecall_view.xml',
        'planning_project_crm_phonecall_view.xml',
        'planning_project_crm_phonecall_menu.xml',
        'planning_project_view.xml',
        'planning_project_ticket_workflow.xml',
        'project_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
