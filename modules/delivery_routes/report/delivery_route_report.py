# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Akkadian - http://www.akkadian.com.mx/
#    All Rights Reserved.
#    info Akkadian
############################################################################
#    Coded by: 
#              Juan Manuel Oropeza Salas (joropeza@akkadian.com.mx)
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
import time
from openerp.report import report_sxw

class delivery_route_report(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(delivery_route_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time
            })
        


report_sxw.report_sxw(
    'report.imprimir.entrega', # Nombre del reporte declarado en el xml donde se crea o se da de alta 
    'delivery.route.line', # Modelo o clase donde se generara el reporte
    '../delivery_routes/report/delivery_route_report.rml', # Ruta donde se encuentra el archivo 'rml'
    parser=delivery_route_report,  # Nombre de la clase que genera el reporte
    header=False
)
