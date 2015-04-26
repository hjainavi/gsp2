from openerp import models, fields, api, _
from openerp.tools.translate import _

class hr_employee(models.Model):   
    _inherit='hr.employee'
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        #print "---------in name_search hr_employee",self._context
        ids=super(hr_employee,self).name_search(name=name,args=args,operator='ilike',limit=100)
        #print "---------in name_search hr_employee",ids
        if self._context.get('wc_id',False):
            name_list=[]
            hr_ids_obj=self.env['mrp.workcenter'].browse(self._context.get('wc_id')).employees_allowed
            hr_ids=map(int, hr_ids_obj or [])
            for rec in ids:
                if rec[0] in hr_ids:
                    name_list.append(rec)
            #print "--name_list-------",name_list
            return name_list
        return ids 