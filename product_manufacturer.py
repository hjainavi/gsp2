# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class product_manufacturer(models.Model):
    _name='product.manufacturer'
    manufacturer_partner=fields.Many2one('res.partner',string='Manufacturer')
    product_manufacturer=fields.Many2one('product.product',ondelete='cascade')