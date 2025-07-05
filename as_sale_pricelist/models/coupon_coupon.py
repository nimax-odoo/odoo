from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CouponCoupon(models.Model):
    _name = 'coupon.coupon'
    _description = 'Coupon'
    _order = "id desc"

    name = fields.Char(string="Coupon Name", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    code = fields.Char(string="Coupon Code", required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('coupon.coupon'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    program_id = fields.Many2one('coupon.program', string='Program', ondelete='cascade', required=True)
    discount_percentage = fields.Float(related='program_id.discount_percentage', readonly=True)
    discount_fixed_amount = fields.Float(related='program_id.discount_fixed_amount', readonly=True)
    discount_type = fields.Selection(related='program_id.discount_type', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    order_id = fields.Many2one('sale.order', string='Order')
    date = fields.Datetime(string='Usage Date', readonly=True)
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='Expiration Date')
    active = fields.Boolean(default=True, string='Active')
    
    _sql_constraints = [
        ('unique_coupon_code', 'unique(code)', 'The coupon code must be unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('coupon.coupon') or _('New')
            _logger.info("[CouponCoupon] Creating new coupon with values: %s", vals)
        result = super(CouponCoupon, self).create(vals_list)
               
        return result
        
    def write(self, vals):
        _logger.info("[CouponCoupon] Updating coupon %s with values: %s", self.name, vals)
        result = super(CouponCoupon, self).write(vals)
        
        # Fix para el bug de follower con model_field False
        if self:
            self.env.cr.execute("""
                DELETE FROM mail_followers
                WHERE res_model = 'coupon.coupon'
                AND res_id IN %s
                AND id IN (
                    SELECT f.id FROM mail_followers f
                    LEFT JOIN res_partner p ON f.partner_id = p.id
                    WHERE p.id IS NULL OR p.active = false
                )
            """, [tuple(self.ids)])
            
        return result
        
    def unlink(self):
        for coupon in self:
            if coupon.state != 'draft':
                raise ValidationError(_('You cannot delete a coupon which is not in draft state'))
        return super(CouponCoupon, self).unlink()
        
    def action_confirm(self):
        for coupon in self:
            coupon.state = 'sent'
        
    def action_cancel(self):
        for coupon in self:
            coupon.state = 'cancelled'
    
    def action_use(self):
        for coupon in self:
            coupon.write({
                'state': 'used',
                'date': fields.Datetime.now()
            })
            
    def _check_validity(self):
        self.ensure_one()
        if self.state != 'sent':
            return {'error': _('This coupon %s is not valid anymore.') % self.code}
        if self.date_end and fields.Datetime.now() > self.date_end:
            self.state = 'expired'
            return {'error': _('This coupon has expired (%s).') % self.date_end}
        if self.date_start and fields.Datetime.now() < self.date_start:
            return {'error': _('This coupon is not valid yet (%s).') % self.date_start}
        return {} 