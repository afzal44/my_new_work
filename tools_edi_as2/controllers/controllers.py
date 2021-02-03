# -*- coding: utf-8 -*-
from odoo import http
import logging
from odoo.http import request,Response
from odoo.addons.tools_edi_as2.pyas2lib import Mdn as As2Mdn
from odoo.addons.tools_edi_as2.pyas2lib import Message as As2Message
from odoo.addons.tools_edi_as2.pyas2lib.exceptions import DuplicateDocument
import json
from odoo.addons.tools_edi_as2.models.utils import run_post_send,run_post_receive
logger = logging.getLogger("tools_edi_as2")


class ReceiveAs2Message(http.Controller):
    """
          Class receives AS2 requests from partners.
          Checks whether its an AS2 message or an MDN and acts accordingly.
       """

    @staticmethod
    def find_message(message_id, partner_id):
        """ Find the message using the message_id  and return its
         pyas2 version"""
        print("@staticmethod@staticmethod@staticmethod@staticmethod:::find_message::",message_id, partner_id)
        message = request.env['message.message'].search([('message_id','=',message_id),('partner_id','=',partner_id.strip())],limit=1)
        if message:
            return message.as2message

    @staticmethod
    def check_message_exists(message_id, partner_id):
        """ Check if the message already exists in the system """
        print("@staticmethod@staticmethod@staticmethod@staticmethod:::check_message_exists::", message_id, partner_id)
        message = request.env['message.message'].search([('message_id', '=', message_id), ('partner.as2_name','=', partner_id)])
        if message:
            return message
        else:
            return False


    @staticmethod
    def find_organization(org_id):
        """ Find the org using the As2 Id and return its pyas2 version"""
        print("@staticmethod@staticmethod@staticmethod@staticmethod:: find_organization::",org_id)
        org = request.env['organization.organization'].search([('as2_name', '=', org_id)], limit=1)
        # org = Organization.objects.filter(as2_name=org_id).first()
        if org:
            return org.as2org

    @staticmethod
    def find_partner(partner_id):
        """ Find the partner using the As2 Id and return its pyas2 version"""
        print("@staticmethod@staticmethod@staticmethod@staticmethod:: find_partner::", partner_id)
        partner = request.env['partner.partner'].search([('as2_name', '=', partner_id)], limit=1)
        if partner:
            return partner.as2partner

    @http.route('/as2receive', type='http',methods=['POST','GET'], auth='public', csrf=False,website=True)
    def as2recieve(self,*args, **kwargs):

        # extract the  headers from the http request

        if http.request.httprequest.method == 'GET':
            return http.request.render('tools_edi_as2.index')

        as2headers = str(request.httprequest.headers)
        data = request.httprequest.data
        # build the body along with the headers
        request_body = as2headers.encode() + data

        logger.info(
            f'Received an HTTP POST from {request.httprequest.remote_addr} '
            f"with payload :\n{len(request_body)}"
        )

        # First try to see if this is an MDN
        logger.info("Check to see if payload is an Asynchronous MDN.")
        as2mdn = As2Mdn()

        # Parse the mdn and get the message status
        status, detailed_status = as2mdn.parse(request_body, self.find_message)

        if not detailed_status == "mdn-not-found":
            message = request.env['message.message'].search([('message_id','=',as2mdn.orig_message_id),('direction', '=', "OUT")])

            logger.info(
                f"Asynchronous MDN received for AS2 message {as2mdn.message_id} to organization "
                f"{message.organization.as2_name} from partner {message.partner.as2_name}"
            )

            # Update the message status and return the response
            if status == "processed":
                message.status = "S"
                run_post_send(message)
            else:
                message.status = "E"
                message.detailed_status = (
                    f"Partner failed to process message: {detailed_status}"
                )
            # Save the message and create the mdn
            request.env['mdn.mdn'].create_from_as2mdn(as2mdn=as2mdn, message_id=message.id, status="R")

            return Response("AS2 ASYNC MDN has been received")

        else:
            logger.info("Payload is not an MDN parse it as an AS2 Message")
            as2message = As2Message()

            status, exception, as2mdn = as2message.parse(
                request_body,
                self.find_organization,
                self.find_partner,
                self.check_message_exists,
            )

            logger.info(
               'Received an AS2 message with id %s for organization %s from partner %s.' % (as2message.headers.get("message-id"),as2message.headers.get("as2-to")
                                                                    ,as2message.headers.get("as2-from"))
            )

            # In case of duplicates update message id
            if isinstance(exception[0], DuplicateDocument):
                as2message.message_id += "_duplicate"

            # Create the Message and MDN objects

            message, full_fn = request.env['message.message'].create_from_as2message(
                as2message=as2message,
                payload=as2message.content,
                direction="IN",
                filename=as2message.payload.get_filename(),
                status="S" if status == "processed" else "E",
                detailed_status=exception[1],
            )

            # run post receive command on success
            if status == "processed":
                run_post_receive(message, full_fn)

            # Return the mdn in case of sync else return text message
            if as2mdn and as2mdn.mdn_mode == "SYNC":
                message.mdn = request.env['mdn.mdn'].create_from_as2mdn(
                    as2mdn=as2mdn, message_id=message.id, status="S"
                )

                response= Response(as2mdn.content)

                for key, value in as2mdn.headers.items():
                    if key == 'user-agent':
                        val = 'Odoo EDI AS2 Message'
                        response.headers[key] = val
                        continue
                    response.headers[key] = value

                # return response)
                # return True

                return response

            elif as2mdn and as2mdn.mdn_mode == "ASYNC":
                request.env['mdn.mdn'].create_from_as2mdn(
                    as2mdn=as2mdn,
                    message_id=message.id,
                    status="P",
                    return_url=as2mdn.mdn_url,
                )
            Response.status = '200'
            return Response("AS2 message has been received")


# class SendAs2Message(http.Controller):
#     @http.route(['/as2send/form'], type='http', auth="public", website=True)
#     def as2send_form(self, **post):
#         organization_rec = request.env['organization.organization'].search([])
#         partner_rec = request.env['partner.partner'].search([])
#         return request.render("tools_edi_as2.tmp_as2send_form", {'organization_rec':organization_rec,
#                                                                  'partner_rec':partner_rec})
#
#     @http.route(['/as2send/form/submit'], type='http', auth="public", website=True,csrf=False)
#     def customer_form_submit(self, **post):
#         print(post)
#         print(request.httprequest.form.fromkeys())
#
#
#         data = {'organization': post.get('organization_id'),
#                 'partner': post.get('partner_id'),
#                 'file': post.get('attachment'),
#
#                 }
#         for i in data:
#             print(f"PRINTING FROM GETTING DATA FROM FORM SUBMIT : {i},{data[i]} ,{type(i)}")
#         # inherited the model to pass the values to the model from the form#
#         return request.render("tools_edi_as2.tmp_as2send_form_success")
        # finally send a request to render the thank you page#

    # as2send / form / submit
#     template_name = "pyas2/send_as2_message.html"
#     form_class = SendAs2MessageForm
#     success_url = reverse_lazy(
#         f"admin:{Message._meta.app_label}_{Message._meta.model_name}_changelist"
#     )
#
#     def get_context_data(self, **kwargs):
#         context = super(SendAs2Message, self).get_context_data(**kwargs)
#         context.update(
#             {
#                 "opts": Partner._meta,
#                 "change": True,
#                 "is_popup": False,
#                 "save_as": False,
#                 "has_delete_permission": False,
#                 "has_add_permission": False,
#                 "has_change_permission": False,
#             }
#         )
#         return context
#
#     def form_valid(self, form):
#         # Send the file to the partner
#         payload = form.cleaned_data["file"].read()
#         as2message = As2Message(
#             sender=form.cleaned_data["organization"].as2org,
#             receiver=form.cleaned_data["partner"].as2partner,
#         )
#         logger.debug(
#             f'Building message from {form.cleaned_data["file"].name} to send to partner '
#             f"{as2message.receiver.as2_name} from org {as2message.sender.as2_name}."
#         )
#         as2message.build(
#             payload,
#             filename=form.cleaned_data["file"].name,
#             subject=form.cleaned_data["partner"].subject,
#             content_type=form.cleaned_data["partner"].content_type,
#             disposition_notification_to=form.cleaned_data["organization"].email_address
#             or "no-reply@pyas2.com",
#         )
#
#         message, _ = Message.objects.create_from_as2message(
#             as2message=as2message,
#             payload=payload,
#             filename=form.cleaned_data["file"].name,
#             direction="OUT",
#             status="P",
#         )
#         message.send_message(as2message.headers, as2message.content)
#         if message.status in ["S", "P"]:
#             messages.success(
#                 self.request, "Message has been successfully send to Partner."
#             )
#         else:
#             messages.error(
#                 self.request,
#                 "Message transmission failed, check Messages tab for details.",
#             )
#         return super(SendAs2Message, self).form_valid(form)
#
#
# class DownloadFile(View):
#     """ A generic view for downloading files such as payload, certificates..."""
#
#     def get(self, request, obj_type, obj_id, *args, **kwargs):
#         filename = ""
#         file_content = ""
#         # Get the file content based
#         if obj_type == "message_payload":
#             obj = get_object_or_404(Message, pk=obj_id)
#             filename = os.path.basename(obj.payload.name)
#             file_content = obj.payload.read()
#
#         elif obj_type == "mdn_payload":
#             obj = get_object_or_404(Mdn, pk=obj_id)
#             filename = os.path.basename(obj.payload.name)
#             file_content = obj.payload.read()
#
#         elif obj_type == "public_cert":
#             obj = get_object_or_404(PublicCertificate, pk=obj_id)
#             filename = obj.name
#             file_content = obj.certificate
#
#         elif obj_type == "private_key":
#             obj = get_object_or_404(PrivateKey, pk=obj_id)
#             filename = obj.name
#             file_content = obj.key
#
#         # Return the file contents as attachment
#         if filename and file_content:
#             response = HttpResponse(content_type="application/x-pem-file")
#             disposition_type = "attachment"
#             response["Content-Disposition"] = (
#                 disposition_type + "; filename=" + filename
#             )
#             response.write(bytes(file_content))
#             return response
#         else:
#             raise Http404()