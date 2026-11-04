# -*- coding: utf-8 -*-

import logging
from datetime import date

from odoo import api, fields, models, _
from odoo import models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def compute_nimax_prices_batch(self, partner, pricelist, promos_disponibles):
        """
        Calcula precios NIMAX para varios productos.
        Retorna:
            {
                product_id: {
                    'precio': 150.00,
                    'promo': False
                }
            }
        No crea ni modifica registros.
        """

        partner.ensure_one()
        pricelist.ensure_one()

        if not self:
            return {}
        Product = self.env['product.product'].sudo()
        company = self.env.company
        today = fields.Date.context_today(self)
        Program = self.env['coupon.program'].sudo()

        # 1. Preparar parámetros comerciales por categoría.
        parametros = {}

        for param in partner.tf_vendor_parameter_ids:
            if param.category_id:
                parametros[param.category_id.id] = param

        # 2. Seleccionar primera variante de cada plantilla.
        variantes = Product.search([
            (
                'product_tmpl_id',
                'in',
                self.mapped('product_tmpl_id').ids
            )
        ])

        primeras = {}

        for variante in variantes:
            primeras.setdefault(
                variante.product_tmpl_id.id,
                variante
            )

        productos = Product.browse([
            p.id for p in primeras.values()
        ])

        # 3. Preparar resultados.
        precios_base = {}
        sin_promocion = []
        precios_finales = {}
        promos_aplicadas = {}

        # 4. Evaluar promociones.
        for product in productos:

            promos_aplicadas[product.id] = False

            param = parametros.get(
                product.categ_id.id
            )

            if not param:
                precios_finales[product.id] = 0.0
                continue

            try:
                promo = Program.search_promo(
                    product,
                    partner.id,
                    promos_disponibles
                )

                if promo and promo[0]:

                    # Precio definido por promoción.
                    precios_finales[product.id] = (
                        promo[1] or 0.0
                    )

                    # Promoción aplicada.
                    promocion = promo[0]

                    # Si es un registro Odoo, guardar su ID.
                    # Si ya es un ID, conservarlo.
                    # Si devuelve True, conservar True.
                    promos_aplicadas[product.id] = (
                        promocion.id
                        if hasattr(promocion, 'id')
                        else promocion
                    )

                else:
                    sin_promocion.append(product.id)

            except Exception:
                _logger.exception(
                    "Error promoción producto %s",
                    product.id
                )

                precios_finales[product.id] = 0.0
                promos_aplicadas[product.id] = False

        # 5. Calcular reglas de lista de precios por lote.
        rules = {}

        productos_normales = Product.browse(
            sin_promocion
        )

        if productos_normales:
            try:
                rules = pricelist._compute_price_rule(
                    products=productos_normales,
                    quantity=1,
                    currency=pricelist.currency_id,
                    date=today
                )

            except Exception:
                _logger.exception(
                    "Error calculando lista en lote; "
                    "usando cálculo individual de respaldo"
                )

                for product in productos_normales:
                    try:
                        rules.update(
                            pricelist._compute_price_rule(
                                products=product,
                                quantity=1,
                                currency=pricelist.currency_id,
                                uom=product.uom_id,
                                date=today
                            )
                        )

                    except Exception:
                        rules[product.id] = (
                            product.list_price,
                            False
                        )

        # 6. Aplicar fórmula comercial NIMAX.
        for product in productos_normales:

            try:
                param = parametros[
                    product.categ_id.id
                ]

                price_unit = rules.get(
                    product.id,
                    (product.list_price, False)
                )[0]

                if not price_unit:
                    precios_base[product.id] = 0.0
                    continue

                precios_base[product.id] = (
                    product.list_price
                    * (1 - param.partner_discount / 100)
                    * (param.cost_deal_import / 100)
                    * (product.tf_import_tax / 100)
                )

            except Exception:
                _logger.exception(
                    "Error fórmula NIMAX producto %s",
                    product.id
                )

                precios_finales[product.id] = 0.0

        # 7. Convertir moneda y aplicar utilidad.
        expected = (
            pricelist.expected_earning or 0.0
        )

        divisor = 1 - expected / 100

        for product in productos:

            # Productos promocionados ya tienen precio final.
            if product.id in precios_finales:
                continue

            try:
                base = precios_base.get(
                    product.id,
                    0.0
                )

                convertido = company.currency_id._convert(
                    base,
                    pricelist.currency_id,
                    company,
                    today
                )

                precios_finales[product.id] = (
                    convertido / divisor
                    if expected
                    else convertido
                )

            except Exception:
                _logger.exception(
                    "Error precio final producto %s",
                    product.id
                )

                precios_finales[product.id] = 0.0

        # 8. Retornar precio y promoción por producto.
        resultado = {}

        for product in self:

            primera = primeras.get(
                product.product_tmpl_id.id
            )

            if primera:
                resultado[product.id] = {
                    'precio': precios_finales.get(
                        primera.id,
                        0.0
                    ),
                    'promo': promos_aplicadas.get(
                        primera.id,
                        False
                    )
                }

            else:
                resultado[product.id] = {
                    'precio': 0.0,
                    'promo': False
                }

        return resultado
