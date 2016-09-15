# -*- encoding: utf-8 -*-

{
    "name": "CDS Automatico Miscellaneous",
    "version": "1.0",
    "description": """1.- Agrega constrain para que duplicar plantillas con el mismo nombre
       	\n2.- Agrega el campo is_maintenance_parts en Productos
    """,
    "author": "Ing. Gustavo Isidoro",
    "category": "Tools",
    "depends": [
       	    'email_template',
       	    'product',
                ],
    "data":['product_product_view.xml'],
    "update_xml": [],
    "demo_xml": [],
    "update_xml": [],
    "installable": True,
    "auto_install": False,
}
