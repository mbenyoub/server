# -*- coding: utf-8 -*-
##############################################################################


from openerp.addons.crm import crm
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext

class selfhelp(osv.osv):

    _name = "selfhelp"
    _description = "Modulo de auto-ayuda"
    
   
    _columns = {
            'name': fields.char('Nombre'),
            'active': fields.boolean('Active', required=False),
            'description1': fields.text('Descripcion'),
            'description2': fields.text('Descripcion'),
            'description3': fields.text('Descripcion'),
            'description4': fields.text('Descripcion'),
            'user_id': fields.many2one('res.users', 'Responsable'),
            'more1': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more2': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more3': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more4': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more5': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more6': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'more7': fields.many2one('selfhelp', 'Temas Relacionados', help='Tema Relacionado'),
            'image1': fields.binary("Imagen de Ayuda",help="Imagen de Ayuda, Tamano limitado a 1024x1024px"),
            'image2': fields.binary("Imagen de Ayuda",help="Imagen de Ayuda, Tamano limitado a 1024x1024px"),
    }
    _defaults = {
        'active': 1,
    }

    
    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: