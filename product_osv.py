from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round


class product_product(osv.osv):
    _inherit = "product.product"
    
    
    def _virtual_minus_incoming(self, cr, uid, ids, field_names=None, arg=False, context=None):
        context = context or {}
        res={}
        for product in self.browse(cr, uid, ids, context=context):
            id=product.id
            res[id] = float(product.virtual_available) - float(product.incoming_qty)
        return res
        
    
    _columns={
              'virtual_minus_incoming_qty': fields.function(_virtual_minus_incoming,
            type='float',string='Unreserved quantity in stock')
              }