# Copyright 2018 Alessandro Camilli <alessandrocamilli@openforce.it>
# Copyright 2019 Silvio Gregorini <silviogregorini@openforce.it>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'ITA - Enasarco',
    'version': '12.0.1.0.1',
    'category': 'Localization/Italy',
    'summary': "Gestione Enasarco su fatture",
    'author': 'Openforce',
    'website': 'https://github.com/OCA/l10n-italy/tree/11.0/l10n_it_enasarco',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_it_withholding_tax'
    ],
    'data': [
        'views/res_config_setting.xml',
        'views/account_invoice_view.xml',
    ],
    'qweb': [
        'static/src/xml/account_payment.xml',
    ],
    'installable': True
}
