# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Augustin Cisterne-Kaas <augustin.cisterne-kaas@elico-corp.com>
#    Eric Caudal <eric.caudal@elico-corp.com>

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
from openerp.addons.connector.event import (on_record_write,
                                            on_record_create,
                                            on_record_unlink
                                            )
from openerp.addons.base_intercompany.unit.export_synchronizer import (
    export_record)

_MODEL_NAMES = ('sale.order', 'sale.order.line',
                'purchase.order', 'purchase.order.line')
_BIND_MODEL_NAMES = ('icops.sale.order', 'icops.sale.order.line',
                     'icops.purchase.order', 'icops.purchase.order.line')
_UNLINK_MODEL_NAMES = ('sale.order', 'purchase.order')
_UNLINK_BIND_MODEL_NAMES = ('icops.sale.order', 'icops.purchase.order')


@on_record_create(model_names=_BIND_MODEL_NAMES)
@on_record_write(model_names=_BIND_MODEL_NAMES)
def delay_export(session, model_name, record_id, fields=None):
    """ Delay a job which export a binding record.

    (A binding record being a ``icops.res.partner``,
    ``icops.sale.order``, ...)
    """
    export_record(session, model_name, record_id, fields=fields)


@on_record_write(model_names=_MODEL_NAMES)
def delay_export_all_bindings(session, model_name, record_id, fields=None):
    """ Delay a job which export all the bindings of a record.

    In this case, it is called on records of normal models and will delay
    the export for all the bindings.
    """
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    for binding in record.icops_bind_ids:
        export_record(session, binding._model._name, binding.id,
                      fields=fields)


@on_record_unlink(model_names=_UNLINK_MODEL_NAMES)
def delay_unlink(session, model_name, record_id):
    """ Delay a job which delete a record on Magento.

    Called on binding records."""
    fields = {'icops_delete': True}
    delay_export_all_bindings(session, model_name, record_id, fields)


@on_record_unlink(model_names=_UNLINK_BIND_MODEL_NAMES)
def delay_unlink_binding(session, model_name, record_id):
    """ Delay a job which delete a record on Magento.

    Called on binding records."""
    fields = {'icops_delete': True}
    delay_export(session, model_name, record_id, fields)
