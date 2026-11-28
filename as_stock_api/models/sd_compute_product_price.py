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

    _cliente_producto_uniq = models.Constraint(
        'UNIQUE(name, product_id)',
        'Ya existe un precio para este cliente y producto.'
    )

    name = fields.Many2one('res.partner', string='Cliente', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', related = 'pricelist_id.currency_id')
    nimax_price_usd = fields.Monetary(string='Precio USD', required=True, currency_field='currency_id')
    nimax_price_mxn = fields.Monetary(string='Precio MXN', required=True, currency_field='currency_id')
    date_update = fields.Datetime(string='Fecha de Actualización', required=True)
    fuente = fields.Char(string='Fuente', required=True)
    promo_id = fields.Many2one('coupon.program', string='Promoción Aplicada', readonly=True)


    def get_users_ids(self, partner_id=False):
        domain = []
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        users = self.env['res.users'].sudo().search(domain)
        return users
    
    def get_product_ids(self,product_id = False):
        product_ids = product_id
        if not product_ids:
            domain = [('id', '!=', False),('is_storable', '=', True)]
            product_ids = self.env['product.product'].search(domain)
        return product_ids

    def get_promo_ids(self,product, partner,promos_disponibles):
        promo_ids = self.env['coupon.program'].sudo().search_promo(product,partner.id,promos_disponibles)
        return promo_ids
    
    def extract_prices(self, partner_id=False, pricelist_id=False):
        sql = """
            SELECT name, product_id, nimax_price_usd, nimax_price_mxn
            FROM sd_compute_product_price
        """
        params = ()
        conditions = []
        if partner_id:
            conditions.append("name = %s")
            params += (partner_id,)
        if pricelist_id:
            conditions.append("pricelist_id = %s")
            params += (pricelist_id,)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        self.env.cr.execute(sql, params)
        return {(p, prod): {'usd': usd, 'mxn': mxn} for p, prod, usd, mxn in self.env.cr.fetchall()}

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
        self.compute_price_fast(partner_id=partner_id,fuente=fuente)
    
    def extract_product(self, locations_product, as_partner_id, warehouse_locations, default_code,location_id, rate_usd):
        list_product = []
        ubicaciones = warehouse_locations
        if location_id:
            ubicaciones = warehouse_locations[location_id]
        domain = [('name', '=', as_partner_id.id),('product_id.active', '=', True)]
        if default_code:
            domain.append(('product_id.default_code', '=', default_code))
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

    def get_pricelists(self, Users=False):
        return Users.mapped('as_pricelist')
    


    def compute_price_fast(self,product_id=False,partner_id=False,promo_ids=False,fuente='Cron',product_records=None,user_records=None,):
        Price = self.env['sd.compute.product.price'].sudo()
        Users = self.env['res.users'].sudo()
        Product = self.env['product.product'].sudo()
        Currency = self.env['res.currency'].sudo()
        CouponProgram = self.env['coupon.program'].sudo()
        resumen = {
            'calculados': 0,
            'creados': 0,
            'actualizados': 0,
            'sin_cambios': 0,
        }

        # 1. OBTENER USUARIOS Y PRODUCTOS
        users_disponibles = (
            user_records
            if user_records is not None
            else self.get_users_ids(partner_id)
        )

        products = (
            product_records
            if product_records is not None
            else self.get_product_ids(product_id)
        )

        if isinstance(users_disponibles, int):
            users_disponibles = Users.browse(
                users_disponibles
            )
        elif isinstance(users_disponibles, (list, tuple, set)):
            users_disponibles = Users.browse(
                list(users_disponibles)
            )

        if isinstance(products, int):
            products = Product.browse(product_id or products)
        elif isinstance(products, (list, tuple, set)):
            products = Product.browse(list(products))

        users_disponibles = users_disponibles.exists()
        products = products.exists()

        if not users_disponibles or not products:
            return resumen

        product_ids = set(products.ids)

        partner_ids = set(
            users_disponibles.mapped('as_partner_id').ids
        )

        # 2. PREPARAR PROMOCIONES

        if promo_ids is False or promo_ids is None:
            promo_ids = CouponProgram.search_promo_disponibles(
                product_ids=product_ids,
                partner_ids=partner_ids,
            )

        # 3. MONEDAS

        usd = Currency.search([
            ('name', '=', 'USD')
        ], limit=1)

        mxn = Currency.search([
            ('name', '=', 'MXN')
        ], limit=1)

        if not usd or not mxn:
            raise UserError(
                "No se encontraron las monedas USD/MXN"
            )

        company = self.env.company
        today = fields.Date.context_today(self)

        # Un registro por cliente + producto.
        # Evitar procesar dos veces al mismo cliente
        # si tiene varios usuarios API.
        clientes_procesados = set()

        # 4. RECORRER USUARIOS

        for user in users_disponibles:

            partner = user.as_partner_id

            if not partner:
                continue

            if partner.id in clientes_procesados:
                continue

            clientes_procesados.add(partner.id)

            inicio_cliente = resumen.copy()

            # IMPORTANTE:
            # La lista vigente se obtiene del contacto.
            # No de la lista almacenada en el precio.
            pricelist = user.as_pricelist

            if not pricelist:
                _logger.warning(
                    "NIMAX: cliente %s sin lista de precios",
                    partner.id,
                )
                continue

            categorias = set(
                partner.tf_vendor_parameter_ids
                .mapped('category_id').ids
            )

            # 5. PROMOCIONES DEL CLIENTE

            promos_cliente = CouponProgram.get_promos_cliente(
                partner=partner,
                product_ids=product_ids,
                promos_disponibles=promo_ids,
            )

            # 6. PRODUCTOS EN LOTES DE 200

            for offset in range(0, len(products), 200):

                batch = products[offset:offset + 200]

                # Productos que requieren fórmula NIMAX.
                con_descuento = batch.filtered(
                    lambda p:
                        p.categ_id.id in categorias
                        and p.id not in promos_cliente
                )

                prices = (
                    con_descuento.compute_nimax_prices_batch(
                        partner,
                        pricelist,
                        []
                    )
                    if con_descuento
                    else {}
                )

                # 7. BUSCAR REGISTROS EXISTENTES
                #
                # CAMBIO PRINCIPAL:
                # NO filtrar por pricelist_id.
                #
                # Así se encuentra el mismo registro
                # aunque cambie la lista del contacto.

                existing = Price.search([
                    ('name', '=', partner.id),
                    ('product_id', 'in', batch.ids),
                ])

                price_map = {}

                for rec in existing:

                    if rec.product_id.id in price_map:
                        raise UserError(
                            "Hay precios duplicados para "
                            f"cliente {partner.id}, "
                            f"producto {rec.product_id.id}. "
                            "Revise los registros antes "
                            "de continuar."
                        )

                    price_map[rec.product_id.id] = rec

                to_create = []
                now = fields.Datetime.now()

                # 8. CALCULAR CADA PRODUCTO

                for product in batch:

                    promo = promos_cliente.get(product.id)

                    promo_aplicada_id = (
                        promo['promo'].id
                        if promo is not None
                        else False
                    )

                    precio_data = prices.get(
                        product.id, {}
                    )

                    amount = (
                        precio_data.get('precio', 0.0)
                        if isinstance(precio_data, dict)
                        else precio_data
                    )

                    # PRIORIDAD 1: PROMOCIÓN
                    if promo is not None:
                        amount = promo['price_unit_usd']
                        moneda_origen = usd

                    # PRIORIDAD 2: DESCUENTO NIMAX
                    elif (
                        product.categ_id.id in categorias
                        and amount
                    ):
                        moneda_origen = pricelist.currency_id

                    # PRIORIDAD 3: PRECIO BASE
                    else:
                        amount = product.lst_price
                        moneda_origen = company.currency_id

                    if (
                        isinstance(amount, bool)
                        or not isinstance(amount, (int, float))
                        or amount < 0
                    ):
                        raise UserError(
                            f"Precio inválido para "
                            f"producto {product.id}: {amount!r}"
                        )

                    # 9. CONVERSIONES

                    price_usd = moneda_origen._convert(
                        amount,
                        usd,
                        company,
                        today,
                    )

                    price_mxn = moneda_origen._convert(
                        amount,
                        mxn,
                        company,
                        today,
                    )

                    resumen['calculados'] += 1

                    # 10. BUSCAR PRECIO POR PRODUCTO

                    existing_price = price_map.get(
                        product.id
                    )

                    if existing_price:

                        cambios = {}

                        # ACTUALIZAR LISTA DE PRECIOS
                        if (
                            existing_price.pricelist_id.id
                            != pricelist.id
                        ):
                            cambios['pricelist_id'] = (
                                pricelist.id
                            )

                        # ACTUALIZAR PRECIO USD
                        if float_compare(
                            existing_price.nimax_price_usd,
                            price_usd,
                            precision_rounding=usd.rounding,
                        ) != 0:
                            cambios['nimax_price_usd'] = (
                                price_usd
                            )

                        # ACTUALIZAR PRECIO MXN
                        if float_compare(
                            existing_price.nimax_price_mxn,
                            price_mxn,
                            precision_rounding=mxn.rounding,
                        ) != 0:
                            cambios['nimax_price_mxn'] = (
                                price_mxn
                            )

                        # ACTUALIZAR PROMOCIÓN
                        if (
                            existing_price.promo_id.id
                            != promo_aplicada_id
                        ):
                            cambios['promo_id'] = (
                                promo_aplicada_id
                            )

                        # ACTUALIZAR MISMO REGISTRO
                        if cambios:

                            cambios.update({
                                'date_update': now,
                                'fuente': fuente,
                            })

                            existing_price.write(cambios)

                            resumen['actualizados'] += 1

                            _logger.info(
                                "NIMAX UPDATE | "
                                "registro=%s cliente=%s "
                                "producto=%s lista=%s "
                                "promo=%s",
                                existing_price.id,
                                partner.id,
                                product.id,
                                pricelist.id,
                                promo_aplicada_id,
                            )

                        else:
                            resumen['sin_cambios'] += 1

                    else:

                        # Crear solo cuando NO existe
                        # ningún registro para ese
                        # cliente + producto.

                        to_create.append({
                            'name': partner.id,
                            'product_id': product.id,
                            'pricelist_id': pricelist.id,
                            'nimax_price_usd': price_usd,
                            'nimax_price_mxn': price_mxn,
                            'promo_id': promo_aplicada_id,
                            'date_update': now,
                            'fuente': fuente,
                        })

                # 11. CREACIÓN MASIVA

                if to_create:
                    Price.create(to_create)
                    resumen['creados'] += len(to_create)

            resumen_cliente = {
                k: resumen[k] - inicio_cliente[k]
                for k in resumen
            }

            _logger.info(
                "NIMAX FAST cliente %s lista %s: %s",
                partner.id,
                pricelist.id,
                resumen_cliente,
            )

        _logger.info(
            "NIMAX FAST TOTAL: %s",
            resumen,
        )

        return resumen
