# -*- encoding: utf-8 -*-
 
{
    "name": "Iniciativas CDS",
    "version": "1.0",
    "description": """1.- Crea la seccion PANT
	\n2.- Crea la seccion Llamada
	\n3.- Crea la seccion Formulario
	\n4.- Crea la seccion Reunion
	\n5.- Crea la seccion Negociacion
	\n6.- Solicitud de cancelacion
	\n7.- Solicitud de reprogramacion
    """,
    "author": "Ing. Gustavo Isidoro",
    "category": "Tools",
    "depends": [
	    'crm','mail','email_template'
                ],
    "data":['wizard/w_cancel_lead_view.xml','wizard/w_reprogram_lead_view.xml','crm_lead_view.xml','pant_phonecall_view.xml','pant_form_view.xml','op_meeting_view.xml'],
    "update_xml": [                   ],
    "demo_xml": [],
    "update_xml": [],
    "installable": True,
    "auto_install": False,
}
