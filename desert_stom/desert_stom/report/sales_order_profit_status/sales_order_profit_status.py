import frappe
from frappe import _
from frappe.utils import flt


STITCHING_COST_PER_QTY = 35  # SAR per item qty


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 160,
		},
		{
			"label": _("Date"),
			"fieldname": "transaction_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Stitching Status"),
			"fieldname": "stitching_status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Item Cost"),
			"fieldname": "item_cost",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Stitching Cost"),
			"fieldname": "stitching_cost",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Total Cost"),
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Estimated Profit"),
			"fieldname": "estimated_profit",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Advance Collected"),
			"fieldname": "advance_collected",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Outstanding"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Measurements"),
			"fieldname": "measurement_count",
			"fieldtype": "Int",
			"width": 100,
		},
	]


def get_data(filters):
	conditions = "so.docstatus = 1"
	values = {}

	if filters.get("from_date"):
		conditions += " AND so.transaction_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND so.transaction_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	if filters.get("company"):
		conditions += " AND so.company = %(company)s"
		values["company"] = filters["company"]

	if filters.get("stitching_status"):
		conditions += " AND so.stitching_status = %(stitching_status)s"
		values["stitching_status"] = filters["stitching_status"]

	if filters.get("customer"):
		conditions += " AND so.customer = %(customer)s"
		values["customer"] = filters["customer"]

	orders = frappe.db.sql("""
		SELECT
			so.name AS sales_order,
			so.transaction_date,
			so.customer,
			so.customer_name,
			so.stitching_status,
			so.grand_total,
			so.advance_collected,
			so.outstanding_amount
		FROM `tabSales Order` so
		WHERE {conditions}
		ORDER BY so.transaction_date DESC, so.name
	""".format(conditions=conditions), values, as_dict=True)

	data = []
	for so in orders:
		# Calculate costs
		items = frappe.db.sql("""
			SELECT item_code, qty FROM `tabSales Order Item`
			WHERE parent = %s
		""", so["sales_order"], as_dict=True)

		item_cost = 0
		total_qty = 0
		for item in items:
			total_qty += flt(item.qty)
			valuation_rate = flt(
				frappe.db.get_value("Item", item.item_code, "valuation_rate")
			)
			item_cost += valuation_rate * flt(item.qty)

		stitching_cost = total_qty * STITCHING_COST_PER_QTY
		total_cost = item_cost + stitching_cost
		estimated_profit = flt(so["grand_total"]) - total_cost

		# Get measurement count
		measurement_count = frappe.db.count(
			"Tailoring Measurement",
			{"sales_order": so["sales_order"], "docstatus": ["!=", 2]},
		)

		data.append({
			"sales_order": so["sales_order"],
			"transaction_date": so["transaction_date"],
			"customer_name": so["customer_name"],
			"stitching_status": so["stitching_status"] or "",
			"grand_total": so["grand_total"],
			"item_cost": item_cost,
			"stitching_cost": stitching_cost,
			"total_cost": total_cost,
			"estimated_profit": estimated_profit,
			"advance_collected": flt(so["advance_collected"]),
			"outstanding_amount": flt(so["outstanding_amount"]),
			"measurement_count": measurement_count,
		})

	return data
