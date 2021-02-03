# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime,timedelta,date
import requests

time_doctor_api_base_url = 'https://api.staff.com/api/1.0'
headers = {
'Connection': 'keep-alive',
'Accept': 'application/json, text/plain, */*',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
'Content-Type': 'application/json',
'Origin': 'https://2.timedoctor.com',
'Sec-Fetch-Site': 'cross-site',
'Sec-Fetch-Mode': 'cors',
'Sec-Fetch-Dest': 'empty',
'Referer': 'https://2.timedoctor.com/',
'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        }
end_points = {
        'self_check':'/users/me',
        'login':'/authorization/login?company=',
        'user_details':'/users',
        'users_details_all':'/users/all',
        'projects':'/projects',
        'worked-project':'/stats/project-total',
        'tasks':'/tasks',
        'worked-task':'/stats/task-total',
        'timesheet':'/activity/worklog',
        'user-project-access':'/projects/{project_id}/users/{user_id}'
        }

class TimeDoctorInstance(models.Model):
    _name = 'time_doctor_instance'

    name = fields.Char('Name')
    login_id = fields.Char('Time Doctor Login Id',required=True)
    password = fields.Char('Time Doctor Login Password',required=True)
    token = fields.Char('Time Doctor Access Token',readonly=True)
    token_expire_date = fields.Datetime('Token Expiry Date',readonly=True)
    active = fields.Boolean('Active',default=True)
    time_doctor_user_id = fields.Many2one(comodel_name='time_doctor_user',string='User',readonly=True)
    company_ids = fields.One2many(comodel_name='time_doctor_company',inverse_name='instance_id',string='Company_ids')

    def validate_companies(self,companies):
        if not companies or not isinstance(companies,type(self.env['time_doctor_company'])):
            companies = self.company_ids
        return companies

    def is_token_expired(self):
        print("\n\n\n\n\n",self)
        data = {
                'token':self.token,
                'company':self.company_ids[0].company_id,
                'task-project-names': False
                }
        zero_hour = timedelta(minutes=2)
        if (self.token_expire_date-datetime.now())<zero_hour:
            return True
        else:
            self_response = requests.get(time_doctor_api_base_url+end_points['self_check'],params=data,headers=headers)
            print("\n\n\n\n",self_response.text)
            if self_response.status_code == 200:
                return False
            else:
                return True

    def login(self):
        data={"email":self.login_id,"password":self.password,"deviceId":"Odoo-ERP","no-workspaces":1}
        response = requests.post(time_doctor_api_base_url+end_points['login'],json=data,headers=headers)
        if response.status_code == 200:
            res_data = response.json().get('data')
            instance_data = {
                    'token':res_data.get('token'),
                    'token_expire_date':res_data.get('expires'),
                    'active':res_data.get('active'),
                    'name':('').join([self.name.split('(')[0] if self.name else '' ,' (',res_data.get('name'),')'])
                    }

            company_details = res_data.get('companies',None)
            company_data = []
            if company_details:
                for company in company_details:
                    old_company_rec = self.company_ids.filtered(lambda cmpny:cmpny.company_id==company.get('id'))
                    company_rec_data = {
                            'name':company.get('name'),
                            'company_id':company.get('id'),
                            'creation_date':company.get('companyCreatedAt'),
                            'subscription_expiry_date':company.get('subscription').get('expires') if company.get('subscription',False) else False,
                            }
                    if not old_company_rec:
                        company_data.append((0,0,company_rec_data))
                    else:
                        old_company_rec.write(company_rec_data)
            instance_data['company_ids']=company_data
            super_admin = self.time_doctor_user_id
            if not super_admin:
                super_admin = self.env['time_doctor_user'].create({
                    'name':res_data.get('name'),
                    'user_id':res_data.get('id'),
                    'is_super_admin':True,
                    'active':res_data.get('active'),
                    'user_name':res_data.get('email'),
                    'emailconfirmed':res_data.get('emailconfirmed'),

                                                           })
            instance_data['time_doctor_user_id']=super_admin.id
            self.write(instance_data)

    def get_task_details(self,company,get_all=True):
        data=[]
        params={
                'company': company.company_id,
                'show-integration': 'true', 
                'token': self.token,
                }
        if self.is_token_expired():
            self.login()
        project_reponse = requests.get(time_doctor_api_base_url+end_points['tasks'],params=params,headers=headers)
        if project_reponse.status_code==200:
            data = project_reponse.json().get('data',[])
        return data


    def get_projects_details(self,company,get_all=True):
        data=[]
        params={
                'company': company.company_id,
                'show-integration': 'true', 
                'token': self.token,
                'detail': 'users', 
                'all': 'true'}
        if self.is_token_expired():
            self.login()
        project_reponse = requests.get(time_doctor_api_base_url+end_points['projects'],params=params,headers=headers)
        if project_reponse.status_code==200:
            data = project_reponse.json().get('data',[])
        return data


    def get_user_data(self,company,user_ids=[],level='info'):
        data=[]
        if self.is_token_expired():
            self.login()
        params = {
               'company':company.company_id,
               'token':self.token,
               'self': 'include',
               'page': 0,
               'limit': 500,
               'detail':level
                }
        if user_ids:
            params.update({
                'users':user_ids
                })
        user_response = requests.get(time_doctor_api_base_url+end_points['user_details'],params=params,headers=headers)
        if user_response.status_code==200:
            data = user_response.json().get('data',{})
        return data
             

    def get_timesheet(self,company,user_ids=[],from_date=False,to_date=False):
        start_time = datetime.strptime(from_date,'%Y-%m-%d') if from_date else datetime.now()-timedelta(days=1,hours=1)
        end_time = datetime.strptime(to_date,'%Y-%m-%d') if to_date else datetime.now()
        res = []
        from_date = start_time
        while(end_time-from_date > timedelta(days=1)):
            to_date = from_date+timedelta(days=1)
            data=[]
            if self.is_token_expired():
                self.login()
            params = {
                   'company':company.company_id,
                   'token':self.token,
                   'self': 'include',
                   'from': from_date.strftime('%Y-%m-%d'),
                   'to': to_date.strftime('%Y-%m-%d'),
                   'user':(',').join(user_ids)
                    }
            user_response = requests.get(time_doctor_api_base_url+end_points['timesheet'],params=params,headers=headers)
            if user_response.status_code==200:
                data = user_response.json().get('data',{})
                for rec in map(lambda x:x,data):
                    res+=rec
            from_date = to_date
        return res

    def sync_users(self,companies=False,users=[]):
        companies = self.validate_companies(companies)
        for company in companies:
            user_data = self.get_user_data(company,users)
            for user in user_data:
                user_rec_data = {
                    'name':user.get('name'),
                    'user_id':user.get('id'),
                    'active':user.get('active'),
                    'user_name':user.get('email'),
                    'emailconfirmed':user.get('emailconfirmed'),
                    'online':user.get('lastTrack',{}).get('online',False),
                                                           }
                old_user_rec = company.time_doctor_users_ids.filtered(lambda usr:usr.user_id==user.get('id'))
                if not old_user_rec:
                    old_user_rec = self.env['time_doctor_user'].search([('user_id','=',user.get('id'))])
                    if not old_user_rec:
                         old_user_rec =  self.env['time_doctor_user'].create(user_rec_data)
                    company.write({'time_doctor_users_ids':[(4,old_user_rec.id)]})
                else:
                    old_user_rec.write(user_rec_data)
                odoo_user = self.env['res.users'].search([('login','=',old_user_rec.user_name)])
                if odoo_user:
                    old_user_rec.odoo_user_id=odoo_user

    def sync_projects(self,companies=False,users=[]):
        companies = self.validate_companies(companies)
        for company in companies:
            project_data = self.get_projects_details(company)
            for project in project_data:
                rec_user = self.env['time_doctor_user'].search([('user_id','=',project.get('creatorId'))])
                rec_data = {
                        'project_id':project.get('id'),
                        'name':project.get('name'),
                        'description':project.get('description'),
                        'owner_id':rec_user.id if rec_user else False,
                        'deleted':project.get('deleted')
                        }
                project_rec = self.env['time_doctor_projects'].search(['|',('name','=',project.get('name')),('project_id','=',project.get('id'))])
                rec_project = self.env['project.project'].search([('id','=',project_rec.odoo_project_id.id)])
                if not project_rec:
                    project_rec = self.env['time_doctor_projects'].create(rec_data)
                if not rec_project:
                    rec_project = self.env['project.project'].search([('name','=',project.get('name')),('user_id','=',rec_user.odoo_user_id.id)])
                    if rec_project:
                        project_rec.write({'odoo_project_id':rec_project.id})
        self.sync_tasks(companies,users)

    def sync_tasks(self,companies=False,users=[]):
        companies = self.validate_companies(companies)
        for company in companies:
            task_data = self.get_task_details(company)
            for task in task_data:
                rec_project = self.env['time_doctor_projects'].search([('project_id','=',task.get('project',{}).get('id',False))])
                rec_task = self.env['time_doctor_task'].search([('task_id','=',task.get('id',False))])
                task_rec_data = {
                        'name':task.get('name'),
                        'project_id':rec_project.id,
                        'task_id':task.get('id'),
                        'status':task.get('status'),
                        'company_id':company.id,

                        }
                if rec_task:
                    rec_task.write(task_rec_data)
                else:
                    rec_task = self.with_context({'from_update':1}).env['time_doctor_task'].create(task_rec_data)



    def sync_timesheet(self,companies=False,users=[],from_date=False,to_date=False):
        companies = self.validate_companies(companies)
        for company in companies:
            timesheet_data = self.get_timesheet(company,[u.user_id for u in company.time_doctor_users_ids],from_date,to_date)
            count=0
            for timesheet in timesheet_data:
                rec_project = self.env['time_doctor_projects'].search([('project_id','=',timesheet.get('projectId'))])
                rec_task = self.env['time_doctor_task'].search([('task_id','=',timesheet.get('taskId'))])
                rec_user = self.env['time_doctor_user'].search([('user_id','=',timesheet.get('userId'))])
                old_rec = self.env['time_doctor_worklogs'].search([('start_time','=',timesheet.get('start')),('project_id','=',rec_project.id),('task_id','=',rec_task.id),('user_id','=',rec_user.id)])
                count+=1
                rec_data = {
                        'project_id':rec_project.id,
                        'task_id':rec_task.id,
                        'user_id':rec_user.id,
                        'mode':timesheet.get('mode'),
                        'time':round(timesheet.get('time')/3600,5),
                        'start_time':timesheet.get('start')
                        }
                if not old_rec:
                    old_rec=self.env['time_doctor_worklogs'].create(rec_data)
                else:
                    old_rec.write(rec_data)
                self.env.cr.commit()

    def create_task(self,task=False):
        if self.is_token_expired():
            self.login()
        params = {
                'company':task.company_id.company_id,
                'token':self.token,
                }
        data = {
                   "reporter": task.project_id.owner_id.user_id,
                   "project": {
                     "id": task.project_id.project_id,
                     "weight": 0
                   },
                   "name": task.name,
                   "description": task.odoo_task_id.description if task.odoo_task_id else False,
                   "status": task.status,
                   "weight": 0,
                   "folders": [
                     {
                       "id": "",
                       "weight": 0
                     }
                   ],
                   "deleted": False,
                   "assignedTo": task.assinged_to.user_id,
                   "id": "",
                   "rev": 0,
                   "createdAt": task.create_date.strftime('%Y-%m-%d'),
                   "modifiedAt": task.write_date.strftime('%Y-%m-%d')
                 }
        task_response = requests.post(time_doctor_api_base_url+end_points['tasks'],params=params,json=data,headers=headers)
        if task_response.status_code==200:
            data = task_response.json().get('data',{})
            return data.get('id')
        return False


    def create_project(self,task=False):
        if self.is_token_expired():
            self.login()
        params = {
                'company':task.company_id.company_id,
                'token':self.token,
                }
        data = {
               "creatorId": task.assinged_to.user_id,
               "scope": "user",
               "users": [
                 {
                   "id": task.assinged_to.user_id,
                   "role": "admin"
                 }
               ],
               "cloneTasksFromId": "",
               "cloneAccessFromId": "",
               "name": task.odoo_task_id.project_id.name,
               "description": '',
               "deleted": False,
               "weight": 0,
               "id": "",
               "rev": 0,
               "createdAt": task.create_date.strftime('%Y-%m-%d'),
               "modifiedAt": task.write_date.strftime('%Y-%m-%d'),
             }
        project_response = requests.post(time_doctor_api_base_url+end_points['projects'],params=params,json=data,headers=headers)
        print(time_doctor_api_base_url+end_points['projects'],params,headers,"\n\n\n\n",project_response.json())
        if project_response.status_code==200:
            data = project_response.json().get('data',{})
            return data.get('id')
        return False

    def add_user_to_project(self,company_id=False,project_id=False,user_id=False):
        params = {
                'company':company_id,
                'token':self.token,
                }
        data = {
                "role": "user"
                }
        add_user = requests.put(time_doctor_api_base_url+end_points['user-project-access'].format(project_id=project_id,user_id=user_id),params=params,json=data,headers=headers)
        print("\n\n\n\n\n",add_user.text,add_user.status_code)
        if add_user.status_code==200:
            return True
        return False

    def remove_user_to_project(self,project_id=False,user_id=False):
        params = {
                'company':task.company_id.company_id,
                'token':self.token,
                }
        rm_user = requests.delete(time_doctor_api_base_url+end_points['user-project-access'].format(project_id=project_id,user_id=user_id),params=params,headers=headers)
        if rm_user.status_code==200:
            return True
        return False


