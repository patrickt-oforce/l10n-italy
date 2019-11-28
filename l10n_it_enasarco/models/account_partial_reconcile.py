# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model
    def create(self, vals):
        """ If there's an enasarco move, disable wt generation """
        aml_obj = self.env['account.move.line']
        ctx = dict(self.env.context)

        aml_ids = []
        if vals.get('debit_move_id'):
            aml_ids.append(vals.get('debit_move_id'))
        if vals.get('credit_move_id'):
            aml_ids.append(vals.get('credit_move_id'))
        if aml_ids and aml_obj.browse(aml_ids).filtered('enasarco_move'):
            ctx.update(no_generate_wt_move=True)

        return super(PartialReconcile, self.with_context(ctx)).create(vals)
