from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_stock_reassignment(self):
        self.ensure_one()
        return {
            "name": _("Reasignar piezas"),
            "type": "ir.actions.act_window",
            "res_model": "nx.stock.reassignment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_order_id": self.id,
            },
        }
