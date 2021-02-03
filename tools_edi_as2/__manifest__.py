# -*- coding: utf-8 -*-
{
    'name': "Odoo AS2 App",

    'summary': """
        This app allows to send message from organization to partner using as2 edi encyption technique""",

    'description': """
        this is an AS2 messanging service use encryption to send and receive method
    """,

    'author': "Wen Energy Systems",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Message',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        'static/forms/as2send_form_menu.xml',
        'static/forms/as2send_template.xml',
        'static/forms/as2send_success.xml',
        'wizards/success.xml',
        'wizards/send_message.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}