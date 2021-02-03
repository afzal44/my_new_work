# -*- coding: utf-8 -*-
import logging

import traceback
from email.parser import HeaderParser
from uuid import uuid4
from odoo import models, fields, api
import requests

from base64 import b64decode, b64encode
from . config_edi import settings


from odoo.addons.tools_edi_as2.pyas2lib import (
    Mdn as As2Mdn,
    Message as As2Message,
    Organization as As2Organization,
    Partner as As2Partner,
)
from odoo.addons.tools_edi_as2.pyas2lib.utils import extract_certificate_info
from . import config_edi
from odoo.addons.tools_edi_as2.models.utils import run_post_send

logger = logging.getLogger('tools_edi_as2')
DATA_DIR = 'data_edi'

class PrivateKey(models.Model):
    _name = 'privatekey.privatekey'

    name = fields.Char(string='Name',size=255)

    key = fields.Binary(string='Key',attachment=True)
    file_name = fields.Char(string='file_name',size=255)

    key_pass = fields.Char(string='Private Key Password',default=' ',size=100)

    valid_from = fields.Datetime(string='Valid From')

    valid_to = fields.Datetime(string='Valid To')

    serial_number = fields.Char(string='Serial Number',size=64)

    @api.model
    def create(self, vals):
        cert_info = extract_certificate_info(b64decode(vals['key'].encode('ascii')))

        # 2021 - 01 - 02 19: 24:07

        vals['valid_from'] = cert_info["valid_from"].strftime("%Y-%m-%d %H:%M:%S")

        vals['valid_to'] = cert_info["valid_to"].strftime("%Y-%m-%d %H:%M:%S")
        if not cert_info["serial"] is None:
            vals['serial_number'] = cert_info["serial"].__str__()
        vals['name'] = vals['file_name']

        rec = super(PrivateKey, self).create(vals)
        return rec


#
class PublicCertificate(models.Model):
    _name = 'publiccertificate.publiccertificate'

    name = fields.Char(string='Name',size=255)
    certificate = fields.Binary(string='Certificate',attachment=True)
    file_name = fields.Char(string='file_name', size=255)
#
#     // might get issue
    certificate_ca = fields.Binary(string='Local CA Store')
    file_name1 = fields.Char(string='file_name1', size=255)

    verify_cert = fields.Boolean(string='Verify Certificate',default=True,help="Uncheck this option to disable certificate verification.")

    valid_from = fields.Datetime(string='Valid from',blank=True)

    valid_to = fields.Datetime(string='Valid to',blank=True)

    serial_number = fields.Char(blank=True,zise=64)

    @api.model
    def create(self,vals):

        cert_info = extract_certificate_info(b64decode(vals['certificate'].encode('ascii')))
        vals['valid_from'] = cert_info["valid_from"].strftime("%Y-%m-%d %H:%M:%S")
        vals['valid_to'] = cert_info["valid_to"].strftime("%Y-%m-%d %H:%M:%S")
        if not cert_info["serial"] is None:
           vals['serial_number'] = cert_info["serial"].__str__()
        vals['name']= vals['file_name']
        rec = super(PublicCertificate, self).create(vals)
        return rec
#
#
class Organization(models.Model):
    _name = 'organization.organization'
    name = fields.Char(string='Organization Name',size=100)

    as2_name = fields.Char(string='AS2 Identifier',size=100)
    _sql_constraints = [ ('as2_name_uniq', 'unique(as2_name)', 'as2_name cannot be with the same name!') ]

    email_address = fields.Char(string='Email Address',help="This email will be used for the Disposition-Notification-To header. If left blank, header defaults to: no-reply@pyas2.com")
#     encryption_key = models.ForeignKey(
#         PrivateKey, null=True, blank=True, on_delete=models.SET NULL
#     )
    encryption_key = fields.Many2one('privatekey.privatekey',string='Encryption Key',on_delete='SET NULL')

    signature_key = fields.Many2one('privatekey.privatekey',string='Signature Key',on_delete='SET NULL')

    confirmation_message = fields.Text(string='Confirmation Message',help="Use this field to send a customized message in the MDN Confirmations for this Organization")



    def gen_cert(self):
        return {
                   'type': 'ir.actions.act_window',
                   'res_model': 'cert.data',
                   'context': {'Organization': self.id},
                   'view_mode': 'form',
                    'target':'new',
        }
    @property
    def as2org(self):
        """ Returns an object of pyas2lib's Organization class"""
        params = {"id":self.id,"as2_name": self.as2_name, "mdn_url": settings.MDN_URL}
        # print("PARAMETERS FROM AS2ORG ::",params)
        if self.signature_key:
            params["sign_key"] = bytes(b64decode(self.signature_key.key))
            params["sign_key_pass"] = self.signature_key.key_pass

        if self.encryption_key:
            params["decrypt_key"] = bytes(b64decode(self.encryption_key.key))
            params["decrypt_key_pass"] = self.encryption_key.key_pass

        if self.confirmation_message:
            params["mdn_confirm_text"] = self.confirmation_message
        return As2Organization(**params)



#
class Partner(models.Model):
    _name = 'partner.partner'
    CONTENT_TYPE_CHOICES = [
        ("application/EDI-X12", "application/EDI-X12"),
        ("application/EDIFACT", "application/EDIFACT"),
        ("application/edi-consent", "application/edi-consent"),
        ("application/XML", "application/XML"),
        ("application/octet-stream", "binary"),
    ]
    ENCRYPT_ALG_CHOICES = [
        ("tripledes_192_cbc", "3DES"),
        ("rc2_128_cbc", "RC2-128"),
        ("rc4_128_cbc", "RC4-128"),
        ("aes_128_cbc", "AES-128"),
        ("aes_192_cbc", "AES-192"),
        ("aes_256_cbc", "AES-256"),
    ]
    SIGN_ALG_CHOICES = [
        ("sha1", "SHA-1"),
        ("sha224", "SHA-224"),
        ("sha256", "SHA-256"),
        ("sha384", "SHA-384"),
        ("sha512", "SHA-512"),
    ]
    MDN_TYPE_CHOICES = [
        ("SYNC", "Synchronous"),
        ("ASYNC", "Asynchronous"),
    ]
    DATA_EXCHANGE_CHOICE = [
        ('EDI_AS2','EDI AS2'),
        ('FTP','FTP/SFTP'),
        ('REST_API','REST API'),
    ]

    name = fields.Char(string='Partner Name',size=100)
    as2_name = fields.Char(string='AS2 Identifier',size=100)
    _sql_constraints = [
        ('AS2_Identifier', 'unique(as2_name)', 'AS2 Identifier must be unique!'),
    ]

    email_address = fields.Char(string='Email Address',blank=True)

    http_auth = fields.Boolean(string='HTTP Auth',default=False)
    http_auth_user = fields.Char(string='HTTP Auth User',blank=True,size=100)

    http_auth_pass = fields.Char(string='HTTP Auth Pass',blank=True,size=100)

    https_verify_ssl = fields.Boolean(string="Verify SSL Certificate",default=True,help='Uncheck this option to disable SSL certificate verification to HTTPS.')

    target_url = fields.Char(string='Target Url')

    subject = fields.Char(string="Subject",default="EDI Message sent using pyas2",size=255)

    content_type = fields.Selection(CONTENT_TYPE_CHOICES,string="Content Type",default="application/edi-consent",size=100)

    compress = fields.Boolean(string="Compress Message",default=False)

    encryption = fields.Selection(ENCRYPT_ALG_CHOICES,string="Encrypt Message")

    encryption_cert = fields.Many2one('publiccertificate.publiccertificate',string='PublicCertificate',ondelete='SET NULL')

    signature = fields.Selection(SIGN_ALG_CHOICES,string='Sign Message')

    signature_cert = fields.Many2one('publiccertificate.publiccertificate',string='signature_cert',ondelete='SET NULL')

    mdn = fields.Boolean(string='Request MDN',default=False)

    mdn_mode = fields.Selection(MDN_TYPE_CHOICES,string='MDN Mode')

    mdn_sign = fields.Selection(SIGN_ALG_CHOICES,string='"Request Signed MDN"')

    confirmation_message = fields.Text(string='Confirmation Message',blank=True,help="Use this field to send a customized message in the MDN Confirmations for this Partner")

    keep_filename = fields.Boolean(string='Keep Original Filename',default=False,help='Use Original Filename to to store file on receipt, use this option ,'
                                                                                      'only if you are sure partner sends unique names')

    cmd_send = fields.Text(string='Command on Message Send',blank=True,help='Command executed after successful message send, replacements are $filename,'
                                         ' $sender, $receiver, $messageid and any message header such as $Subject')

    cmd_receive = fields.Text(string='Command on Message Receipt',blank=True,help='Command executed after successful message receipt, replacements'
                                        'are $filename, $fullfilename, $sender, $receiver, $messageid and any message header such as $Subject')
    exchange_mode = fields.Selection(DATA_EXCHANGE_CHOICE,string='Exchange Mode',default='EDI_AS2')
    ftp_user = fields.Char(string='FTP User')
    ftp_passwd = fields.Char(string='FTP Password')
    @property
    def as2partner(self):
        """ Returns an object of pyas2lib's Partner class"""
        params = {
            "id": self.id,
            "as2_name": self.as2_name,
            "compress": self.compress,
            "sign": True if self.signature else False,
            "digest_alg": self.signature,
            "encrypt": True if self.encryption else False,
            "enc_alg": self.encryption,
            "mdn_mode": self.mdn_mode,
            "mdn_digest_alg": self.mdn_sign,
        }

        if self.signature_cert:
            params["verify_cert"] = bytes(b64decode(self.signature_cert.certificate))

            if self.signature_cert.certificate_ca:
                params["verify_cert_ca"] = bytes(self.signature_cert.certificate_ca)
            params["validate_certs"] = self.signature_cert.verify_cert

        if self.encryption_cert:
            params["encrypt_cert"] = bytes(b64decode(self.encryption_cert.certificate))
            if self.encryption_cert.certificate_ca:
                params["encrypt_cert_ca"] = bytes(b64decode(self.encryption_cert.certificate_ca))
            params["validate_certs"] = self.encryption_cert.verify_cert

        if self.confirmation_message:
            params["mdn_confirm_text"] = self.confirmation_message

        return As2Partner(**params)

    def send_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'msg.sendmsg',
            'context':{'partner':self.id},
            'view_mode': 'form',
            'target': 'new'
        }


# def get_message_store(instance, filename):
#     current_date = timezone.now().strftime("%Y%m%d")
#     if instance.direction == "OUT":
#         target_dir = os.path.join(
#             "messages", "__store", "payload", "sent", current_date
#         )
#     else:
#         target_dir = os.path.join(
#             "messages", "__store", "payload", "received", current_date
#         )
#     return "{0}/{1}".format(target_dir, filename)


class Message(models.Model):
    _name = 'message.message'
    _rec_name = 'message_id'
    DIRECTION_CHOICES =[
    ('IN', 'Inbound'),
    ('OUT', 'Outbound'),
                        ]
    STATUS_CHOICES = [
        ("S", "Success"),
        ("E", "Error"),
        ("W", "Warning"),
        ("P", "Pending"),
        ("R", "Retry"),
    ]
    MODE_CHOICES = [
        ("SYNC", "Synchronous"),
        ("ASYNC", "Asynchronous"),
    ]

    message_id = fields.Char(string='Message Id')
    direction = fields.Selection(DIRECTION_CHOICES,string='Direction')
    timestamp = fields.Datetime(string='Timestamp',default=lambda self: fields.datetime.now())

    status = fields.Selection(STATUS_CHOICES,string='Status')
    detailed_status = fields.Text(string='Detailed Status')

    organization = fields.Many2one('organization.organization', string="Organization",blank=True,ondelete='SET NULL')
    partner = fields.Many2one('partner.partner', blank=True,string='Partner', ondelete='SET NULL')

    headers = fields.Binary(string='Headers',attachment=True)
    headers_name = fields.Char(string='Headers Name')

    payload = fields.Binary(string='Payload',attachment=True)
    payload_name = fields.Char(string='Payload Name')

    compressed = fields.Boolean(string='Compressed')
    encrypted = fields.Boolean(string='Encrypted',default=False)

    signed = fields.Boolean(string='Signed', default=False)

    mdn_mode = fields.Selection(MODE_CHOICES,string='MDN Mode')

    mic = fields.Char(string='MIC',size=100,blank=True)
    retries = fields.Integer(blank=True)


    def create_from_as2message(
        self,
        as2message,
        payload,
        direction,
        status,
        filename=None,
        detailed_status=None,
    ):
        """Create the Message from the pyas2lib's Message object"""

        if direction == "IN":
            organization = as2message.receiver.id if as2message.receiver else None
            organization_dir = as2message.receiver.as2_name if as2message.receiver else None
            partner = as2message.sender.id if as2message.sender else None
            partner_dir = as2message.sender.as2_name if as2message.sender else None
        else:
            partner = as2message.receiver.id if as2message.receiver else None
            partner_dir = as2message.receiver.as2_name if as2message.receiver else None
            organization = as2message.sender.id if as2message.sender else None
            organization_dir = as2message.sender.as2_name if as2message.sender else None
        exist = self.env['message.message'].search([('message_id','=',as2message.message_id)])
        # print(f"PRINT  RECORD SUSPECTED :: partner : {partner},organization:{organization}")
        # print(f"exist:{exist},as2message.message_id:{as2message.message_id} ")
        if not filename:
            filename = "%s.msg" % uuid4()
        name = "%s.header" % filename

        content = as2message.headers_str

        content_payload = payload

        vals = dict(message_id=as2message.message_id,
            partner=partner,
            organization=organization,
            direction=direction,
            status=status,
            compressed=as2message.compressed,
            encrypted=as2message.encrypted,
            signed=as2message.signed,
            detailed_status=detailed_status,
            headers_name=name,
            headers=b64encode(content),
            payload_name=filename,
            payload=b64encode(content_payload),
            )
        # print(vals)
        if exist:
            id_ = self.env['message.message'].write(vals)
        else:
            id_ = self.env['message.message'].create(vals)


       # Save the payload to the inbox folder
        full_filename = None
       #  if direction == "IN" and status == "S":
       #      if DATA_DIR:
       #          dirname= os.path.join(
       #              DATA_DIR, "messages", organization_dir, "inbox", partner_dir
       #          )
       #      else:
       #          dirname= os.path.join("messages", organization_dir, "inbox", partner_dir)
       #
       #      if not self.partner.keep_filename or not filename:
       #          filename = f"{id_.message_id}.msg"
       #      full_filename = "".join([dirname, filename])
            # binary_format = bytearray(payload)
            # print(payload)
            #
            # with open(full_filename,'wb+') as f:
            #     f.write(binary_format)
            #     f.close()

        # import pdb;
        # pdb.set_trace()
        return id_, full_filename
    # class Meta:
    #     unique_together = ("message_id", "partner")
    sql_constraints = [
        ('name_uniq', 'unique(message_id, partner)', 'The partner and message_id Key is not Unique!'),
    ]

    @property
    def as2message(self):
        """ Returns an object of pyas2lib's Message class"""
        if self.direction == "IN":
            as2m = As2Message(
                sender=self.partner.as2partner, receiver=self.organization.as2org
            )
        else:
            as2m = As2Message(
                sender=self.organization.as2org, receiver=self.partner.as2partner
            )

        as2m.message_id = self.message_id
        as2m.mic = self.mic

        return as2m

    @property
    def status_icon(self):
        """ Return the icon for message status """
        if self.status == "S":
            return "admin/img/icon-yes.svg"
        elif self.status == "E":
            return "admin/img/icon-no.svg"
        elif self.status in ["W", "P", "R"]:
            return "admin/img/icon-alert.svg"
        else:
            return "admin/img/icon-unknown.svg"

    def send_message(self, header, payload):

        """ Send the message to the partner"""

        logger.info(
            'Sending message %s from organization %s to partner %s' %(self.message_id,self.organization.name,self.partner.name)

        )

        # Set up the http auth if specified in the partner profile
        auth = None
        if self.partner.http_auth:
            auth = (self.partner.http_auth_user, self.partner.http_auth_pass)

        # Send the message to the partner
        try:

            response = requests.post(
                self.partner.target_url,
                auth=auth,
                headers=header,
                data=payload,
                verify=self.partner.https_verify_ssl,
            )
            response.raise_for_status()
            print("GOT THIS RESPONSE FROM THERE:::::::",response.headers,response.body)
        except requests.exceptions.RequestException:
            print("GOt THis Exception in exception request:::::",requests.exceptions.RequestException)
            self.status = "R"
            self.detailed_status = (
                "Failed to send message, error:\n %s" % traceback.format_exc()
            )
        except Exception as e:
            print("Got thi unknown exception ::: ",e)
            return

        # Process the MDN based on the partner profile settings

        if self.partner.mdn:
            if self.partner.mdn_mode == "ASYNC":
                self.status = "P"
            else:
                # Process the synchronous MDN received as response

                # Get the response headers, convert key to lower case
                # for normalization
                mdn_headers = dict(
                    (k.lower().replace("_", "-"), response.headers[k])
                    for k in response.headers
                )

                # create the mdn content with message-id and content-type
                # header and response content
                mdn_content = (
                    'message-id: %s\n' % mdn_headers.get("message-id", self.message_id)
                )
                mdn_content += 'content-type: %s\n\n' % mdn_headers["content-type"]
                mdn_content = mdn_content.encode("utf-8") + response.content

                # Parse the as2 mdn received
                logger.info(
                    "Received MDN response for message %s with content: %s" % (self.message_id,mdn_content)
                )
                as2mdn = As2Mdn()
                mdn_status, mdn_detailed_status = as2mdn.parse(
                    mdn_content, lambda x, y: self.as2message
                )

                # Update the message status and return the response
                if mdn_status == "processed":
                    self.status = "S"
                    run_post_send(self)
                else:
                    self.status = "E"
                    self.detailed_status = (
                        "Partner failed to process message: %s" % mdn_detailed_status
                    )
                if mdn_detailed_status != "mdn-not-found":
                    self.env['mdn.mdn'].create_from_as2mdn(
                        as2mdn=as2mdn, message_id=self.id, status="R"
                    )
        else:
            # No MDN requested mark message as success and run command
            self.status = "S"
            run_post_send(self)







# def get_mdn_store(instance, filename):
#     current_date = timezone.now().strftime("%Y%m%d")
#     if instance.status == "S":
#         target_dir = os.path.join("messages", "__store", "mdn", "sent", current_date)
#     else:
#         target_dir = os.path.join(
#             "messages", "__store", "mdn", "received", current_date
#         )
#
#     return "{0}/{1}".format(target_dir, filename)


class Mdn(models.Model):
    _name = 'mdn.mdn'
    _rec_name = 'mdn_id'
    STATUS_CHOICES = [
        ("S", "Sent"),
        ("R", "Received"),
        ("P", "Pending"),
    ]


    mdn_id = fields.Char(string='MDN Id',size=255)

    message = fields.Many2one('message.message',string='Massage')
    _sql_constraints = [
        ('message_unique', 'UNIQUE(message)',
         'The message already exists !'),
    ]

    timestamp = fields.Datetime(string='Timestamp',default=lambda self: fields.datetime.now())

    status = fields.Selection(STATUS_CHOICES,string='Status')

    signed = fields.Boolean(string="Signed",default=False)

    return_url = fields.Char(string='Return Url',blank=True)

    headers = fields.Binary(string='Headers')
    headers_filename = fields.Char(string='Header Filename',required=True)

    payload = fields.Boolean(string='Payload' ,)
    payload_filename = fields.Char(string='Payload Filename')


    def create_from_as2mdn(self, as2mdn, message_id, status, return_url=None):
        """Create the MDN from the pyas2lib's MDN object"""
        signed = True if as2mdn.digest_alg else False
        exist = self.env['mdn.mdn'].search([('message.id', '=', message_id)])
        filename = "%s.mdn" % uuid4()

        vals = dict(
                message=message_id,
                mdn_id=as2mdn.message_id,
                status=status,
                signed=signed,
                return_url=return_url,
                headers_filename="%s.header" % filename,
                headers=as2mdn.headers_str,
                payload_filename=filename,
                payload=as2mdn.content,
            )
        if exist:
            mdn = exist.write(vals)
        else:
            mdn = exist.create(vals)

        return mdn


    def send_async_mdn(self):
        """ Send the asynchronous MDN to the partner"""

        # convert the mdn headers to dictionary
        headers = HeaderParser().parsestr(self.headers.read().decode())

        # Send the mdn to the partner
        try:
            response = requests.post(
                self.return_url, headers=dict(headers.items()), data=self.payload.read()
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            return

        # Update the status of the MDN
        self.status = "S"
