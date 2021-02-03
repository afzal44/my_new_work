# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning
#
#class Projects(models.Model):
#    _inherit='project.project'
#
#    _sql_constraints = [
#        ('name_uniq', 'UNIQUE (name,user_id)',  'You can not have two Projects with the same name for one Manager!')
#    ]
#
#class ProjectTask(models.Model):
#    _inherit='project.task'
#
#    @api.model
#    def create(self,vals):
#        rec = super(ProjectTask,self).create(vals)
#        timecompany = self.env['time_doctor_company'].search([('odoo_company_id','=',self.env.user.company_id.id)])
#        timeuser = self.env['time_doctor_user'].search([('odoo_user_id','=',rec.user_id.id)])
#        timeproject = self.env['time_doctor_projects'].search([('odoo_project_id','=',rec.project_id.id)])
#        time_task = self.env['time_doctor_task'].create({
#            'name':rec.name,
#            'odoo_task_id':rec.id,
#            'project_id':timeproject.id,
#            'status':rec.stage_id.name,
#            'assinged_to':timeuser.id,
#            'odoo_user_assigned_to':rec.user_id.id,
#            'company_id':timecompany.id,
#            })
#        return rec
#    
#    @api.model
#    def write(self,vals):
#        print("\n\n\n",vals)
#        if 'user_id' in vals:
#            timetask = self.env['time_doctor_task'].search([('odoo_task_id','=',self.id)])
#            timeuser = self.env['time_doctor_user'].search([('odoo_user_id','=',vals.get('user_id'))])
#            timetask.write({'assinged_to':timeuser.id,'odoo_user_assigned_to':vals.get('assinged_to')})
#        rec = super(ProjectTask,self).write(vals)
#        return rec
#
#
class TimeDoctorProjects(models.Model):
    _name = 'time_doctor_projects'

    name = fields.Char('Project')
    project_id = fields.Char('Time Doctor ID',readonly=True)
    owner_id = fields.Many2one(comodel_name='time_doctor_user',string='Time Doctor User/Owner')
    odoo_project_id = fields.Many2one(comodel_name='project.project',string='Odoo Project')
    time_doctor_users_ids = fields.Many2many(comodel_name='time_doctor_user',relation='time_doctor_project_user_rel',column1='project_id',column2='user_id',string='Users')
    description = fields.Text('Description')
    deleted = fields.Boolean('Deleted',default=False)
    task_ids = fields.One2many(comodel_name='time_doctor_task',inverse_name='project_id',string='Tasks')
    company_id = fields.Many2one(comodel_name='time_doctor_company',string='Company ID')



class TimeDoctorTask(models.Model):
    _name = 'time_doctor_task'

    name = fields.Char('Name')
    project_id =  fields.Many2one(comodel_name='time_doctor_projects',string='Time Doctor Project')
    task_id = fields.Char('Time Doctor ID',readonly=True)
    odoo_task_id = fields.Many2one(comodel_name='project.task',string='Odoo Task')
    status = fields.Char('Status',readonly=True)
    assinged_to = fields.Many2one(comodel_name='time_doctor_user',string='Time Doctor User/Owner')
    odoo_user_assigned_to = fields.Many2one(comodel_name='res.users',string='Odoo User Assigned to')
    timesheet_ids = fields.One2many(comodel_name='time_doctor_worklogs',inverse_name='task_id',string='Timesheet')
    company_id = fields.Many2one(comodel_name='time_doctor_company',string='Company ID')

    @api.model
    def create(self,vals):
        rec = super(TimeDoctorTask,self).create(vals)
        print("create time task",self.env.context)
        if not self.env.context.get('from_update',False):
            instance=rec.company_id.instance_id
            project = self.env['time_doctor_projects'].search([('odoo_project_id','=',rec.odoo_task_id.project_id.id),('owner_id','=',rec.assinged_to.id)])
            if not project:
                project_id = instance.create_project(rec)
                project = self.env['time_doctor_projects'].create({
                   'project_id':project_id,
                   'name':rec.odoo_task_id.project_id.name,
                   'description':'',
                   'owner_id':rec.assinged_to.id,
                   'odoo_project_id':rec.odoo_task_id.project_id.id,
                   'deleted':False
                   
                    })
            if not rec.project_id.id==project.id:
                rec.project_id = project
            rec.task_id = instance.create_task(rec)
        return rec

    @api.model
    def write(self,vals):
        if 'assinged_to' in vals:
            instance=self.company_id.instance_id
            timeuser = self.env['time_doctor_user'].search([('odoo_user_id','=',vals.get('assinged_to'))])
            print("\n\n\n",instance)
            if instance.add_user_to_project(self.company_id.company_id,self.project_id.project_id,timeuser.user_id):
                rec = super(TimeDoctorTask,self).write(vals)
            else:
                raise Warning("Can't Assign rights to user in time doctor!!!")
        return rec


    


class TimeDoctorTimeSheet(models.Model):
    _name = 'time_doctor_worklogs'

    project_id =  fields.Many2one(comodel_name='time_doctor_projects',string='Time Doctor Project')
    task_id =  fields.Many2one(comodel_name='time_doctor_task',string='Time Doctor Task')
    user_id = fields.Many2one(comodel_name='time_doctor_user',string='Time Doctor User')
    mode = fields.Char('Mode')
    time = fields.Float('Working hours')
    start_time = fields.Datetime(string='Start Datetime')
    company_id = fields.Many2one(comodel_name='time_doctor_company',string='Company ID')





