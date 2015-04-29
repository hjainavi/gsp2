# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'GSP MODIFICATIONS',
    'version' : '0.1',
    'author' : 'Intellerist',
    'category' : 'modifications',
    'description' : """
    
   """,
    'website': '',
    'images' : [],
    'data': ['product_uom_mm.xml','multi_level_bom.xml','color_paper.xml','bom_property.xml','resource_view.xml','sale_order.xml','mrp_view.xml','product_view.xml','views/sale_line_form.xml','product_category.xml','product_manufacturer_view.xml','mrp_operations_workflow.xml','security/ir.model.access.csv','security/mrp_security.xml'], 
    'depends' : ['base','product','sale','mrp','sale_mrp','mrp_operations','procurement','resource','hr','gsp_workorder','web_m2x_options'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:t

