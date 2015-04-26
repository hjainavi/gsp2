openerp.gsp2= function (instance) {
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.gsp2 = instance.web.gsp2|| {};

    instance.web.ListView.include({
        editable: function () {
        	var self = this;
        	if (this.model == 'sale.order.line'){
        		if ($("input[name='is_manufacture']")[0] && $("input[name='is_manufacture']")[0].checked){
        			return false
        		}        		
        	}

		return !this.grouped
                && !this.options.disable_editable_mode
                && (this.fields_view.arch.attrs.editable
                || this._context_editable
                || this.options.editable);
        },

    });
};

