from datetime import datetime, time

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare

from .nx_utils import nx_check_group

ESTADOS = [
    ('solicitado', 'Solicitado (falta PM)'),
    ('por_asignar', 'Por asignar a OC'),
    ('en_oc', 'En OC sin confirmar'),
    ('confirmada', 'OC confirmada'),
    ('parcial', 'Recibido parcial'),
    ('recibido', 'Mercancía llegó'),
    ('facturado', 'Facturado'),
    ('cancelado', 'Cancelado'),
]
ENTREGA = [
    ('entregado', 'Entregado'),
    ('en_tiempo', 'En tiempo'),
    ('vence_hoy', 'Vence hoy'),
    ('retrasado', 'Retrasado'),
    ('sin_fecha', 'Sin fecha prevista'),
]
OC_EDITABLE = ('draft', 'sent')
PARAM_DIAS = 'nx_fabrica_logistica.dias_alerta'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ------------------------------------------------------------------
    # Campos que se crean
    # ------------------------------------------------------------------
    # Mismo nombre técnico que ya tenían en producción (se conservan los datos)
    x_studio_linea_product_fabric = fields.Boolean(string='Solicitar a Fabrica', copy=False)
    x_studio_oc_id = fields.Many2one(
        'purchase.order', string='Orden de compra (Logística)', copy=False, index=True,
        ondelete='set null', domain=[('state', 'in', OC_EDITABLE)],
        help='La elige Logística. Solo se ofrecen OC sin confirmar.')
    x_studio_fecha_asignacion = fields.Datetime(
        string='Fecha de asignación', copy=False, readonly=True)
    # Nota por línea del lado de Ventas (columna "Comentarios Ejecutivo" del Excel)
    x_studio_nota_venta = fields.Text(string='Nota (Ventas)', copy=False)

    # ------------------------------------------------------------------
    # Campos que se jalan solos (no se capturan)
    # ------------------------------------------------------------------
    nx_estado = fields.Selection(ESTADOS, string='Estado fábrica',
                                 compute='_compute_nx_estado', store=True, index=True)
    nx_cerrado = fields.Boolean(
        string='Cerrado', compute='_compute_nx_cerrado', store=True, index=True,
        help='Se marca solo cuando la línea queda Facturada. Mientras no se facture, sigue abierta.')
    nx_purchase_line_id = fields.Many2one('purchase.order.line', string='Línea de OC',
                                          compute='_compute_nx_compra')
    nx_fecha_oc = fields.Datetime(string='FechaOC', compute='_compute_nx_compra')
    nx_fecha_prevista = fields.Datetime(string='Fecha prevista de llegada', compute='_compute_nx_compra')
    nx_qty_recibida = fields.Float(string='Cantidad recibida', compute='_compute_nx_compra',
                                   digits='Product Unit')
    nx_entradas = fields.Char(string='Entradas', compute='_compute_nx_compra')
    nx_oc_nombre = fields.Char(related='x_studio_oc_id.name', string='Orden Compra', readonly=True)
    nx_fecha_llegada = fields.Datetime(string='Fecha de llegada', compute='_compute_nx_compra')
    nx_dias = fields.Integer(string='Días transcurridos', compute='_compute_nx_compra')
    # Se capturan en la línea de la OC (purchase.order.line)
    nx_orden_fabricante = fields.Char(string='Orden del fabricante (Sales Order)',
                                      compute='_compute_nx_compra',
                                      search='_search_nx_orden_fabricante')
    nx_nota_compra = fields.Text(string='Nota (Compras)', compute='_compute_nx_compra')
    nx_entrega = fields.Selection(ENTREGA, string='Estado de entrega', compute='_compute_nx_entrega')
    nx_retrasado = fields.Boolean(string='Retrasado', compute='_compute_nx_entrega',
                                  search='_search_nx_retrasado')
    # Colores de la fila: solo verde y rojo
    nx_rojo = fields.Boolean(string='Alerta roja', compute='_compute_nx_colores')
    nx_verde = fields.Boolean(string='Verde', compute='_compute_nx_colores')

    # Datos del pedido, solo para mostrarlos en la lista
    nx_ordenado = fields.Boolean(related='order_id.x_studio_ordenado_a_fabricante',
                                 string='Ordenado a Fabricante', readonly=True)
    nx_marca = fields.Selection(related='order_id.x_studio_marca', string='Marca', readonly=True)
    nx_sucursal_id = fields.Many2one(related='order_id.team_id', string='Sucursal', readonly=True)
    nx_usuario_final = fields.Char(related='order_id.as_usuario_final',
                                   string='Usuario (UF)', readonly=True)
    nx_oc_cliente = fields.Char(related='order_id.x_studio_orden_de_compra',
                                string='OC del cliente', readonly=True)
    nx_fecha_oc_cliente = fields.Date(related='order_id.x_studio_fecha_oc_cliente',
                                      string='Fecha OC del cliente', readonly=True)
    nx_proyecto = fields.Char(related='order_id.x_studio_proyecto_otras_marcas',
                              string='Proyecto otras marcas', readonly=True)
    nx_price_concession = fields.Char(related='order_id.x_studio_price_concession_zebra',
                                      string='Price Concession Zebra', readonly=True)
    nx_dr_zebra = fields.Char(related='order_id.x_studio_dr_zebra', string='DR ZEBRA', readonly=True)
    nx_comentarios = fields.Text(related='order_id.x_studio_comentarios',
                                 string='Comentarios del pedido', readonly=True)
    nx_asistente_id = fields.Many2one(related='order_id.create_uid', string='Asistente', readonly=True)
    nx_clave_cliente = fields.Char(related='order_partner_id.ref', string='Clave de cliente', readonly=True)

    # ------------------------------------------------------------------
    # Cálculos
    # ------------------------------------------------------------------
    def _nx_linea_compra_activa(self):
        """Línea de OC enlazada (sale_line_id) cuya OC no está cancelada."""
        self.ensure_one()
        return self.sudo().purchase_line_ids.filtered(lambda l: l.order_id.state != 'cancel')[:1]

    @api.model
    def _nx_dias_alerta(self):
        valor = self.env['ir.config_parameter'].sudo().get_param(PARAM_DIAS, '15')
        try:
            return int(valor)
        except (TypeError, ValueError):
            return 15

    @api.depends('x_studio_linea_product_fabric', 'display_type', 'invoice_status',
                 'order_id.state', 'order_id.x_studio_ordenado_a_fabricante',
                 'purchase_line_ids.order_id.state', 'purchase_line_ids.qty_received',
                 'purchase_line_ids.product_qty')
    def _compute_nx_estado(self):
        for line in self:
            if not line.x_studio_linea_product_fabric or line.display_type:
                line.nx_estado = False
                continue
            order = line.order_id
            if order.state == 'cancel':
                line.nx_estado = 'cancelado'
            elif order.state != 'sale' or not order.x_studio_ordenado_a_fabricante:
                line.nx_estado = 'solicitado'
            else:
                pl = line._nx_linea_compra_activa()
                if not pl:
                    line.nx_estado = 'por_asignar'
                elif pl.order_id.state in ('draft', 'sent', 'to approve'):
                    line.nx_estado = 'en_oc'
                else:
                    recibida = pl.qty_received or 0.0
                    completo = float_compare(recibida, pl.product_qty, precision_digits=4) >= 0
                    if completo:
                        line.nx_estado = 'facturado' if line.invoice_status == 'invoiced' else 'recibido'
                    elif recibida > 0:
                        line.nx_estado = 'parcial'
                    else:
                        line.nx_estado = 'confirmada'

    @api.depends('nx_estado')
    def _compute_nx_cerrado(self):
        for line in self:
            line.nx_cerrado = line.nx_estado == 'facturado'

    @api.depends('nx_estado', 'purchase_line_ids.order_id.state', 'purchase_line_ids.order_id.date_approve',
                 'purchase_line_ids.date_planned', 'purchase_line_ids.qty_received',
                 'purchase_line_ids.x_studio_orden_fabricante', 'purchase_line_ids.x_studio_nota_compra',
                 'purchase_line_ids.move_ids.state', 'purchase_line_ids.move_ids.date')
    def _compute_nx_compra(self):
        ahora = fields.Datetime.now()
        for line in self:
            pl = line._nx_linea_compra_activa() if line.id else self.env['purchase.order.line']
            line.nx_purchase_line_id = pl
            line.nx_fecha_oc = pl.order_id.date_approve if pl else False
            line.nx_fecha_prevista = pl.date_planned if pl else False
            line.nx_qty_recibida = pl.qty_received if pl else 0.0
            line.nx_orden_fabricante = (pl.x_studio_orden_fabricante or False) if pl else False
            line.nx_nota_compra = (pl.x_studio_nota_compra or False) if pl else False
            movs = pl.move_ids.filtered(lambda m: m.state != 'cancel') if pl else self.env['stock.move']
            line.nx_entradas = ', '.join(movs.picking_id.mapped('name')) or False
            hechos = movs.filtered(lambda m: m.state == 'done')
            fechas = hechos.picking_id.filtered('date_done').mapped('date_done') or hechos.mapped('date')
            llegada = max(fechas) if fechas else False
            line.nx_fecha_llegada = llegada
            if line.nx_fecha_oc:
                fin = llegada if (llegada and line.nx_estado in ('recibido', 'facturado')) else ahora
                line.nx_dias = max((fin - line.nx_fecha_oc).days, 0)
            else:
                line.nx_dias = 0

    @api.depends('nx_estado', 'nx_fecha_prevista')
    def _compute_nx_entrega(self):
        hoy = fields.Date.context_today(self)
        for line in self:
            entrega = False
            if line.nx_estado in ('recibido', 'facturado'):
                entrega = 'entregado'
            elif line.nx_estado in ('confirmada', 'parcial'):
                if not line.nx_fecha_prevista:
                    entrega = 'sin_fecha'
                else:
                    prevista = fields.Datetime.context_timestamp(line, line.nx_fecha_prevista).date()
                    if prevista < hoy:
                        entrega = 'retrasado'
                    elif prevista == hoy:
                        entrega = 'vence_hoy'
                    else:
                        entrega = 'en_tiempo'
            line.nx_entrega = entrega
            line.nx_retrasado = entrega == 'retrasado'

    @api.depends('nx_estado', 'nx_entrega', 'nx_fecha_llegada', 'nx_fecha_oc', 'order_id.date_order')
    def _compute_nx_colores(self):
        """ROJO: cancelado | retrasado | llegó y lleva más de N días sin facturar |
        lleva más de N días sin ordenarse (falta PM) o sin asignarse a OC.
        VERDE: llegó o facturado (si no está en rojo). N = parámetro dias_alerta (15)."""
        limite = self._nx_dias_alerta()
        ahora = fields.Datetime.now()
        for line in self:
            estado = line.nx_estado
            rojo = False
            if estado == 'cancelado' or line.nx_entrega == 'retrasado':
                rojo = True
            elif estado == 'recibido':
                base = line.nx_fecha_llegada or line.nx_fecha_oc
                rojo = bool(base) and (ahora - base).days > limite
            elif estado in ('solicitado', 'por_asignar'):
                fecha = line.order_id.date_order
                rojo = bool(fecha) and (ahora - fecha).days > limite
            line.nx_rojo = rojo
            line.nx_verde = estado in ('recibido', 'facturado') and not rojo

    def _search_nx_retrasado(self, operator, value):
        if operator not in ('=', '!='):
            raise UserError(_('Operador no soportado.'))
        positivo = (operator == '=') == bool(value)
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        hoy = fields.Date.context_today(self)
        inicio = tz.localize(datetime.combine(hoy, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        lineas = self.env['sale.order.line'].sudo().search([
            ('nx_estado', 'in', ('confirmada', 'parcial')),
            ('purchase_line_ids.date_planned', '<', inicio),
        ])
        return [('id', 'in' if positivo else 'not in', lineas.ids)]

    def _search_nx_orden_fabricante(self, operator, value):
        """Permite buscar en la lista por el número de orden del fabricante."""
        if operator not in ('=', 'ilike', 'like', '=ilike', 'in'):
            raise UserError(_('Para buscar por Orden del fabricante usa "contiene" o "igual a".'))
        pols = self.env['purchase.order.line'].sudo().search([
            ('sale_line_id', '!=', False),
            ('x_studio_orden_fabricante', operator, value),
        ])
        return [('id', 'in', pols.sale_line_id.ids)]

    # ------------------------------------------------------------------
    # Asignación a la OC (única acción manual de Logística)
    # ------------------------------------------------------------------
    def write(self, vals):
        if self.env.context.get('nx_skip_oc_sync'):
            return super().write(vals)
        cambia_oc = 'x_studio_oc_id' in vals
        if cambia_oc:
            nx_check_group(self.env, 'group_nx_fabrica_logistica',
                           _('Solo Logística puede asignar la orden de compra.'))
        if 'x_studio_linea_product_fabric' in vals and not vals['x_studio_linea_product_fabric']:
            asignadas = self.filtered('x_studio_oc_id')
            if asignadas:
                raise UserError(_('No se puede quitar "Solicitar a Fabrica": la línea ya está asignada a %s. '
                                  'Logística debe quitar la OC primero.')
                                % ', '.join(asignadas.mapped('x_studio_oc_id.name')))
        anterior = {l.id: l.x_studio_oc_id.id for l in self} if cambia_oc else {}
        res = super().write(vals)
        if cambia_oc:
            self._nx_sincronizar_oc(anterior)
        elif 'product_uom_qty' in vals:
            self._nx_sincronizar_cantidad()
        return res

    def _nx_validar_asignable(self, po):
        self.ensure_one()
        if self.display_type or not self.product_id:
            raise UserError(_('Solo se pueden asignar líneas con producto.'))
        if self.order_id.state != 'sale':
            raise UserError(_('El pedido %s no está confirmado.') % self.order_id.name)
        if not self.x_studio_linea_product_fabric:
            raise UserError(_('La línea "%s" no está marcada como "Solicitar a Fabrica".')
                            % self.product_id.display_name)
        if not self.order_id.x_studio_ordenado_a_fabricante:
            raise UserError(_('El PM aún no marca "Ordenado a Fabricante" en el pedido %s.')
                            % self.order_id.name)
        if po.state not in OC_EDITABLE:
            raise UserError(_('La OC %s ya está confirmada; elige una OC sin confirmar.') % po.name)
        if po.company_id != self.company_id:
            raise UserError(_('La OC %s es de otra empresa.') % po.name)

    def _nx_crear_linea_oc(self, po):
        self.ensure_one()
        product = self.product_id
        vals = {
            'order_id': po.id,
            'product_id': product.id,
            'product_qty': self.product_uom_qty,
            'product_uom_id': self.product_uom_id.id,
            'sale_line_id': self.id,
        }
        if 'x_studio_sku_no_de_parte' in self.env['purchase.order.line']._fields:
            vals['x_studio_sku_no_de_parte'] = product.default_code or False
        return self.env['purchase.order.line'].sudo().create(vals)

    def _nx_sincronizar_oc(self, anterior):
        ahora = fields.Datetime.now()
        for line in self:
            po = line.x_studio_oc_id
            activa = line._nx_linea_compra_activa()
            previa = anterior.get(line.id)
            sudo_line = line.sudo().with_context(nx_skip_oc_sync=True)
            if po:
                if activa and activa.order_id == po:
                    continue
                line._nx_validar_asignable(po)
                if activa:
                    if activa.order_id.id != previa:
                        raise UserError(_('La línea "%s" ya tiene una línea de compra en la OC %s que no '
                                          'asignó Logística. Revísala antes de asignarla.')
                                        % (line.product_id.display_name, activa.order_id.name))
                    if activa.order_id.state not in OC_EDITABLE:
                        raise UserError(_('La línea ya está en la OC %s, que está confirmada. '
                                          'No se puede mover.') % activa.order_id.name)
                    activa.with_context(nx_skip_oc_sync=True).unlink()
                line._nx_crear_linea_oc(po)
                sudo_line.write({'x_studio_fecha_asignacion': ahora})
                po.sudo().message_post(body=_('Línea agregada desde el pedido %s (%s x %s) por %s.') % (
                    line.order_id.name, line.product_id.display_name, line.product_uom_qty,
                    self.env.user.name))
                line.order_id.sudo().message_post(body=_('"%s" asignado a la OC %s por %s.') % (
                    line.product_id.display_name, po.name, self.env.user.name))
            else:
                if activa and activa.order_id.id == previa:
                    if activa.order_id.state not in OC_EDITABLE:
                        raise UserError(_('La línea está en la OC %s, que ya está confirmada. '
                                          'No se puede quitar.') % activa.order_id.name)
                    activa.with_context(nx_skip_oc_sync=True).unlink()
                    line.order_id.sudo().message_post(body=_('"%s" fue retirado de la OC %s por %s.') % (
                        line.product_id.display_name, activa.order_id.name, self.env.user.name))
                sudo_line.write({'x_studio_fecha_asignacion': False})

    def _nx_sincronizar_cantidad(self):
        for line in self:
            if not line.x_studio_oc_id:
                continue
            activa = line._nx_linea_compra_activa()
            if not activa or activa.order_id != line.x_studio_oc_id:
                continue
            if activa.product_qty == line.product_uom_qty:
                continue
            if activa.order_id.state in OC_EDITABLE:
                activa.with_context(nx_skip_oc_sync=True).write({'product_qty': line.product_uom_qty})
                activa.order_id.message_post(body=_('Cantidad actualizada desde el pedido %s: %s') % (
                    line.order_id.name, line.product_uom_qty))
            else:
                raise UserError(_('No se puede cambiar la cantidad: la línea ya está en la OC %s, que está '
                                  'confirmada. Avisa a Logística.') % activa.order_id.name)

    def action_nx_abrir_asignar(self):
        if not self:
            raise UserError(_('Selecciona al menos una línea.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Asignar a orden de compra'),
            'res_model': 'nx.fabrica.asignar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_line_ids': [(6, 0, self.ids)]},
        }
