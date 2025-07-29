from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CouponProgram(models.Model):
    _name = 'coupon.program'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = 'Coupon Program'
    _order = "sequence, id"

    active = fields.Boolean('Active', default=True,tracking=True)
    name = fields.Char('Coupon Program', required=True,tracking=True)
    sequence = fields.Integer(copy=False,tracking=True)
    rule_date_from = fields.Datetime('Start Date',tracking=True)
    rule_date_to = fields.Datetime('End Date',tracking=True)
    rule_partners_domain = fields.Char(string='Customer', default='[]',tracking=True)
    rule_products_domain = fields.Char(string='Products', default='[]',tracking=True)
    rule_min_quantity = fields.Integer(string='Minimum Quantity',tracking=True)
    rule_minimum_amount = fields.Float('Minimum Purchase Amount',tracking=True)
    rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')
    ], string="Tax Inclusion",tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,tracking=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')
    ], default='percentage', string='Discount Type', required=True,tracking=True)
    discount_percentage = fields.Float('Discount',tracking=True)
    discount_fixed_amount = fields.Float('Fixed Amount Discount',tracking=True)
    discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('specific_products', 'Specific Products')
    ], default='on_order', string='Apply On',tracking=True)
    discount_specific_product_ids = fields.Many2many('product.product', string='Products',tracking=True)
    discount_max_amount = fields.Float('Maximum Amount',tracking=True)
    promo_code = fields.Char('Promotion Code',tracking=True)
    promo_code_usage = fields.Selection([
        ('no_code_needed', 'Automatically Applied'),
        ('code_needed', 'Use a code')
    ], default='no_code_needed',tracking=True)
    program_type = fields.Selection([
        ('promotion_program', 'Promotional Program'),
        ('coupon_program', 'Coupon Program')
    ], default='promotion_program', required=True,tracking=True)
    maximum_use_number = fields.Integer('Maximum Use Number',tracking=True)
    validity_duration = fields.Integer('Validity Duration (days)',tracking=True)
    reward_description = fields.Text('Reward Description',tracking=True)
    reward_type = fields.Selection([
        ('discount', 'Discount'),
        ('product', 'Free Product')
    ], default='discount', string='Reward Type', required=True,tracking=True)
    reward_product_id = fields.Many2one('product.product', string='Free Product',tracking=True)
    reward_product_quantity = fields.Integer('Quantity',tracking=True)
    total_order_count = fields.Integer(compute='_compute_total_order_count', string='Total Order Count',tracking=True)
    order_count = fields.Integer(compute='_compute_order_count', string='Order Count',tracking=True)
    coupon_ids = fields.One2many('coupon.coupon', 'program_id', string='Cupones',tracking=True)
    coupon_count = fields.Integer(compute='_compute_coupon_count', string='Cupones',tracking=True)
    
    # Campo añadido para solucionar el error
    expected_earning = fields.Float(string='Expected Earning (%)', default=0.0,
                                   help="Expected earning percentage for this pricelist",tracking=True)
    
    # Campos adicionales para los diferentes tipos de promociones
    as_type = fields.Selection([
        ('NORMAL', 'Normal'),
        ('DEAL', 'Oportunidad'),
        ('DEMO', 'Demo'),
        ('ESPECIAL', 'Precio Especial'),
        ('FABRICANTE', 'Rebate')
    ], string='Tipo de Promoción', default='DEAL',tracking=True)
    
    # Campos específicos para diferentes tipos de promociones
    PRICE_UNIT_USD = fields.Float('Precio Unitario USD', help='Para promociones tipo ESPECIAL',tracking=True)
    COST_NIMAX_USD = fields.Float('Costo NIMAX USD', help='Para promociones tipo ESPECIAL',tracking=True)
    DISCOUNT_AMOUNT_USD = fields.Float('Monto Descuento USD', help='Para promociones tipo FABRICANTE',tracking=True)
    COSTO = fields.Float('Costo (%)', help='Porcentaje de costo para promociones tipo DEMO',tracking=True)
    tf_gifted_qty = fields.Integer('Cantidad Regalada', default=0,tracking=True)
    tf_max_gifted_qty = fields.Integer('Cantidad Máxima Regalada', default=999999,tracking=True)
    tf_balance = fields.Float('Balance', compute='_compute_balance',tracking=True)

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