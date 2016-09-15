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

from openerp.osv import fields, osv

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'user_mail': fields.many2one('res.users', 'Quien envia', selected=1, help="Usuario por el que van a salir los correos"),
        'birthday_subject': fields.char("Asunto", size=128, help="Asunto del mensaje"),
        'birthday_body': fields.text('Mensaje para notificaciones cumpleaños', help="Contenido del mensaje"),
    }

    _defaults = {
        'birthday_subject': "Grupo ${COMPANY} te desea un feliz cumpleaños",
        'user_mail': 1 or None,
        'birthday_body': '''${PARTNER}. <br><br>
<div>
    En esta fecha tan especial deseamos expresarte de todo corazon el gran cariño y admiracion
    que sentimos hacia ti. ¡Feliz Cumpleaños!
</div>
<br>
<div>
    ¡Gracias por seleccionar a ${COMPANY}!. <br>
    Estamos para servirle.
</div>
<br>
<div style="width: 375px; margin: 0px; padding: 0px; background-color: #8E0000; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px; background-repeat: repeat no-repeat;">
    <h3 style="margin: 0px; padding: 2px 14px; font-size: 12px; color: #DDD;">
        <strong style="text-transform:uppercase;">${COMPANY}</strong></h3>
</div>
<div style="width: 347px; margin: 0px; padding: 5px 14px; line-height: 16px; background-color: #F2F2F2;">
    <span style="color: #222; margin-bottom: 5px; display: block; ">
        ${COMPANY_STREET}<br/>
        ${COMPANY_ZIP} ${COMPANY_CITY}<br/>
        ${COMPANY_STATE} ${COMPANY_COUNTRY}<br/>
    </span>
    <div style="margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: 0px; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px; ">
        Teléfono:&nbsp; ${COMPANY_PHONE}
    </div>
    <div>
        Pagina web :&nbsp;<a href="${COMPANY_WEBSITE}"/a>
    </div>
    <p></p>
</div>
'''
    }

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
