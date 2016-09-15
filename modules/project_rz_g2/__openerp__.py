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
    'name' : "Personalizacion Reto Zapopan G-II",
    'category' : "Project Management",
    'version' : "1.0",
    'depends' : [
        'base',
        'project_evaluation',
        'project_reto_zapopan',
        'report_webkit'
    ],
    'author' : "Akkadian",
    'description' : """\
Herramientas para la administracion de proyectos Emprendedores
=======================================================================

Este modulo contiene herramientas que nos permiten dar seguimiento a los proyectos
adaptados para la Generacion 2 de reto zapopan.
    """,
    'data' : [
        'security/project_reto_zapopan_security.xml',
        'security/ir.model.access.csv',
        #'data/project.template.project.csv',
        #'data/project.template.phase.csv',
        #'data/project.template.task.csv',
        'wizard/create_project_phase_view.xml',
        'wizard/apply_meeting_evaluation_phase_view.xml',
        'wizard/upload_file_task_view.xml',
        'wizard/upload_file_meeting_view.xml',
        'wizard/apply_evaluation_consultor_view.xml',
        'project_template_view.xml',
        'project_ticket_view.xml',
        'project_view.xml',
        'project_long_term_workflow.xml',
        'crm_meeting_view.xml',
        'project_log_view.xml',
        'res_users_view.xml',
        'res_partner_view.xml',
        'res_partner_evaluation_view.xml',
        'project_rz_g2_view.xml',
        #'data/res.partner.evaluation.phase.csv',
        #'data/res.partner.evaluation.category.csv',
        #'data/res.partner.evaluation.template.csv',
        'dashboard/board_project_rz_g2_view.xml',
        'report/progress_project_webkit.xml'
    ],
    'installable': True,
    'auto_install': False,
}
