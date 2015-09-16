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

    
    