# -*- coding: utf-8 -*-
{
    'name': 'Sale report',
   ' version': '1.0',
    'category': 'Customization',
    'description': 'Detalle de factura',

    'depends': [
        'sale',
        'account',
        'product',
        #'product_cost'
    ],

    'author': 'Akkadian',

    'update_xml': [],

    'data': [

        # Ventas
        'sale_report_view.xml',
        'sale_report_menu.xml',

        # Contabilidad
        #'account.xml',
    ],

    'demo': [],

    'test': [],

    'installable': True,
    'auto_installable': False,
    'application': False,
}
