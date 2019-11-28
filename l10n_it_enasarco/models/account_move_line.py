# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re

from odoo import _, api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    enasarco_move = fields.Boolean(
        "Enasarco Move",
        compute='compute_enasarco_move',
        store=True
    )

    @api.multi
    @api.depends('invoice_id', 'invoice_id.enasarco_move_id')
    def compute_enasarco_move(self):
        for line in self:
            if line.invoice_id and line.invoice_id.enasarco_move_id:
                line.enasarco_move = True
            else:
                line.enasarco_move = False

    @api.model
    def _prepare_move_lines(
            self, move_lines,
            target_currency=False, target_date=False, recs_count=0
    ):
        lines_data = super()._prepare_move_lines(
            move_lines, target_currency, target_date, recs_count
        )

        for line_data in lines_data:
            if not line_data.get('id', False):
                continue
            line = self.browse(line_data['id'])
            # Recalculate values considering enasarco amount
            if line.invoice_id and line.invoice_id.enasarco_amount_total:
                line_data['debit'] = \
                    (line_data['debit'] -
                     line.invoice_id.enasarco_amount_total) \
                    if line_data['debit'] else 0.0
                line_data['credit'] = \
                    (line_data['credit'] -
                     line.invoice_id.enasarco_amount_total) \
                    if line_data['credit'] else 0.0
                # Replace net to pay value set by witholding tax module
                net_to_pay_string = _('(Net to pay: %s)') % (
                    line_data['debit'] or line_data['credit'])
                if '(Net to pay:' in line_data['name']:
                    line_data['name'] = re.sub(
                        r'\(Net to pay: .+\)',
                        '',
                        line_data['name']) + net_to_pay_string
                else:
                    line_data['name'] = line_data['name'] + net_to_pay_string
                # FYI Enasarco is used only in the some company currency
                # context. So, it's not important to recalculate amount
                # in another currency value

        return lines_data
