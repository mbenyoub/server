#!/usr/bin/python                                                                                                                                  
# -*- encoding: utf-8 -*-                                                                           
###############################################################################                     
#    Module Writen to OpenERP, Open Source Management Solution                                      
#    Copyright (C) Vauxoo (<http://www.vauxoo.com>).                                                
#    All Rights Reserved                                                                            
# Credits######################################################                                     
#    Coded by: Yanina Aular <yanina.aular@vauxoo.com> 
#    Planified by: Humberto Arocha <humbertoarocha@gmail.com>
#    Audited by: Humberto Arocha <humbertoarocha@gmail.com>
###############################################################################                     
#    This program is free software: you can redistribute it and/or modify                           
#    it under the terms of the GNU Affero General Public License as published                       
#    by the Free Software Foundation, either version 3 of the License, or                           
#    (at your option) any later version.                                                            
#                                                                                                   
#    This program is distributed in the hope that it will be useful,                                
#    but WITHOUT ANY WARRANTY; without even the implied warranty of                                 
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                  
#    GNU Affero General Public License for more details.                                            
#                                                                                                   
#    You should have received a copy of the GNU Affero General Public License                       
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.                          
###############################################################################

{                                                                                                                                                  
    'name': 'MRP Request Add Item',                                                       
    'version': '1.0',                                                                               
    'summary': 'Add new item in the wizard of Request/Return in order manufacturing',
    'description': """                                                                             

MRP Request Add Item
====================

Allows you to add new requests of materials through mrp_request_return button not belonging to the
BOM.

""",
    'category': 'MRP',                                                                       
    'author': 'Vauxoo C.A',                                                                         
    'website': 'http://vauxoo.com',                                                                 
    'license' : 'AGPL-3',
    'depends': ['mrp','mrp_consume_produce','mrp_request_return'],
    'data': [
        'wizard/mrp_request_return_view.xml',
        ],
    'demo': [],
    'installable': True,                                                                            
    'auto_install' : False,
    'js': [],
    'qweb': [],
    'css': [],
    'images': [],
    'test' : [],
}
