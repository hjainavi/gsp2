# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta


class mrp_bom_line(models.Model):
    _inherit='mrp.bom.line'
    component_line_bom=fields.Many2one('mrp.bom')

class mrp_production(models.Model):
    _inherit='mrp.production'
    delivery_datetime=fields.Datetime(string='Deadline',readonly=True, states={'draft': [('readonly', False)]})
    
        
    
class mrp_bom(models.Model):
    _inherit='mrp.bom'
    mo_start_date=fields.Datetime("Starting date of MO")
    
    def false_bom_find(self, cr, uid, product_tmpl_id=None, product_id=None, properties=None, context=None):
        if properties is None:
            properties = []
        if product_id:
            if not product_tmpl_id:
                product_tmpl_id = self.pool['product.product'].browse(cr, uid, product_id, context=context).product_tmpl_id.id
            domain = [
                '|',
                    ('product_id', '=', product_id),
                    '&',
                        ('product_id', '=', False),
                        ('product_tmpl_id', '=', product_tmpl_id)
            ]
        elif product_tmpl_id:
            domain = [('product_id', '=', False), ('product_tmpl_id', '=', product_tmpl_id)]
        else:
            # neither product nor template, makes no sense to search
            return False
        domain = domain + [ '|', ('date_start', '=', False), ('date_start', '<=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                            '|', ('date_stop', '=', False), ('date_stop', '>=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
        domain = domain + [('active','=',False)]
        # order to prioritize bom with product_id over the one without
        ids = self.search(cr, uid, domain, order='product_id', context=context)
        #print "=========ids===========",ids
        # Search a BoM which has all properties specified, or if you can not find one, you could
        # pass a BoM without any properties
        bom_empty_prop = []
        #print "domain=======",domain
        for bom in self.pool.get('mrp.bom').browse(cr, uid, ids, context=context):
            if set(map(int, bom.property_ids or [])) == set(properties or []):
                if properties:
                    bom_empty_prop.append(bom.id)
        return bom_empty_prop

    

class procurement_order(models.Model):
    _inherit='procurement.order'
    
    def _get_date_planned(self, cr, uid, procurement, context=None):
        print "-----------in _get_date_planned",procurement.name,procurement.property_ids
        format_date_planned = datetime.strptime(procurement.date_planned,
                                                DEFAULT_SERVER_DATETIME_FORMAT)
        date_planned = format_date_planned - relativedelta(days=procurement.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=procurement.company_id.manufacturing_lead)
        print "-----------in _get_date_planned---date_planned procurement.order",date_planned
        return date_planned
    
    def make_mo(self, cr, uid, ids, context=None):
        res=super(procurement_order, self).make_mo(cr,uid,ids,context)
        production_obj = self.pool.get('mrp.production')
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            if procurement.production_id:
                if procurement.bom_id:
                    property_ids_list=tuple(map(int, procurement.bom_id.property_ids))   
                    print "============property_ids_list=======",property_ids_list
                    print "********************************************************"
                    print "select order_id from sale_order_line_property_rel where property_id in (%s);"%(property_ids_list)
                    cr.execute('select order_id from sale_order_line_property_rel where property_id in %s',(property_ids_list,))
                    result=cr.fetchall()
                    print "************************cr.fetchall",result
                    if len(result)==1:
                        date=self.pool.get('sale.order.line').browse(cr,uid,result[0][0]).delivery_datetime
                        self.pool.get('mrp.production').write(cr,uid,procurement.production_id.id,{'delivery_datetime':date})
                        self.pool.get('sale.order.line').write(cr,uid,result[0][0],{'mo_id':procurement.production_id.id})
                        
        return res

    def _prepare_mo_vals(self, cr, uid, procurement, context=None):
        res=super(procurement_order, self)._prepare_mo_vals(cr,uid,procurement,context)
        result = procurement.move_dest_id and procurement.move_dest_id.procurement_id and procurement.move_dest_id.procurement_id.sale_line_id and procurement.move_dest_id.procurement_id.sale_line_id.order_id or False
        if result and result.is_manufacture and result.mo_location_dest_id:
            res['location_dest_id']=result.mo_location_dest_id.id
        print "====mo_vals===result===",result 
        return res
                    
    
    
    def check_bom_exists(self, cr, uid, ids, context=None):
        """ Finds the bill of material for the product from procurement order.
        @return: True or False
        """
        print "in check_bom_exists====================="
        for procurement in self.browse(cr, uid, ids, context=context):
            properties = [x.id for x in procurement.property_ids]
            print "checking procurement",procurement.product_id.name
            print "properties=========",properties
            print "procurement origin====",procurement.origin
            print "procurement production",procurement.production_id
            if properties==[]:
                mo=procurement.origin.split(':')[-1] if procurement.origin else ''
                print "mo===========split",mo
                domain=[('group_id','=',procurement.group_id.id)]
                ids_prop=self.search(cr,uid,domain,context=context)
                for procure in self.browse(cr, uid, ids_prop, context=context):
                    if procure.production_id.name==mo and procure.property_ids:
                        properties = [x.id for x in procure.property_ids]
                        if properties:
                            bom_id=self.pool.get('mrp.bom').false_bom_find(cr, uid, product_id=procurement.product_id.id,properties=properties, context=context)
                            if bom_id and len(bom_id)==1:
                                self.write(cr,uid,procurement.id,{'bom_id':bom_id[0]})
                                return True
                            if bom_id and len(bom_id)>1:
                                multi_level_bom_ids=self.pool.get('sale.order.line.bom').search(cr,uid,[('bom_line','in',bom_id)])
                                for component in self.pool.get('sale.order.line.bom').browse(cr,uid,multi_level_bom_ids):
                                    if component.sale_order_line.is_multi_level:
                                        if procurement.product_qty==component.product_uom_qty*component.sale_order_line.product_uom_qty:
                                            self.write(cr,uid,procurement.id,{'bom_id':component.bom_line.id})
                                            return True
                                         
                        
                        
            else:
                properties = [x.id for x in procurement.property_ids]
                bom_id=self.pool.get('mrp.bom').false_bom_find(cr, uid, product_id=procurement.product_id.id,properties=properties, context=context)
                if bom_id:
                    self.write(cr,uid,procurement.id,{'bom_id':bom_id[0]})
                    return True
            
        return super(procurement_order, self).check_bom_exists(cr,uid,ids,context)


class mrp_routing_workcenter(models.Model):
    _inherit='mrp.routing.workcenter'
    _description='adding saturation field for cost calculation'
    saturation=fields.Char(default='default')
    qty=fields.Float()
    cost_by=fields.Char('Cost By')
    time_est_hour_nbr=fields.Float(help='Float for hour_nbr for time_est')
    
class mrp_routing(models.Model):
    _inherit='mrp.routing'
    _description='adding paper amount field in mrp.routing for cost calculation'
    paper_amount=fields.Float()
    


class mrp_workcenter(models.Model):
    _inherit='mrp.workcenter'
    _description='Fields'
    
    @api.model
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            b=self.env['product.uom'].search([('id', '=', a)])
            return b
        except:
            print "error in mrp.workcenter"
            b=self.env['product.uom'].search([('id', '=', 1)])
            return b
            
    
    max_height=fields.Float(string=_("Maximum Height"),help='Put 0 if there is no height restriction')
    max_height_uom = fields.Many2one('product.uom',default=get_mm_id)
    max_width=fields.Float(string=_("Maximum Width"))
    max_width_uom = fields.Many2one('product.uom',default=get_mm_id)
    edge_space=fields.Float(string=_('Edge Space'))
    edge_uom=fields.Many2one('product.uom',default=get_mm_id)
    lap_bw_products=fields.Float(string=_("Lap Between Products"))
    lap_uom=fields.Many2one('product.uom',default=get_mm_id)
    pricing=fields.One2many('cost.workcenter','workcenter_id',string="Costing")
    employees_allowed=fields.Many2many(comodel_name='hr.employee',string='Employees Allowed',help='Employees allowed to operate the workcenter')
    cost_method=fields.Selection(selection=[('paper','By Paper'),('product','By Product'),('sq_meter','Per Sq. meter')],string=_('Cost Method'),required=True,default='sq_meter')
            
    
    
    def _search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        print "==== in search ===args,context= in gsp2*****==",self,args,context
        ids= super(mrp_workcenter,self)._search(cr, user, args, offset, limit, order, context, count, access_rights_uid)
        if context.get('paper_product',False):
            try:
                id_list=[]
                #print "=====================",self._context.get('paper_product',False)
                obj=self.pool.get('product.product').browse(cr,user,context.get('paper_product'))
                #print "obj",obj
                product_width=obj.product_width
                product_height=obj.product_height
                for id in ids:
                    rec = self.browse(cr,user,id)
                    if rec.max_width != 0.0 and rec.max_height == 0.0 and (rec.max_width>=product_height or rec.max_width>=product_width):
                        id_list.append(id)
                    elif rec.max_width == 0.0 and rec.max_height != 0.0 and (rec.max_height>=product_height or rec.max_height>=product_width):
                        id_list.append(id)
                    elif (rec.max_height!=0 and rec.max_width!=0) and ((rec.max_height>=product_height and rec.max_width>=product_width) or (rec.max_height>=product_width and rec.max_width>=product_height)):
                        id_list.append(id)
            except:
                raise
                print "error in name_search of mrp.workcenter"
                return ids
            return id_list
        print "in search of mrp.workcenter returnig ids ",ids
        return ids

    
    @api.one
    @api.constrains('max_width','capacity_per_cycle')
    def force_width(self):
        #print "======================= force_width",self.max_width
        if self.capacity_per_cycle==0.0:
            raise except_orm(("Error"),("Please Set a capacity greater than 0"))
    
class cost_workcenter(models.Model):
    _name='cost.workcenter'
    '''costing one2many for workcenter'''
    
    @api.model
    def type_name(self):
        names=[('default',"Default")]
        saturation=self.env['color.paper'].search([]).name_get()
        names=names+[(i[1],i[1]) for i in saturation]
        return names
    
    workcenter_id=fields.Many2one('mrp.workcenter',ondelete='cascade')
    type=fields.Selection(selection='type_name',string="Select Type",default='default',required=True)
    cost_workcenter_array=fields.One2many('cost.workcenter.array','cost_workcenter',string='Workcenter Cost')
    
    def calc_cost(self,cr,uid,workcenter_id,qty,type=None):
        '''type is a string -default ,,, and other-type are ids of saturation
        first check for the id,,, then for default'''
        if type==None or False:type='default'
        print "type and workcenter_id",type,workcenter_id
        ids=self.search(cr,uid,[('workcenter_id','=',workcenter_id),('type','=',type)])
        print " ids calc cost",ids
        if ids:
            id=ids[0]
            cr.execute('select quantity from cost_workcenter_array where cost_workcenter = %s',(id,))
            qty_list=list(i[0] for i in cr.fetchall())
            print "qty_list",qty_list
            sorted_qty_list=[]
            if qty_list:
                sorted_qty_list=sorted(qty_list)
                print sorted_qty_list
                quantity=0.0
                for i in sorted_qty_list:
                    if i>qty:break
                    if i<=qty:
                        quantity=i
                if quantity==0.0:quantity=sorted_qty_list[0]
            
            if sorted_qty_list:
                cr.execute('select cost from cost_workcenter_array where cost_workcenter = %s and quantity = %s',(id,quantity))
                cost=list(i[0] for i in cr.fetchall())[0] or 0.0
                print "in calc_cost",cost
                print "in calc_cost*qty",cost*qty
                return cost*qty
        return 0 
        
    
class cost_workcenter_array(models.Model):
    _name='cost.workcenter.array'
    _order='quantity asc'
    
    cost_workcenter=fields.Many2one('cost.workcenter',ondelete='cascade')
    quantity=fields.Integer('Quantity of paper/product/sq.meter',default=0,help="Enter 0 for all quantities")
    cost=fields.Float('Cost per paper/product/sq.meter')
    
    
