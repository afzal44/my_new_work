# -*- coding: utf-8 -*-

from odoo import models, fields, api

class tools_edi_as2(models.Model):
    _name = 'edi.documents'

    as2_name = fields.Char(string="AS2 Uninque Name",help="The unique AS2 name")
    document_model = fields.Char(string="Model Name",help="Model Name of the document")
    structure = fields.Many2many('edi.code.struct',string="Structure Details")
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
class edi_structure(models.Model):
    _name = 'edi.code.struct'
    code = fields.Char(string="Code of document")
    vlaue = fields.Char(string="Value of document")
    field = fields.Char(string="Value of field")