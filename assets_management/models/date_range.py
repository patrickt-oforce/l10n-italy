# Author(s): Silvio Gregorini (silviogregorini@openforce.it)
# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DateRange(models.Model):
    _inherit = 'date.range'

    @api.model
    def get_fiscal_year_by_date(
            self, date,
            limit=1, company=None, active_type=True, raise_if_missing=True
    ):
        """
        Retrieves fiscal year by given ``date``.

        By default, only 1 fiscal year will be returned, unless specified
        differently.
        If ``raise_if_missing`` is True and no fiscal year is found, an error
        will be raised.
        """
        domain = self.get_fiscal_year_by_date_domain(
            date, company, active_type
        )
        fiscal_years = self.search(domain, limit=limit)

        if not fiscal_years and raise_if_missing:
            date_str = fields.Datetime.from_string(date).strftime('%d-%m-%Y')
            raise UserError(
                _("No fiscal year defined for date ") + date_str
            )

        return fiscal_years

    @api.model
    def get_fiscal_year_by_date_domain(
            self, date,
            company=None, active_type=True
    ):
        """
        Prepares a search() domain to retrieve fiscal years by given ``date``.
        """
        domain = [
            ('date_start', '<=', date),
            ('date_end', '>=', date),
            ('type_id.fiscal_year', '=', True)
        ]

        if active_type:
            domain.append(('type_id.active', '=', True))
        if company:
            domain.append(('company_id', 'in', company.ids))

        return domain
