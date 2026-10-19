from odoo import _
from odoo.exceptions import UserError

PARAM_ENFORCE = 'nx_fabrica_logistica.enforce_groups'


def nx_check_group(env, group_name, mensaje):
    """Valida el grupo SOLO si el parámetro del sistema está activo ('1').
    Por defecto está apagado: los permisos se activan al final de las pruebas."""
    if env.su:
        return
    valor = env['ir.config_parameter'].sudo().get_param(PARAM_ENFORCE, '0')
    if valor not in ('1', 'True', 'true'):
        return
    if env.user.has_group('base.group_system'):
        return
    if not env.user.has_group('nx_fabrica_logistica.%s' % group_name):
        raise UserError(mensaje)
