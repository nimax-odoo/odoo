# -*- coding: utf-8 -*-
from asyncio.log import logger
import logging
import uuid
from odoo.tools import float_compare
from odoo.exceptions import UserError
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

class RequestLogger(models.Model):
    _name = 'sd.compute.product.price'
    _description = 'Modelo que permite calcular el precio de los productos de acuerdo a las reglas de negocio'
    
    name = fields.Many2one('res.partner', string='Cliente', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', related = 'pricelist_id.currency_id')
    nimax_price_usd = fields.Monetary(string='Precio USD', required=True, currency_field='currency_id')
    nimax_price_mxn = fields.Monetary(string='Precio MXN', required=True, currency_field='currency_id')
    date_update = fields.Datetime(string='Fecha de Actualización', required=True)
    fuente = fields.Char(string='Fuente', required=True)
    promo_id = fields.Many2one('coupon.program', string='Promoción Aplicada', readonly=True)
   
    def get_partner_ids(self, partner_id=False):
        if partner_id:
            if isinstance(partner_id, int):
                return self.env['res.partner'].browse(partner_id)
            return partner_id

        users = self.env['res.users'].sudo().search([
            ('as_api_enabled', '=', True),
            ('as_partner_id', '!=', False),
            ('as_pricelist', '!=', False),
        ])

        return users.mapped('as_partner_id')
    
    def get_product_ids(self,product_id = False):
        product_ids = product_id
        if not product_ids:
            domain = [('id', '!=', False),('is_storable', '=', True)]
            product_ids = self.env['product.product'].search(domain)
        return product_ids

    def get_promo_ids(self,product, partner,promos_disponibles):
        promo_ids = self.env['coupon.program'].sudo().search_promo(product,partner.id,promos_disponibles)
        return promo_ids
    

                

    def compute_price(self,product_id = False, partner_id = False, promo_ids = False, fuente = 'Cron'):
        partner_ids = self.get_partner_ids(partner_id)
        product_ids = self.get_product_ids(product_id)
        for partner_id in partner_ids:
            user_id = self.env['res.users'].search([('partner_id', '=', partner_id.id)])
            pricelist_id = user_id.as_pricelist
            if pricelist_id:
                for product in product_ids:
                    price = product.product_tmpl_id.compute_price_nimax_without_promo(partner_id, pricelist_id, promo_ids)
                    mxn_currency = self.env['res.currency'].sudo().search([('name', '=', 'MXN')], limit=1)
                    usd_currency = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
                    price_usd = pricelist_id.currency_id._convert(from_amount=price,to_currency=usd_currency,company=self.env.company,date=fields.Datetime.now())
                    price_mxn = pricelist_id.currency_id._convert(from_amount=price,to_currency=mxn_currency,company=self.env.company,date=fields.Datetime.now())
                    if price is None or price == 0:
                        continue
                    vals = {
                        'name': partner_id.id,
                        'product_id': product.id,
                        'pricelist_id': pricelist_id.id,
                        'nimax_price_usd': price_usd,
                        'nimax_price_mxn': price_mxn,
                        'date_update': fields.Datetime.now(),
                        'fuente': fuente,
                    }
                    stock_factor = user_id.as_stock_percentaje
                    # vals['stock'] = round(vals['stock'] * stock_factor, 2)
                    product_prices = self.env['sd.compute.product.price'].sudo().search([
                        ('name', '=', partner_id.id),
                        ('product_id', '=', product.id),
                        ('pricelist_id', '=', pricelist_id.id),
                    ])
                    if not product_prices:
                        self.env['sd.compute.product.price'].sudo().create(vals)
                    else:
                        product_prices.write(vals)
            _logger.info("CLIENTE %s PRICELIST %s", partner_id.name, pricelist_id.name)
            
        
    def syn_cron_prices(self):
        promos_disponibles = self.env['coupon.program'].sudo().search_promo_disponibles()
        self.compute_price_fast(promo_ids = promos_disponibles, fuente='Cron')

    def syn_product_prices(self, product_id, fuente):
        promos_disponibles = self.env['coupon.program'].sudo().search_promo_disponibles()
        self.compute_price_fast(product_id=product_id, promo_ids = promos_disponibles, fuente=fuente)


    def syn_partner_prices(self, partner_id, fuente):
        if isinstance(partner_id, int):
            partner_id = self.env['res.partner'].browse(partner_id)

        users = self.env['res.users'].sudo().search([
            ('as_partner_id', 'in', partner_id.ids),
            ('as_api_enabled', '=', True),
            ('as_pricelist', '!=', False),
        ], limit=1)

        if users:
            self.compute_price_fast(
                partner_id=partner_id,
                fuente=fuente
            )

        # {
        #     "location": "NIMAX/STOCK/CDMX",
        #     "product_code": "C31C163272",
        #     "product_name": "[C31C163272] TMU295-071 SLIP SERIAL C/D ECW",
        #     "product_id": 7920,
        #     "stock": 0,
        #     "reserved_quantity": 0,
        #     "nimax_price_usd": 385.93,
        #     "nimax_price_mxn": 7112.63,
        #     "rate_usd": 18.43,
        #     "attribute_line_ids": [
        #         {
        #             "attribute_name": "Brand",
        #             "values": [
        #                 "Epson"
        #             ]
        #         },
        #         {
        #             "attribute_name": "Brand",
        #             "values": [
        #                 "Epson"
        #             ]
        #         }
        #     ],
        #     "pricelist_name": "N7",
        #     "pricelist_id": 24,
        #     "pricelist_currency": "USD",
        #     "partner_id": 15827,
        #     "partner_name": "CYBERPUERTA"
        # },
    # extract_products(locations_product, user.as_partner_id, warehouse_locations, default_code,location_id):
    
    def extract_product(self, locations_product, as_partner_id, warehouse_locations, default_code,location_id, rate_usd):
        list_product = []
        ubicaciones = warehouse_locations
        if location_id:
            ubicaciones = warehouse_locations[location_id]
        domain = [('name', '=', as_partner_id.id)]
        if default_code:
            domain = [('product_id.default_code', '=', default_code)]
        for location in ubicaciones:
            location_orm = self.env['stock.location'].browse(location)
            if location_orm.usage != 'internal':
                continue
            if location in locations_product:
                not_product = [product for product in locations_product[location] if product not in warehouse_locations]
            else:
                not_product = []

            if location in locations_product:
                not_product = [product for product in locations_product[location] if product not in warehouse_locations]
            else:
                not_product = []
            price_customer = self.env['sd.compute.product.price'].sudo().search([
                *domain,
                ('product_id', 'not in', not_product),
            ])  
            
            for prod_cus in price_customer:
                
                list_product.append({
                "location": location_orm.name,
                "product_code": prod_cus.product_id.default_code,
                "product_name": prod_cus.product_id.name,
                "product_id": prod_cus.product_id.id,
                "stock": 0,
                "reserved_quantity": 0,
                "nimax_price_usd": prod_cus.nimax_price_usd,
                "nimax_price_mxn": prod_cus.nimax_price_mxn,
                "rate_usd": rate_usd,
                "attribute_line_ids": self.get_atribute(prod_cus.product_id.id),
                "pricelist_name": prod_cus.pricelist_id.name,
                "pricelist_id": prod_cus.pricelist_id.id,
                "pricelist_currency": prod_cus.pricelist_id.currency_id.name,
                "partner_id": prod_cus.name.id,
                "partner_name": prod_cus.name.name
                })
        return list_product


    def get_atribute(self, product_id):
        attribute_lines = []
        try:
            product = self.env['product.product'].browse(product_id)
            if product.product_tmpl_id and product.product_tmpl_id.sudo().attribute_line_ids:
                for attr_line in product.product_tmpl_id.sudo().attribute_line_ids:
                    values = []
                    try:
                        for val in attr_line.value_ids:
                            values.append(val.name)
                    except Exception as e:
                        _logger.warning("[as_get_stock_with_price] Error al procesar los valores de attribute_line_id: %s", str(e))
                        
                    attribute_lines.append({
                        "attribute_name": attr_line.attribute_id.name,
                        "values": values
                    })
        except Exception as e:
            _logger.warning("[as_get_stock_with_price] Error al procesar attribute_line_ids para producto %s: %s", product_id, str(e))
            attribute_lines = []
        return attribute_lines

    def extract_products(self, as_partner_id, default_code, rate_usd):
        list_product = []
        domain = [('name', '=', as_partner_id.id)]
        if default_code:
            domain.append(('product_id.default_code', '=', default_code))
        price_customer = self.env['sd.compute.product.price'].sudo().search(domain)
        
        for prod_cus in price_customer:
            
            list_product.append({
            "product_code": prod_cus.product_id.default_code,
            "product_name": prod_cus.product_id.name,
            "product_id": prod_cus.product_id.id,
            "reserved_quantity": 0,
            "nimax_price_usd": prod_cus.nimax_price_usd,
            "nimax_price_mxn": prod_cus.nimax_price_mxn,
            "rate_usd": rate_usd,
            "attribute_line_ids": self.get_atribute(prod_cus.product_id.id),
            "pricelist_name": prod_cus.pricelist_id.name,
            "pricelist_id": prod_cus.pricelist_id.id,
            "pricelist_currency": prod_cus.pricelist_id.currency_id.name,
            "partner_id": prod_cus.name.id,
            "partner_name": prod_cus.name.name
            })
        return list_product




    def compute_price_fast(self,product_id=False,partner_id=False,promo_ids=False,fuente='Cron'):
        Price = self.env['sd.compute.product.price'].sudo()
        Users = self.env['res.users'].sudo()
        Currency = self.env['res.currency'].sudo()
        partners = self.get_partner_ids(partner_id)
        products = self.get_product_ids(product_id)
        if isinstance(partners, int):
            partners = self.env['res.partner'].browse(partners)
        if isinstance(products, int):
            products = self.env['product.product'].browse(products)
        if promo_ids is False:
            promo_ids = self.env['coupon.program'].sudo(
            ).search_promo_disponibles()

        usd = Currency.search([('name', '=', 'USD')], limit=1)
        mxn = Currency.search([('name', '=', 'MXN')], limit=1)
        if not usd or not mxn:
            raise UserError("No se encontraron las monedas USD/MXN")
        company = self.env.company
        today = fields.Date.context_today(self)
        resumen = {
            'calculados': 0,
            'creados': 0,
            'actualizados': 0,
            'sin_cambios': 0,
        }
        # Agrupar productos por categoria una sola vez.
        productos_por_categoria = {}

        for producto in products:
            productos_por_categoria.setdefault(producto.categ_id.id, []).append(producto.id)
        # Procesar cada cliente una sola vez.
        for partner in partners:
            inicio_cliente = resumen.copy()
            # Buscar todos los usuarios asociados
            # mediante as_partner_id.
            users = Users.search([
                ('as_partner_id', '=', partner.id),
                ('as_api_enabled', '=', True),
                ('as_pricelist', '!=', False),
            ])
            if not users:
                _logger.warning("Cliente %s sin usuarios API con lista de precios",partner.id)
                continue
            # Obtener listas de precios unicas.
            # Varios usuarios pueden compartir una lista.
            pricelists = users.mapped('as_pricelist')
            # Obtener categorias autorizadas del cliente.
            categorias_cliente = set(partner.tf_vendor_parameter_ids.mapped('category_id').ids)
            ids_cliente = []
            for categoria_id in categorias_cliente:
                ids_cliente.extend(
                    productos_por_categoria.get(
                        categoria_id, []
                    )
                )
            productos_cliente = self.env['product.product'].browse(ids_cliente)
            if not productos_cliente:
                _logger.info(
                    "Cliente %s sin productos autorizados",
                    partner.id
                )
                continue
            # Procesar cada lista de precios una sola vez.
            for pricelist in pricelists:
                # Procesamiento por lotes de 200 productos.
                for offset in range(0, len(productos_cliente), 200):
                    batch = productos_cliente[offset:offset + 200]
                    # Calcular precios del lote.
                    prices = batch.compute_nimax_prices_batch(partner,pricelist,promo_ids,)
                    # Buscar registros existentes del lote.
                    existing = Price.search([('name', '=', partner.id),('product_id', 'in', batch.ids),('pricelist_id', '=', pricelist.id),
                    ])
                    price_map = {}
                    for rec in existing:
                        key = rec.product_id.id

                        if key in price_map:
                            raise UserError(
                                "Existen precios duplicados para "
                                f"cliente {partner.id}, "
                                f"producto {key}, "
                                f"lista {pricelist.id}"
                            )

                        price_map[key] = rec
                    to_create = []
                    now = fields.Datetime.now()
                    for product in batch:
                        price_data = prices.get(product.id, {})
                        amount = price_data.get('precio', 0.0)
                        promo_aplicada = price_data.get('promo', False)

                        if not amount:
                            continue
                        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
                            raise UserError(f"Precio inválido para producto {product.id}: {amount!r}")

                        resumen['calculados'] += 1
                        price_usd = pricelist.currency_id._convert(amount, usd, company, today)
                        price_mxn = pricelist.currency_id._convert(amount, mxn, company, today)
                        if not amount:
                            continue
                        resumen['calculados'] += 1
                        # Convertir precio a USD.
                        price_usd = (pricelist.currency_id._convert(amount,usd,company,today))
                        # Convertir precio a MXN.
                        price_mxn = (
                            pricelist.currency_id._convert(amount,mxn,company,today
                            )
                        )

                        existing_price = price_map.get(
                            product.id
                        )

                        if existing_price:
                            cambios = {}

                            # Comparar precio USD.
                            if float_compare(
                                existing_price.nimax_price_usd,
                                price_usd,
                                precision_rounding=usd.rounding,
                            ) != 0:
                                cambios[
                                    'nimax_price_usd'
                                ] = price_usd

                            # Comparar precio MXN.
                            if float_compare(
                                existing_price.nimax_price_mxn,
                                price_mxn,
                                precision_rounding=mxn.rounding,
                            ) != 0:
                                cambios[
                                    'nimax_price_mxn'
                                ] = price_mxn

                            if cambios:
                                cambios.update({
                                    'date_update': now,
                                    'fuente': fuente,
                                })

                                existing_price.write(cambios)

                                resumen['actualizados'] += 1

                            else:
                                resumen['sin_cambios'] += 1

                        else:
                            to_create.append({
                                'name': partner.id,
                                'product_id': product.id,
                                'pricelist_id': pricelist.id,
                                'nimax_price_usd': price_usd,
                                'nimax_price_mxn': price_mxn,
                                'date_update': now,
                                'fuente': fuente,
                            })

                    # Crear registros nuevos por lote.
                    if to_create:
                        Price.create(to_create)

                        resumen['creados'] += len(
                            to_create
                        )

            # Resumen individual del cliente.
            resumen_cliente = {
                clave: resumen[clave] - inicio_cliente[clave]
                for clave in resumen
            }

            _logger.info(
                "NIMAX FAST cliente %s: %s",
                partner.id,
                resumen_cliente
            )

        _logger.info(
            "NIMAX FAST TOTAL: %s",
            resumen
        )

        return resumen
