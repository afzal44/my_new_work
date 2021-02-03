# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TimeDoctorCompany(models.Model):
    _name = 'time_doctor_company'

    name = fields.Char('Company')
    company_id = fields.Char('Time Doctor ID',readonly=True)
    time_doctor_users_ids = fields.Many2many(comodel_name='time_doctor_user',relation='time_doctor_company_user_rel',column1='company_id',column2='user_id',string='Users')
    instance_id = fields.Many2one(comodel_name='time_doctor_instance',string='Time Doctor Instance')
    creation_date = fields.Datetime(string='Company Create Date')
    subscription_expiry_date = fields.Datetime(string='Subscription Expiry Date')
    odoo_company_id = fields.Many2one(comodel_name='res.company',string='Odoo Company')



class TimeDoctorUser(models.Model):
    _name = 'time_doctor_user'

    name = fields.Char('Name')
    user_name = fields.Char('User Name/Login Id')
    user_id = fields.Char('Time Doctor ID',readonly=True)
    odoo_user_id = fields.Many2one(comodel_name='res.users',string='Internal/Odoo User')
    password = fields.Integer('Password')
    is_super_admin = fields.Boolean('Is Super Admin',default=False)
    active = fields.Boolean('Active',default=True)
    online = fields.Boolean('Online',default=False)
    emailconfirmed = fields.Boolean('Email Confirmed',default=False)
    company_ids = fields.Many2many(comodel_name='time_doctor_company',relation='time_doctor_company_user_rel',column1='user_id',column2='company_id',string='Companies')



