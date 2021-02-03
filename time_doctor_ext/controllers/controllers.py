# -*- coding: utf-8 -*-
from odoo import http

# class TimeDoctorExt(http.Controller):
#     @http.route('/time_doctor_ext/time_doctor_ext/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/time_doctor_ext/time_doctor_ext/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('time_doctor_ext.listing', {
#             'root': '/time_doctor_ext/time_doctor_ext',
#             'objects': http.request.env['time_doctor_ext.time_doctor_ext'].search([]),
#         })

#     @http.route('/time_doctor_ext/time_doctor_ext/objects/<model("time_doctor_ext.time_doctor_ext"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('time_doctor_ext.object', {
#             'object': obj
#         })