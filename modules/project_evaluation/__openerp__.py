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
    'name' : "Evaluaciones a Proyectos y Contactos",
    'category' : "Project Management",
    'version' : "1.0",
    'depends' : ['base', 'project','project_issue','crm','hr', 'contacts'],
    'author' : "Akkadian",
    'description' : """\
Herramientas para la administracion de proyectos y tareas
=======================================================================

Este modulo contiene herramientas que nos permiten generar evaluaciones a los contactos y a los proyectos.
    """,
    'data' : [
        'security/project_evaluation_security.xml',
        'security/ir.model.access.csv',
        'wizard/evaluate_project_view.xml',
        'project_evaluation_view.xml',
        'project_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
