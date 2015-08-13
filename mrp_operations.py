from openerp.osv import fields,osv ,orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta

class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    
    def _get_delay_actual(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,SUPERUSER_ID,ids,context):
            res[obj.id]=0.0
            print "---- in get delay actual in mrp.py in gsp2---5555-obj.last_started_date--- ",obj.last_started_date
            if obj.state=='startworking' and obj.last_started_date: 
                res[obj.id]=obj.hours_worked + (datetime.strptime(fields.datetime.now(),'%Y-%m-%d %H:%M:%S')-(datetime.strptime(obj.last_started_date,'%Y-%m-%d %H:%M:%S'))).total_seconds()/3600.0
            else:
                res[obj.id]=obj.hours_worked
        return res
    
    
    def _get_employee_cost(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,SUPERUSER_ID,ids,context):
            res[obj.id]=0.0
            if obj.state=='done':
                '''get employee working costs on workcenter '''
                schedule_pay={'monthly':30,'quarterly':91,'semi-annually':183,'annually':365,'weekly':7,'bi-weekly':3.5,'bi-monthly':15}
                print "self.hr_wc_ids------------------",obj.hr_wc_ids
                print "self.hr_wc_ids.contract_ids------",obj.hr_wc_ids.contract_ids
                if obj.hr_wc_ids and obj.hr_wc_ids.contract_ids:
                    for contract in obj.hr_wc_ids.contract_ids:
                        if obj.date_start>=contract.date_start and obj.date_finished<=contract.date_end:
                            per_hour_cost=contract.wage/(schedule_pay.get(contract.schedule_pay,30*24)*24)
                            print "===================per_hour_cost*self.delay",per_hour_cost,obj.delay_actual,per_hour_cost*obj.delay_actual
                            res[obj.id]=per_hour_cost*obj.delay_actual
        


    
    _columns={'delivery_datetime':fields.related('production_id','delivery_datetime',string='Project Deadline',type='datetime'),
                'hr_wc_ids':fields.many2one('hr.employee',string='Employees Allowed', readonly=True, states={'draft': [('readonly', False)]},help='Employees allowed to operate the workcenter'),
                'delay_actual':fields.function(_get_delay_actual,string="Actual working hours",type='float'),
                'employee_cost':fields.function(_get_employee_cost,string='Employee Cost',type='float'),
                'hr_wc_uid':fields.related('hr_wc_ids','user_id',type='many2one',relation='res.users',store=True),
                'last_started_date':fields.datetime(),
                'hours_worked':fields.float(digits=(5,2))}
    
    _defaults={'hours_worked':0.0}

    def write(self,cr,uid,ids,vals,context=None,update=True):
        print "---- in get delay actual in mrp.py in gsp2--00000000000000--"
        
        for rec in self.browse(cr,uid,ids):
            if vals.get('state',False)=='startworking' and not rec.hr_wc_ids:
                hr_wc_ids=[rec_c1.id for rec_c1 in rec.workcenter_id.employees_allowed if (rec_c1.user_id and rec_c1.user_id.id==uid)]
                print "00000000000000000000000000000000009----------_",hr_wc_ids
                if hr_wc_ids:vals['hr_wc_ids']=hr_wc_ids[0]

            if vals.get('state',False)=='startworking': 
                print "---- in get delay actual in mrp.py in gsp2--1111--"
                vals['last_started_date']=fields.datetime.now()
                
            if vals.get('state',False) in ['pause','done'] and rec.last_started_date:
                print "---- in get delay actual in mrp.py in gsp2--2222--"
                vals['hours_worked']=rec.hours_worked + (datetime.strptime(fields.datetime.now(),'%Y-%m-%d %H:%M:%S')-(datetime.strptime(rec.last_started_date,'%Y-%m-%d %H:%M:%S'))).total_seconds()/3600.0
                
            if vals.get('state',False)=='done' and not rec.last_started_date:
                print "---- in get delay actual in mrp.py in gsp2--4444--"
                vals['hours_worked']=(datetime.strptime(fields.datetime.now(),'%Y-%m-%d %H:%M:%S')-(datetime.strptime(rec.last_started_date,'%Y-%m-%d %H:%M:%S'))).total_seconds()/3600.0
            
        return super(mrp_production_workcenter_line, self).write(cr,uid,ids,vals,context,update)
    
        
    def test_sequence_order(self, cr, uid, ids):
        """ Tests whether production is done or not.
        @return: True or False
        """
        print " in test sequence order ==============",ids,uid
        res = True
        for rec in self.browse(cr,uid,ids):
            
            employees_allowed_uid=[rec_c1.user_id.id for rec_c1 in rec.workcenter_id.employees_allowed if rec_c1.user_id]
            groups=self.pool.get('ir.model.data').get_object_reference(cr,uid,'mrp','group_mrp_user')[1]
            mrp_user_group=self.pool.get('res.groups').browse(cr,uid,groups)
            mrp_user_group_user_ids=map(int,mrp_user_group.users or [])
            
            groups=self.pool.get('ir.model.data').get_object_reference(cr,uid,'mrp','group_mrp_manager')[1]
            mrp_manager_group=self.pool.get('res.groups').browse(cr,uid,groups)
            mrp_manager_group_user_ids=map(int,mrp_user_group.users or [])
            
            print "11111144444,employees,employee_group_user_ids,uid",employees_allowed_uid,mrp_user_group_user_ids,uid
            if uid in mrp_user_group_user_ids and uid not in mrp_manager_group_user_ids and uid!=SUPERUSER_ID and (uid not in employees_allowed_uid or (uid in employees_allowed_uid and rec.hr_wc_ids and uid!=rec.hr_wc_ids.user_id.id)) :
                raise orm.except_orm(_('Warning'), _('You are not allowed to operate the workcenter. Please contact the administrator.'))

            work_orders_ids=self.search(cr,uid,[('production_id','=',rec.production_id.id),('state','not in',['cancel','done'])])
            work_orders_obj=self.browse(cr,uid,work_orders_ids)
            for rec_orders in work_orders_obj:
                if rec_orders.sequence<rec.sequence:
                    raise orm.except_orm(_('Warning'), _('Please cancel or finish work orders of lower sequence first.'))
        
        return res
    
    
    
    