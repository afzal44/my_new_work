# -*- coding: utf-8 -*-
{
    'name': "Time Doctor Integration",

    'summary': """
        This module is used to integrate Time Doctor with Odoo ERP to export Projects and task,import Worklogs and screenshots""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Abhishek(@wen-lighting)",
    'website': "https://wenlighting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','project','hr_timesheet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/instance_view.xml',
        'views/project_view.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application' : True,
    'active': True,
}
