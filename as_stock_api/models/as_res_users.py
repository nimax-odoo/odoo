# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import logging
import uuid
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AsResUsers(models.Model):
    """
    Extensión del modelo res.users para agregar funcionalidad de API key.
    """
    _inherit = 'res.users'

    as_api_key = fields.Char(
        string='Clave API de Stock',
        copy=False,
        help='Clave para autenticación en la API de Stock'
    )
    
    as_api_enabled = fields.Boolean(
        string='API de Stock Habilitada',
        default=False,
        help='Indica si el usuario tiene acceso a la API de Stock'
    )
    
    as_api_key_display = fields.Char(
        string='Clave API (para copiar)',
        compute='_as_compute_api_key_display',
        help='Campo para mostrar y copiar la clave API'
    )
    
    as_stock_percentaje = fields.Float(
        string='Porcentaje de Stock a Mostrar',
        default=1.0,
        help='Porcentaje del stock real que se mostrará en la API. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.'
    )
    
    as_pricelist = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios API',
        help='Lista de precios que se utilizará por defecto en la API de Stock con precios. Si se deja vacío, se usará la lista de precios del cliente.'
    )
    
    as_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente Predeterminado',
        help='Cliente que se utilizará por defecto en las consultas de la API de Stock con precios. '
             'Si se especifica, no será necesario incluir el parámetro partner_id en las llamadas a la API.'
    )
    
    as_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Almacenes Visibles en API',
        help='Almacenes cuyos productos se mostrarán en la API. Si no se selecciona ninguno, se mostrarán todos los almacenes.'
    )
    
    def _as_compute_api_key_display(self):
        """
        Calcula el valor del campo as_api_key_display.
        """
        for user in self:
            user.as_api_key_display = user.as_api_key

    def as_generate_api_key(self):
        """
        Genera una nueva clave API aleatoria para el usuario.
        
        Returns:
            dict: Acción para mostrar notificación
        """
        self.ensure_one()
        new_key = str(uuid.uuid4())
        self.as_api_key = new_key
        self.as_api_enabled = True
        _logger.info("[as_generate_api_key] Generada nueva clave API de Stock para el usuario %s", self.name)
        
        # Mostrar un mensaje con la clave generada
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Clave API generada'),
                'message': _('Se ha generado una nueva clave API: %s. Puede copiarla desde el campo "Clave API (para copiar)".') % new_key,
                'sticky': True,
                'type': 'success',
            }
        }
        
    def as_clear_api_key(self):
        """
        Elimina la clave API del usuario y deshabilita el acceso a la API.
        
        Returns:
            dict: Acción para mostrar notificación
        """
        self.ensure_one()
        self.as_api_key = False
        self.as_api_enabled = False
        _logger.info("[as_clear_api_key] Eliminada clave API de Stock para el usuario %s", self.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Clave API eliminada'),
                'message': _('Se ha eliminado la clave API y deshabilitado el acceso a la API de Stock.'),
                'sticky': False,
                'type': 'success',
            }
        }
        
    def as_copy_api_key(self):
        """
        Copia la clave API al portapapeles.
        
        Returns:
            dict: Acción para mostrar notificación
        """
        self.ensure_one()
        if not self.as_api_key:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No hay clave API para copiar. Genere una primero.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Clave API copiada'),
                'message': _('La clave API ha sido copiada al portapapeles.'),
                'sticky': False,
                'type': 'success',
            }
        } 