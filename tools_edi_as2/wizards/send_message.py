from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.addons.tools_edi_as2.pyas2lib import Message as As2Message
import logging
from base64 import b64decode,b64encode
import ftplib
import requests
import subprocess
from configparser import ConfigParser
logger = logging.getLogger(__name__)

class send_message_wizard(models.TransientModel):
    _name = "msg.sendmsg"
    _description = 'Wizard to send message'
    Organization = fields.Many2one(comodel_name="organization.organization",string="Organization")
    Partner = fields.Many2one(comodel_name="partner.partner",string="Partner")
    File = fields.Binary(string='File',required=True)
    file_name = fields.Char(string='File Name',required=True,default='filename')

    def send_confirm_message(self,status):
        if status:
            message_id = self.env['message.wizard'].create(
                {'message': "Message has been successfully send to Partner."})
            return {
                'name': 'Successful',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                # pass the id
                'res_id': message_id.id,
                'target': 'new'
            }
        else:
            message_id = self.env['message.wizard'].create(
                {'message': "Message transmission failed, check Messages tab for details."})
            return {
                'name': 'Failed',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                # pass the id
                'res_id': message_id.id,
                'target': 'new'
            }

    def send_message(self,header):
        """ Send the message to the partner"""
        if self.Partner.exchange_mode == 'FTP':
            session = ftplib.FTP(self.Partner.target_url, self.Partner.ftp_user, self.Partner.ftp_passwd)
            # file = open('kitten.jpg', 'rb')  # file to send
            session.storbinary(self.file_name, self.File)  # send the file
            # file.close()  # close file and FTP
            session.quit()
        elif self.Partner.exchange_mode == 'REST_API':
            files = {"file": (self.file_name, self.File)}
            resp = requests.post(self.Partner.target_url, files=files)
            if resp.status_code == 200:
                self.send_confirm_message(True)
            else:
                self.send_confirm_message(False)
        else:
            payload = b64decode(self.File)
            as2message = As2Message(
                sender=self.Organization.as2org,
                receiver=self.Partner.as2partner,
            )

            logger.info(
                "Building message from %s to send to partner %s from org %s." % (self.file_name,as2message.receiver.as2_name,as2message.sender.as2_name)
            )

            as2message.build(
                payload,
                filename=self.file_name,
                subject=self.Partner.subject,
                content_type=self.Partner.content_type,
                disposition_notification_to=self.Organization.email_address
                                            or "no-reply@pyas2.com",
            )
            # print(" After as2message build", vars(as2message) )
            message, _ = self.env['message.message'].create_from_as2message(
                as2message=as2message,
                payload=payload,
                filename=self.file_name,
                direction="OUT",
                status="P",
            )
            message.send_message(as2message.headers, as2message.content)
            if message.status in ["S", "P"]:
                self.send_confirm_message(True)
            else:
               self.send_confirm_message(False)

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Message', required=True)

    @api.multi
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}


class certificate_creation(models.TransientModel):
    _name = 'cert.data'
    _description = 'Wizard to Generate Certificate'
    organization = fields.Many2one(comodel_name="organization.organization", string="Organization")
    countryName = fields.Char(string='Country Name',size=2)
    stateOrProvinceName = fields.Char(string='State or Province')
    localityName = fields.Char(string='Locality Name')
    organizationName = fields.Char(string='Organization Name')
    organizationalUnitName = fields.Char(string='Org. Unit Name')
    commonName = fields.Char(string='Common Name')
    emailAddress = fields.Char(string='Email')
    passphrase = fields.Char(string='PassPhrase',default='Odoo_EDI',help='This field requires a password for decryption keys deafult value is : Odoo_EDI')
    @api.model
    def default_get(self,vals):
        org_id = self._context.get('active_id')
        print("ORGANIZATID :::::::::::::::::::::::",org_id,vals)
        return {'organization':org_id}


    def generate_cert(self):
        # import pdb;pdb.set_trace()
        # config_object = ConfigParser()
        conf_file = 'openssl_conf.cnf'
        private_key = "%s_private.pem" % self.organization.as2_name
        public_key = "%s_public.pem" % self.organization.as2_name
        cmd1 = "cat %s >> %s" % (public_key,private_key)
        cmd = "openssl req -x509 -newkey rsa:2048 -sha256 -keyout %s -out %s -days 365 -passout pass:%s -subj '/C=%s/ST=%s/L=%s/O=%s/CN=%s' && %s" % \
              (private_key,public_key,self.passphrase,self.countryName,self.stateOrProvinceName,self.localityName,self.organizationName,self.commonName,cmd1)
        print("CMDCMDCMDCMDCMDCMDCMDCMD CREATED :: ",cmd)

        p=subprocess.Popen(cmd, shell=True)
        print("AFTER SUB PROCESS RUNNING :: ")
        p.wait()


        private_key_data = b64encode(open(private_key,'rb').read())
        pvt_cer_id = self.env['privatekey.privatekey'].create({'key':private_key_data.decode('ascii'),
                                                  'file_name':private_key,
                                                'key_pass':self.passphrase})
        pub_cer_id = self.env['publiccertificate.publiccertificate'].create({'certificate': private_key_data.decode('ascii'),
                                                               'file_name': private_key})
        self.organization.encryption_key = pvt_cer_id.id
        self.organization.signature_key = pvt_cer_id.id
        message_id = self.env['message.wizard'].create(
                {'message': "Certificate Generated and added to this Organization Successfully,"
                            "Also added in private and public certificate lists"})
        return {
                'name': 'Successful',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                # pass the id
                'res_id': message_id.id,
                'target': 'new'
            }