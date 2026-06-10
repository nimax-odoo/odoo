from odoo import http
from odoo.http import request

class QuinielaPortal(http.Controller):

    @http.route('/quiniela', auth='public', website=True)
    def quiniela(self, **kw):
        winners = request.env['sd.register.winner'].sudo().search(
            [],
            order='sequence asc'
        )
        winners_json = {}
        for winner in winners:
            winners_json[winner] = winner.proposticos_winner_ids
            
        return request.render(
            'sd_quiniela_model.quiniela',
            {
                'winners': winners_json,
            }
        )