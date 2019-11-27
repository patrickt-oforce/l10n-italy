# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    enasarco_account_id = fields.Many2one(
        'account.account',
        string="Enasarco Account *",
    )

    enasarco_journal_id = fields.Many2one(
        'account.journal',
        string="Enasarco Journal *",
    )

    @api.model
    def default_get(self, fields_list):
        """ Get Enasarco data from settings' company """
        default_vals = super().default_get(fields_list)
        company_id = default_vals.get('company_id')
        if company_id:
            company = self.env['res.company'].browse(company_id)
            default_vals.update(company.get_enasarco_vals())
        return default_vals

    @api.multi
    def execute(self):
        """ Update company with Enasarco data """
        if self.company_id:
            self.company_id.write(self.set_enasarco_company_vals())
        return super().execute()

    def set_enasarco_company_vals(self):
        """
        Gets Enasarco data from current res.config.settings record and returns
        a dict of values for res.company write()
        """
        self.ensure_one()
        return {
            'enasarco_account_id': self.enasarco_account_id.id,
            'enasarco_journal_id': self.enasarco_journal_id.id,
        }
