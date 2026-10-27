from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class StockReassignmentWizard(models.TransientModel):
    _name = "nx.stock.reassignment.wizard"
    _description = "Reasignar piezas reservadas entre pedidos"

    source_order_id = fields.Many2one(
        "sale.order",
        string="Pedido origen",
        required=True,
        readonly=True,
    )
    source_move_id = fields.Many2one(
        "stock.move",
        string="Producto / movimiento origen",
        required=True,
        domain="[('id', 'in', available_source_move_ids)]",
    )
    available_source_move_ids = fields.Many2many(
        "stock.move",
        compute="_compute_available_source_moves",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        related="source_move_id.product_id",
        readonly=True,
    )
    source_reserved_qty = fields.Float(
        string="Reservado en origen",
        compute="_compute_quantities",
        digits="Product Unit of Measure",
    )
    destination_order_id = fields.Many2one(
        "sale.order",
        string="Pedido destino",
        required=True,
        domain="[('id', 'in', available_destination_order_ids)]",
    )
    available_destination_order_ids = fields.Many2many(
        "sale.order",
        compute="_compute_available_destinations",
    )
    destination_move_id = fields.Many2one(
        "stock.move",
        string="Movimiento destino",
        required=True,
        domain="[('id', 'in', available_destination_move_ids)]",
    )
    available_destination_move_ids = fields.Many2many(
        "stock.move",
        compute="_compute_available_destination_moves",
    )
    destination_pending_qty = fields.Float(
        string="Pendiente por reservar en destino",
        compute="_compute_quantities",
        digits="Product Unit of Measure",
    )
    quantity = fields.Float(
        string="Cantidad a reasignar",
        required=True,
        digits="Product Unit of Measure",
    )

    @api.depends("source_order_id")
    def _compute_available_source_moves(self):
        for wizard in self:
            wizard.available_source_move_ids = wizard._get_order_moves(
                wizard.source_order_id
            ).filtered(lambda move: move.quantity > 0)

    @api.depends("source_move_id", "source_order_id")
    def _compute_available_destinations(self):
        SaleOrder = self.env["sale.order"]
        for wizard in self:
            if not wizard.source_move_id:
                wizard.available_destination_order_ids = SaleOrder
                continue
            product = wizard.source_move_id.product_id
            warehouse = wizard.source_order_id.warehouse_id
            candidate_moves = self.env["stock.move"].search([
                ("product_id", "=", product.id),
                ("state", "in", ["confirmed", "partially_available", "assigned"]),
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("sale_line_id.order_id", "!=", wizard.source_order_id.id),
                ("sale_line_id.order_id.state", "in", ["sale", "done"]),
                ("sale_line_id.order_id.warehouse_id", "=", warehouse.id),
            ])
            valid_moves = candidate_moves.filtered(
                lambda move: move.product_uom_qty > move.quantity
            )
            wizard.available_destination_order_ids = valid_moves.mapped(
                "sale_line_id.order_id"
            )

    @api.depends("destination_order_id", "source_move_id")
    def _compute_available_destination_moves(self):
        StockMove = self.env["stock.move"]
        for wizard in self:
            if not wizard.destination_order_id or not wizard.source_move_id:
                wizard.available_destination_move_ids = StockMove
                continue
            wizard.available_destination_move_ids = wizard._get_order_moves(
                wizard.destination_order_id
            ).filtered(
                lambda move: move.product_id == wizard.source_move_id.product_id
                and move.product_uom_qty > move.quantity
            )

    @api.depends("source_move_id", "destination_move_id")
    def _compute_quantities(self):
        for wizard in self:
            wizard.source_reserved_qty = wizard.source_move_id.quantity
            wizard.destination_pending_qty = max(
                wizard.destination_move_id.product_uom_qty
                - wizard.destination_move_id.quantity,
                0.0,
            )

    @api.onchange("source_move_id")
    def _onchange_source_move_id(self):
        self.destination_order_id = False
        self.destination_move_id = False
        self.quantity = 0.0

    @api.onchange("destination_order_id")
    def _onchange_destination_order_id(self):
        self.destination_move_id = False
        moves = self.available_destination_move_ids
        if len(moves) == 1:
            self.destination_move_id = moves

    def _get_order_moves(self, order):
        if not order:
            return self.env["stock.move"]
        return order.order_line.move_ids.filtered(
            lambda move: move.state in ("confirmed", "partially_available", "assigned")
            and move.picking_id
            and move.picking_id.picking_type_id.code == "outgoing"
            and not move.scrapped
        )

    def _validate_moves(self):
        self.ensure_one()
        source = self.source_move_id
        destination = self.destination_move_id
        rounding = source.product_uom.rounding

        if not self.env.user.has_group("stock.group_stock_manager"):
            raise UserError(_("Solo un administrador de inventario puede reasignar piezas."))
        if source == destination:
            raise ValidationError(_("El movimiento origen y destino deben ser diferentes."))
        if source.product_id != destination.product_id:
            raise ValidationError(_("Solo se puede reasignar exactamente el mismo producto."))
        if source.product_uom != destination.product_uom:
            raise ValidationError(_("Ambos movimientos deben utilizar la misma unidad de medida."))
        if self.source_order_id.warehouse_id != self.destination_order_id.warehouse_id:
            raise ValidationError(_("Los pedidos deben pertenecer al mismo almacen."))
        if source.location_id != destination.location_id:
            raise ValidationError(_("Las entregas deben reservar desde la misma ubicacion de origen."))
        if source.state not in ("confirmed", "partially_available", "assigned"):
            raise ValidationError(_("El movimiento origen ya no permite cambiar reservas."))
        if destination.state not in ("confirmed", "partially_available", "assigned"):
            raise ValidationError(_("El movimiento destino ya no permite recibir reservas."))
        if source.move_line_ids.filtered("picked") or destination.move_line_ids.filtered("picked"):
            raise ValidationError(_("No se pueden modificar operaciones que ya fueron marcadas como recogidas."))
        if float_compare(self.quantity, 0.0, precision_rounding=rounding) <= 0:
            raise ValidationError(_("La cantidad debe ser mayor que cero."))
        if float_compare(self.quantity, source.quantity, precision_rounding=rounding) > 0:
            raise ValidationError(_("No puede reasignar mas de lo reservado en el pedido origen."))
        destination_pending = destination.product_uom_qty - destination.quantity
        if float_compare(self.quantity, destination_pending, precision_rounding=rounding) > 0:
            raise ValidationError(_("La cantidad supera lo pendiente por reservar en el pedido destino."))

    def action_reassign(self):
        self.ensure_one()
        self._validate_moves()

        source = self.source_move_id
        destination = self.destination_move_id
        qty = self.quantity
        source_reserved_before = source.quantity
        destination_reserved_before = destination.quantity
        source_restore_qty = source_reserved_before - qty

        # Liberamos el movimiento origen completo para que Odoo actualice quants y
        # lineas de movimiento con su logica estandar. Luego el destino toma solo
        # la cantidad solicitada y el origen recupera el resto.
        source._do_unreserve()
        destination._action_assign(force_qty=qty)

        received_qty = destination.quantity - destination_reserved_before
        rounding = source.product_uom.rounding
        if float_compare(received_qty, qty, precision_rounding=rounding) < 0:
            raise UserError(_(
                "No fue posible reservar la cantidad completa en el pedido destino. "
                "La operacion fue cancelada sin guardar cambios."
            ))

        if float_compare(source_restore_qty, 0.0, precision_rounding=rounding) > 0:
            source._action_assign(force_qty=source_restore_qty)
            if float_compare(source.quantity, source_restore_qty, precision_rounding=rounding) < 0:
                raise UserError(_(
                    "No fue posible devolver al pedido origen todas las piezas que debian permanecer reservadas. "
                    "La operacion fue cancelada sin guardar cambios."
                ))

        product_name = source.product_id.display_name
        source_order = self.source_order_id
        destination_order = self.destination_order_id
        message = _(
            "Se reasignaron %(qty)s %(uom)s de %(product)s desde %(source)s hacia %(destination)s.",
            qty=qty,
            uom=source.product_uom.name,
            product=product_name,
            source=source_order.name,
            destination=destination_order.name,
        )
        source_order.message_post(body=message)
        destination_order.message_post(body=message)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Reasignacion completada"),
                "message": message,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
