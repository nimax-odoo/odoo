# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class as_product_template(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_services')
    
    as_proveedor = fields.Many2one(comodel_name='res.partner', string='Cliente - Proveedor')
    tf_import_tax = fields.Float('IMPORT TAX')
    as_product_comisionable = fields.Boolean('Producto no Comisionable')
    as_zebra = fields.Boolean('Es Zebra')
    default_code = fields.Char('SKU ó No. de Parte', index=True,tracking=True)
    standard_price = fields.Float(
        'Costo', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        help="""Value of the product (automatically computed in AVCO).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""",tracking=True)
    categ_id = fields.Many2one(
        'product.category', 'Categoría',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True,tracking=True)
