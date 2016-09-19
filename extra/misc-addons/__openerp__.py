# -*- encoding: utf-8 -*-

{
    "name": "CDS Automatico Miscellaneous",
    "version": "1.0",
    "description": """1.- Agrega constrain para que duplicar plantillas con el mismo nombre
       	\n2.- Agrega el campo is_maintenance_parts en Productos
	\n3.- Agrega campos obligatorios en iniciativas 
    """,
    "author": "Ing. Gustavo Isidoro",
    "category": "Tools",
    "depends": [
       	    'email_template',
       	    'product',
	    'crm',
	    'hr_expense',
                ],
    "data":['product_product_view.xml','cmr_lead_view.xml'],
    "update_xml": [],
    "demo_xml": [],
    "update_xml": [],
    "installable": True,
    "auto_install": False,
}
