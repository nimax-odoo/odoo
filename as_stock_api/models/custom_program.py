
from collections import defaultdict
from asyncio.log import logger
import logging
import uuid
from odoo.tools import float_compare
from odoo.exceptions import UserError
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)
from odoo import api, models
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)


class CouponProgram(models.Model):
    _inherit = 'coupon.program'

    sd_apply_toprunner_api = fields.Boolean('Aplicar automaticamente al API')
    sd_apply_toprunner_ecommerce = fields.Boolean('Aplicar automaticamente al Ecommerce')

    _NIMAX_FIELDS = {
        'active',
        'sd_apply_toprunner_api',
        'sd_apply_toprunner_ecommerce',
        'rule_products_domain',
        'rule_partners_domain',
        'PRICE_UNIT_USD',
    }

    def _nimax_get_scope(
        self, product_ids=None, partner_ids=None
    ):
        """
        Obtiene productos y clientes de UNA promoción.

        Permite restringir la búsqueda a IDs concretos.
        """

        self.ensure_one()

        empty = {
            'productos': set(),
            'clientes': set(),
        }

        if not self.active:
            return empty

        if not (
            self.sd_apply_toprunner_api
            or self.sd_apply_toprunner_ecommerce
        ):
            return empty

        if not (
            self.rule_products_domain
            and self.rule_partners_domain
        ):
            return empty

        Product = self.env['product.product'].sudo()
        Partner = self.env['res.partner'].sudo()

        domain_product = list(
            safe_eval(self.rule_products_domain)
        )
        domain_partner = list(
            safe_eval(self.rule_partners_domain)
        )

        if product_ids is not None:
            domain_product.append(
                ('id', 'in', list(product_ids))
            )

        if partner_ids is not None:
            domain_partner.append(
                ('id', 'in', list(partner_ids))
            )

        productos = set(
            Product.search(domain_product).ids
        )

        if not productos:
            return empty

        clientes = set(
            Partner.search(domain_partner).ids
        )

        return {
            'productos': productos,
            'clientes': clientes,
        }

    @api.model
    def search_promo_disponibles(
        self, product_ids=None, partner_ids=None
    ):
        """
        Carga promociones disponibles, opcionalmente
        limitadas a productos y clientes específicos.

        Mantiene la estructura original de promo_ids.
        """

        if product_ids is not None:
            product_ids = set(product_ids)

        if partner_ids is not None:
            partner_ids = set(partner_ids)

        if (
            product_ids is not None and not product_ids
        ) or (
            partner_ids is not None and not partner_ids
        ):
            return []

        promociones = self.sudo().search([
            ('active', '=', True),
            '|',
            ('sd_apply_toprunner_api', '=', True),
            ('sd_apply_toprunner_ecommerce', '=', True),
        ])

        resultado = []

        for promo in promociones:
            try:
                scope = promo._nimax_get_scope(
                    product_ids=product_ids,
                    partner_ids=partner_ids,
                )

                if not (
                    scope['productos']
                    and scope['clientes']
                ):
                    continue

                resultado.append({
                    'promo': promo,
                    'productos': scope['productos'],
                    'clientes': scope['clientes'],
                    'price_unit_usd': (
                        promo.PRICE_UNIT_USD or 0.0
                    ),
                })

            except Exception:
                _logger.exception(
                    "Error preparando promoción %s",
                    promo.id,
                )
                raise

        return resultado

    @api.model
    def _nimax_recalculate_scopes(self, scopes):
        """
        Recalcula exclusivamente las combinaciones
        producto/cliente afectadas.

        Recibe los alcances anteriores y posteriores
        de las promociones modificadas.
        """

        afectados = defaultdict(set)

        # Cada scope conserva su propia relación
        # entre productos y clientes.
        for scope in scopes:
            productos = scope['productos']
            clientes = scope['clientes']

            if not productos or not clientes:
                continue

            for partner_id in clientes:
                afectados[partner_id].update(productos)

        if not afectados:
            return

        PriceModel = self.env[
            'sd.compute.product.price'
        ].sudo()

        Product = self.env['product.product'].sudo()
        Users = self.env['res.users'].sudo()

        # Reutilizamos las reglas existentes para
        # obtener usuarios habilitados para API.
        users = PriceModel.get_users_ids(False)

        if isinstance(users, int):
            users = Users.browse(users)

        if not users:
            return

        # Solo clientes que tienen usuarios disponibles.
        clientes_con_usuarios = {
            user.as_partner_id.id
            for user in users
            if user.as_partner_id
        }

        afectados = {
            pid: productos
            for pid, productos in afectados.items()
            if pid in clientes_con_usuarios
        }

        if not afectados:
            return

        todos_productos = set()

        for productos in afectados.values():
            todos_productos.update(productos)

        # Cargar TODAS las promociones actuales que
        # podrían aplicar a los registros afectados.
        # No solamente la promoción modificada.
        promos_disponibles = (
            self.env['coupon.program']
            .sudo()
            .search_promo_disponibles(
                product_ids=todos_productos,
                partner_ids=set(afectados),
            )
        )

        # Agrupar clientes que necesitan recalcular
        # exactamente el mismo conjunto de productos.
        grupos = defaultdict(list)

        for partner_id, productos in afectados.items():
            grupos[frozenset(productos)].append(
                partner_id
            )

        for productos_ids, clientes_ids in grupos.items():

            clientes_set = set(clientes_ids)

            usuarios_grupo = users.filtered(
                lambda u: (
                    u.as_partner_id.id in clientes_set
                )
            )

            productos_grupo = Product.browse(
                list(productos_ids)
            ).exists()

            if not usuarios_grupo or not productos_grupo:
                continue

            resumen = PriceModel.compute_price_fast(
                product_records=productos_grupo,
                user_records=usuarios_grupo,
                promo_ids=promos_disponibles,
                fuente='Promocion',
            )

            _logger.info(
                "NIMAX recálculo promociones "
                "clientes=%s productos=%s resumen=%s",
                clientes_ids,
                len(productos_grupo),
                resumen,
            )


    def compute_promo(self):
        """
        Recalcula los precios de la promoción actual,
        incluyendo registros que todavía tienen
        esta promoción asignada.
        """

        scopes = [
            promo._nimax_get_scope()
            for promo in self
        ]

        # Recuperar precios que tenían esta promoción
        # previamente aplicada.
        precios = self.env[
            'sd.compute.product.price'
        ].sudo().search([
            ('promo_id', 'in', self.ids)
        ])

        afectados = defaultdict(set)

        for precio in precios:
            afectados[precio.name.id].add(
                precio.product_id.id
            )

        for partner_id, productos in afectados.items():
            scopes.append({
                'productos': productos,
                'clientes': {partner_id},
            })

        self._nimax_recalculate_scopes(scopes)

        return True


    def write(self, vals):

        if (
            self.env.context.get('skip_nimax_promo_recalc')
            or not (self._NIMAX_FIELDS & vals.keys())
        ):
            return super().write(vals)

        # 1. Alcance ANTES del cambio.
        scopes_antes = [
            promo._nimax_get_scope()
            for promo in self
        ]

        # 2. Guardar los cambios.
        result = super().write(vals)

        # 3. Alcance DESPUÉS del cambio.
        scopes_despues = [
            promo._nimax_get_scope()
            for promo in self
        ]

        # 4. Recalcular afectados anteriores y nuevos.
        self._nimax_recalculate_scopes(
            scopes_antes + scopes_despues
        )

        return result

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        if not self.env.context.get(
            'skip_nimax_promo_recalc'
        ):
            scopes = [
                promo._nimax_get_scope()
                for promo in records
            ]

            self._nimax_recalculate_scopes(scopes)

        return records

    def unlink(self):

        scopes = [
            promo._nimax_get_scope()
            for promo in self
        ]

        result = super().unlink()

        if not self.env.context.get(
            'skip_nimax_promo_recalc'
        ):
            self._nimax_recalculate_scopes(scopes)

        return result


    @api.model
    def get_promos_cliente(
        self, partner, product_ids, promos_disponibles
    ):
        """
        Obtiene las promociones aplicables a un cliente.

        Retorna:
            {product_id: info_promocion}

        Respeta el orden y la primera promoción.
        No realiza consultas SQL.
        """

        partner_id = (
            partner.id if hasattr(partner, 'id')
            else partner
        )

        pendientes = set(product_ids)
        promos_cliente = {}

        for info in promos_disponibles or []:

            if partner_id not in info['clientes']:
                continue

            coincidentes = (
                pendientes & info['productos']
            )

            for product_id in coincidentes:
                promos_cliente[product_id] = info

            pendientes.difference_update(coincidentes)

            if not pendientes:
                break

        return promos_cliente


    @api.model
    def search_promo(
        self, product, partner, promos_disponibles
    ):
        """
        Busca una promoción en las promociones
        previamente cargadas.

        Retorna:
            (cumple, precio_usd, promocion)

        No realiza consultas SQL.
        """

        product_id = (
            product.id
            if hasattr(product, 'id')
            else product
        )

        partner_id = (
            partner.id
            if hasattr(partner, 'id')
            else partner
        )

        for info in promos_disponibles or []:

            if product_id not in info['productos']:
                continue

            if partner_id not in info['clientes']:
                continue

            return (
                True,
                info['price_unit_usd'],
                info['promo'],
            )

        return (
            False,
            0.0,
            self.env['coupon.program'],
        )
