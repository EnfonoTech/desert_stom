import frappe
from frappe import _


@frappe.whitelist()
def create_advance_payment(so_name, amount, mode_of_payment, reference_no=""):
	"""Create a Payment Entry (Receive) linked to a Sales Order as advance."""
	so = frappe.get_doc("Sales Order", so_name)
	amount = frappe.utils.flt(amount)

	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero"))

	company = so.company
	# Get payment account from Mode of Payment
	mop_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
	account = None
	for acc in mop_doc.accounts:
		if acc.company == company:
			account = acc.default_account
			break

	if not account:
		# Fallback to default cash account
		account = frappe.get_cached_value(
			"Company", company, "default_cash_account"
		) or frappe.get_cached_value("Company", company, "default_bank_account")

	if not account:
		frappe.throw(
			_("No account found for Mode of Payment {0} and Company {1}").format(
				mode_of_payment, company
			)
		)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.party_type = "Customer"
	pe.party = so.customer
	pe.company = company
	pe.mode_of_payment = mode_of_payment
	pe.paid_from = frappe.get_cached_value("Company", company, "default_receivable_account")
	pe.paid_to = account
	pe.paid_amount = amount
	pe.received_amount = amount

	if reference_no:
		pe.reference_no = reference_no
		pe.reference_date = frappe.utils.today()

	pe.append(
		"references",
		{
			"reference_doctype": "Sales Order",
			"reference_name": so_name,
			"allocated_amount": amount,
		},
	)

	pe.insert(ignore_permissions=True)
	pe.submit()

	# Update advance_collected on SO
	total_advance = frappe.utils.flt(so.advance_collected) + amount
	updates = {
		"advance_collected": total_advance,
		"outstanding_amount": frappe.utils.flt(so.grand_total) - total_advance,
	}

	# Auto-transition to Job Order after first advance payment
	if so.stitching_status in ("Order", "Measurement"):
		updates["stitching_status"] = "Job Order"

	frappe.db.set_value("Sales Order", so_name, updates)

	return pe.name


@frappe.whitelist()
def create_sales_invoice(so_name, selected_items=None, update_stock=1):
	"""Create a Sales Invoice from a Sales Order."""
	so = frappe.get_doc("Sales Order", so_name)

	if isinstance(selected_items, str):
		selected_items = frappe.parse_json(selected_items)

	update_stock = frappe.utils.cint(update_stock)

	items_to_process = []
	for item in so.items:
		if not selected_items or item.name in selected_items:
			items_to_process.append(item)

	if not items_to_process:
		frappe.throw(_("No items selected"))

	si = frappe.new_doc("Sales Invoice")
	si.customer = so.customer
	si.company = so.company
	si.set_posting_time = 1
	si.posting_date = frappe.utils.today()
	si.due_date = frappe.utils.today()
	si.currency = so.currency
	si.conversion_rate = so.conversion_rate
	si.update_stock = update_stock

	for item in items_to_process:
		si.append(
			"items",
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"qty": item.qty,
				"rate": item.rate,
				"amount": item.amount,
				"uom": item.uom,
				"warehouse": item.warehouse,
				"sales_order": so.name,
				"so_detail": item.name,
			},
		)

	# Copy taxes from SO to SI
	for tax in so.taxes:
		si.append("taxes", {
			"charge_type": tax.charge_type,
			"account_head": tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"cost_center": tax.cost_center,
			"included_in_print_rate": tax.included_in_print_rate,
		})

	# Allocate existing advance payments from SO against this invoice
	si.allocate_advances_automatically = 1

	si.insert(ignore_permissions=True)

	# Fetch and allocate advances (Payment Entries linked to the SO)
	si.set_advances()
	if si.advances:
		si.save()

	si.submit()

	return si.name


@frappe.whitelist()
def complete_order(so_name, values):
	"""Complete an order by creating SI, PE, DN as requested."""
	if isinstance(values, str):
		values = frappe.parse_json(values)

	so = frappe.get_doc("Sales Order", so_name)
	result = {"si": None, "pe": None, "dn": None}

	create_si = frappe.utils.cint(values.get("create_si"))
	create_pe = frappe.utils.cint(values.get("create_pe"))
	create_dn = frappe.utils.cint(values.get("create_dn"))
	payment_amount = frappe.utils.flt(values.get("payment_amount"))
	mode_of_payment = values.get("mode_of_payment", "Cash")
	selected_items = values.get("selected_items", [])
	discount_type = values.get("discount_type", "None")
	discount_percentage = frappe.utils.flt(values.get("discount_percentage"))
	discount_amount = frappe.utils.flt(values.get("discount_amount"))

	# Filter SO items to selected ones
	items_to_process = []
	for item in so.items:
		if not selected_items or item.name in selected_items:
			items_to_process.append(item)

	if not items_to_process:
		frappe.throw(_("No items selected"))

	# Create Sales Invoice
	if create_si:
		si = frappe.new_doc("Sales Invoice")
		si.customer = so.customer
		si.company = so.company
		si.set_posting_time = 1
		si.posting_date = frappe.utils.today()
		si.due_date = frappe.utils.today()
		si.currency = so.currency
		si.conversion_rate = so.conversion_rate

		# If DN is NOT being created separately, SI handles stock out
		if not create_dn:
			si.update_stock = 1

		for item in items_to_process:
			si.append(
				"items",
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount,
					"uom": item.uom,
					"warehouse": item.warehouse,
					"sales_order": so.name,
					"so_detail": item.name,
				},
			)

		# Copy taxes from SO to SI
		for tax in so.taxes:
			si.append("taxes", {
				"charge_type": tax.charge_type,
				"account_head": tax.account_head,
				"description": tax.description,
				"rate": tax.rate,
				"cost_center": tax.cost_center,
				"included_in_print_rate": tax.included_in_print_rate,
			})

		# Apply discount if specified
		if discount_type == "Percentage" and discount_percentage > 0:
			si.additional_discount_percentage = discount_percentage
			si.apply_discount_on = "Grand Total"
		elif discount_type == "Amount" and discount_amount > 0:
			si.discount_amount = discount_amount
			si.apply_discount_on = "Grand Total"

		# Allocate existing advance payments from SO against this invoice
		si.allocate_advances_automatically = 1

		si.insert(ignore_permissions=True)

		# Fetch and allocate advances (Payment Entries linked to the SO)
		si.set_advances()
		if si.advances:
			si.save()

		si.submit()
		result["si"] = si.name

	# Create Payment Entry
	if create_pe and payment_amount > 0:
		target_doctype = "Sales Invoice" if result["si"] else "Sales Order"
		target_name = result["si"] or so_name

		company = so.company
		mop_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
		account = None
		for acc in mop_doc.accounts:
			if acc.company == company:
				account = acc.default_account
				break

		if not account:
			account = frappe.get_cached_value(
				"Company", company, "default_cash_account"
			) or frappe.get_cached_value("Company", company, "default_bank_account")

		# Get actual outstanding amount to avoid over-allocation
		if target_doctype == "Sales Invoice":
			outstanding = frappe.utils.flt(
				frappe.db.get_value("Sales Invoice", target_name, "outstanding_amount")
			)
			allocated = min(payment_amount, outstanding) if outstanding > 0 else payment_amount
		else:
			allocated = payment_amount

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.party_type = "Customer"
		pe.party = so.customer
		pe.company = company
		pe.mode_of_payment = mode_of_payment
		pe.paid_from = frappe.get_cached_value(
			"Company", company, "default_receivable_account"
		)
		pe.paid_to = account
		pe.paid_amount = payment_amount
		pe.received_amount = payment_amount
		pe.reference_no = result["si"] or so_name
		pe.reference_date = frappe.utils.today()

		pe.append(
			"references",
			{
				"reference_doctype": target_doctype,
				"reference_name": target_name,
				"allocated_amount": allocated,
			},
		)

		pe.insert(ignore_permissions=True)
		pe.submit()
		result["pe"] = pe.name

	# Create Delivery Note when requested (SI has update_stock=0 when DN is also created)
	if create_dn:
		dn = frappe.new_doc("Delivery Note")
		dn.customer = so.customer
		dn.company = so.company
		dn.set_posting_time = 1
		dn.posting_date = frappe.utils.today()
		dn.currency = so.currency
		dn.conversion_rate = so.conversion_rate

		for item in items_to_process:
			dn.append(
				"items",
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount,
					"uom": item.uom,
					"warehouse": item.warehouse,
					"against_sales_order": so.name,
					"so_detail": item.name,
				},
			)

		dn.insert(ignore_permissions=True)
		dn.submit()
		result["dn"] = dn.name

	# Mark SO as Delivered
	frappe.db.set_value("Sales Order", so_name, "stitching_status", "Delivered")

	return result


@frappe.whitelist()
def get_so_stats(so_name):
	"""Get measurement count and profit/loss stats for a Sales Order."""
	so = frappe.get_doc("Sales Order", so_name)

	# Measurement count
	measurement_count = frappe.db.count(
		"Tailoring Measurement", {"sales_order": so_name}
	)

	STITCHING_COST_PER_QTY = 35  # SAR per item qty

	# Calculate item cost (valuation rate from Item master)
	item_cost = 0
	total_qty = 0
	for item in so.items:
		total_qty += frappe.utils.flt(item.qty)
		valuation_rate = frappe.utils.flt(
			frappe.db.get_value("Item", item.item_code, "valuation_rate")
		)
		item_cost += valuation_rate * frappe.utils.flt(item.qty)

	# Stitching cost: 35 SAR per item qty
	stitching_cost = total_qty * STITCHING_COST_PER_QTY
	total_cost = item_cost + stitching_cost

	# Revenue: sum of linked Sales Invoice grand_total (submitted only)
	revenue = frappe.utils.flt(frappe.db.sql("""
		SELECT COALESCE(SUM(si.grand_total), 0)
		FROM `tabSales Invoice` si
		JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE sii.sales_order = %s
		AND si.docstatus = 1
	""", so_name)[0][0])

	# If no invoice yet, use SO grand_total as expected revenue
	if not revenue:
		revenue = frappe.utils.flt(so.grand_total)

	estimated_profit = revenue - total_cost

	# Persist values to SO fields (without triggering modified timestamp)
	frappe.db.set_value("Sales Order", so_name, {
		"measurement_count": measurement_count,
		"item_cost": item_cost,
		"stitching_cost": stitching_cost,
		"total_cost": total_cost,
		"revenue": revenue,
		"estimated_profit": estimated_profit,
	}, update_modified=False)

	return {
		"measurement_count": measurement_count,
		"item_cost": item_cost,
		"stitching_cost": stitching_cost,
		"total_cost": total_cost,
		"revenue": revenue,
		"estimated_profit": estimated_profit,
	}


@frappe.whitelist()
def process_sales_return(so_name, return_items, return_reason="",
                         create_credit_note=1, create_refund=0,
                         mode_of_payment="Cash"):
	"""Process a sales return against a Sales Order.
	Creates a Credit Note (return Sales Invoice) and optionally a refund Payment Entry."""
	if isinstance(return_items, str):
		return_items = frappe.parse_json(return_items)

	create_credit_note = frappe.utils.cint(create_credit_note)
	create_refund = frappe.utils.cint(create_refund)

	so = frappe.get_doc("Sales Order", so_name)
	result = {"credit_note": None, "return_dn": None, "refund": None}

	if not return_items:
		frappe.throw(_("No items selected for return"))

	# Find the original Sales Invoice linked to this SO
	original_si = frappe.db.get_value(
		"Sales Invoice Item",
		{"sales_order": so_name, "docstatus": 1},
		"parent",
	)
	original_si_update_stock = 0
	if original_si:
		original_si_update_stock = frappe.utils.cint(
			frappe.db.get_value("Sales Invoice", original_si, "update_stock")
		)

	# Find the original Delivery Note linked to this SO (used when the order
	# was completed with a separate DN instead of the invoice moving stock)
	original_dn = frappe.db.get_value(
		"Delivery Note Item",
		{"against_sales_order": so_name, "docstatus": 1},
		"parent",
	)

	# Create Credit Note (Return Sales Invoice)
	if create_credit_note:
		si = frappe.new_doc("Sales Invoice")
		si.customer = so.customer
		si.company = so.company
		si.is_return = 1
		if original_si:
			si.return_against = original_si
		si.set_posting_time = 1
		si.posting_date = frappe.utils.today()
		si.due_date = frappe.utils.today()
		si.currency = so.currency
		si.conversion_rate = so.conversion_rate
		# Only reverse stock through the invoice if the original invoice itself
		# moved stock. If delivery happened via a separate Delivery Note,
		# stock is reversed via a Return Delivery Note below instead —
		# ERPNext rejects update_stock=1 here otherwise ("items are not
		# delivered via <invoice>").
		si.update_stock = 1 if original_si_update_stock else 0

		total_return_amount = 0
		for ri in return_items:
			qty = frappe.utils.flt(ri.get("qty", 1))
			rate = frappe.utils.flt(ri.get("rate", 0))
			amount = qty * rate
			total_return_amount += amount
			si.append("items", {
				"item_code": ri["item_code"],
				"item_name": ri.get("item_name", ri["item_code"]),
				"qty": qty * -1,  # negative qty for return
				"rate": rate,
				"uom": frappe.db.get_value("Item", ri["item_code"], "stock_uom") or "Nos",
				"warehouse": so.items[0].warehouse if so.items else None,
				"sales_order": so_name,
				"so_detail": ri.get("so_detail"),
			})

		# Copy taxes from SO
		for tax in so.taxes:
			si.append("taxes", {
				"charge_type": tax.charge_type,
				"account_head": tax.account_head,
				"description": tax.description,
				"rate": tax.rate,
				"cost_center": tax.cost_center,
				"included_in_print_rate": tax.included_in_print_rate,
			})

		if return_reason:
			si.remarks = return_reason

		si.insert(ignore_permissions=True)
		si.submit()
		result["credit_note"] = si.name

	# Create Return Delivery Note when the order was delivered via a separate
	# DN (not the invoice) — this is what actually reverses the stock in that case.
	if create_credit_note and original_dn and not original_si_update_stock:
		dn = frappe.new_doc("Delivery Note")
		dn.customer = so.customer
		dn.company = so.company
		dn.is_return = 1
		dn.return_against = original_dn
		dn.set_posting_time = 1
		dn.posting_date = frappe.utils.today()
		dn.currency = so.currency
		dn.conversion_rate = so.conversion_rate

		for ri in return_items:
			qty = frappe.utils.flt(ri.get("qty", 1))
			dn.append("items", {
				"item_code": ri["item_code"],
				"item_name": ri.get("item_name", ri["item_code"]),
				"qty": qty * -1,
				"rate": frappe.utils.flt(ri.get("rate", 0)),
				"uom": frappe.db.get_value("Item", ri["item_code"], "stock_uom") or "Nos",
				"warehouse": so.items[0].warehouse if so.items else None,
				"against_sales_order": so_name,
				"so_detail": ri.get("so_detail"),
			})

		dn.insert(ignore_permissions=True)
		dn.submit()
		result["return_dn"] = dn.name

	# Create Refund Payment Entry
	if create_refund and result.get("credit_note"):
		refund_amount = abs(frappe.utils.flt(
			frappe.db.get_value("Sales Invoice", result["credit_note"], "grand_total")
		))

		if refund_amount > 0:
			company = so.company
			mop_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
			account = None
			for acc in mop_doc.accounts:
				if acc.company == company:
					account = acc.default_account
					break
			if not account:
				account = frappe.get_cached_value(
					"Company", company, "default_cash_account"
				) or frappe.get_cached_value("Company", company, "default_bank_account")

			pe = frappe.new_doc("Payment Entry")
			pe.payment_type = "Pay"
			pe.party_type = "Customer"
			pe.party = so.customer
			pe.company = company
			pe.mode_of_payment = mode_of_payment
			pe.paid_from = account
			pe.paid_to = frappe.get_cached_value("Company", company, "default_receivable_account")
			pe.paid_amount = refund_amount
			pe.received_amount = refund_amount
			pe.reference_no = result["credit_note"]
			pe.reference_date = frappe.utils.today()

			pe.append("references", {
				"reference_doctype": "Sales Invoice",
				"reference_name": result["credit_note"],
				"allocated_amount": refund_amount * -1,
			})

			pe.insert(ignore_permissions=True)
			pe.submit()
			result["refund"] = pe.name

	return result


@frappe.whitelist()
def get_previous_measurements(customer):
	"""Get the latest Tailoring Measurement for a customer to pre-fill a new one."""
	measurement_fields = [
		"name", "measurement_date", "measurements_json",
		"length", "shoulder", "sleeve_length",
		"loose_1", "loose_2", "bottom", "bottom_size",
		"sleeve_loose", "shoulder_alt", "sleeve_alt",
		"collar_style", "collar_type",
		"neck_style", "neck_type",
		"hip", "hip_type",
		"special_button", "thobe", "delivery_type",
	]

	latest = frappe.get_all(
		"Tailoring Measurement",
		filters={"customer": customer, "docstatus": ["!=", 2]},
		fields=measurement_fields,
		order_by="creation desc",
		limit_page_length=1,
	)

	if latest:
		return latest[0]
	return {}
