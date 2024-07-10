
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cron = env.ref(
        "website_sale_cart_expire.ir_cron_cart_expire",
        raise_if_not_found=False,
    )
    if cron:
        cron.code = "model._scheduler_website_expire_cart(autocommit=True)"
