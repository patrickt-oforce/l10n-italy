# Copyright 2015  Davide Corio <davide.corio@abstract.it>
# Copyright 2015-2016  Lorenzo Battistini - Agile Business Group
# Copyright 2016  Alessio Gerace - Agile Business Group
# Copyright 2023  Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_sp = fields.Float(
        string="Split Payment",
        digits="Account",
        store=True,
        readonly=True,
        compute="_compute_amount",
    )
    split_payment = fields.Boolean(
        string="Is Split Payment", related="fiscal_position_id.split_payment"
    )

    def _compute_amount(self):
        res = super()._compute_amount()
        for move in self:
            if move.split_payment:
                if move.is_purchase_document():
                    continue
                if move.tax_totals:
                    move.amount_sp = (
                        move.tax_totals["amount_total"]
                        - move.tax_totals["amount_untaxed"]
                    )
                    move.amount_residual -= move.amount_tax
                    move.amount_tax = 0.0
                else:
                    move.amount_sp = 0.0
                move.amount_total = move.amount_untaxed
            else:
                move.amount_sp = 0.0
        return res

    def write(self, vals):
        sp_moves = self.filtered(lambda am: am.split_payment)
        # In account move(s) where fiscal position value is changed
        # manually, can happen that are not set as split payment
        # Check if the value is present in vals, allow include the
        # move(s) becoming split payment in this write, even if the
        # value set for fiscal position is the old value
        fiscal_position_id = vals.get("fiscal_position_id", 0)
        fiscal_position = self.env["account.fiscal.position"].browse(fiscal_position_id).exists()
        if fiscal_position and fiscal_position.split_payment:
            sp_moves = self

        if sp_moves:
            # Skip check move(s) validity, until split payment write-off
            # completed
            sp_moves_ctx = sp_moves.with_context(check_move_validity=False)
            res = super(AccountMove, sp_moves_ctx).write(vals)

            # Keep checking validity of move(s) that are not split
            # payment
            other_moves = self.with_context(check_move_validity=True) - sp_moves

            # If no move(s) that are not in split payment, avoid write
            # on empty recordset. Because Odoo methods keep processing
            # relational commands in vals, that refer to non existent
            # account.move.line managed by first write
            if other_moves:
                res = super(AccountMove, other_moves).write(vals)
        else:
            res = super().write(vals)
        if self.env.context.get("skip_split_payment_computation"):
            return res
        self.with_context(check_move_validity=False).compute_split_payment()
        container = {"records": self}
        self._check_balanced(container)
        return res

    def copy(self, default=None):
        if self.split_payment:
            res = super(AccountMove, self.with_context(check_move_validity=False)).copy(
                default=default
            )
            res.compute_split_payment()
        else:
            res = super().copy(default=default)
        return res

    def compute_split_payment(self):
        for move in self:
            if move.split_payment:
                line_sp = fields.first(
                    move.line_ids.filtered(lambda move_line: move_line.is_split_payment)
                )
                for line in move.line_ids:
                    if line.display_type == "tax" and not line.is_split_payment:
                        write_off_line_vals = line._build_writeoff_line()
                        if line_sp:
                            if (
                                float_compare(
                                    line_sp.price_unit,
                                    write_off_line_vals["price_unit"],
                                    precision_rounding=move.currency_id.rounding,
                                )
                                != 0
                            ):
                                line_sp.write(write_off_line_vals)
                        else:
                            if move.amount_sp:
                                move.with_context(
                                    skip_split_payment_computation=True
                                ).line_ids = [Command.create(write_off_line_vals)]
