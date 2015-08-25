# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class product_category(models.Model):
    _inherit = "product.category"
    _description = "gsp2 product category"
    
    is_paper = fields.Boolean('Paper Category')
    
    
class product_template(models.Model):
    _inherit='product.template'
    _description='Product Fields'
    
    @api.model
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            b=self.env['product.uom'].search([('id', '=', a)])
            return b
        except:
            print "error in product.template"
            b=self.env['product.uom'].search([('id', '=', 1)])
            return b
    
    produce_delay=fields.Float(default=0.0,string='Manufacturing Lead Time', help="Average delay in days to produce this product. In the case of multi-level BOM, the manufacturing lead times of the components will be added.")    
    sale_delay=fields.Float(default=0.0,string='Customer Lead Time', help="The average delay in days between the confirmation of the customer order and the delivery of the finished products. It's the time you promise to your customers.")
    
    product_width = fields.Float(related=('product_variant_ids','product_width'),string = _('Paper Width'),required=True,default=0,help="Width in mm")
    width_uom=fields.Many2one(related=('product_variant_ids','width_uom'),default=get_mm_id)
    product_height = fields.Float(related=('product_variant_ids','product_height'),string = _('Paper Height'),required=True,default=0,help="Height in mm")
    height_uom=fields.Many2one(related=('product_variant_ids','height_uom'),default=get_mm_id)
    product_weight = fields.Float(related=('product_variant_ids','product_weight'),string = _('Paper Weight'),default=0,help="Weight in gsm")
    weight_uom=fields.Many2one(related=('product_variant_ids','weight_uom'))
    workcenter=fields.Many2one(related=('product_variant_ids','workcenter'),string = _('Service Workcenter'),default=False)
    manufacturer=fields.Many2many('res.partner',string = _('Manufacturer'))
    
    
    # writing fields that have to be carried over to product.product and 
    # readonly fields has to be written this way ...coz no value of them in vals    
    @api.model
    def create(self,vals):
        #print "vals======= p.t.c",vals
        a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
        product_template_id=super(product_template,self).create(vals)
        #print "===========here before write of measurements"
        product_template_id.write({'check':True,'manufacturer':vals.get('manufacturer',False),'workcenter':vals.get('workcenter',False),'product_width':vals.get('product_width',0),'product_height':vals.get('product_height',0),'product_weight':vals.get('product_weight',0),'width_uom':vals.get('width_uom',a),'height_uom':vals.get('height_uom',a),'weight_uom':vals.get('weight_uom',False)})
        return product_template_id
    
    
    
    
class product_product(models.Model):
    _inherit="product.product"
    _description="product.product changes"
    
    @api.model
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            b=self.env['product.uom'].search([('id', '=', a)])
            return b
        except:
            print "error in product.product"
            b=self.env['product.uom'].search([('id', '=', 1)])
            return b
        
    product_width = fields.Float(string = _('Paper Width'),required=True,default=0,help="Width in mm")
    width_uom=fields.Many2one('product.uom',default=get_mm_id)
    product_height = fields.Float(string = _('Paper Height'),required=True,default=0,help="Height in mm")
    height_uom=fields.Many2one('product.uom',default=get_mm_id)
    product_weight = fields.Float(string = _('Paper Weight'),default=0,help="Weight in gsm")
    weight_uom=fields.Many2one('product.uom')
    workcenter=fields.Many2one('mrp.workcenter',string = _('Service Workcenter'),default=False)
    
    
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids=super(product_product,self).name_search(name=name,args=args,operator='ilike',limit=100)
        try:
                if self._context.get('additional_service',False):
                    list=[]
                    for name_wk in range(len(ids)):
                        product=self.browse(ids[name_wk][0])
                        if product.workcenter.cost_method!='paper':
                            list.append(ids[name_wk])
                    print "====1",list
                    return list

                if self._context.get('print_machine',False):
                    list=[]
                    obj=self.env['mrp.workcenter'].browse(self._context.get('print_machine'))
                    max_width=obj.max_width
                    max_height=obj.max_height
                    for name_wk in range(len(ids)):
                        rec=self.browse(ids[name_wk][0])
                        if max_height!=0 and rec.product_height<=max_height and rec.product_width<=max_width:
                            list.append(ids[name_wk])
                        if max_height==0 and rec.product_width<=max_width:
                            list.append(ids[name_wk]) 
                    print "====2",list
                    return list
        except:
            raise
            print "error in name_search of product.product"
        print "in name_search of product.product returnig ids "
        return ids
    
    #changes name_get only in sale order line form in sale order 
    @api.multi
    @api.model
    def name_get(self):
        result = []
        if self._context.get('paper_product',False):
            print "in name_get product.product",self._context
            k=super(product_product,self).name_get()
            for i in k:
                product=self.browse(i[0])
                name=i[1]+(" (%s%sx%s%s,%s%s, Categ-%s )"%(product.product_width,product.width_uom.name or '',product.product_height,product.height_uom.name or '',product.product_weight,product.weight_uom.name or '',product.categ_id.name or '--'))
                id_name=(i[0],name)
                result.append(id_name)
            print "--------in name_get product.product",result
            return result
        return super(product_product,self).name_get()
    
    
    
    
    
    
