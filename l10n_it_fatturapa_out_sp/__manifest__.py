# Copyright 2020 Marco Colombo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "ITA - Fattura elettronica - Emissione - Scissione Pagamenti",
    "version": "14.0.1.0.1+PR2717",
    "development_status": "Beta",
    "category": "Localization/Italy",
    "summary": "Scissione pagamenti in fatturapa",
    "author": "Marco Colombo," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-italy" "l10n_it_fatturapa_out_sp",
    "license": "AGPL-3",
    "depends": [
        "l10n_it_fatturapa_out",
        "l10n_it_split_payment",
        "l10n_it_fatturapa_out_rc",
    ],
    "data": [
        "view/invoice_it_template.xml",
    ],
    "installable": True,
}
