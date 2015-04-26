from openerp.osv import fields,osv ,orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    
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
            print "11111144444,employees,employee_group_user_ids,uid",employees_allowed_uid,mrp_user_group_user_ids,uid
            if uid in mrp_user_group_user_ids and uid!=SUPERUSER_ID and (uid not in employees_allowed_uid or (uid in employees_allowed_uid and rec.hr_wc_ids and uid!=rec.hr_wc_ids.user_id.id)) :
                raise orm.except_orm(_('Warning'), _('You are not allowed to operate the workcenter. Please contact the administrator.'))

            work_orders_ids=self.search(cr,uid,[('production_id','=',rec.production_id.id),('state','not in',['cancel','done'])])
            work_orders_obj=self.browse(cr,uid,work_orders_ids)
            for rec_orders in work_orders_obj:
                if rec_orders.sequence<rec.sequence:
                    raise orm.except_orm(_('Warning'), _('Please cancel or finish work orders of lower sequence first.'))
        
        return res
    
    def write(self,cr,uid,ids,vals,context=None,*args,**kwargs):
        print "----------------in write mrp.production.workcenter.line",vals
        for rec in self.browse(cr,uid,ids):
            if vals.get('state',False)=='startworking' and not rec.hr_wc_ids:
                hr_wc_ids=[rec_c1.id for rec_c1 in rec.workcenter_id.employees_allowed if (rec_c1.user_id and rec_c1.user_id.id==uid)]
                print "00000000000000000000000000000000009----------_",hr_wc_ids
                if hr_wc_ids:vals['hr_wc_ids']=hr_wc_ids[0]
            
        return super(mrp_production_workcenter_line, self).write(cr,uid,ids,vals,context,*args,**kwargs)
    
    
    