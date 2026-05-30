import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	create_custom_fields(get_custom_fields(), update=True)
	_cleanup_removed_fields()
	_setup_search_fields()
	_setup_stock_settings()
	_setup_extras_item_group()
	_setup_number_cards()


def get_custom_fields():
	return {
		"Customer": [
			{
				"fieldname": "custom_phone",
				"fieldtype": "Data",
				"label": "Phone",
				"options": "Phone",
				"insert_after": "customer_name",
				"allow_in_quick_entry": 1,
			},
		],
		"Sales Order": [
			{
				"fieldname": "customer_phone",
				"fieldtype": "Data",
				"label": "Customer Phone",
				"options": "Phone",
				"fetch_from": "customer.custom_phone",
				"fetch_if_empty": 1,
				"insert_after": "customer_name",
				"in_standard_filter": 1,
				"search_index": 1,
			},
			{
				"fieldname": "stitching_status",
				"fieldtype": "Select",
				"label": "Stitching Status",
				"options": "\nOrder\nMeasurement\nJob Order\nProcessing\nProcess Completed\nReady for Delivery\nDelivered",
				"default": "Order",
				"insert_after": "delivery_date",
				"allow_on_submit": 1,
				"translatable": 0,
			},
			{
				"fieldname": "advance_collected",
				"fieldtype": "Currency",
				"label": "Advance Collected",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "grand_total",
			},
			{
				"fieldname": "outstanding_amount",
				"fieldtype": "Currency",
				"label": "Outstanding Amount",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "advance_collected",
			},
			{
				"fieldname": "measurement_count",
				"fieldtype": "Int",
				"label": "Measurement Count",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "outstanding_amount",
			},
			{
				"fieldname": "profit_loss_section",
				"fieldtype": "Section Break",
				"label": "Profit & Loss (Reference)",
				"collapsible": 0,
				"insert_after": "measurement_count",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "item_cost",
				"fieldtype": "Currency",
				"label": "Item Cost",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "profit_loss_section",
				"description": "Total valuation cost of items",
			},
			{
				"fieldname": "stitching_cost",
				"fieldtype": "Currency",
				"label": "Stitching Cost",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "item_cost",
				"description": "35 SAR per item qty",
			},
			{
				"fieldname": "total_cost",
				"fieldtype": "Currency",
				"label": "Total Cost",
				"read_only": 1,
				"allow_on_submit": 1,
				"bold": 1,
				"insert_after": "stitching_cost",
			},
			{
				"fieldname": "profit_cb",
				"fieldtype": "Column Break",
				"insert_after": "total_cost",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "revenue",
				"fieldtype": "Currency",
				"label": "Revenue",
				"read_only": 1,
				"allow_on_submit": 1,
				"insert_after": "profit_cb",
				"description": "From linked Sales Invoice",
			},
			{
				"fieldname": "estimated_profit",
				"fieldtype": "Currency",
				"label": "Estimated Profit",
				"read_only": 1,
				"allow_on_submit": 1,
				"bold": 1,
				"insert_after": "revenue",
			},
		],
	}


def _cleanup_removed_fields():
	"""Remove custom fields that are no longer needed."""
	removed = [
		"Sales Order-book_number",
		"Sales Order-top_number",
		"Sales Order-stitching_unit",
	]
	for name in removed:
		if frappe.db.exists("Custom Field", name):
			frappe.delete_doc("Custom Field", name, force=True)
	frappe.db.commit()


def _setup_search_fields():
	"""Add phone number to search_fields for Sales Order and Customer
	so users can search by phone in list views and link fields."""
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	# Add customer_phone to Sales Order search_fields
	so_search = "status,transaction_date,customer,customer_name,customer_phone,territory,order_type,company"
	make_property_setter(
		"Sales Order", None, "search_fields", so_search, "Data", for_doctype=True
	)

	# Add custom_phone to Customer search_fields
	cust_search = "customer_group,territory,mobile_no,custom_phone,primary_address"
	make_property_setter(
		"Customer", None, "search_fields", cust_search, "Data", for_doctype=True
	)

	frappe.db.commit()


def _setup_stock_settings():
	"""Enable UOM filtering to only show UOMs defined in Item master."""
	frappe.db.set_single_value(
		"Stock Settings", "allow_uom_with_conversion_rate_defined_in_item", 1
	)
	frappe.db.commit()


def _setup_extras_item_group():
	"""Create the 'Extras' item group for add-on items."""
	if not frappe.db.exists("Item Group", "Extras"):
		doc = frappe.new_doc("Item Group")
		doc.item_group_name = "Extras"
		doc.parent_item_group = "All Item Groups"
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


def _setup_number_cards():
	"""Create Number Card documents for the workspace dashboard."""
	cards = [
		{
			"name": "Total Orders",
			"label": "Total Orders",
			"document_type": "Sales Order",
			"function": "Count",
			"filters_json": '[["Sales Order","docstatus","=",1]]',
			"color": "#2490EF",
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly",
		},
		{
			"name": "Orders Under Processing",
			"label": "Orders Under Processing",
			"document_type": "Sales Order",
			"function": "Count",
			"filters_json": '[["Sales Order","docstatus","=",1],["Sales Order","stitching_status","in",["Processing","Process Completed"]]]',
			"color": "#F5A623",
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly",
		},
		{
			"name": "Ready to Deliver",
			"label": "Ready to Deliver",
			"document_type": "Sales Order",
			"function": "Count",
			"filters_json": '[["Sales Order","docstatus","=",1],["Sales Order","stitching_status","=","Ready for Delivery"]]',
			"color": "#29CD42",
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly",
		},
		{
			"name": "Orders Completed",
			"label": "Orders Completed",
			"document_type": "Sales Order",
			"function": "Count",
			"filters_json": '[["Sales Order","docstatus","=",1],["Sales Order","stitching_status","=","Delivered"]]',
			"color": "#7B68EE",
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly",
		},
	]

	for card_data in cards:
		if not frappe.db.exists("Number Card", card_data["name"]):
			doc = frappe.new_doc("Number Card")
			doc.name = card_data["name"]
			doc.label = card_data["label"]
			doc.document_type = card_data["document_type"]
			doc.function = card_data["function"]
			doc.filters_json = card_data["filters_json"]
			doc.color = card_data.get("color")
			doc.show_percentage_stats = card_data.get("show_percentage_stats", 1)
			doc.stats_time_interval = card_data.get("stats_time_interval", "Monthly")
			doc.is_public = 1
			doc.owner = "Administrator"
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
