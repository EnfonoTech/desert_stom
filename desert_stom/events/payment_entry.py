import frappe
from frappe.utils import flt


def update_so_advance(doc, method):
	"""Recalculate advance_collected on linked Sales Orders
	whenever a Payment Entry is submitted or cancelled."""
	if doc.party_type != "Customer":
		return

	so_names = set()
	for ref in doc.references:
		if ref.reference_doctype == "Sales Order" and ref.reference_name:
			so_names.add(ref.reference_name)

	for so_name in so_names:
		_recalculate_advance(so_name)


def _recalculate_advance(so_name):
	"""Sum all submitted Payment Entry amounts allocated against this SO."""
	total_advance = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(per.allocated_amount), 0)
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE per.reference_doctype = 'Sales Order'
			AND per.reference_name = %s
			AND pe.docstatus = 1
			AND pe.party_type = 'Customer'
	""", so_name)[0][0])

	grand_total = flt(frappe.db.get_value("Sales Order", so_name, "grand_total"))

	frappe.db.set_value("Sales Order", so_name, {
		"advance_collected": total_advance,
		"outstanding_amount": grand_total - total_advance,
	}, update_modified=False)
