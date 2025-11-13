# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time
from odoo.tools.safe_eval import safe_eval
from datetime import date, datetime, time
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, is_html_empty
from odoo.tools.translate import html_translate
from odoo.http import request
from odoo.tools import format_amount
#from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('parent_id')
    def depends_parent_id(self):
        for partner in self:
            if partner.parent_id:
                vandors_categ = []
                if partner.parent_id.tf_vendor_parameter_ids:
                    for vendor in partner.parent_id.tf_vendor_parameter_ids:
                        vandors_categ.append(vendor.id)
                partner.sd_desc_percentaje = partner.parent_id.sd_desc_percentaje
                partner.sd_pricelist = partner.parent_id.sd_pricelist
                partner.sd_pricelist_ids = partner.parent_id.sd_pricelist_ids
                partner.tf_vendor_parameter_ids = [(6, 0, vandors_categ)]

    def action_assigned_vendor(self):
        for partner in self:
            if partner.parent_id:
                vandors_categ = []
                for vendor in partner.parent_id.tf_vendor_parameter_ids:
                    vandors_categ.append(vendor.id)
                partner.tf_vendor_parameter_ids = [(6, 0, vandors_categ)]
            if not partner.parent_id:
                vandors_categ = []
                for vendor in partner.tf_vendor_parameter_ids:
                    vandors_categ.append(vendor.id)
                for chield in partner.child_ids:
                    chield.tf_vendor_parameter_ids = [(6, 0, vandors_categ)]

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.action_assigned_vendor()
        return res

    def write(self, vals):
        res = super().write(vals)
        for pay in self:
            pay._modify_vendor_parameter()
        return res

    @api.depends('parent_id', 'tf_vendor_parameter_ids','sd_desc_percentaje','sd_pricelist')
    def _modify_vendor_parameter(self):
        for partner in self:
            vandors_categ = []
            if partner.child_ids and partner.tf_vendor_parameter_ids:
                for vendor in partner.tf_vendor_parameter_ids:
                    vandors_categ.append(vendor.id)
                for chield in partner.child_ids:
                    chield.sd_desc_percentaje = partner.sd_desc_percentaje
                    chield.sd_pricelist = partner.sd_pricelist
                    chield.sd_pricelist_ids = partner.sd_pricelist_ids
                    chield.tf_vendor_parameter_ids = [(6, 0, vandors_categ)]