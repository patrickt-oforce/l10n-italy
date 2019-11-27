# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _amount_withholding_tax(self):
        super()._amount_withholding_tax()
        for invoice in self:
            invoice.amount_net_pay = invoice.amount_net_pay - \
                invoice.enasarco_amount

    enasarco = fields.Boolean(
        states={'draft': [('readonly', False)]},
        string="Enasarco",
        readonly=True,
    )

    enasarco_amount = fields.Monetary(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string="Enasarco amount",
        track_visibility='onchange',
    )

    enasarco_amount_total = fields.Monetary(
        related='enasarco_amount',
        string='Enasarco amount',
    )

    enasarco_date = fields.Date(
        help="Date for account move",
        readonly=True,
        states={'draft': [('readonly', False)]},
        string="Enasarco date",
    )

    enasarco_move_id = fields.Many2one(
        'account.move',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        string="Enasarco Account Move",
    )

    @api.multi
    def action_invoice_cancel(self):
        """ Delete Enasarco moves """
        for invoice in self.filtered('enasarco_move_id'):
            invoice.enasarco_move_id.line_ids.remove_move_reconcile()
            invoice.enasarco_move_id.button_cancel()
            invoice.enasarco_move_id.unlink()
        return super().action_invoice_cancel()

    @api.multi
    def action_invoice_open(self):
        """ Create Enasarco moves """
        res = super().action_invoice_open()
        self.check_enasarco_config()
        for inv in self.filtered(self.needs_enasarco_move):
            inv.set_enasarco_move()
            inv.reconcile_enasarco_move_lines()
        return res

    @api.onchange('date')
    def enasarco_onchange_date(self):
        for inv in self:
            if inv.date:
                inv.enasarco_date = inv.date

    def check_enasarco_config(self):
        self.mapped('company_id').check_enasarco_config()

    def get_enasarco_move_lines_vals(self):
        self.ensure_one()
        enasarco_amt = self.enasarco_amount
        num = self.number
        partner = self.partner_id

        # Reconciliation line
        rec_line = {
            'name': _('Enasarco for {}').format(num),
            'partner_id': partner.id,
            'account_id': self.account_id.id,
            'debit': enasarco_amt,
            'credit': 0,
            'enasarco_move': True,
        }
        # Enasarco debit line
        enasarco_debit_line = {
            'name': _('Enasarco for {} - {}').format(num, partner.name),
            'partner_id': False,
            'account_id': self.company_id.enasarco_account_id.id,
            'debit': 0,
            'credit': enasarco_amt,
            'enasarco_move': True,
        }

        return rec_line, enasarco_debit_line

    def get_enasarco_move_vals(self):
        self.ensure_one()
        return {
            'date': self.enasarco_date or self.date,
            'journal_id': self.company_id.enasarco_journal_id.id,
            'line_ids': [
                (0, 0, v) for v in self.get_enasarco_move_lines_vals()
            ],
            'ref': _('Enasarco per {} - {}').format(
                self.number, self.partner_id.name
            ),
        }

    def needs_enasarco_move(self):
        self.ensure_one()
        dp = self.env['decimal.precision'].precision_get('Account')
        return self.enasarco and not float_is_zero(self.enasarco_amount, dp)

    def reconcile_enasarco_move_lines(self):
        """
        Reconciling transfer with invoice to simulate a payment, Odoo will
        manage the cash accounting registration
        """
        self.ensure_one()
        inv_lines_to_rec = self.move_id.line_ids.filtered(
            lambda l: not l.reconciled
            and l.account_id.user_type_id.type == 'payable'
        )
        ena_lines_to_rec = self.enasarco_move_id.line_ids.filtered(
            lambda l: l.debit > 0
        )
        lines_to_rec = inv_lines_to_rec + ena_lines_to_rec
        if lines_to_rec:
            lines_to_rec.with_context(no_generate_wt_move=True).reconcile()

    def set_enasarco_move(self, post_move=True):
        self.ensure_one()
        vals = self.get_enasarco_move_vals()
        self.enasarco_move_id = self.env['account.move'].create(vals)
        if post_move:
            self.enasarco_move_id.post()
