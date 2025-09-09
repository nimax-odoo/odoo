import logging
from markupsafe import Markup

from odoo.tools.zeep import Client
from odoo import _, models
from lxml import etree
_logger = logging.getLogger(__name__)


class L10nClEdiUtilMixin(models.AbstractModel):
    _inherit = 'l10n_cl.edi.util'
    
    def _get_token(self, mode, digital_signature):
        cesion = False
        if self._name == 'account.move' and self.move_type == 'entry':
            cesion = True
        if digital_signature.last_token and not cesion:
            return digital_signature.last_token
        seed = self._get_seed(mode)
        if not seed:
            return self._connection_exception('exception', _('No possible to get a seed'))
        signed_token = self._get_signed_token(digital_signature, seed)
        response = self._get_token_ws(mode, etree.tostring(
            etree.fromstring(signed_token), pretty_print=True, encoding='ISO-8859-1').decode())
        try:
            response_parsed = etree.fromstring(response.encode('utf-8'))
        except (ValueError, AttributeError) as error:
            return self._connection_exception('exception', error)
        status = response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ESTADO')
        if status is None or status in ['-07', '12', '11']:
            error = (_('No response trying to get a token') if status is None else
                     response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/GLOSA'))
            return self._connection_exception(status, error)
        digital_signature.last_token = response_parsed[0][0].text
        return response_parsed[0][0].text