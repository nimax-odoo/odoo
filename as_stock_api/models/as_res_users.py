# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from datetime import date, timedelta
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
        help='Porcentaje del stock real que se mostrará en la API. Si es 0.8, se mostrará el 80% del stock real. Si está vacío o es 1, se mostrará el 100%.',
        related='partner_id.as_stock_percentaje',
        readonly=False,
        store=False,
    )
    
    as_pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        string='Lista de precios',
        related='partner_id.property_product_pricelist',
        readonly=False,
        store=False,
    )
    
    as_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente Predeterminado",
        help='Cliente que se utilizará por defecto en las consultas de la API de Stock con precios. '
             'Si se especifica, no será necesario incluir el parámetro partner_id en las llamadas a la API.',
        related='partner_id.as_partner_id',
        readonly=False,
        store=False,
    )
    
    as_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Almacenes Visibles en API',
        help='Almacenes cuyos productos se mostrarán en la API. Si no se selecciona ninguno, se mostrarán todos los almacenes.'
    )
    #Campos de API gestión de ventas cyberpuerta
    
    sd_cy_token = fields.Char(
        string='Token para Sincronizar',
        copy=False,
        help='Token proporcionado (solictado por Cyberpuerta) para sincronizar'
    )
    sd_cy_webhook_active = fields.Boolean(
        string='Activar envio de catálogo a Cliente',
        copy=False,
        help='Activar envio de catálogo a Cliente'
    )
    sd_cy_url = fields.Char(
        string='URL del sistema del cliente',
        copy=False,
        help='URL del sistema del cliente para enviar el catálogo'
    )
    sd_sync_lock_until = fields.Datetime(
        string='Fecha de Bloqueo de Sincronización',
        copy=False,
        help='Fecha hasta la cual se bloqueará la sincronización'
    )
    sd_sync_lock_until_cant = fields.Integer(
        string='Cantidad de Tiempo de Bloqueo',
        copy=False,
        help='Cantidad de tiempo para el bloqueo de sincronización'
    )
    sd_sync_lock_until_type  = fields.Selection(
        [('Minutos', 'Minutos'), ('Horas', 'Horas')],
        string='Tipo de Bloqueo de Sincronización',
        default='Horas',
    )
    
    _sql_constraints = [
        ('unique_token', 'unique(sd_cy_token)', 'El token debe ser único')
    ]

    def compute_price_api(self):
        for user in self:
            partner = user.partner_id
            self.env['sd.compute.product.price'].sudo().syn_partner_prices(partner.id, 'Usuario')
            
    def set_sync_lock(self):
        """
        Establece la fecha de bloqueo de sincronización para el usuario.
        Args:
            date (datetime): Fecha hasta la cual se bloqueará la sincronización.
        """
        self.ensure_one()
        
        self.sd_sync_lock_until = fields.Datetime.now()
        _logger.info("[set_sync_lock] Usuario %s bloqueado hasta %s",self.name,self.sd_sync_lock_until)
        
    def is_sync_locked(self):
        """
        Obtiene la fecha de desbloqueo de sincronización para el usuario.
        
        Returns:
            datetime: Fecha de desbloqueo de sincronización.
        """
        self.ensure_one()
        lock = False
        if self.sd_sync_lock_until_cant and self.sd_sync_lock_until_type and self.sd_sync_lock_until:
            if self.sd_sync_lock_until_type == 'Minutos':
                delta = timedelta(minutes=self.sd_sync_lock_until_cant)
            else:
                delta = timedelta(hours=self.sd_sync_lock_until_cant)
            date_until = self.sd_sync_lock_until + delta
            if fields.Datetime.now() < date_until:
                lock = True
        return lock

    def get_remaining_time(self):
        """
        Retorna el tiempo restante del bloqueo.
        """
        self.ensure_one()

        if not self.sd_sync_lock_until:
            return {
                'locked': False,
                'seconds': 0,
                'message': ''
            }

        if self.sd_sync_lock_until_type == 'Minutos':
            unlock_date = self.sd_sync_lock_until + timedelta(
                minutes=self.sd_sync_lock_until_cant
            )
        else:
            unlock_date = self.sd_sync_lock_until + timedelta(
                hours=self.sd_sync_lock_until_cant
            )

        remaining = unlock_date - fields.Datetime.now()

        if remaining.total_seconds() <= 0:
            return {
                'locked': False,
                'seconds': 0,
                'message': ''
            }

        total_seconds = int(remaining.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        parts = []
        parts.append("Debe esperar")
        if hours:
            parts.append(f"{hours} hora{'s' if hours != 1 else ''}")

        if minutes:
            parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")

        if seconds or not parts:
            parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")

        return {
            'locked': True,
            'seconds': total_seconds,
            'message': ", ".join(parts)
        }
    
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

class AsResPartner(models.Model):
    """
    Extensión del modelo res.partner para agregar funcionalidad de API key.
    """
    _inherit = 'res.partner'

    is_access_api = fields.Selection(
        [('on', 'Habilitado'), ('off', 'Deshabilitado'), ('parent', 'Principal')],
        string='Acceso API',
        default='off',compute="_compute_action_api"
    )
    is_access_ecommerce = fields.Selection(
        [('on', 'Habilitado'), ('off', 'Deshabilitado'), ('parent', 'Principal')],
        string='Acceso ecommerce',
        default='off', compute="_compute_action_api"
    )
    # as_stock_percentaje = fields.Float(
    #     string='Porcentaje de Stock',
    #     help='Porcentaje de stock que se utilizará por defecto en la API de Stock. Si se deja vacío, se usará el porcentaje del cliente.'
    # )
    # as_partner_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string="Cliente Predeterminado",
    #     help='Cliente que se utilizará por defecto en las consultas de la API de Stock con precios. '
    #          'Si se especifica, no será necesario incluir el parámetro partner_id en las llamadas a la API.',
    # )
    user_api_ecommerce_ids = fields.One2many(
        comodel_name='res.users',
        inverse_name='as_partner_id',
        string='Usuarios',
    )


    def _as_get_root_partner(self):
        self.ensure_one()

        partner = self

        while partner.parent_id:
            partner = partner.parent_id

        return partner


    @api.depends('parent_id', 'as_partner_id')
    def _compute_user_api_ecommerce_ids(self):

        Users = self.env['res.users']

        for partner in self:

            parent = partner._as_get_root_partner()

            partner.user_api_ecommerce_ids = Users.search([
                ('partner_id.as_partner_id', '=', parent.id),
            ])


    def _inverse_user_api_ecommerce_ids(self):

        Users = self.env['res.users']

        for partner in self:

            parent = partner._as_get_root_partner()

            current_users = Users.search([
                ('partner_id.as_partner_id', '=', parent.id),
            ])

            selected_users = partner.user_api_ecommerce_ids

            users_to_add = selected_users - current_users
            users_to_remove = current_users - selected_users

            if users_to_add:
                users_to_add.write({
                    'as_partner_id': parent.id,
                })

            if users_to_remove:
                users_to_remove.write({
                    'as_partner_id': False,
                })

            family = parent._as_get_partner_family()

            family.invalidate_recordset([
                'user_api_ecommerce_ids',
            ])

            
    def _compute_action_api(self):
        for partner in self:
            user = self.env['res.users'].sudo().search([('partner_id','=',partner.id)])
            partner.is_access_api= 'off'
            partner.is_access_ecommerce = 'off'
            if user:
                partner.is_access_ecommerce = 'on'
                if user.as_api_enabled:
                    partner.is_access_api= 'on'
            user = self.env['res.users'].sudo().search([('as_partner_id','=',partner.id)])
            if user:
                partner.is_access_ecommerce = 'parent'
                partner.is_access_api = 'parent'

    def compute_price_api(self):
        for partner in self:
            porcentaje = partner.as_stock_percentaje
            pricelist = partner.property_product_pricelist
            if partner.parent_id:
                partner.parent_id.as_stock_percentaje = porcentaje
                partner.parent_id.property_product_pricelist = pricelist
            for child in partner.child_ids:
                child.as_stock_percentaje = porcentaje
                child.property_product_pricelist = pricelist
            for partner_user in partner.user_api_ecommerce_ids:
                partner_user.as_stock_percentaje = porcentaje
                partner_user.property_product_pricelist = pricelist  
            if len(partner.user_api_ecommerce_ids) > 0:
                partner = partner.user_api_ecommerce_ids[0].partner_id
            self.env['sd.compute.product.price'].sudo().syn_partner_prices(partner.id, 'Contacto')

    # Campos que deben mantenerse sincronizados.
    _AS_SYNC_FIELDS = (
        'as_stock_percentaje',
        'property_product_pricelist',
    )


    def _as_get_api_main_partner(self):
        """
        Obtiene el cliente principal de la API.

        Si el contacto tiene un cliente predeterminado,
        utiliza ese cliente. De lo contrario, utiliza
        el propio contacto.
        """
        self.ensure_one()

        return self.as_partner_id or self


    def _as_get_api_sync_partners(self):
        """
        Obtiene el cliente principal y los contactos
        asociados a sus usuarios API/ecommerce.
        """
        self.ensure_one()

        main_partner = self._as_get_api_main_partner()

        users = self.env['res.users'].with_context(
            active_test=False
        ).search([
            ('partner_id.as_partner_id', '=', main_partner.id),
        ])

        return main_partner | users.mapped('partner_id') | self


    def _as_get_api_sync_values(self):
        """
        Obtiene los valores actuales de configuración API.
        """
        self.ensure_one()

        return {
            'as_stock_percentaje': self.as_stock_percentaje,
            'property_product_pricelist': (
                self.property_product_pricelist.id or False
            ),
        }


    def _as_sync_api_partners(self, sync_vals):
        """
        Sincroniza los campos entre el cliente principal
        y todos los contactos de sus usuarios API.
        """
        if not sync_vals:
            return

        processed_ids = set()

        for partner in self:

            main_partner = partner._as_get_api_main_partner()

            if main_partner.id in processed_ids:
                continue

            processed_ids.add(main_partner.id)

            partners = partner._as_get_api_sync_partners()

            partners_to_update = self.env['res.partner']

            for member in partners:

                for field_name, new_value in sync_vals.items():

                    current_value = member[field_name]

                    if member._fields[field_name].type == 'many2one':
                        current_value = current_value.id or False
                        new_value = new_value or False

                    if current_value != new_value:
                        partners_to_update |= member
                        break

            if partners_to_update:

                partners_to_update.with_context(
                    as_skip_partner_sync=True
                ).write(sync_vals)


    @api.model_create_multi
    def create(self, vals_list):

        partners = super().create(vals_list)

        if self.env.context.get('as_skip_partner_sync'):
            return partners

        # Los nuevos contactos heredan la configuración
        # de su cliente predeterminado.
        for partner in partners:

            if partner.as_partner_id:

                sync_vals = (
                    partner.as_partner_id._as_get_api_sync_values()
                )

                partner.with_context(
                    as_skip_partner_sync=True
                ).write(sync_vals)

        return partners


    def write(self, vals):

        res = super().write(vals)

        # Evitar recursividad infinita.
        if self.env.context.get('as_skip_partner_sync'):
            return res

        # Si cambia el cliente predeterminado,
        # heredar su configuración.
        if 'as_partner_id' in vals:

            for partner in self:

                if partner.as_partner_id:

                    sync_vals = (
                        partner.as_partner_id._as_get_api_sync_values()
                    )

                    partner.with_context(
                        as_skip_partner_sync=True
                    ).write(sync_vals)

            if vals.get('as_partner_id'):
                return res

        # Obtener únicamente los campos modificados.
        sync_vals = {
            field_name: vals[field_name]
            for field_name in self._AS_SYNC_FIELDS
            if field_name in vals
        }

        # Sincronizar cliente principal y usuarios asociados.
        if sync_vals:
            self._as_sync_api_partners(sync_vals)

        return res