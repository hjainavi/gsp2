# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class additional_works(models.Model):
    _name='additional.works'
    _description="additional works workcenter and product in sale order line"
    
    @api.model
    def _get_sequence(self):
        print "self=========",self._context
        counter=1
        if self._context.get('additional_works',False):
            for line in self._context.get('additional_works'):
                if line[0]!=2:counter+=1
                print "counter",counter
        return counter
    
    
    '''@api.model
    def default_get(self, fields_list):
        res=super(additional_works, self).default_get(fields_list)
        print "-----------in default_get",res,self._context
        if self._context.get('additional_works',False):
            counter=1
            for line in self._context.get('additional_works'):
                if line[0]!=2:counter+=1
                print "counter",counter
            res.update({'sequence': counter})
        print "1999999999999",res
        return res'''
    
    product=fields.Many2one('product.product',"Product", )
    qty=fields.Float("Product Qty",default=0.00)
    service_qty=fields.Float("Service Qty",default=1.0)
    product_unit=fields.Many2one(compute='_onchange_product',comodel_name='product.uom',string="Unit")
    service=fields.Many2one('product.product',"Service")
    workcenter=fields.Many2one(compute='_onchange_service',comodel_name='mrp.workcenter',string="Workcenter")
    sequence = fields.Integer(_compute="_get_sequence_1",string="Sequence",default=_get_sequence)
    sale_order_line=fields.Many2one('sale.order.line',ondelete='cascade')
    sale_order_line_bom=fields.Many2one('sale.order.line.bom',ondelete='cascade')
    cycle_nbr=fields.Float('cycle_nbr')
    hour_nbr=fields.Float('hour_nbr')
    costing_service=fields.Char(compute='_onchange_service',string=_('Costing'))
    
    
    @api.multi
    @api.constrains('workcenter','service')
    def _workcenter_constrains(self):
        for check in self:
            if check.service and check.workcenter==False:
                 raise except_orm(("Error"),("Please Set a workcenter in the service product %s of additional works") % (check.service.name))
            if check.service and check.service.workcenter.cost_method==False:
                 raise except_orm(("Error"),("Please Set a Cost Method in the workcenter %s ") % (check.service.workcenter.name))
            print check
            if check.service and check.service.workcenter.cost_method=='paper' and check._name=='sale.order.line' and check.sale_order_line.is_multi_level:
                 raise except_orm(("Error"),("Please choose a service where Workcenter Cost Method is 'By Product' in additional works (%s)") % (check.service.name))
    
    @api.one
    @api.depends('service')
    def _onchange_service(self):
        if self.service and not self.service.workcenter and not self.service.workcenter.cost_method:
            self.workcenter=False
            self.costing_service=None
            raise except_orm(("Error"),("Please Set a Workcenter in the service product and Cost method in the Workcenter/Pricing"))
        if self.service and not self.service.workcenter:
            self.workcenter=False
            raise except_orm(("Error"),("Please Set a workcenter in the service product %s of additional works") % (self.service.name))
        if self.service and not self.service.workcenter.cost_method:
            self.costing_service=None
            raise except_orm(("Error"),("Please Set a Cost Method in the workcenter %s ") % (self.service.workcenter.name))
        if self.service and self.service.workcenter.cost_method=='paper' and self._name=='sale.order.line' and self.sale_order_line.is_multi_level:
            raise except_orm(("Error"),("Please choose a service where Workcenter Cost Method is 'By Product' in additional works (%s)") % (self.service.name))
        if self.service and self.service.workcenter:
            self.workcenter=self.service.workcenter.id
        if self.service and self.service.workcenter.cost_method:
            dict={'paper':'By Paper','product':'By Product','sq_meter':'Per Sq. meter'}
            self.costing_service=dict.get(self.service.workcenter.cost_method,None)
         
            
    @api.one
    @api.depends('product')
    def _onchange_product(self):
        print "in _onchange_product"
        if self.product:
            self.product_unit=self.product.uom_id.id
        
        