app_name = "asafat_tailoring"
app_title = "Asafat Tailoring"
app_publisher = "Asafat Sahran"
app_description = "Tailoring workflow for Asafat Sahran"
app_email = "dev@asafat.com"
app_license = "mit"

# Includes in <head>
app_include_css = ["/assets/asafat_tailoring/css/measurement.css"]
# DocType JS
doctype_js = {
	"Sales Order": "public/js/sales_order.js",
}

doctype_list_js = {
	"Sales Order": "public/js/sales_order_list.js",
}

# Installation
after_install = "asafat_tailoring.install.after_install"

# Fixtures
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "in", ["Sales Order", "Customer"]],
			["fieldname", "in", [
				"stitching_status", "advance_collected",
				"outstanding_amount", "measurement_count",
				"customer_phone", "custom_phone",
				"profit_loss_section", "item_cost", "stitching_cost",
				"total_cost", "profit_cb", "revenue", "estimated_profit",
			]],
		],
	},
	{
		"dt": "Print Format",
		"filters": [["module", "=", "Asafat Tailoring"]],
	},
	{
		"dt": "Property Setter",
		"filters": [
			["doc_type", "in", ["Sales Order", "Sales Invoice"]],
			["property", "=", "default_print_format"],
		],
	},
]

# Dashboard overrides
override_doctype_dashboards = {
	"Sales Order": "asafat_tailoring.overrides.sales_order_dashboard.get_data",
}

# Document Events
doc_events = {
	"Sales Order": {
		"on_submit": "asafat_tailoring.events.sales_order.on_submit",
	},
	"Payment Entry": {
		"on_submit": "asafat_tailoring.events.payment_entry.update_so_advance",
		"on_cancel": "asafat_tailoring.events.payment_entry.update_so_advance",
	},
}
