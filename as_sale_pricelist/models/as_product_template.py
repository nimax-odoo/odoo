# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

import logging
_logger = logging.getLogger(__name__)

class as_product_template(models.Model):
    _inherit = 'product.template'
   
    as_proveedor = fields.Many2one(comodel_name='res.partner', string='Cliente - Proveedor')
    tf_import_tax = fields.Float('IMPORT TAX')
    as_product_comisionable = fields.Boolean('Producto no Comisionable')
    as_zebra = fields.Boolean('Es Zebra')

    def write(self, vals):
        """
        Sobrescribe el método write para registrar en el log y en el chatter la data en formato JSON al actualizar un producto.
        """
        # Convertir los valores a formato JSON legible
        json_data = json.dumps(vals, ensure_ascii=False, indent=4)
        
        # Registrar los datos de actualización en el log
        _logger.info(f"Actualizando producto.template con ID {self.ids} con los siguientes datos: {json_data}")
        
        # Llamar al método original para aplicar los cambios
        result = super(as_product_template, self).write(vals)
        
        # Publicar el JSON en el chatter del producto actualizado
        for record in self:
            record.message_post(body=f"Registro actualizado con los siguientes datos: <pre>{json_data}</pre>")
        
        return result

    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para registrar en el log y en el chatter la data en formato JSON al crear un producto.
        """
        # Convertir los valores a formato JSON legible
        json_data = json.dumps(vals, ensure_ascii=False, indent=4)
        
        # Registrar los datos de creación en el log
        _logger.info(f"Creando producto.template con los siguientes datos: {json_data}")
        
        # Crear el registro usando el método original
        product = super(as_product_template, self).create(vals)
        
        # Publicar el JSON en el chatter del producto creado
        product.message_post(body=f"Registro creado con los siguientes datos: <pre>{json_data}</pre>")
        
        return product