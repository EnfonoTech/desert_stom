import json

import frappe
from frappe.model.document import Document

PER_ITEM_FIELDS = [
	"length", "shoulder", "sleeve_length", "loose_1", "loose_2",
	"bottom", "bottom_size", "sleeve_loose", "shoulder_alt", "sleeve_alt",
	"collar_style", "collar_type", "neck_style", "neck_type",
	"hip", "hip_type", "special_button",
]


class TailoringMeasurement(Document):
	def before_save(self):
		self._sync_measurements_json()

	def _sync_measurements_json(self):
		"""Save the currently displayed field values into measurements_json
		under the active cloth_name key."""
		try:
			data = json.loads(self.measurements_json or "{}")
		except (json.JSONDecodeError, TypeError):
			data = {}

		if self.cloth_name:
			data[self.cloth_name] = {f: self.get(f) for f in PER_ITEM_FIELDS}

		# Clean up keys for items no longer in measurement_items
		# Build valid names including #N suffixes for duplicates
		valid_names = set()
		name_count = {}
		for row in self.measurement_items or []:
			name = row.item_name or row.item_code
			if name:
				name_count[name] = name_count.get(name, 0) + 1

		name_seen = {}
		for row in self.measurement_items or []:
			name = row.item_name or row.item_code
			if name:
				name_seen[name] = name_seen.get(name, 0) + 1
				if name_count[name] > 1:
					valid_names.add(name + " #" + str(name_seen[name]))
				else:
					valid_names.add(name)

		if valid_names:
			data = {k: v for k, v in data.items() if k in valid_names}

		self.measurements_json = json.dumps(data)

	def on_submit(self):
		"""Auto-update linked Sales Order status and add extras."""
		if self.sales_order:
			current_status = frappe.db.get_value(
				"Sales Order", self.sales_order, "stitching_status"
			)
			# Only upgrade from Order to Measurement (don't downgrade)
			if current_status == "Order":
				frappe.db.set_value(
					"Sales Order", self.sales_order,
					"stitching_status", "Measurement"
				)
			self._add_extras_to_sales_order()

	def _add_extras_to_sales_order(self):
		"""Append extra/add-on items to the linked Sales Order."""
		if not self.extra_items:
			return

		so = frappe.get_doc("Sales Order", self.sales_order)
		so.flags.ignore_validate_update_after_submit = True

		default_warehouse = so.items[0].warehouse if so.items else None

		for extra in self.extra_items:
			stock_uom = frappe.db.get_value("Item", extra.item_code, "stock_uom") or "Nos"
			qty = frappe.utils.flt(extra.qty) or 1
			rate = frappe.utils.flt(extra.rate)
			# If rate is 0 but amount was entered, derive rate from amount
			if not rate and frappe.utils.flt(extra.amount):
				rate = frappe.utils.flt(extra.amount) / qty
			amount = qty * rate
			so.append("items", {
				"item_code": extra.item_code,
				"item_name": extra.item_name,
				"qty": qty,
				"rate": rate,
				"amount": amount,
				"base_rate": rate,
				"base_amount": amount,
				"net_rate": rate,
				"net_amount": amount,
				"base_net_rate": rate,
				"base_net_amount": amount,
				"delivery_date": so.delivery_date,
				"warehouse": default_warehouse,
				"uom": stock_uom,
				"stock_uom": stock_uom,
				"conversion_factor": 1,
			})

		so.flags.ignore_mandatory = True
		so.calculate_taxes_and_totals()
		so.save()
		so.reload()

		# Refresh outstanding amount
		advance = frappe.utils.flt(so.advance_collected)
		frappe.db.set_value(
			"Sales Order", self.sales_order,
			"outstanding_amount", frappe.utils.flt(so.grand_total) - advance,
			update_modified=False,
		)

		frappe.msgprint(
			f"{len(self.extra_items)} extra item(s) added to {self.sales_order}",
			alert=True,
		)

	def on_cancel(self):
		"""Remove extra items from linked Sales Order on cancellation."""
		if self.sales_order and self.extra_items:
			self._remove_extras_from_sales_order()
		# Revert stitching status back to Order if it's still at Measurement
		if self.sales_order:
			current_status = frappe.db.get_value(
				"Sales Order", self.sales_order, "stitching_status"
			)
			if current_status == "Measurement":
				frappe.db.set_value(
					"Sales Order", self.sales_order,
					"stitching_status", "Order"
				)

	def _remove_extras_from_sales_order(self):
		"""Remove extra/add-on items that were added by this measurement."""
		extra_item_codes = [e.item_code for e in self.extra_items]

		so = frappe.get_doc("Sales Order", self.sales_order)
		so.flags.ignore_validate_update_after_submit = True

		# Remove matching extra items from the end of SO items
		# (extras are appended at the end during submission)
		items_to_keep = []
		extras_to_remove = list(extra_item_codes)  # copy to track removal

		# Iterate in reverse to remove from end first
		so_items_reversed = list(reversed(so.items))
		for item in so_items_reversed:
			if item.item_code in extras_to_remove:
				extras_to_remove.remove(item.item_code)
			else:
				items_to_keep.append(item)

		items_to_keep.reverse()

		if len(items_to_keep) < len(so.items):
			so.items = []
			for idx, item_data in enumerate(items_to_keep, 1):
				item_data.idx = idx
				so.items.append(item_data)

			so.flags.ignore_mandatory = True
			so.calculate_taxes_and_totals()
			so.save()
			so.reload()

			# Refresh outstanding amount
			advance = frappe.utils.flt(so.advance_collected)
			frappe.db.set_value(
				"Sales Order", self.sales_order,
				"outstanding_amount", frappe.utils.flt(so.grand_total) - advance,
				update_modified=False,
			)

			removed_count = len(extra_item_codes) - len(extras_to_remove)
			frappe.msgprint(
				f"{removed_count} extra item(s) removed from {self.sales_order}",
				alert=True,
			)

	def validate(self):
		if self.measurements_json:
			try:
				json.loads(self.measurements_json)
			except (json.JSONDecodeError, TypeError):
				frappe.throw("Invalid measurements data")
