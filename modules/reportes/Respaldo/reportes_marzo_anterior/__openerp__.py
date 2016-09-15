# -*- encoding: utf-8 -*-
{
    'name': 'Reportes',
    'category': 'custom',
    'description': 'Modulo de exportacion',
    'depends': [
        'base',
        'product',
        'stock',
        'sale',
        'purchase',
        'account',
    ],
    'autor': 'Lic. Jose de Jesus Ruvalcaba Luna',
    'data': [
        'reportes_view.xml',
    ],
    'qweb': [],
    'images': 'images/logo_white.bmp',
    'js': [],
    'css': [],
    'instalable': True,
    'auto_install': False,
}