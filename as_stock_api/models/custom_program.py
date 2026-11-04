# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
class CouponProgram(models.Model):
    _inherit = 'coupon.program'
    
    sd_apply_toprunner_api = fields.Boolean('Aplicar automaticamente al API')

    @api.model
    def search_promo_disponibles(self):
        """
        Carga promociones una sola vez.

        OPTIMIZACIONES:
        - Evita reutilizar productos de otras promociones.
        - Convierte IDs en sets para búsquedas rápidas.
        - Ignora promociones sin dominio válido.
        - Conserva el orden de las promociones.
        """

        promos = []

        Product = self.env['product.product'].sudo()
        Partner = self.env['res.partner'].sudo()

        promociones = self.sudo().search([
            ('sd_apply_toprunner_api', '=', True),
            ('active', '=', True),
        ])

        for promo in promociones:

            # El código original requiere que
            # coincidan producto y cliente.
            if not (
                promo.rule_products_domain
                and promo.rule_partners_domain
            ):
                continue

            try:
                # 1. Evaluar dominio de productos.
                domain_product = safe_eval(
                    promo.rule_products_domain
                )

                product_ids = set(
                    Product.search(domain_product).ids
                )

                if not product_ids:
                    continue

                # 2. Evaluar dominio de clientes.
                domain_partner = safe_eval(
                    promo.rule_partners_domain
                )

                partner_ids = set(
                    Partner.search(domain_partner).ids
                )

                if not partner_ids:
                    continue

                # 3. Guardar información en memoria.
                promos.append({
                    'promo': promo,
                    'productos': product_ids,
                    'clientes': partner_ids,
                    'price_unit_usd': (
                        promo.PRICE_UNIT_USD or 0.0
                    ),
                })

            except Exception:
                _logger.exception(
                    "Error preparando promoción ID %s",
                    promo.id,
                )
                raise

        return promos

    @api.model
    def search_promo(
        self, product, partner, promos_disponibles
    ):
        """
        Busca una promoción sin consultar PostgreSQL.

        Mantiene el retorno original:
        (cumple, precio_usd, promo)
        """

        product_id = (
            product.id if hasattr(product, 'id')
            else product
        )

        partner_id = (
            partner.id if hasattr(partner, 'id')
            else partner
        )

        for promo in promos_disponibles or []:

            # La pertenencia a un set es O(1) promedio.
            if product_id not in promo['productos']:
                continue

            if partner_id not in promo['clientes']:
                continue

            # Primera promoción aplicable.
            return (
                True,
                promo['price_unit_usd'],
                promo['promo'],
            )

        return (
            False,
            0.0,
            self.env['coupon.program'],
        )