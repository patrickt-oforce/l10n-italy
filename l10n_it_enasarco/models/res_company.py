# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    enasarco_account_id = fields.Many2one(
        'account.account',
        string="Enasarco Account *",
    )

    enasarco_journal_id = fields.Many2one(
        'account.journal',
        string="Enasarco Journal *",
    )

    def check_enasarco_config(self):
        for company in self:
            if not company.enasarco_account_id:
                raise ValidationError(
                    _("Missing Enasarco Account in company configuration")
                )
            if not company.enasarco_journal_id:
                raise ValidationError(
                    _("Missing Enasarco Journal in company configuration")
                )

    def get_enasarco_vals(self):
        """
        Gets Enasarco data from current company and returns a dict of default
        values for res.config.settings record
        """
        self.ensure_one()
        return {
            'enasarco_account_id': self.enasarco_account_id.id,
            'enasarco_journal_id': self.enasarco_journal_id.id,
        }
