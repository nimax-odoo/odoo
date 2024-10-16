from datetime import timedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cart_expire_date = fields.Datetime(
        compute="_compute_cart_expire_date",
        help="Campo técnico: La fecha en que este carrito expirará automáticamente",
    )

    def _should_bypass_cart_expiration(self):
        """Método gancho para prevenir que un carrito expire"""
        self.ensure_one()
        # No cancelar carritos que ya están en pago.
        return any(
            tx.state in ["pending", "authorized", "done"] for tx in self.transaction_ids
        )

    @api.depends(
        "write_date",
        "website_id.cart_expire_delay",
        "transaction_ids.last_state_change",
    )
    def _compute_cart_expire_date(self):
        for rec in self:
            if (
                rec.state == "draft"
                and rec.website_id.cart_expire_delay
                and not rec._should_bypass_cart_expiration()
            ):
                # En el caso de registros en borrador, usar la fecha actual
                from_date = rec.write_date or fields.Datetime.now()
                # En el caso de registros con transacciones, considerar la última fecha de transacción
                if rec.transaction_ids:
                    last_tx_date = max(
                        rec.transaction_ids.mapped(
                            lambda x: x.last_state_change or x.write_date
                        )
                    )
                    from_date = max(from_date, last_tx_date)
                expire_delta = timedelta(hours=rec.website_id.cart_expire_delay)
                rec.cart_expire_date = from_date + expire_delta
            elif rec.cart_expire_date:
                rec.cart_expire_date = False
