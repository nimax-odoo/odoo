from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CouponProgram(models.Model):
    _name = 'coupon.program'
    _description = 'Coupon Program'
    _order = "sequence, id"

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Coupon Program', required=True)
    sequence = fields.Integer(copy=False)
    rule_date_from = fields.Datetime('Start Date')
    rule_date_to = fields.Datetime('End Date')
    rule_partners_domain = fields.Char(string='Customer', default='[]')
    rule_products_domain = fields.Char(string='Products', default='[]')
    rule_min_quantity = fields.Integer(string='Minimum Quantity')
    rule_minimum_amount = fields.Float('Minimum Purchase Amount')
    rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')
    ], string="Tax Inclusion")
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')
    ], default='percentage', string='Discount Type', required=True)
    discount_percentage = fields.Float('Discount')
    discount_fixed_amount = fields.Float('Fixed Amount Discount')
    discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('specific_products', 'Specific Products')
    ], default='on_order', string='Apply On')
    discount_specific_product_ids = fields.Many2many('product.product', string='Products')
    discount_max_amount = fields.Float('Maximum Amount')
    promo_code = fields.Char('Promotion Code')
    promo_code_usage = fields.Selection([
        ('no_code_needed', 'Automatically Applied'),
        ('code_needed', 'Use a code')
    ], default='no_code_needed')
    program_type = fields.Selection([
        ('promotion_program', 'Promotional Program'),
        ('coupon_program', 'Coupon Program')
    ], default='promotion_program', required=True)
    maximum_use_number = fields.Integer('Maximum Use Number')
    validity_duration = fields.Integer('Validity Duration (days)')
    reward_description = fields.Text('Reward Description')
    reward_type = fields.Selection([
        ('discount', 'Discount'),
        ('product', 'Free Product')
    ], default='discount', string='Reward Type', required=True)
    reward_product_id = fields.Many2one('product.product', string='Free Product')
    reward_product_quantity = fields.Integer('Quantity')
    total_order_count = fields.Integer(compute='_compute_total_order_count', string='Total Order Count')
    order_count = fields.Integer(compute='_compute_order_count', string='Order Count')
    coupon_ids = fields.One2many('coupon.coupon', 'program_id', string='Cupones')
    coupon_count = fields.Integer(compute='_compute_coupon_count', string='Cupones')
    
    # Campo añadido para solucionar el error
    expected_earning = fields.Float(string='Expected Earning (%)', default=0.0,
                                   help="Expected earning percentage for this pricelist")
    
    # Campos adicionales para los diferentes tipos de promociones
    as_type = fields.Selection([
        ('NORMAL', 'Normal'),
        ('DEAL', 'Oportunidad'),
        ('DEMO', 'Demo'),
        ('ESPECIAL', 'Precio Especial'),
        ('FABRICANTE', 'Rebate')
    ], string='Tipo de Promoción', default='DEAL')
    
    # Campos específicos para diferentes tipos de promociones
    PRICE_UNIT_USD = fields.Float('Precio Unitario USD', help='Para promociones tipo ESPECIAL')
    COST_NIMAX_USD = fields.Float('Costo NIMAX USD', help='Para promociones tipo ESPECIAL')
    DISCOUNT_AMOUNT_USD = fields.Float('Monto Descuento USD', help='Para promociones tipo FABRICANTE')
    COSTO = fields.Float('Costo (%)', help='Porcentaje de costo para promociones tipo DEMO')
    tf_gifted_qty = fields.Integer('Cantidad Regalada', default=0)
    tf_max_gifted_qty = fields.Integer('Cantidad Máxima Regalada', default=999999)
    tf_balance = fields.Float('Balance', compute='_compute_balance')

    def _compute_balance(self):
        for rec in self:
            rec.tf_balance = rec.tf_max_gifted_qty - rec.tf_gifted_qty
            
    @api.depends('coupon_ids')
    def _compute_coupon_count(self):
        for program in self:
            program.coupon_count = len(program.coupon_ids)

    @api.depends('rule_date_from', 'rule_date_to')
    def _check_dates(self):
        for program in self:
            if program.rule_date_from and program.rule_date_to and program.rule_date_from > program.rule_date_to:
                raise ValidationError(_('The start date must be before the end date'))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        for program in self:
            if program.discount_type == 'percentage' and not (0 <= program.discount_percentage <= 100):
                raise ValidationError(_('Discount percentage must be between 0 and 100'))

    @api.constrains('promo_code')
    def _check_promo_code_uniqueness(self):
        for program in self:
            if program.promo_code:
                domain = [('id', '!=', program.id), ('promo_code', '=', program.promo_code)]
                if self.search_count(domain):
                    raise ValidationError(_('The promo code must be unique'))

    def _compute_total_order_count(self):
        for program in self:
            program.total_order_count = 0

    def _compute_order_count(self):
        for program in self:
            program.order_count = 0

    def name_get(self):
        result = []
        for program in self:
            result.append((program.id, '%s%s' % (
                program.name,
                ' - ' + program.promo_code if program.promo_code else ''
            )))
        return result

    def action_view_coupons(self):
        """Vista de cupones del programa."""
        self.ensure_one()
        return {
            'name': _('Cupones'),
            'type': 'ir.actions.act_window',
            'res_model': 'coupon.coupon',
            'view_mode': 'list,form',
            'domain': [('program_id', '=', self.id)],
            'context': {'default_program_id': self.id},
        }

    def action_view_coupon_program_statistics(self):
        """Vista de estadísticas del programa."""
        self.ensure_one()
        return {
            'name': _('Estadísticas'),
            'type': 'ir.actions.act_window',
            'res_model': 'coupon.coupon',
            'view_mode': 'graph,pivot',
            'domain': [('program_id', '=', self.id)],
            'context': {'default_program_id': self.id},
        } 