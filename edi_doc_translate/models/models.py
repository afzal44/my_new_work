# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
import base64
import logging
import re
_logger = logging.getLogger(__name__)
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    edi_mapping = fields.Many2one(comodel_name='message.message',string='EDI Messages')
    edi_json = fields.Text("EDI JSON")


class EdiDoc(models.Model):
    _name = 'edi_doc'
    _description = 'EDI Document model'
    models = fields.Many2one(comodel_name="ir.model", string="models")
    name = fields.Char(string='Doc Name',default='EDI Doc.')
    prefix = fields.Char(string='Prefix',default='TC_#810')
    code = fields.Char(string='Code')
    organization = fields.Many2one(comodel_name="organization.organization", string="Organization")
    partner = fields.Many2one(comodel_name="partner.partner", string="Partner")
    delimiter = fields.Char(string='Delimiter', default='*')
    data = fields.One2many(comodel_name='edi_code_detail', inverse_name='edi_doc_id', string='Data Header Mapping')

    @api.model
    def auto_create_invoice_cron(self, args={}):
        """
        Use: To create purchase order invoices on the basis of received edi message
        :param args:
        :return:
        """
        msgs = self.env['message.message'].search([('imported', '=', False)])

        for msg in msgs:
            data_seg = base64.b64decode(msg.payload).decode('ascii').split('\r\n')
            edi_docs = self.search([('partner.id', '=', msg.partner.id)])
            edi_doc_ids = edi_docs.ids if isinstance(edi_docs.ids,list) else [edi_docs.ids]
            # delimiter="*"
            print("edi_doc_idsedi_doc_idsedi_doc_idsedi_doc_idsedi_doc_ids:::",edi_doc_ids)

            isa_line = self.env['edi_code_detail'].search(
                [('seg_id', '=', "ISA"), ('edi_doc_id.id', 'in', edi_doc_ids)])
            # if not isa_line:
            #     raise UserError("Isa line is not define")
            delimiters = tuple(set(edi_docs.mapped('delimiter')))

            print("THIS DELIMETER IS FOUND IN FILE  :: ",delimiters,msg.payload_name)
            # import pdb;pdb.set_trace()
            for sep in delimiters:
                print("THIS IS SEPRATOR AND THIS IS DATA SEG 0 :: ",data_seg[0],sep)
                msg_doc_code = data_seg[0].split(sep)
                print("\n\n\\n\n\n\n\n",sep,"\n\n\n\n\\n\n\nn\\n\nn\n\n\n",len(msg_doc_code),len(isa_line.data))
                # if len(msg_doc_code)-1 == len(isa_line.data):
            delimiter = sep
                #     break

            msg_doc_code = data_seg[2].split(delimiter)[1]
            edi_doc = self.search([('partner.id', '=', msg.partner.id),('delimiter','=',delimiter),('code','=',msg_doc_code)])
            tem_dict = {}
            for ele in data_seg:
                if not ele:
                    continue
                # print()
                list_ele = ele.split(delimiter)
                data_line = self.env['edi_code_detail'].search(
                    [('seg_id', '=', list_ele[0]), ('edi_doc_id', 'in', [edi_doc.id])])
                if list_ele[0] == data_line.seg_id:
                    # tem_dict = {}
                    for field in data_line.data:

                        temp =re.findall(r"\d+",field.ref)
                        ind = list(map(int, temp))[0]
                        print("THIS IS IND VALUE BE CAUTIOUSS::",ind)
                        if ind > 100:
                            ind = ind%100
                        print("IND AFTER REMIDER OPERATION ::",ind)

                        try:
                            if field.nature == 'fixed':
                                if field.ref in tem_dict:
                                    tem_dict[field.ref+'_1'] = list_ele[ind]
                                else:
                                    tem_dict[field.ref] = list_ele[ind]
                            elif field.fields_mapping.name == 'date_invoice' :
                                tem_dict[field.fields_mapping.name]=datetime.datetime.strptime(list_ele[ind],"%Y%m%d").date()
                            elif field.fields_mapping.name == 'partner_id':
                                tem_dict[field.fields_mapping.name] = msg.partner.partner_id.id
                            elif field.fields_mapping.name == 'type':
                                if list_ele[ind] == 'DR':
                                    list_ele[ind] = 'in_invoice'
                                elif list_ele[ind] == 'CR':
                                    list_ele[ind] = 'in_refund'
                                tem_dict[field.fields_mapping.name] = list_ele[ind]
                            else:
                                if field.fields_mapping.name in tem_dict:
                                    tem_dict[field.fields_mapping.name+'_1'] = list_ele[ind]
                                else:
                                    tem_dict[field.fields_mapping.name] = list_ele[ind]

                        except IndexError:
                            # raise UserError(f"IndexError Occurred these are values : field.nature:{field.nature} list_ele:{list_ele} ind:{ind}")
                            _logger.info(f"IndexError Occurred these are values : field.nature:{field.nature} list_ele:{list_ele} ind:{ind}")

                    print("ELEMENT IN Line  :::\n", list_ele, data_line.seg_id)

                    print("\nTemp dict :: ",tem_dict)
            # import pdb;pdb.set_trace()
            if 'partner_id' not in tem_dict:
                tem_dict['partner_id'] = msg.partner.partner_id.id
            print("\nTemp dict :: ", tem_dict)
            if edi_doc.models.model:
                create_rec = self.env[edi_doc.models.model].create(tem_dict)

                print("THIS IS RECORD CREATION FOR THE MODEL :: %s" % create_rec)

                update_msg_rec = msg.write({'model_name':edi_doc.models.model,'rec_id':create_rec.id})

                # print(dir(res))
            tem_dict = {}

                # data_field = ele.split(delimiter)




class EdiCodeDetail(models.Model):
    _name = 'edi_code_detail'
    _description = 'This model shows us detail about template section'
    required_state = [
        ('M', 'Mandatory'),
        ('O', 'Optional'),
        ('X', 'X'),
    ]
    seg_identifier = fields.Char(string='Segment Identifier')
    edi_doc_id = fields.Many2one(comodel_name="edi_doc", string="EDI DOC")
    code = fields.Char(related='edi_doc_id.code',string='Code')
    pos_name = fields.Integer(string='Pos')
    seg_id = fields.Char(string='Id')
    seg_name = fields.Char(string='Segment Name')
    req_state = fields.Selection(required_state, string='Req')
    eai_req = fields.Selection(required_state, string='EAI Req')
    max_use = fields.Integer(string='Max Use')
    repeat = fields.Char(string='Repeat')
    delimiter = fields.Char(related='edi_doc_id.delimiter')
    data = fields.One2many(comodel_name='edi_content_mapping', inverse_name='edi_code_id', string='Data Segment Mapping')
    extra_fields = fields.Text(string='Extra Segment Fields')




class EdiContentMapping(models.Model):
    _name = 'edi_content_mapping'
    _description = 'This module maps the edi doc contents'
    required_state = [
        ('M','Mandatory'),
        ('O','Optional'),
        ('X','X'),
    ]
    field_nature = [
        ('fixed','Fixed'),
        ('eval','Eval'),
    ]

    @api.onchange('nature','fields_mapping')
    def set_domain_for_fields_mapping(self):
        active_id = self._context.get('active_id')
        print("******************************::::::::::::", active_id,self._context,self.edi_code_id.edi_doc_id.models.model)
        res= {'domain':{}}
        res['domain']['fields_mapping']=[('model','=',self.env['edi_doc'].browse(active_id).models.model or self.edi_code_id.edi_doc_id.models.model)]
        return res


    fields_mapping = fields.Many2one(comodel_name='ir.model.fields',string='Field Mapping EDI')
    edi_code_id = fields.Many2one(comodel_name="edi_code_detail", string="EDI Template Code")
    ref = fields.Char(string='Reference',)
    ref_id = fields.Char(string='Reference ID')
    description = fields.Char(string='Description')
    req = fields.Selection(required_state,string='Required State')
    type = fields.Char(string='Type')
    min_max = fields.Char(string='Min/Max')
    # max = fields.Integer(string='Max')
    val_comm = fields.Char(string='Value/Comments/Qualifiers/Definitions')


    nature = fields.Selection(field_nature,string='Field Nature')
    @api.onchange('nature')
    def get_field_val(self):
        if self.nature == 'eval':
            print("ACTION NEED TO BE PERFORMED _____________ ***************************")







class EdiPartner(models.Model):
    _inherit = 'partner.partner'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact",required=True)
    qualifier = fields.Char(string='Qualifier')
    qualifier_id = fields.Char(string='Qualifier ID')
    # @api.model
    # def create(self,vals):
    #     rec = super(EdiPartner, self).create(vals)
    #     rec.partner_id = self.env['res.partner'].create({'name':rec.name})
    #     return rec
class EdiPartner(models.Model):
    _inherit = 'organization.organization'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact",required=True)
class EdiMessage(models.Model):
    _inherit = 'message.message'
    rec_id = fields.Integer(string='Record Id')
    model_name = fields.Char(string='Model Name')
    imported = fields.Boolean(string='Imported',default=False)
    exported = fields.Boolean(string='Exported',default=False)
