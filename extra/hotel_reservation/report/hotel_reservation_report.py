# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

class reservation_detail_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(reservation_detail_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'get_data': self.get_data,
            'get_checkin': self.get_checkin,
            'get_checkout': self.get_checkout,
#            'get_room':self.get_room,
            'get_room_type':self._get_room_type,
            'get_room_nos':self._get_room_nos,
            'get_room_used_detail':self._get_room_used_detail,
        })
        self.context=context

    def _get_room_type(self, reservation_line):
        room_types = ''
        for line in reservation_line:
            if line.categ_id:
                room_types += line.categ_id.name
                room_types += ' '
                
        return room_types

    def _get_room_nos(self, reservation_line):
        room_nos  = ''
        for line in reservation_line:
            for room in line.reserve:
                room_nos += room.name
                room_nos += ' '
        return room_nos

    def get_data(self, date_start, date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr, self.uid, [('checkin', '>=', date_start), ('checkout', '<=', date_end)])
        res = reservation_obj.browse(self.cr, self.uid, tids)
        return res

    def get_checkin(self, date_start, date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr, self.uid, [('checkin', '>=', date_start), ('checkin', '<=', date_end)])
        res = reservation_obj.browse(self.cr, self.uid, tids)
        return res

    def get_checkout(self,date_start,date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr,self.uid,[('checkout', '>=', date_start),('checkout', '<=', date_end)])
        res = reservation_obj.browse(self.cr,self.uid,tids)
        return res

    def _get_room_used_detail(self, date_start, date_end):
        room_used_details = []
        hotel_room_obj = self.pool.get('hotel.room')
        room_ids = hotel_room_obj.search(self.cr, self.uid, [])
        for room in hotel_room_obj.browse(self.cr, self.uid, room_ids):
            counter = 0
            details = {}
            if room.room_reservation_line_ids:
                for room_resv_line in room.room_reservation_line_ids:
                    if room_resv_line.check_in >= date_start and room_resv_line.check_in <= date_end:
                        counter += 1
                if counter >= 1:
                    details.update({'name': room.name or '', 'no_of_times_used': counter})
                    room_used_details.append(details)
        return room_used_details

#    def get_room(self, date_start, date_end):
#        self.cr.execute("select pt.name,count(pt.name) as No_of_times from hotel_reservation as hr " \
#                   "inner join hotel_reservation_line as hrl on hrl.line_id=hr.id " \
#                   "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id=hrl.id " \
#                   "inner join product_product as pp on pp.product_tmpl_id=hrlrr.hotel_reservation_line_id " \
#                   "inner join product_template as pt on pt.id=pp.product_tmpl_id " \
#                   "where hr.state<>'draft' and hr.checkin >= %s and hr.checkout <= %s group by pt.name " \
#                   ,(date_start,date_end))
#        res2=self.cr.dictfetchall()
#        return res2

report_sxw.report_sxw('report.reservation.detail', 'hotel.reservation', 'addons/hotel_reservation/report/room_res.rml', parser=reservation_detail_report)
report_sxw.report_sxw('report.checkin.detail', 'hotel.reservation', 'addons/hotel_reservation/report/checkinlist.rml', parser=reservation_detail_report)
report_sxw.report_sxw('report.checkout.detail', 'hotel.reservation', 'addons/hotel_reservation/report/checkoutlist.rml', parser=reservation_detail_report)
report_sxw.report_sxw('report.maxroom.detail', 'hotel.reservation', 'addons/hotel_reservation/report/maxroom.rml', parser=reservation_detail_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: