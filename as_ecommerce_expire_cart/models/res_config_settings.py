from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cart_expire_delay = fields.Float(
        related="website_id.cart_expire_delay", readonly=False
    )
