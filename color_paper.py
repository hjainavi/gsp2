from openerp import models, fields, api, _

class color_paper(models.Model):
    _name="color.paper"
    _description="options for color print sides and cost"
    side_1=fields.Integer("Side 1",required=True)
    side_2=fields.Integer("Side 2",default=0)
    
    @api.multi
    @api.model
    def name_get(self):
        #print "in name_get product.product"
        result = []
        for rec in self:
            result.append((rec.id,"%s+%s"%(rec.side_1,rec.side_2)))
        return result

    '''@api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids=super(color_paper,self).name_search(name=name,args=args,operator='ilike',limit=100)
        print "in name_search of color.paper returnig ids ",ids
        try:
                if self._context.get('print_machine',False):
                    return_list=[]
                    cr=self._cr
                    cr.execute("select type from cost_workcenter where workcenter_id = %s",(self._context.get('print_machine'),))
                    saturation_list=list(i[0] for i in cr.fetchall())
                    for name_wk in range(len(ids)):
                        saturation=ids[name_wk][1]
                        if saturation in saturation_list:return_list.append(ids[name_wk])
                    print "====1",return_list
                    return return_list
        except:
            raise
            print "error in name_search of product.product"
        return ids'''
    