# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models
from odoo.tools.float_utils import float_is_zero


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def default_get(self, fields):
        """ Redifine amount to pay proportionally to ``amount total - wt`` """
        vals = super().default_get(fields)

        inv_default_vals = self.resolve_2many_commands(
            'invoice_ids', vals.get('invoice_ids', [])
        )
        if len(inv_default_vals) == 1:
            [inv_vals] = inv_default_vals
            dp = self.env['decimal.precision'].precision_get('Account')
            if not float_is_zero(inv_vals.get('enasarco_amount', 0), dp):
                vals['amount'] = inv_vals['amount_net_pay'] \
                    * (inv_vals['residual'] + inv_vals['enasarco_amount']) \
                    / inv_vals['amount_total']

        return vals
