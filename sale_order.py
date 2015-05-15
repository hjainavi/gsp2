# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import math
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class stock_picking(models.Model):
    _inherit='stock.picking'
    
    def create(self,cr,uid,vals,context=None):
        id=super(stock_picking, self).create(cr,uid,vals,context)
        print "in create of stock.picking id",id
        print "in create of stock.picking vals",vals
        return id

class stock_move(models.Model):
    _inherit='stock.move'
    
    def create(self,cr,uid,vals,context=None):
        id=super(stock_move, self).create(cr,uid,vals,context)
        print "in create of stock.move id",id
        print "in create of stock.move vals",vals
        return id


class sale_order_line(models.Model):
    _inherit="sale.order.line"
    _description = "gsp2 sale order line"
    
    
    @api.one
    @api.depends('paper_product','manufacture_size','print_machine','height','width','product_uom_qty')
    def _get_product_count(self):
        #print "================in get product count"
        if self.paper_product and (self.paper_product.product_width==0.0 or self.paper_product.product_height==0.0):
            raise Warning("Please set the measurements in the product inventory page of product %s"%(self.paper_product.name_template))
        try:
            effective_paper_width=self.paper_product.product_width - (self.print_machine.edge_space*2) + self.print_machine.lap_bw_products
            effective_paper_height=self.paper_product.product_height - (self.print_machine.edge_space*2) + self.print_machine.lap_bw_products
            effective_manufacture_width=self.width + self.print_machine.lap_bw_products
            effective_manufacture_height=self.height + self.print_machine.lap_bw_products
            width_count=int(effective_paper_width/effective_manufacture_width)
            height_count=int(effective_paper_height/effective_manufacture_height)
            product_count=width_count*height_count
            self.product_count=product_count
            self.paper_amount=math.ceil(self.product_uom_qty/product_count)
        except:
            self.product_count=0.0
            self.paper_amount=0.0
            print "error encountered in get_product_count========"
            
    @api.one
    @api.depends('paper_product')
    def _get_quantity_available(self):
        print "=========in _get_quantity_available \njjjjjjjjjjjj"
        if self.paper_product:
            self.warehouse_qty = float(self.paper_product.virtual_available) - float(self.paper_product.incoming_qty)
        else:
             self.warehouse_qty = 0
             
    @api.onchange('manufacture_size')
    def _onchange_size(self):
        print "onchange 1"
        if self.manufacture_size and self.manufacture_size <> 15:
            self.width = self.list_size[self.manufacture_size][0]
            self.height = self.list_size[self.manufacture_size][1]
        else:
            self.width = 0
            self.height = 0
            
    @api.onchange('manufacture_size','width','height','category_id','paper_product','saturation','additional_works','multi_level_bom','is_multi_level')
    def _onchange_desc(self):
        if self.is_multi_level:
            weight=0.0
            for rec in self.multi_level_bom:
                weight=rec.paper_product.product_height * rec.paper_product.product_width * rec.paper_product.product_weight * rec.paper_amount
                for add_work in rec.additional_works:
                    amount=0.0
                    if add_work.service.workcenter_cost_method=='paper':amount=rec.paper_amount*add_work.qty
                    if add_work.service.workcenter_cost_method=='product':amount=rec.product_uom_qty*add_work.qty*self.product_uom_qty
                    weight+=add_work.product.weight_net*amount
            desc=str(self.product_id.name) + ' Total weight ' + str(weight) +  "\n"
            
            for rec in self.multi_level_bom:
                desc+= str(rec.product_id.name or '') + ' ' + str(rec.width or '') + str(rec.width and ' mm' or '') + ' ' +  str(rec.height or '') + str(rec.height and ' mm ' or '') + str(rec.bom_category_id.name or '') + ' ' + str(rec.paper_product.name or '') + ' ' + str(rec.paper_product.product_weight or '') + str(rec.paper_product.product_weight and rec.paper_product.weight_uom.name or '') + ' ' + str(rec.saturation.display_name or '') + "\n"
                    
                for add_work in rec.additional_works:
                    desc+= str(add_work.sequence or '') + ' ' + str(add_work.service.name or '') + '\n'
        else:
            weight=self.paper_product.product_height * self.paper_product.product_width * self.paper_product.product_weight * self.paper_amount
            for add_work in self.additional_works:
                amount=0.0
                if add_work.service.workcenter_cost_method=='paper':amount=self.paper_amount*add_work.qty
                if add_work.service.workcenter_cost_method=='product':amount=self.product_uom_qty*add_work.qty
                weight+=add_work.product.weight_net*amount
            desc=(self.product_id.name or 'False') + ' Total weight ' + str(weight) + "\n"
            desc+= str(self.width or '') + str(self.width and ' mm ' or '') + ' ' + str(self.height or '') + str(self.height and ' mm ' or '') +   (self.category_id.name or '') + ' ' + (self.paper_product.name or '') + ' ' + str(self.paper_product.product_weight or '') + str(self.paper_product.product_weight and self.paper_product.weight_uom.name or '') + ' ' + str(self.saturation.display_name or '') + "\n"
            for add_work in self.additional_works:
                    desc+= str(add_work.sequence or '') + ' ' + str(add_work.service.name or '') + '\n'
        self.name=desc
    
    @api.onchange('paper_product')
    def _onchange_category(self):
        if not self.category_id:
            self.category_id = self.paper_product.categ_id.id
    
    list_size = [
                 (0,0),(594,840),(420,594),(297,420),(210,297),(148,210),(105,148),(74,105),(52,74),(320,488),(85,54),(320,450),(225,320),
                 (90,50),(1188,841)
                 ]
    
    category_id = fields.Many2one('product.category',string = _("Product Category"))
    is_multi_level = fields.Boolean(string=_("Does the product have multi-level BOM ?"))
    multi_level_bom=fields.One2many('sale.order.line.bom','sale_order_line',copy=True)
    manufacture_size = fields.Selection([(14,"A0 - size 1188x841 mm"),(1,'A1 - size 594x840 mm'),(2,'A2 - size 420x594 mm'),(3,'A3 - size 297x420 mm'),
                                         (4,'A4 - size 210x297 mm'),(5,'A5 - size 148x210 mm'),(6,'A6 - size 105x148 mm'),
                                         (7,'A7 - size 74x105 mm'),(8,'A8 - size 52x74 mm'),(9,'Padidintas SRA3 - size 320x488 mm'),
                                         (10,'Plastikinė kortelė - size 85x54 mm'),(11,'SRA3 - size 320x450 mm'),
                                         (12,'SRA4 - size 225x320 mm'),(13,'Vizitine 90x50 - 90x50 mm'),(15,'Custom Size')
                                         ],default=False)
    height = fields.Float(string=_('Height'),default = 0)
    width = fields.Float(string=_('Width'),default = 0)
    paper_product = fields.Many2one('product.product',string=_("Weight and dimensions"),help="Displays paper from categories of paper")
    warehouse_qty = fields.Float(compute='_get_quantity_available',string = _("Unreserved Quantity in Stock"),help="Quantity available in stock - quantity reserved for other operations")
    print_machine = fields.Many2one('mrp.workcenter',String=_("Printing Machine"))
    product_count = fields.Float(compute='_get_product_count',string = _('Product Count on Chosen Paper'))
    saturation = fields.Many2one('color.paper',string=_("Saturation"))
    mo_id=fields.Many2one('mrp.production',copy=False)
    additional_works=fields.One2many('additional.works','sale_order_line',string="Additional Works",copy=True)
    bom_line=fields.Many2one('mrp.bom',copy=False)
    paper_amount=fields.Float(compute='_get_product_count',string ='Paper Amount to be used')
    estimate_unit_cost=fields.Float('Estimate Unit Cost',readonly=True)
    final_cost=fields.Float(compute='check_final_cost',string='Final Unit Cost',store=True)
    delivery_datetime=fields.Datetime('Deadline')
    expected_delivery=fields.Datetime(string='Expected Delivery Date')
    
    @api.constrains('manufacture_size','width','height','is_multi_level','product_count','paper_product','print_machine')
    def check_for_product_count(self):
        if self.is_multi_level==False and self.manufacture_size!=False and self.product_count == 0.0 :
            raise Warning(('Product count cannot be zero .  Please revise the data entered in product-line "%s" ') % (self.product_id.name))
    
        
    @api.one
    @api.depends('mo_id.state')
    def check_final_cost(self):
        '''changing uid to SUPERUSER_ID'''
        self.final_cost=0.0
        if self.sudo().mo_id.state=='done':
            print "in check_final_cost=-=-=-=-=-=-=-=-=-=-=-=-=-"
            total_cost=0.0
            sale_env=self.env['sale.order']
            mo_obj=self.sudo().mo_id
            '''get employee working costs on workcenter '''
            if mo_obj.routing_id:
                for wo in mo_obj.workcenter_lines:
                    total_cost=total_cost+wo.employee_cost
            if mo_obj.routing_id:
                res=sale_env.estimate_routing_cost(mo_obj.routing_id)
                main_routing_cost=res[0]
                print "check_final_cost main_routing_cost",main_routing_cost
                total_cost=total_cost+main_routing_cost
                
            product_id_bom_id_mo_id=[]
            for line in mo_obj.bom_id.bom_line_ids:
                if line.component_line_bom:
                    records_mo=self.env['mrp.production'].search([('bom_id','=',line.component_line_bom.id)])
                    print "check_final_cost records_mo",records_mo
                    for mo in records_mo:
                        procurement=self.env['procurement.order'].search([('production_id','=',mo.id)])
                        print "check_final_cost procurement",procurement
                        for rec in procurement:
                            if mo_obj.name in rec.origin:
                                product_id_bom_id_mo_id.append([line.product_id.id,line.component_line_bom.id,rec.production_id])
            print "check_final_cost product_id_bom_id_mo_id",product_id_bom_id_mo_id                    
            for line in mo_obj.move_lines2:
                if line.product_id.id in [i[0] for i in product_id_bom_id_mo_id]:continue
                cost=line.product_id.standard_price*line.product_uom_qty
                print "check_final_cost cost,product",cost,line.product_id.name
                total_cost=total_cost+cost
            for mo in (rec[2] for rec in product_id_bom_id_mo_id):
                res=mo.routing_id and sale_env.estimate_routing_cost(mo.routing_id) or [0.0]
                main_routing_cost=res[0]
                print "check_final_cost routing_cost",main_routing_cost
                total_cost=total_cost+main_routing_cost
                for line in mo.move_lines2:
                    cost=line.product_id.standard_price*line.product_uom_qty
                    print "check_final_cost cost,product",cost,line.product_id.name,line.product_uom_qty
                    total_cost=total_cost+cost
                    print "check_final_cost total cost",total_cost
            self.final_cost=total_cost/self.product_uom_qty
            print "check_final_cost total_cost final_cost",total_cost,self.final_cost
                
        
            
        '''cr.execute('select distinct production_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in %s)',(tuple(ids),))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        ids=[i[0] for i in result_cr if i[0]]'''
        

    
class sale_order(models.Model):
    _inherit='sale.order'
    _description='changes in sale'
    
    '''@api.multi
    def name_get(self):
        res = super(sale_order,self).name_get()
        print "in name_get of sale.order"
        print res
        return res'''
    
    
    
    @api.one
    @api.model
    def change_order_qty(self):
        for line in self.order_line:
            line.product_uom_qty = 1
    
    @api.multi
    def write(self,vals,context=None):
        print "sale.order vals-----------------",vals
        if not vals.get('edited_by_bom_button',False):vals['edited_by_bom_button']=False
        result = super(sale_order,self).write(vals)
        if self.test_order:
            self.change_order_qty()
        return result
    
    @api.model
    def create(self,vals):
        #print "================vals sale_ordre",vals
        id = super(sale_order,self).create(vals)
        if id.test_order:
            id.change_order_qty()
        return id
    
    @api.onchange('test_order')
    def _onchange_quantity(self):
        for line in self.order_line:
            line.product_uom_qty = 1
    
    def do_view_po(self, cr, uid, ids, context=None):
        if not context:context={}
        '''
        This function returns an action that display the Purchase order related to this sales order
        '''
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        pro_obj=self.pool.get('procurement.order')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_po')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in %s))',(tuple(ids),))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        ids=[i[0] for i in result_cr if i[0]]
        print "ids=========",ids
        result['domain'] = "[('id','in',[" + ','.join(map(str,ids)) + "])]"
        return result
        
            
    def do_view_mo(self, cr, uid, ids, context=None):
        if not context:context={}
        '''
        This function returns an action that display the Manufacturing order related to this sales order
        '''
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        pro_obj=self.pool.get('procurement.order')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_mo')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        
        cr.execute('select distinct production_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in %s)',(tuple(ids),))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        ids=[i[0] for i in result_cr if i[0]]
        print "ids=========",ids
        result['domain'] = "[('id','in',[" + ','.join(map(str,ids)) + "])]"
        return result
        
            
    def do_view_pickings_sale(self, cr, uid, ids, context=None):
        if not context:context={}
        '''
        This function returns an action that display the pickings of the procurements belonging
        to the same procurement group of given ids.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_pickings_sale_action')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        group_ids = set([proc.procurement_group_id.id for proc in self.browse(cr, uid, ids, context=context) if proc.procurement_group_id])
        print "ids==================in  do_view_pickings",ids
        print "group_ids=====",group_ids
        print "type(group_ids)=====",type(group_ids)
        print "list(group_ids)========",list(group_ids)
        print "type(list(group_ids))========",type(list(group_ids))
        result['domain'] = "[('group_id','in',[" + ','.join(map(str, list(group_ids))) + "])]"
        return result
        
    @api.one
    @api.depends()
    def _count_all(self):
        cr=self._cr
        print "====================== in _count_all"
        group_id=False
        if self.procurement_group_id:group_id=[self.procurement_group_id.id]
        if group_id:
            print "group_id==============",group_id
            cr.execute('select distinct production_id from procurement_order where group_id = %s and production_id is not null',(group_id))
            mo_count=cr.fetchall()
            print "mo_count============",mo_count
            self.mo_count=len(mo_count)
            
            cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(group_id))
            po_count=cr.fetchall()
            print "po_count============",po_count
            self.po_count=len(po_count)
            
            cr.execute('select distinct id from stock_picking where group_id = %s and id is not null',(group_id))
            picking_count=cr.fetchall()
            print "picking_count============",picking_count
            self.picking_count=len(picking_count)
    
    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        date_planned = datetime.strptime(order.date_confirm, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=line.delay or 0.0)
        return date_planned
    
    date_confirm=fields.Datetime('Confirmation Date', readonly=True, select=True, help="Date on which sales order is confirmed.", copy=False)
    is_manufacture = fields.Boolean(string='Manufacture',default=False)
    production_date = fields.Datetime('Production Date')
    test_order = fields.Boolean('Test Order')
    priority = fields.Integer('Priority')
    po_count=fields.Integer(compute='_count_all')
    mo_count=fields.Integer(compute='_count_all')
    picking_count=fields.Char(compute='_count_all')
    edited_by_bom_button=fields.Boolean()
    sale_sale_line_cost=fields.One2many('sale.order.line.cost','sale_sale_line_cost',string='Sale Line Cost',readonly=True,copy=False)
    sale_delivery_date=fields.One2many('sale.line.delivery.date','sale_delivery_date_rel',String="Expected Delivery Date")
    
    
    def get_sale_lines_time(self,cr,uid,sale_obj):
        uid=SUPERUSER_ID
        all_date_lines=[]
        del_lines=[]
        for line in sale_obj.order_line:
            if line.bom_line and line.bom_line.routing_id:
                date_line_dict={'product_id':line.product_id.id,
                               'qty':line.product_uom_qty,
                               'sale_line_id':line.id,
                               }
                all_date_lines.append([0,0,date_line_dict]) 
        for line in sale_obj.sale_delivery_date:
            del_lines.append([2,line.id])
        
        if del_lines:self.pool.get('sale.order').write(cr,uid,sale_obj.id,{'sale_delivery_date':del_lines})
        self.pool.get('sale.order').write(cr,uid,sale_obj.id,{'sale_delivery_date':all_date_lines})
                
    
    def action_button_confirm(self, cr, uid, ids, context=None):
        if not context:context={}
        sale_obj=self.browse(cr,uid,ids[0])
        import datetime
        #self.write(cr,uid,ids[0],{'date_order':datetime.datetime.now()},context)
        print "action button confirm sale_obj.edited_by_bom_button",sale_obj.edited_by_bom_button
        if sale_obj.edited_by_bom_button==False: self.make_bom_cost(cr,uid,ids,context)
        return super(sale_order, self).action_button_confirm(cr, uid, ids, context)        
    
    
    def estimate_routing_cost(self,cr,uid,routing_obj):
            routing_lines=[]
            routing_cost=0.0
            total_routing_cost=0.0
            for line_wc in routing_obj.workcenter_lines:
                routing_cost=self.pool.get('cost.workcenter').calc_cost(cr,SUPERUSER_ID,line_wc.workcenter_id.id,line_wc.qty,line_wc.saturation)
                total_routing_cost=total_routing_cost+routing_cost
                routing_cost_dict={'name':line_wc.name,
                                   'workcenter_id':line_wc.workcenter_id.id,
                                   'qty':line_wc.qty,
                                   'total_cost':routing_cost,
                                   'saturation':line_wc.saturation,
                                   'cost_by':line_wc.cost_by
                                   }
                routing_lines.append([0,0,routing_cost_dict]) 
                #coz if 4+4 cycles will be doubled but cost is by paper amount that's why line.qty
            return total_routing_cost,routing_lines
    
    ''' for final routing cost if extra work order is added ( not used) '''
    def final_workorders_cost(self,cr,uid,mo_obj):
            routing_cost=0.0
            total_routing_cost=0.0
            for line_wc in mo_obj.workcenter_lines:
                routing_cost=self.pool.get('cost.workcenter').calc_cost(cr,uid,line_wc.workcenter_id.id,line_wc.qty,line_wc.saturation)
                total_routing_cost=total_routing_cost+routing_cost
                #coz if 4+4 cycles will be doubled but cost is by paper amount that's why line.qty
            return total_routing_cost
    
    def delete_bom(self , cr, uid,obj_del_bom):
        try:
            un_bom_id= obj_del_bom.bom_line and [obj_del_bom.bom_line.id] or []
            un_routing_id= obj_del_bom.bom_line and obj_del_bom.bom_line.routing_id and [obj_del_bom.bom_line.routing_id.id] or []
            if obj_del_bom._name=='sale.order.line':
                un_property_ids=list(set(map(int, obj_del_bom.property_ids or [])))
                print "in delete_bom un_property_ids",tuple(un_property_ids)
                if un_property_ids:
                    cr.execute('select order_id from sale_order_line_property_rel where property_id in %s',(tuple(un_property_ids),))
                    res=cr.fetchall()
                    print res
                    if len(res)==1:
                        self.pool.get('mrp.property').unlink(cr, SUPERUSER_ID, un_property_ids)
            self.pool.get('mrp.routing').unlink(cr, SUPERUSER_ID, un_routing_id)
            self.pool.get('mrp.bom').unlink(cr, SUPERUSER_ID, un_bom_id)
            print "in delete bom"
        except:
            raise
            print "error in deletion delete_bom()"
    
    def create_bom_all(self,cr,uid,obj_cr_bom,sale_line_mrp_property):
        routing_id=self.create_routing(cr,uid,obj_cr_bom)
        bom_lines=self.create_bom_lines(obj_cr_bom)
        bom_id=self.create_bom(cr,uid,obj_cr_bom,bom_lines,routing_id,sale_line_mrp_property)
        print "in create bom all"
        if bom_id:return bom_id
        return False

    
    def make_bom_cost(self,cr,uid,ids,context=None):
        uid=SUPERUSER_ID
        if not context:context={}
        if type(ids)==type([]):id=ids[0]
        sale_obj=self.browse(cr,uid,id)
                    
        
        
        for line in sale_obj.order_line:
            if line.is_multi_level and (line.multi_level_bom or line.additional_works):
                sale_line_mrp_property=self.get_sale_line_property(cr,uid,line)
                for component in line.multi_level_bom:
                    # making of rouitng and bom of the component in multi_level_bom 
                    if component.paper_amount!=0.0 or component.additional_works:
                        #print "vals_bom===============",vals_bom
                        bom_id=self.create_bom_all(cr,uid,component, sale_line_mrp_property)
                        if bom_id:
                            self.delete_bom(cr,uid,component)
                            print "===========================writing property on sale line"
                            self.pool.get('sale.order.line.bom').write(cr, uid, component.id, {'bom_line': bom_id})
                            print "written in component -bom",bom_id
                
                # making of routing and BOM of the sale line ---BOM has components in it.
                bom_id=self.create_bom_all(cr,uid,line, sale_line_mrp_property)
                if bom_id:
                    self.delete_bom(cr,uid,line)
                    self.pool.get('sale.order.line').write(cr, uid, line.id, {'bom_line': bom_id,'property_ids': [(6,0,sale_line_mrp_property)]})
                    print "written in line -bom",bom_id
            
            elif line.paper_amount!=0.0 or line.additional_works:
                sale_line_mrp_property=self.get_sale_line_property(cr,uid,line)
                bom_id=self.create_bom_all(cr,uid,line, sale_line_mrp_property)
                if bom_id:
                    self.delete_bom(cr,uid,line)
                    print "===========================writing property on sale line"
                    self.pool.get('sale.order.line').write(cr, uid, line.id, {'bom_line': bom_id,'property_ids': [(6,0,sale_line_mrp_property)]})
                    print "written in line -bom",bom_id
            
        
        self.estimate_line_cost(cr,uid,sale_obj)
        self.get_sale_lines_time(cr,uid,sale_obj)
        self.write(cr,uid,id,{'edited_by_bom_button':True})
    
    
    def bom_lines_cost(self,cr,uid,line):
        bom_lines=[]
        total_bom_cost=0.0
        component_lines=[]
        for lines_bom in line.bom_line.bom_line_ids:
            bom_cost=0.0
            bom_cost=lines_bom.product_id.standard_price*lines_bom.product_qty
            if lines_bom.component_line_bom:
                res=self.component_cost(cr,uid,lines_bom.component_line_bom)
                bom_cost=res[0]
                component_lines.append(res[1])
            bom_cost_dict={'product_id':lines_bom.product_id.id,
                           'qty':lines_bom.product_qty,
                           'total_cost':bom_cost
                           }
            total_bom_cost=total_bom_cost+bom_cost
            bom_lines.append([0,0,bom_cost_dict])
        return total_bom_cost,bom_lines,component_lines
    
        
    def estimate_main_product_cost(self,cr,uid,line):
        total_unit_cost=0.0
        res_rout=line.bom_line.routing_id and self.estimate_routing_cost(cr,uid,line.bom_line.routing_id) or [0,[]]
        routing_cost=res_rout[0]
        routing_lines=res_rout[1]
        res_bom=self.bom_lines_cost(cr,uid,line)
        bom_cost=res_bom[0]
        bom_lines=res_bom[1]
        component_lines=res_bom[2]
        total_unit_cost=(routing_cost+bom_cost)/line.product_uom_qty
        sale_line=[0,0,{'product_id':line.product_id.id,
                        'qty':line.product_uom_qty,
                        'routing_cost_lines':routing_lines,
                        'product_cost_lines':bom_lines,
                        'component_cost_lines':component_lines,
                        'sale_line_id':line.id,
                        }]
        #component_cost=line.is_multi_level and 
        return total_unit_cost,sale_line
    
    def estimate_line_cost(self,cr,uid,sale_obj):
        all_sale_lines=[]
        del_lines=[]
        for line in sale_obj.order_line:
            if line.bom_line:
                res=self.estimate_main_product_cost(cr,uid,line)
                estimate_unit_cost=res[0]
                all_sale_lines.append(res[1])
                self.pool.get('sale.order.line').write(cr,uid,line.id,{'estimate_unit_cost':estimate_unit_cost})
        
        for line in sale_obj.sale_sale_line_cost:
            del_lines.append([2,line.id])
        
        if del_lines:self.pool.get('sale.order').write(cr,uid,sale_obj.id,{'sale_sale_line_cost':del_lines})
        self.pool.get('sale.order').write(cr,uid,sale_obj.id,{'sale_sale_line_cost':all_sale_lines})
    
    
    def component_cost(self,cr,uid,bom_obj):
        res=bom_obj.routing_id and self.estimate_routing_cost(cr,uid,bom_obj.routing_id) or [0,[]]
        routing_cost=res[0]
        routing_lines=res[1]
        total_bom_cost=0.0
        bom_lines=[]
        for lines_bom in bom_obj.bom_line_ids:
            bom_cost=0.0
            bom_cost=lines_bom.product_id.standard_price*lines_bom.product_qty
            bom_cost_dict={'product_id':lines_bom.product_id.id,
                           'qty':lines_bom.product_qty,
                           'total_cost':bom_cost
                           }
            total_bom_cost=total_bom_cost+bom_cost
            bom_lines.append([0,0,bom_cost_dict])
        final_component_line=[0,0,{'product_id':bom_obj.product_id.id,
                                   'qty':bom_obj.product_qty,
                                   'component_routing_cost_lines':routing_lines,
                                   'component_product_cost_lines':bom_lines,
                                   }]
        total_cost=total_bom_cost+routing_cost
        return total_cost,final_component_line
    
   
    def get_sale_line_property(self,cr,uid,line,context=None):
        if not context:context={}
        property_id = self.pool.get("ir.model.data").get_object_reference(cr,uid,"gsp2","bom_property_SO")[1]
        sale_line_mrp_property_vals={'name':line.order_id.name+':'+line.product_id.name+' '+str(line.id),
                                     'group_id':property_id,
                                     'composition':'min',
                                     }
        sale_line_mrp_property=[self.pool.get('mrp.property').create(cr,uid,sale_line_mrp_property_vals)]
        return sale_line_mrp_property
                    
    def create_bom(self,cr,uid,object,bom_lines,routing_id,sale_line_mrp_property,context=None):
        if not context:context={}
        if not bom_lines and not routing_id:return False
        vals_bom={
                  "product_tmpl_id":object.product_id.product_tmpl_id.id,
                  "product_id":object.product_id.id,
                  "active":False,
                  "product_qty":object.product_uom_qty,
                  "product_uom":object.product_uom.id,
                  "bom_line_ids":bom_lines,
                  "type":'normal',
                  "routing_id":routing_id,
                  "property_ids":[(6,0,sale_line_mrp_property)]
                  }
        if object._name=='sale.order.line':
            vals_bom['name']=object.product_id.name+':'+object.order_id.name
        elif object._name=='sale.order.line.bom':
            vals_bom['product_qty']=object.product_uom_qty*object.sale_order_line.product_uom_qty
            vals_bom['name']=object.product_id.name+':'+object.sale_order_line.order_id.name
        bom_id=self.pool.get('mrp.bom').create(cr,uid,vals_bom,context)
        if bom_id:return bom_id
        return False

    
    def create_bom_lines(self,object):
        
        def print_bom_lines(object):
            bom_lines=[]
            bom_lines1={"product_id":object.paper_product.id,
                       "type":'normal',
                       "product_qty":object.paper_amount,
                       "product_uom":object.paper_product.uom_id.id,
                       "product_rounding":0.0,
                       "product_efficiency":1.0,
                       }
            bom_lines.append([0,0,bom_lines1])
            return bom_lines
        
        def additional_works_bom_lines(object):
            bom_lines=[]
            if object._name=='sale.order.line.bom':check123=True
            elif object._name=='sale.order.line' :check123=False
            paper_amount=object.paper_amount
            for rec in object.additional_works:
                if not rec.product:continue
                if check123:
                    cost_cycle=object.product_uom_qty*object.sale_order_line.product_uom_qty
                    if rec.service and rec.service.workcenter_cost_method=='paper':cost_cycle=paper_amount
                else:
                    cost_cycle=object.product_uom_qty
                    if rec.service and rec.service.workcenter_cost_method=='paper':cost_cycle=paper_amount
                bom_lines1={"product_id":rec.product.id,
                           "type":'normal',
                           "product_qty":rec.qty*cost_cycle,
                           "product_uom":rec.product_unit.id,
                           "product_rounding":0.0,
                           "product_efficiency":1.0,
                           }
                bom_lines.append([0,0,bom_lines1])
            return bom_lines
        
        def create_component_bom_lines(object):
            bom_lines=[]
            for rec in object.multi_level_bom:
                bom_lines1={"product_id":rec.product_id.id,
                           "type":'normal',
                           "product_qty":rec.product_uom_qty*object.product_uom_qty,
                           "product_uom":rec.product_uom.id,
                           "product_rounding":0.0,
                           "product_efficiency":1.0,
                           "component_line_bom":rec.bom_line and rec.bom_line.id
                           }
                bom_lines.append([0,0,bom_lines1])
            return bom_lines
    
        bom_lines=[]
        if object._name=='sale.order.line':
            if object.is_multi_level==False and object.paper_amount!=0:
                bom_lines=bom_lines+print_bom_lines(object)
            if object.is_multi_level:
                bom_lines=bom_lines+create_component_bom_lines(object)
        else:
            if object.paper_amount!=0:
                bom_lines=bom_lines+print_bom_lines(object)
        bom_lines=bom_lines+additional_works_bom_lines(object)

        return bom_lines
    
    
    def create_routing(self,cr,uid,object,context=None):
        if not context:context={}
        '''object is a browsed object of sale order line or of multi_level_bom'''
        '''-(nbr_cycle_print_machine * (object.print_machine.time_cycle or 0.0) * (object.print_machine.time_efficiency or 1.0)), to compensate for _bom_explode calculation of hour'''
        def print_routing(object):
            routing_lines=[]
            saturation=1
            if object.saturation and "0" not in object.saturation.name_get()[0][1]: saturation=2
            nbr_cycle_print_machine=saturation*math.ceil(object.paper_amount/object.print_machine.capacity_per_cycle)
            print_routing_line={"name":object.product_id.name+" print",
                        "sequence":1,
                        "workcenter_id":object.print_machine.id,
                        "cycle_nbr":nbr_cycle_print_machine,
                        "hour_nbr":nbr_cycle_print_machine*(object.print_machine.time_cycle/object.print_machine.capacity_per_cycle)-(nbr_cycle_print_machine * (object.print_machine.time_cycle or 0.0) * (object.print_machine.time_efficiency or 1.0)),
                        "time_est_hour_nbr":nbr_cycle_print_machine*(object.print_machine.time_cycle/object.print_machine.capacity_per_cycle)+object.print_machine.time_start+object.print_machine.time_stop,
                        "saturation":object.saturation and object.saturation.name_get()[0][1] or 'default',
                        "qty":object.paper_amount,
                        "cost_by":'Paper'
                        }
            routing_lines.append([0,0,print_routing_line])
            return routing_lines
        
        def additional_work_routing(object):
            routing_lines=[]
            if object._name=='sale.order.line.bom':check123=True
            elif object._name=='sale.order.line' :check123=False
            paper_amount=object.paper_amount
            for rec in object.additional_works:
                if not rec.service:continue
                if check123:
                    if paper_amount!=0.0 and rec.service.workcenter_cost_method=='paper':
                        cost_cycle=paper_amount
                        cost_by='Paper'
                    else:
                        cost_cycle=object.product_uom_qty*object.sale_order_line.product_uom_qty
                        cost_by="Product"
                else:
                    cost_cycle=object.product_uom_qty
                    cost_by="Product"
                    if not object.is_multi_level and paper_amount!=0.0 and rec.service.workcenter_cost_method=='paper':
                        cost_cycle=paper_amount
                        cost_by="Paper"
                cycle_nbr=math.ceil(cost_cycle/rec.workcenter.capacity_per_cycle)
                vals_routing_lines={"name":rec.service.name,
                           "sequence":rec.sequence+1,
                           "workcenter_id":rec.workcenter.id,
                           "cycle_nbr":cycle_nbr,
                           "hour_nbr":cycle_nbr*(rec.workcenter.time_cycle/rec.workcenter.capacity_per_cycle)-(cycle_nbr * (rec.workcenter.time_cycle or 0.0) * (rec.workcenter.time_efficiency or 1.0)),
                           "time_est_hour_nbr":cycle_nbr*(rec.workcenter.time_cycle/rec.workcenter.capacity_per_cycle) +rec.workcenter.time_start+rec.workcenter.time_stop,
                           "qty":cost_cycle,
                           'cost_by':cost_by
                           }
                '''-(cycle_nbr * (rec.workcenter.time_cycle or 0.0) * (rec.workcenter.time_efficiency or 1.0)), to compensate for _bom_explode calculation of hour'''
                line_dict_12=[0,0,vals_routing_lines]
                routing_lines.append(line_dict_12)
            #print "==================routing_lines",routing_lines
            return routing_lines
        
        routing_obj=self.pool.get('mrp.routing')
        routing_lines=[]
        if object._name=='sale.order.line':
            if object.is_multi_level==False and object.paper_amount!=0:
                routing_lines=routing_lines+print_routing(object)
        else:
            if object.paper_amount!=0:
                routing_lines=routing_lines+print_routing(object)
        routing_lines=routing_lines+additional_work_routing(object)
    
        if routing_lines:
            vals_routing={"active":False,
                          "workcenter_lines":routing_lines,
                          "paper_amount":object.paper_amount
                          }
            if object._name=='sale.order.line':
                vals_routing['name']=object.product_id.name+':'+object.order_id.name
            elif object._name=='sale.order.line.bom':
                vals_routing['name']=object.product_id.name+':'+object.sale_order_line.order_id.name
        
            routing_id=routing_obj.create(cr,uid,vals_routing,context)
            return routing_id
        return False        
    
class sale_line_delivery_date(models.Model):
    _name="sale.line.delivery.date"
    
    product_id=fields.Many2one('product.product',string="Product")
    qty=fields.Float(string='Quantity')
    sale_line_id=fields.Many2one('sale.order.line')
    sale_delivery_date_rel=fields.Many2one('sale.order')
    expected_delivery=fields.Datetime(compute="get_expected_delivery_date",string='Delivery Date')
    
    @api.depends()
    def get_expected_delivery_date(self):
        self.sudo()
        print "-------------in def get_expected_delivery_date(self)",self
        for line in self:
            print "----------sale line id",line.sale_line_id
            line.expected_delivery=fields.Datetime.now()
            line.sale_line_id.write({'expected_delivery':fields.Datetime.now()})
            obj=line.sale_line_id
            if obj.bom_line and obj.bom_line.routing_id:
                if obj.is_multi_level:
                    pass
                else:
                    data=[]
                    start_dt=datetime.strptime(obj.order_id.date_confirm or fields.Datetime.now(),'%Y-%m-%d %H:%M:%S').replace(second=0)
                    end_dt=datetime.strptime(obj.order_id.date_confirm or fields.Datetime.now(),'%Y-%m-%d %H:%M:%S').replace(second=0)
                    #print "======type(start_dt)",start_dt
                    #print "======type(end_dt)",type(end_dt)
                    for line in obj.bom_line.routing_id.workcenter_lines:
                        data.append((line.sequence,line.workcenter_id,line.time_est_hour_nbr))
                    sorted_data=sorted(data, key=lambda tup: tup[0]) # sorting according to sequence
                    for line in sorted_data:
                        #print "-------------line",line
                        self.wc_line_end_time(start_dt,line)
                        #start_dt=res[0]
                        #end_dt=res[1]
    
    def wc_line_end_time(self,cr,uid,start_dt,line):
        delay=0.0
        past_intervals=[]
        intervals_to_remove=[]
        print "\n \n \n \n--------------start_dt",start_dt
        past_intervals=self._get_sorted_planned_intervals(cr, uid, start_dt)
        
        for i in past_intervals:
            if i[0] < start_dt: #i[0] = start date of interval ,,,adding hours of all intervals whose start date is before start_dt 
                print "=======i",i
                delay += (i[1]-i[0]).total_seconds()/3600.0
                intervals_to_remove.append(i)
        planned_intervals=list(set(past_intervals)-set(intervals_to_remove))
        print "========planned_intervals",planned_intervals
        print"=======delay--------------before looooooooooooooooooooooooop",delay
        delay_endtime=self._hour_end_time(cr, uid, start_dt, line, planned_intervals, delay)
        # the planned intervals from delay_endtime will not be carried forward coz they will be consumed or will be automatically used
        # if delay_endtime is less than the next date of workorder of the same day
        planned_intervals=self._get_sorted_planned_intervals(cr, uid, delay_endtime,delay_endtime.replace(hour=23,minute=59,second=59))
        print "\n \n \n \n \n \n \n \n \n \n \n \n --------------line_end_time" 
        line_end_time=self._hour_end_time(cr, uid, delay_endtime, line, planned_intervals, line[2])
        print "===========line_end_time",line_end_time
        
    
    def _hour_end_time(self, cr,uid,start_dt,line,planned_intervals,delay):
        '''
        start_dt === dateteime from whwre scceduling will start
        line ==== line.sequence,line.workcenter_id,line.time_est_hour_nbr))
        planned_intervals =========  intervals of workorders scheduled after start_dt till start_dt(23:59:59)
        delay ============ hours to fit in empty intervals
        returns end_datetime after fitting the delay in empty intervals
                '''
        delay_endtime=False
        while (delay>0):
            print "=====================delay",delay
            print "===============start_dt",start_dt
            print "========planned_intervals",planned_intervals
            #print "-----------in while loop"
            intervals_to_remove=[]
            hours_to_remove=0.0
            remaining_intervals=[]
            remaining_hours=0.0
            working_interval_today,hours_in_day=self._get_working_interval_and_hours_in_day(cr, uid, start_dt, line)
            

            if working_interval_today:
                for i in planned_intervals:
                    if i[1] <= start_dt.replace(hour=23,minute=59,second=59) and i[0] >= start_dt: 
                        hours_to_remove += (i[1]-i[0]).total_seconds()/3600.0
                        intervals_to_remove.append(i)
                print "=========hours_to_remove",hours_to_remove
                print "==========intervals_to_remove",intervals_to_remove
                planned_intervals=list(set(planned_intervals)-set(intervals_to_remove))
                print "========planned_intervals=====after removal",planned_intervals
                
                if intervals_to_remove:
                    for i in working_interval_today :
                        remaining_intervals += self.pool.get('resource.calendar').interval_remove_leaves(i,intervals_to_remove)
                # additional delay to schedule for overlapping planned intervals
                    for i in remaining_intervals:
                        print "===============i===",i
                        remaining_hours += (i[1]-i[0]).total_seconds()/3600.0
                    delay += (remaining_hours+hours_to_remove-hours_in_day) if (remaining_hours+hours_to_remove-hours_in_day)>0 else 0.0
                    #print "=========remaining_intervals",remaining_intervals
                    #print "=========remaining_hours",remaining_hours
                    #print "=========delay",delay
                    interval_schedule_hours=self.pool.get('resource.calendar').interval_schedule_hours(remaining_intervals,delay)
                    #print "==============intervals_schedule_hours",interval_schedule_hours
                    if interval_schedule_hours==remaining_intervals:
                        delay -= remaining_hours
                        if delay==0.0:delay_endtime=interval_schedule_hours[-1][-1]
                    else:
                        delay_endtime=interval_schedule_hours[-1][-1] 
                        break
                    #print "=========delay",delay
                else:
                    interval_schedule_hours=self.pool.get('resource.calendar').interval_schedule_hours(working_interval_today,delay)
                    print "===============working_interval_today in else",working_interval_today
                    print "==============intervals_schedule_hours in else",interval_schedule_hours
                    if interval_schedule_hours==working_interval_today:
                        delay -= hours_in_day
                        if delay==0.0:delay_endtime=interval_schedule_hours[-1][-1]
                    else:
                        delay_endtime=interval_schedule_hours[-1][-1] 
                        break
                    print "=========delay",delay
                    
            start_dt=start_dt.replace(hour=0,minute=0,second=0)+timedelta(days=1)
            end_dt=start_dt.replace(hour=23,minute=59,second=59)
            planned_intervals += self._get_sorted_planned_intervals(cr, uid, start_dt,end_dt)
            #print "========planned_intervals",planned_intervals
        print "================delay_end_time",delay_endtime
        return delay_endtime
    
    
    
    def _get_working_interval_and_hours_in_day(self,cr,uid,start_dt,line):
        hours_in_day=0.0
        #print "----------line=",line
        working_interval_today=self.pool.get('resource.calendar').get_working_intervals_of_day(cr,uid,id=line[1].calendar_id.id,start_dt=start_dt,end_dt=None,leaves=None,compute_leaves=True,resource_id=line[1].resource_id.id,default_interval=(8, 16))
        for i in working_interval_today:
            time_in_day=i[1]-i[0]
            hours_in_day+=time_in_day.total_seconds()/3600.0
        #print "-----------working_interval_today,hours_in_day",working_interval_today,hours_in_day
        return working_interval_today,hours_in_day
        
    def _get_sorted_planned_intervals(self,cr,uid,start_dt,end_dt=None):
        """if no end_dt is given then this func returns all the workorder intervals 
        whose date_planned < start_dt.replace(hour=23,minute=59,second=59)
            else if end_dt is mentioned then this returns all the intervals of workorder whose date_planned is between
            start_dt and end_dt
        """
        intervals=[]
        if end_dt:
            cr.execute("select id from mrp_production_workcenter_line where date_planned < %s and date_planned > %s and state in ('draft','pause')", (end_dt,start_dt))
        else:
            cr.execute("select id from mrp_production_workcenter_line where date_planned < %s and state in ('draft','pause')", (start_dt.replace(hour=23,minute=59,second=59),)) 
        ids=[i[0] for i in cr.fetchall()]
        ops = self.pool.get('mrp.production.workcenter.line').browse(cr, uid, ids)
        date_and_hours_by_cal = [(op.date_planned, op.hour, op.workcenter_id.calendar_id.id,op.workcenter_id.resource_id.id or False) for op in ops if op.date_planned]
        intervals_dict = self.pool.get('resource.calendar').interval_get_multi(cr, uid, date_and_hours_by_cal)
        # extracting all intervals from the 
        for i in intervals_dict:
            for j in intervals_dict.get(i):
                intervals.append(j)
        intervals=sorted(intervals, key=lambda date_time: date_time[0])
        return intervals
    
        

    

class routing_cost(models.Model):
    _name='routing.cost'
    routing_cost_sale=fields.Many2one('sale.order.line.cost',ondelete='cascade')
    component_routing_cost_sale=fields.Many2one('component.cost',ondelete='cascade')
    
    name=fields.Char('Service')
    workcenter_id=fields.Many2one('mrp.workcenter','Workcenter')
    qty=fields.Float('Quantity')
    total_cost=fields.Float('Total Cost')
    saturation=fields.Char('Saturation')
    cost_by=fields.Char('Cost by')
    
class product_cost(models.Model):
    _name='product.cost'
    product_cost_sale=fields.Many2one('sale.order.line.cost',ondelete='cascade')
    component_product_cost_sale=fields.Many2one('component.cost',ondelete='cascade')
    
    product_id=fields.Many2one('product.product',string='Product')
    qty=fields.Float('Quantity')
    total_cost=fields.Float('Total Cost')
    

class component_cost(models.Model):
    _name='component.cost'
    component_cost_sale=fields.Many2one('sale.order.line.cost',ondelete='cascade')
    component_routing_cost_lines=fields.One2many('routing.cost','component_routing_cost_sale',string='Machine Cost',readonly=True)
    component_product_cost_lines=fields.One2many('product.cost','component_product_cost_sale',string='Material Cost',readonly=True)
    
    product_id=fields.Many2one('product.product',string='Component')
    qty=fields.Float('Quantity')

class sale_order_line_cost(models.Model):
    _name='sale.order.line.cost'
    sale_sale_line_cost=fields.Many2one('sale.order',ondelete='cascade')
    product_id=fields.Many2one('product.product','Product')
    qty=fields.Float('Quantity')
    estimate_unit_cost=fields.Float(related='sale_line_id.estimate_unit_cost',default=0,string='Estimate Unit Cost')
    final_unit_cost=fields.Float(related='sale_line_id.final_cost',default=0,string='Final Unit Cost')
    sale_line_id=fields.Many2one('sale.order.line')
    routing_cost_lines=fields.One2many('routing.cost','routing_cost_sale',string='Machine Cost',readonly=True)
    product_cost_lines=fields.One2many('product.cost','product_cost_sale',string='Material Cost',readonly=True)
    component_cost_lines=fields.One2many('component.cost','component_cost_sale',string='Component Cost',readonly=True)