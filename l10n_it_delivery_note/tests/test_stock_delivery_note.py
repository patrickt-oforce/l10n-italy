# Copyright 2021 Alex Comba - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import new_test_user
from odoo.tests.common import Form

from .delivery_note_common import StockDeliveryNoteCommon


class StockDeliveryNote(StockDeliveryNoteCommon):

    # ⇒ "Ordine singolo: consegna parziale"
    def test_partial_delivering_single_so(self):
        #
        #     SO ┐         ┌ DdT
        #        ├ Picking ┘
        #        │
        #        └ Picking ┐
        #                  └ DdT
        #

        user = new_test_user(
            self.env,
            login="test",
            groups="stock.group_stock_manager",
        )
        # change user in order to automatically create delivery note
        # when picking is validated
        self.env.user = user
        StockPicking = self.env["stock.picking"]

        sales_order = self.create_sales_order(
            [
                self.large_desk_line,  # 1
                self.desk_combination_line,  # 1
            ],
        )
        self.assertEqual(len(sales_order.order_line), 2)
        sales_order.action_confirm()
        self.assertEqual(len(sales_order.picking_ids), 1)
        picking = sales_order.picking_ids
        self.assertEqual(len(picking.move_lines), 2)

        # deliver only the first product
        picking.move_lines[0].quantity_done = 1

        res_dict = picking.button_validate()
        wizard = Form(
            self.env[(res_dict.get("res_model"))].with_context(res_dict["context"])
        ).save()
        self.assertEqual(wizard._name, "stock.backorder.confirmation")
        wizard.process()
        self.assertTrue(picking.delivery_note_id)
        picking_backorder = StockPicking.search([("backorder_id", "=", picking.id)])
        self.assertEqual(len(picking_backorder.move_lines), 1)
        picking_backorder.move_lines[0].quantity_done = 1
        picking_backorder.button_validate()
        self.assertTrue(picking_backorder.delivery_note_id)

    # ⇒ "Consegna senza ordine"
    def test_delivery_without_so(self):
        #
        #     Picking ┐
        #             └ DdT
        #
        user = new_test_user(
            self.env,
            login="test",
            groups="stock.group_stock_manager,"
            "l10n_it_delivery_note.use_advanced_delivery_notes",
        )
        # change user in order to activate DN advanced settings
        self.env.user = user

        picking = self.create_picking()

        self.assertEqual(len(picking.move_lines), 1)

        # deliver product
        picking.move_lines.quantity_done = 1
        picking.button_validate()

        # create delivery note with advanced mode
        dn_form = Form(
            self.env["stock.delivery.note.create.wizard"].with_context(
                {"active_id": picking.id, "active_ids": picking.ids}
            )
        )
        dn = dn_form.save()
        dn.confirm()
        self.assertTrue(picking.delivery_note_id)
        picking.delivery_note_id.action_confirm()
        self.assertEqual(picking.delivery_note_id.state, "confirm")
        self.assertEqual(picking.delivery_note_id.invoice_status, "no")

        test_company = self.env["res.company"].create({"name": "Test Company"})
        with self.assertRaises(UserError) as exc:
            picking.delivery_note_id.write({"company_id": test_company.id})
        exc_message = exc.exception.args[0]
        self.assertIn("type_id", exc_message)
        self.assertIn("picking_ids", exc_message)
        self.assertIn("belongs to another company", exc_message)

    def test_delivery_action_confirm(self):
        user = new_test_user(
            self.env,
            login="test",
            groups="stock.group_stock_manager,"
            "l10n_it_delivery_note.use_advanced_delivery_notes",
        )
        # change user in order to activate DN advanced settings
        self.env.user = user

        picking = self.create_picking(
            carrier_id=self.env.ref("delivery.delivery_carrier").id
        )
        picking.move_lines.quantity_done = 1
        picking.button_validate()

        dn_form = Form(
            self.env["stock.delivery.note.create.wizard"].with_context(
                {"active_id": picking.id, "active_ids": picking.ids}
            )
        )
        dn = dn_form.save()
        dn.confirm()

        delivery_note_id = picking.delivery_note_id

        new_picking = self.create_picking(
            carrier_id=self.env.ref("delivery.normal_delivery_carrier").id
        )
        new_picking.move_lines.quantity_done = 1
        new_picking.button_validate()

        delivery_note_id.write({"picking_ids": [(4, new_picking.id)]})

        warning_context = delivery_note_id.action_confirm().get("context")
        self.assertTrue(warning_context)
        self.assertIn(
            "contains pickings related to different transporters",
            warning_context.get("default_warning_message"),
        )

        picking.carrier_id = self.env.ref("delivery.free_delivery_carrier").id
        new_picking.carrier_id = self.env.ref("delivery.free_delivery_carrier").id
        delivery_note_id.carrier_id = self.env.ref(
            "l10n_it_delivery_note.partner_carrier_2"
        ).id

        warning_context = delivery_note_id.action_confirm().get("context")
        self.assertTrue(warning_context)
        self.assertIn(
            "The carrier set in Delivery Note is "
            "different from the carrier set in picking(s)",
            warning_context.get("default_warning_message"),
        )

        delivery_note_id.delivery_method_id = self.env.ref(
            "delivery.free_delivery_carrier"
        ).id
        picking.carrier_id = self.env.ref("delivery.delivery_carrier").id
        new_picking.carrier_id = self.env.ref("delivery.free_delivery_carrier").id
        warning_context = delivery_note_id.action_confirm().get("context")
        self.assertTrue(warning_context)
        self.assertIn(
            "contains pickings related to different "
            "delivery methods from the same transporter",
            warning_context.get("default_warning_message"),
        )

        new_picking.carrier_id = self.env.ref("delivery.delivery_carrier").id
        delivery_note_id.delivery_method_id = self.env.ref(
            "delivery.free_delivery_carrier"
        ).id
        delivery_note_id.carrier_id = self.env.ref(
            "l10n_it_delivery_note.partner_carrier_1"
        ).id
        warning_context = delivery_note_id.action_confirm().get("context")
        self.assertTrue(warning_context)
        self.assertIn(
            "The shipping method set in Delivery Note is "
            "different from the shipping method set in picking(s)",
            warning_context.get("default_warning_message"),
        )

    def test_delivery_action_confirm_without_ref(self):
        user = new_test_user(
            self.env,
            login="test",
            groups="stock.group_stock_manager,"
            "l10n_it_delivery_note.use_advanced_delivery_notes,"
            "l10n_it_delivery_note.group_required_partner_ref",
        )
        # change user in order to activate DN advanced settings
        self.env.user = user

        picking = self.create_picking(
            picking_type_id=self.env.ref("stock.picking_type_in").id,
            carrier_id=self.env.ref("delivery.delivery_carrier").id,
        )
        picking.move_lines.quantity_done = 1
        picking.button_validate()

        dn_form = Form(
            self.env["stock.delivery.note.create.wizard"].with_context(
                {"active_id": picking.id, "active_ids": picking.ids}
            )
        )
        dn = dn_form.save()
        dn.confirm()

        delivery_note_id = picking.delivery_note_id

        with self.assertRaises(UserError) as exc:
            delivery_note_id.action_confirm()
        exc_message = exc.exception.args[0]
        self.assertIn("The field 'Partner reference' is mandatory", exc_message)

        delivery_note_id.partner_ref = "Reference #1234"
        delivery_note_id.action_confirm()

    def test_partner_shipping_delivering_single_so(self):
        # ⇒ "Ordine singolo: consegna a indirizzo diverso"
        self._test_partners()
        # ⇒ "Ordine singolo: consegna a indirizzo di consegna e fatturazione diversi"
        self._test_partners(test_invoice_partner=True)

    def _test_partners(self, test_invoice_partner=False):
        user = new_test_user(
            self.env,
            login=f"test_{'invoice' if test_invoice_partner else 'shipping'}",
            groups="stock.group_stock_manager,"
            "l10n_it_delivery_note.use_advanced_delivery_notes",
        )
        self.env.user = user
        partner_shipping = self.create_partner(
            "Shipping Address Mario Rossi", user.company_id
        )
        partner_shipping.write(
            {
                "parent_id": self.recipient.id,
                "type": "delivery",
            }
        )
        partner_invoicing = self.create_partner("Invoicing Address", user.company_id)
        StockPicking = self.env["stock.picking"]
        sales_order = self.create_sales_order(
            [
                self.large_desk_line,  # 1
                self.desk_combination_line,  # 1
            ],
        )
        if test_invoice_partner:
            sales_order.write(
                {
                    "partner_invoice_id": partner_invoicing.id,
                }
            )
        self.assertEqual(len(sales_order.order_line), 2)
        sales_order.action_confirm()
        self.assertEqual(len(sales_order.picking_ids), 1)
        picking = sales_order.picking_ids
        self.assertEqual(len(picking.move_lines), 2)

        # deliver only the first product
        picking.move_lines[0].quantity_done = 1
        res_dict = picking.button_validate()
        wizard = Form(
            self.env[(res_dict.get("res_model"))]
            .with_user(user)
            .with_context(res_dict["context"])
        ).save()
        wizard.process()
        res_dict = picking.action_delivery_note_create()
        wizard = Form(
            self.env[(res_dict.get("res_model"))]
            .with_user(user)
            .with_context(res_dict["context"])
        ).save()
        wizard.confirm()
        self.assertTrue(picking.delivery_note_id)
        if test_invoice_partner:
            self.assertEqual(picking.delivery_note_id.partner_id, partner_invoicing)
        else:
            self.assertEqual(picking.delivery_note_id.partner_id, self.recipient)
        self.assertEqual(picking.delivery_note_id.partner_shipping_id, partner_shipping)
        picking_backorder = StockPicking.search([("backorder_id", "=", picking.id)])
        self.assertEqual(len(picking_backorder.move_lines), 1)
        picking_backorder.move_lines[0].quantity_done = 1
        picking_backorder.button_validate()
        res_dict = picking_backorder.action_delivery_note_create()
        wizard = Form(
            self.env[(res_dict.get("res_model"))]
            .with_user(user)
            .with_context(res_dict["context"])
        ).save()
        wizard.confirm()
        self.assertTrue(picking_backorder.delivery_note_id)
        if test_invoice_partner:
            self.assertEqual(
                picking_backorder.delivery_note_id.partner_id, partner_invoicing
            )
        else:
            self.assertEqual(
                picking_backorder.delivery_note_id.partner_id, self.recipient
            )
        self.assertEqual(
            picking_backorder.delivery_note_id.partner_shipping_id,
            partner_shipping,
        )

    def test_ddt_line_amount(self):
        user = new_test_user(
            self.env,
            login="test",
            groups="stock.group_stock_manager,"
            "l10n_it_delivery_note.use_advanced_delivery_notes",
        )

        self.env.user = user

        sales_order = self.create_sales_order(
            [
                self.large_desk_line,  # 1
                self.desk_combination_line,  # 1
            ],
        )

        tax_id = self.env["account.tax"].search(
            [("type_tax_use", "=", "sale")], limit=1
        )

        for line in sales_order.order_line:
            line.tax_id = [(6, 0, tax_id.ids)]

        sales_order.action_confirm()
        picking = sales_order.picking_ids

        # deliver all the products
        for move_line in picking.move_lines:
            move_line.quantity_done = 1

        picking.button_validate()
        dn_form = Form(
            self.env["stock.delivery.note.create.wizard"].with_context(
                {"active_id": picking.id, "active_ids": picking.ids}
            )
        )
        dn = dn_form.save()
        dn.confirm()

        delivery_note_id = picking.delivery_note_id
        for note_line in delivery_note_id.line_ids:
            self.assertEqual(
                note_line.price_unit * note_line.product_qty, note_line.untaxed_amount
            )
            self.assertNotEqual(note_line.untaxed_amount, note_line.amount)
