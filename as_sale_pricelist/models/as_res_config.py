from odoo import fields,models,api, _

class res_config(models.TransientModel): 
    _inherit='res.config.settings'
        
    as_margin_minimo = fields.Float(string='Margen Minimo')
    as_margin_global = fields.Float(string='Limite de Margen Global')
    as_password_ventas1 = fields.Char(string='Contraseña para aprobar Ventas')
    
    @api.model
    def get_values(self):
        res = super(res_config, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(as_margin_minimo = float(params.get_param('as_sale_pricelist.as_margin_minimo',default=5)))
        res.update(as_margin_global = float(params.get_param('as_sale_pricelist.as_margin_global',default=0)))
        res.update(as_password_ventas1 = str(params.get_param('as_sale_pricelist.as_password_ventas1')))
        return res
    
    def set_values(self):
        super(res_config,self).set_values()
        ir_parameter = self.env['ir.config_parameter'].sudo()        
        ir_parameter.set_param('as_sale_pricelist.as_margin_minimo', self.as_margin_minimo)
        ir_parameter.set_param('as_sale_pricelist.as_margin_global', self.as_margin_global)
        ir_parameter.set_param('as_sale_pricelist.as_password_ventas1', self.as_password_ventas1)
        
