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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
import xml.dom.minidom
import base64
import codecs
try:
    from SOAPpy import WSDL
except:
    #print "Package SOAPpy missed"
    pass

class account_bank_statement_import(osv.osv_memory):
    _name = 'account.bank.statement.import'
    _description = 'Importar movimientos de bancos'
    
    def action_import_data(self, cr, uid, ids, context=None):
        """
            Importa la informacion de los registros
        """
        bank_obj = self.pool.get('account.bank.statement.bank')
        
        # Obtiene la informacion del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)
        doc_csv = base64.decodestring(wizard.file)
        
        data = []
        import_data = []
        data = doc_csv.split('\n')
        for reg in data:
            # Registros a agregar en los movimientos
            import_data.append(reg.split(","))
        
        #print "************ documento csv ************* ", type(doc_csv) , import_data
        
        # Recorre los archivos importados
        for reg in import_data:
            try:
                # Valida que la fecha sea correcta
                date = datetime.strptime(reg[0] , '%Y-%m-%d')
                amount = float(reg[2])
                # Valida que exista un monto
                if not amount:
                    continue
                
                # Agrega el registro para la conciliacion
                bank_obj.create(cr, uid, {
                            'statement_id': wizard.statement_id.id, 
                            'move': reg[1], 
                            'date': date, 
                            'amount': amount, 
                            'state': 'PREV'}, context=context)
            except Exception:
                # Si el formato no es fecha omite el registro
                date = False
                continue
        #raise osv.except_osv("Test","Detenido Prueba")
        return True
    
    _columns = {
        'statement_id': fields.many2one('account.bank.statement', 'Conciliacion Banco', readonly=True, select=1, ondelete='cascade', required=True, help="Referencia sobre conciliacion de banco"),
        'file': fields.binary('Archivo de importacion', required=True,
            filters='*.csv', help='Archivo CSV recibido por el proveedor para validar la factura'),
    }
    
account_bank_statement_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
