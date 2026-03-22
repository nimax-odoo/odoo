# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    margin2 = fields.Float('Margen 2', digits='Product Price', default=0)
    as_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios',readonly=True,store=True)
    as_log_price = fields.Boolean('Log de price Unit',default=True)
    RECALCULATED_PRICE_UNIT = fields.Float('RECALCULATED PRICE UNIT')
    NIMAX_PRICE_MXP = fields.Float('NIMAX PRICE MXP')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')
    COST_NIMAX_MXP = fields.Float('COST NIMAX MXP')
    MARGIN_MXP = fields.Float('MARGIN MXP')
    MARGIN_USD = fields.Float('MARGIN USD')
    TOTAL_USD = fields.Float('TOTAL USD')
    TOTAL_MXP = fields.Float('TOTAL MXP')
    as_margin_porcentaje = fields.Float('Margen Porcentaje',compute='get_margin_porcentaje',store=True)
    as_product_comisionable = fields.Boolean(related="product_id.as_product_comisionable")
    coupon_ids = fields.Many2many('coupon.program', string='Programas de Cupones', copy=False)
    RECALCULATED_COST_NIMAX_USD = fields.Float('RECALCULATED COST NIMAX USD')
    is_copy = fields.Boolean(string="Es copia")
    
    @api.depends('COST_NIMAX_USD','RECALCULATED_PRICE_UNIT')
    def get_margin_porcentaje(self):
        for record in self:
            if record.COST_NIMAX_USD and record.RECALCULATED_PRICE_UNIT:
                record.as_margin_porcentaje = ((record.RECALCULATED_PRICE_UNIT - record.COST_NIMAX_USD)/record.RECALCULATED_PRICE_UNIT)*100

    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'price_unit', 'product_uom','tax_id', 'analytic_distribution'
        ]
        
    # apply pricelist
    def pricelist_apply(self):
        pricelists = self.env['product.pricelist'].sudo().search([('currency_id','=',self.order_id.currency_id.id)])
        pricelist = []
        for price in pricelists:
            pricelist.append(price.id)
        return {
                'name': _('Aplicar Lista de Precios'),
                'view_mode': 'form',
                'res_model': 'sale.order.pricelist.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'active_id': self.order_id.id, 'active_model': 'sale.order','order_line_id': self.id, 'pricelist_ids': pricelist},
            }
        
    # apply promo
    def promo_apply(self):
        return {
                'name': _('Aplicar Promoción'),
                'view_mode': 'form',
                'res_model': 'as.sale.order.promo.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'promo_apply_dis_per': 'promo_apply_dis_per'},
            }

    @api.depends('product_id')
    def get_option_zebra(self):    
        for sale_line in self:
            if sale_line.product_id.as_zebra:
                sale_line.order_id.as_zebra_sale = True
    
    @api.onchange('price_unit','product_uom_qty')
    def get_margin_utilidad(self):
        moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
        moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
        for sale_line in self:
            if sale_line.product_id.as_zebra:
                sale_line.order_id.as_zebra_sale = True
            if not sale_line.as_product_comisionable:
                if moneda_mxn == sale_line.currency_id:
                    new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_MXP*sale_line.product_uom_qty)
                    sale_line.MARGIN_MXP=new_amrgin
                    sale_line.MARGIN_USD=moneda_mxn._convert_nimax(new_amrgin,moneda_usd, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.get_margin_porcentaje()
                    sale_line.TOTAL_MXP = sale_line.price_unit * sale_line.product_uom_qty
                    sale_line.TOTAL_USD = moneda_mxn._convert_nimax(sale_line.TOTAL_MXP,moneda_usd, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.RECALCULATED_PRICE_UNIT = moneda_mxn._convert_nimax(sale_line.price_unit, moneda_usd,self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.NIMAX_PRICE_MXP = sale_line.price_unit
                else:
                    new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_USD*sale_line.product_uom_qty)
                    sale_line.MARGIN_USD=new_amrgin
                    sale_line.MARGIN_MXP=moneda_usd._convert_nimax(new_amrgin,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.get_margin_porcentaje()
                    sale_line.TOTAL_USD = sale_line.price_unit * sale_line.product_uom_qty
                    sale_line.TOTAL_MXP = moneda_usd._convert_nimax(sale_line.TOTAL_USD,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.RECALCULATED_PRICE_UNIT = sale_line.price_unit
                    sale_line.NIMAX_PRICE_MXP = moneda_usd._convert_nimax(sale_line.price_unit,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                tf_partner_id = self.env['tf.res.partner']
                for x in sale_line.order_id.partner_id.tf_vendor_parameter_ids:
                    if x.category_id.id == sale_line.product_id.categ_id.id:
                        tf_partner_id = x
            if sale_line.as_pricelist_id and sale_line.as_log_price:
                sale_id = self.env['sale.order'].search([('name','=',sale_line.order_id.name)])
                sale_line_id = self.env['sale.order.line'].search([('name','=',sale_line.name)])
                promo = self.env['tf.history.promo'].create(dict(
                    # promotion_id=,
                    vendor_id=tf_partner_id.partner_id.id,
                    product_id=sale_line.product_id.id,
                    customer_id=sale_line.order_id.partner_id.id,
                    customer_type=tf_partner_id.partner_type.id,
                    as_pricelist_id = sale_line.as_pricelist_id.id,
                    category_id=sale_line.product_id.categ_id.id,
                    qty=sale_line.product_uom_qty,
                    recalculated_price_unit=sale_line.RECALCULATED_PRICE_UNIT,
                    recalculated_price_unit_mxp=sale_line.NIMAX_PRICE_MXP,
                    recalculated_cost_nimax_usd=sale_line.COST_NIMAX_USD,
                    recalculated_cost_nimax_mxp=sale_line.COST_NIMAX_MXP,
                    margin_mxp=sale_line.MARGIN_MXP,
                    margin_usd=sale_line.MARGIN_USD,
                    total_usd=sale_line.TOTAL_USD,
                    total_mxp=sale_line.TOTAL_MXP,
                    sale_order_line=sale_line.id,
                    salesman_id=sale_line.order_id.user_id.id,
                    sale_id=sale_id.id,
                ))
            sale_line.as_log_price=True
            if sale_line.as_product_comisionable:
                if moneda_mxn == sale_line.currency_id:
                    sale_line.RECALCULATED_PRICE_UNIT = moneda_mxn._convert_nimax(sale_line.price_unit, moneda_usd,self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.NIMAX_PRICE_MXP = sale_line.price_unit
                else:
                    sale_line.RECALCULATED_PRICE_UNIT = sale_line.price_unit
                    sale_line.NIMAX_PRICE_MXP = moneda_usd._convert_nimax(sale_line.price_unit,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
              
    def get_margin_utilidad_general(self):
        moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
        moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
        for sale_line in self:
            if sale_line.product_id.as_zebra:
                sale_line.order_id.as_zebra_sale=True
            if not sale_line.as_product_comisionable:
                if moneda_mxn == sale_line.currency_id:
                    new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_MXP*sale_line.product_uom_qty)
                    sale_line.MARGIN_MXP=new_amrgin
                    sale_line.MARGIN_USD=moneda_mxn._convert_nimax(new_amrgin,moneda_usd, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.get_margin_porcentaje()
                    sale_line.TOTAL_MXP = sale_line.price_unit * sale_line.product_uom_qty
                    sale_line.TOTAL_USD = moneda_mxn._convert_nimax(sale_line.TOTAL_MXP,moneda_usd, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.RECALCULATED_PRICE_UNIT = moneda_mxn._convert_nimax(sale_line.price_unit, moneda_usd,self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.NIMAX_PRICE_MXP = sale_line.price_unit
                else:
                    new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_USD*sale_line.product_uom_qty)
                    sale_line.MARGIN_USD=new_amrgin
                    sale_line.MARGIN_MXP=moneda_usd._convert_nimax(new_amrgin,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.get_margin_porcentaje()
                    sale_line.TOTAL_USD = sale_line.price_unit * sale_line.product_uom_qty
                    sale_line.TOTAL_MXP = moneda_usd._convert_nimax(sale_line.TOTAL_USD,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.RECALCULATED_PRICE_UNIT = sale_line.price_unit
                    sale_line.NIMAX_PRICE_MXP = moneda_usd._convert_nimax(sale_line.price_unit,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
                tf_partner_id = self.env['tf.res.partner']
                for x in sale_line.order_id.partner_id.tf_vendor_parameter_ids:
                    if x.category_id.id == sale_line.product_id.categ_id.id:
                        tf_partner_id = x
            if sale_line.as_product_comisionable:
                if moneda_mxn == sale_line.currency_id:
                    sale_line.RECALCULATED_PRICE_UNIT = moneda_mxn._convert_nimax(sale_line.price_unit, moneda_usd,self.env.company, fields.Date.today(),sale_line.id)
                    sale_line.NIMAX_PRICE_MXP = sale_line.price_unit
                else:
                    sale_line.RECALCULATED_PRICE_UNIT = sale_line.price_unit
                    sale_line.NIMAX_PRICE_MXP = moneda_usd._convert_nimax(sale_line.price_unit,moneda_mxn, self.env.company, fields.Date.today(),sale_line.id)
            

class SaleOrder(models.Model):
    _inherit = "sale.order"

            
    as_margin = fields.Float(string='Margen(en %)', store=True, readonly=True, compute='_amount_all_marigin', tracking=4)
    as_aprobe = fields.Boolean(string='Aprobar Venta',default=False)
    as_zebra_sale = fields.Boolean(string="Es Zebra")
    as_usuario_final = fields.Char(string="Usuario Final")
    invoice_ids = fields.Many2many("account.move", string='Invoices', compute="_get_invoiced", readonly=True, copy=False,store=True)
    sd_block_user = fields.Selection([], related = "partner_id.sd_block_user", string = "Estado del Usuario", readonly=True )
    sale_warn_msg = fields.Text('Mensaje para orden de venta', tracking = True)
    is_copy = fields.Boolean(string="Es copia",default=False)
    sale_copy_id = fields.Many2one('sale.order', string='Venda copiada')

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        res = super(SaleOrder, self).create(vals_list)
        for vals in vals_list:
            if 'is_copy' in vals and vals['is_copy']:
                sales_copy = res.sale_copy_id
                refs = [sales_copy._get_html_link() for sale in sales_copy]
                message = _("Esta venta se copio a partir de: ") + Markup(',').join(refs)
                res.message_post(body=message)
        return res

    
    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for sale, vals in zip(self, vals_list):
            vals['is_copy'] = True
            vals['sale_copy_id'] = sale.id
        return vals_list

    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        partner = self.partner_id

        if partner.sd_block_user == 'True':

            for rec in self:
                rec.write({'partner_id': ''})

            return {
                'warning': {
                    'title': _("Contacto bloqueado"),
                    'message': _("No se puede crear una cotización de un contacto bloqueado. Por favor, seleccione otro contacto."),
                }
            }
            
    def action_update_quantity(self):
        return {
                'name': _('Ajustar Cantidades'),
                'view_mode': 'form',
                'res_model': 'sd.sale.order.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'active_id': self.id, 'active_model': 'sale.order'},
            }
        
    @api.depends('order_line.price_unit','order_line.COST_NIMAX_USD')
    def _amount_all_marigin(self):
        total_price = 0.0
        total_cost = 0.0
        total_margin = 0.0
        for order in self:
            for line in order.order_line:
                if not line.as_product_comisionable:
                    moneda_mxn = self.env.ref('base.MXN', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','MXN')], limit=1)
                    moneda_usd = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
                    if moneda_usd != line.currency_id:
                        price = moneda_mxn._convert_nimax(line.price_unit,moneda_usd, self.env.company, fields.Date.today(),line.id)
                    else:
                        price = line.price_unit
                    total_price += price * line.product_uom_qty
                    total_cost += line.COST_NIMAX_USD * line.product_uom_qty
                    line.get_margin_utilidad_general()
            if total_price > 0:
                total_margin += (total_price-total_cost)/total_price
            order.update({
                'as_margin': total_margin*100,
            })
    
    @api.onchange('partner_id','pricelist_id')
    def _default_currecy_aux(self):
        if self.pricelist_id:
            self.currency_aux_id = self.currency_id  
        else:
            usd_currency = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name','=','USD')], limit=1)
            self.currency_aux_id = usd_currency.id if usd_currency else False

    @api.onchange('currency_aux_id')
    def _default_currecy(self):
        if self.partner_id:
            tarifa = self.env['product.pricelist'].search([('as_tarifa_base','=',True),('currency_id','=',self.currency_aux_id.id)],limit=1)
            if tarifa:
                self.pricelist_id = tarifa
            else:
                raise ValidationError('Debe crear tarifa base para calculo de moneda')

    last_promo_id = fields.Many2one('coupon.program', 'Last Sale Promo', ondelete='set null')
    currency_aux_id = fields.Many2one("res.currency", string="Moneda", 
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False).id if self.env.ref('base.USD', raise_if_not_found=False) else self.env['res.currency'].search([('name','=','USD')], limit=1).id,
        required=True)
    
    def get_promocion(self,line_id):
        line = self.env['sale.order.line'].search([('id','=',line_id)])
        ultima_promo = self.env['tf.history.promo'].search([('sale_id','=',self.id),('product_id','=',line.product_id.id),('last_applied_promo','=',True)])
        name= ''
        if ultima_promo:
            name = str(ultima_promo.promo_id.id)+' : '+str(ultima_promo.promo_id.name)
        else:
            name =' '
        return name
        
    def action_confirm(self):
        margin_minimo = self.env['ir.config_parameter'].sudo().get_param('as_sale_pricelist.as_margin_minimo')
        margin_global = self.env['ir.config_parameter'].sudo().get_param('as_sale_pricelist.as_margin_global')
        if self.as_aprobe == False:
            access = False
            no_access = False
            for line in self.order_line:
                if not line.as_product_comisionable:
                    if (line.as_margin_porcentaje  > 0) and (line.as_margin_porcentaje  < float(margin_minimo)):
                        access= True
                    elif (float(line.as_margin_porcentaje) < float(margin_global)):
                        no_access = True
            if access:
                action = self.env.ref('as_sale_pricelist.action_aprobe_sales_qweb').read()[0]
                action.update({
                    'context': {
                        'default_as_sale': self.id,
                    
                    },
                })
                return action  
            elif no_access:
                raise ValidationError('No se puede confirmar la venta, modifique sus precios')
        product=[]
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            for line in rec.order_line:
                for promo in line.coupon_ids:
                    promo.tf_gifted_qty += line.product_uom_qty
                    if promo.tf_gifted_qty > promo.tf_max_gifted_qty:
                        raise ValidationError('No se permiten muchas promociones!\n Para la promoción: %s' % promo.name)
                query_ids = ("""
                SELECT id FROM tf_history_promo tf 
                where
                tf.sale_id = """+str(rec.id)+""" and tf.product_id = """+str(line.product_id.id)+""" and sale_order_line= """+str(line.id)+""" 
                order by tf.create_date desc limit 1
                """)
                self.env.cr.execute(query_ids)
                history_table = [j for j in self.env.cr.fetchall()]
                tf_history_id = self.env['tf.history.promo'].search([('id', 'in', history_table)])
                if tf_history_id:
                    tf_history_id.last_applied_promo = True
            if rec.sd_block_user == 'True':
                raise ValidationError('No se puede confirmar la venta del cliente bloqueado : %s' % str(rec.partner_id.name))
        if product != []:
            raise ValidationError('EXISTEN LINEAS PRODUCTO SIN PRECIO BASE : %s' % str(product))
        if self.is_copy and self.sale_copy_id:
            for line in self.order_line:
                if not line.is_copy:
                    raise ValidationError('No ha actualizar precio al producto : %s' % str(line.name))   

        return res

    # def action_cancel(self):

    #     cancel_warning = self._show_cancel_wizard()
    #     if cancel_warning:
    #         self.ensure_one()
    #         template_id = self.env['ir.model.data']._xmlid_to_res_id(
    #             'sale.mail_template_sale_cancellation', raise_if_not_found=False
    #         )
    #         lang = self.env.context.get('lang')
    #         template = self.env['mail.template'].browse(template_id)
    #         if template.lang:
    #             lang = template._render_lang(self.ids)[self.id]
    #         ctx = {
    #             'default_template_id': template_id,
    #             'default_order_id': self.id,
    #             'mark_so_as_canceled': True,
    #             'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
    #             'model_description': self.with_context(lang=lang).type_name,
    #         }
    #         return {
    #             'name': _('Cancel %s', self.type_name),
    #             'view_mode': 'form',
    #             'res_model': 'sale.order.cancel',
    #             'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
    #             'type': 'ir.actions.act_window',
    #             'context': ctx,
    #             'target': 'new'
    #         }
    #     else:
    #         return self._action_cancel()

    def _action_cancel(self):
        res = super(SaleOrder, self)._action_cancel()

        for rec in self:
            for line in rec.order_line:
                for promo in line.coupon_ids:
                    promo.tf_gifted_qty -= line.product_uom_qty
        return res

