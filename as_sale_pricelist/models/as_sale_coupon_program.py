# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from babel.dates import format_datetime
import logging

_logger = logging.getLogger(__name__)

as_type = ([
    ('NORMAL','Normal'),
    ('DEAL','Oportunidad'),
    ('DEMO','Demo'),
    ('ESPECIAL','Precio Especial'),
    ('FABRICANTE','Rebate'),
    ])

class as_CouponProgram(models.Model):
    _inherit = 'coupon.program'
    _description = 'Programa de Cupones'

    # Campos adicionales específicos de Nimax
    as_price_list = fields.Many2one('product.pricelist', string='Lista de Precios', tracking=True)
    as_type = fields.Selection(as_type, string='Tipo de Promocion', default='NORMAL', tracking=True)
    PRICE_UNIT_USD = fields.Float('PRICE UNIT USD', tracking=True)
    COST_NIMAX_USD = fields.Float('COST NIMAX USD', tracking=True)
    DISCOUNT_AMOUNT_USD = fields.Float('DISCOUNT AMOUNT USD', tracking=True)
    COSTO = fields.Float('% COSTO', tracking=True)
    tf_max_gifted_qty = fields.Float('MAX GIFT QTY', tracking=True)
    tf_gifted_qty = fields.Float('Gifted', readonly=True)
    tf_balance = fields.Float('Balance', compute='_compute_balance', store=True)
    coupon_count = fields.Integer(compute='_compute_coupon_count', string='Cupones', store=True)
    
    # Definir la relación One2many con cupones
    coupon_ids = fields.One2many('coupon.coupon', 'program_id', string='Cupones')

    @api.depends('coupon_ids')
    def _compute_coupon_count(self):
        for record in self:
            record.coupon_count = len(record.coupon_ids)

    @api.depends('tf_max_gifted_qty', 'tf_gifted_qty')
    def _compute_balance(self):
        for rec in self:
            rec.tf_balance = rec.tf_max_gifted_qty - rec.tf_gifted_qty

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        for record in self:
            if record.discount_percentage and (record.discount_percentage < 0 or record.discount_percentage > 100):
                raise ValidationError(_('El porcentaje de descuento debe estar entre 0 y 100.'))

    def _check_promo_code(self, order, coupon_code):
        message = {}
        if self.maximum_use_number != 0 and self.total_order_count >= self.maximum_use_number:
            message = {'error': _('El código promocional %s ha expirado.') % (coupon_code)}
        elif not self._filter_on_mimimum_amount(order):
            message = {'error': _(
                'Se requiere una compra mínima de %(amount)s %(currency)s para obtener la recompensa',
                amount=self.rule_minimum_amount,
                currency=self.currency_id.name
            )}
        elif not self.active:
            message = {'error': _('El código promocional no es válido')}
        elif self.rule_date_from and self.rule_date_from > fields.Datetime.now():
            tzinfo = self.env.context.get('tz') or self.env.user.tz or 'UTC'
            locale = self.env.context.get('lang') or self.env.user.lang or 'es_BO'
            message = {'error': _('Este cupón aún no es utilizable. Será válido a partir de %s') % (
                format_datetime(self.rule_date_from, format='short', tzinfo=tzinfo, locale=locale))}
        elif self.rule_date_to and fields.Datetime.now() > self.rule_date_to:
            message = {'error': _('El código promocional ha expirado')}
        return message

    def _filter_on_mimimum_amount(self, order):
        self.ensure_one()
        if not self.rule_minimum_amount:
            return True
        untaxed_amount = order.amount_untaxed
        if self.rule_minimum_amount_tax_inclusion == 'tax_included':
            untaxed_amount += order.amount_tax
        return untaxed_amount >= self.rule_minimum_amount

    def _is_valid_partner(self, partner):
        self.ensure_one()
        if not self.rule_partners_domain:
            return True
        domain = safe_eval(self.rule_partners_domain)
        return bool(partner.search_count([('id', '=', partner.id)] + domain))

    @api.constrains('rule_date_from', 'rule_date_to')
    def _check_dates(self):
        for record in self:
            if record.rule_date_from and record.rule_date_to and record.rule_date_from > record.rule_date_to:
                raise ValidationError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name}"
            if record.as_type:
                name = f"{name} [{dict(as_type)[record.as_type]}]"
            result.append((record.id, name))
        return result

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (Copia)") % self.name
        default['tf_gifted_qty'] = 0.0
        return super(as_CouponProgram, self).copy(default)

    def write(self, vals):
        _logger.info("[as_CouponProgram] Actualizando programa de cupones %s con valores: %s", self.name, vals)
        return super(as_CouponProgram, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _logger.info("[as_CouponProgram] Creando nuevo programa de cupones con valores: %s", vals)
        return super(as_CouponProgram, self).create(vals_list)

    def action_view_coupons(self):
        """Vista de cupones del programa."""
        self.ensure_one()
        return {
            'name': _('Cupones'),
            'type': 'ir.actions.act_window',
            'res_model': 'coupon.coupon',
            'view_mode': 'tree,form',
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