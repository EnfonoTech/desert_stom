import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Invoice"),
			"fieldname": "invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 150,
		},
		{
			"label": _("Invoice Amount"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Payment Entry"),
			"fieldname": "payment_entry",
			"fieldtype": "Link",
			"options": "Payment Entry",
			"width": 150,
		},
		{
			"label": _("Mode of Payment"),
			"fieldname": "mode_of_payment",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Collected Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Outstanding"),
			"fieldname": "outstanding",
			"fieldtype": "Currency",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = "si.docstatus = 1"
	values = {}

	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	if filters.get("company"):
		conditions += " AND si.company = %(company)s"
		values["company"] = filters["company"]

	# Get all submitted Sales Invoices in the date range
	invoices = frappe.db.sql("""
		SELECT
			si.posting_date,
			si.name AS invoice,
			si.customer,
			si.customer_name,
			si.grand_total,
			si.outstanding_amount,
			sii.sales_order
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSales Invoice Item` sii
			ON sii.parent = si.name AND sii.idx = 1
		WHERE {conditions}
		ORDER BY si.posting_date DESC, si.name
	""".format(conditions=conditions), values, as_dict=True)

	# Get Payment Entries in the date range
	pe_conditions = "pe.docstatus = 1"
	pe_values = {}

	if filters.get("from_date"):
		pe_conditions += " AND pe.posting_date >= %(from_date)s"
		pe_values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		pe_conditions += " AND pe.posting_date <= %(to_date)s"
		pe_values["to_date"] = filters["to_date"]

	if filters.get("company"):
		pe_conditions += " AND pe.company = %(company)s"
		pe_values["company"] = filters["company"]

	if filters.get("mode_of_payment"):
		pe_conditions += " AND pe.mode_of_payment = %(mode_of_payment)s"
		pe_values["mode_of_payment"] = filters["mode_of_payment"]

	payments = frappe.db.sql("""
		SELECT
			pe.posting_date,
			pe.name AS payment_entry,
			pe.party AS customer,
			pe.party_name AS customer_name,
			pe.paid_amount,
			pe.mode_of_payment,
			per.reference_doctype,
			per.reference_name
		FROM `tabPayment Entry` pe
		LEFT JOIN `tabPayment Entry Reference` per
			ON per.parent = pe.name AND per.idx = 1
		WHERE pe.payment_type = 'Receive'
			AND pe.party_type = 'Customer'
			AND {conditions}
		ORDER BY pe.posting_date DESC, pe.name
	""".format(conditions=pe_conditions), pe_values, as_dict=True)

	# Build payment lookup by invoice/SO
	payment_by_ref = {}
	standalone_payments = []
	for pe in payments:
		ref_name = pe.get("reference_name", "")
		ref_type = pe.get("reference_doctype", "")
		if ref_type == "Sales Invoice" and ref_name:
			payment_by_ref.setdefault(ref_name, []).append(pe)
		elif ref_type == "Sales Order" and ref_name:
			# Advance payment against SO
			standalone_payments.append(pe)
		else:
			standalone_payments.append(pe)

	data = []

	# Add invoice rows with linked payments
	for inv in invoices:
		linked_payments = payment_by_ref.pop(inv["invoice"], [])
		if linked_payments:
			for i, pe in enumerate(linked_payments):
				row = {
					"posting_date": inv["posting_date"] if i == 0 else "",
					"invoice": inv["invoice"] if i == 0 else "",
					"customer_name": inv["customer_name"] if i == 0 else "",
					"sales_order": inv.get("sales_order") or "" if i == 0 else "",
					"grand_total": inv["grand_total"] if i == 0 else 0,
					"payment_entry": pe["payment_entry"],
					"mode_of_payment": pe["mode_of_payment"],
					"paid_amount": flt(pe["paid_amount"]),
					"outstanding": flt(inv["outstanding_amount"]) if i == 0 else 0,
				}
				data.append(row)
		else:
			data.append({
				"posting_date": inv["posting_date"],
				"invoice": inv["invoice"],
				"customer_name": inv["customer_name"],
				"sales_order": inv.get("sales_order") or "",
				"grand_total": inv["grand_total"],
				"payment_entry": "",
				"mode_of_payment": "",
				"paid_amount": 0,
				"outstanding": flt(inv["outstanding_amount"]),
			})

	# Add advance/standalone payments (not linked to any invoice)
	for pe in standalone_payments:
		ref = pe.get("reference_name", "")
		data.append({
			"posting_date": pe["posting_date"],
			"invoice": "",
			"customer_name": pe["customer_name"],
			"sales_order": ref if pe.get("reference_doctype") == "Sales Order" else "",
			"grand_total": 0,
			"payment_entry": pe["payment_entry"],
			"mode_of_payment": pe["mode_of_payment"],
			"paid_amount": flt(pe["paid_amount"]),
			"outstanding": 0,
		})

	return data
