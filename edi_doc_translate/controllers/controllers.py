# -*- coding: utf-8 -*-
from odoo import http

# class EdiDocTranslate(http.Controller):
#     @http.route('/edi_doc_translate/edi_doc_translate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/edi_doc_translate/edi_doc_translate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('edi_doc_translate.listing', {
#             'root': '/edi_doc_translate/edi_doc_translate',
#             'objects': http.request.env['edi_doc_translate.edi_doc_translate'].search([]),
#         })

#     @http.route('/edi_doc_translate/edi_doc_translate/objects/<model("edi_doc_translate.edi_doc_translate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('edi_doc_translate.object', {
#             'object': obj
#         })