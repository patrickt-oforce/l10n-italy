# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from odoo.tools.sql import column_exists

@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if openupgrade.column_exists(env.cr, 'account_invoice', 'ftpa_withholding_amount'):
        openupgrade.copy_columns(cr, {
            'account_invoice': [
                ('ftpa_withholding_amount', None, None),
            ],
        })
    if column_exists(cr, 'account_invoice', 'ftpa_withholding_type'):
        openupgrade.copy_columns(cr, {
            'account_invoice': [
                ('ftpa_withholding_type', None, None),
            ],
        })
