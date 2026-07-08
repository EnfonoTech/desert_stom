app_name = "desert_stom"
app_title = "Desert Stom"
app_publisher = "Desert Stom"
app_description = "Tailoring workflow for Desert Stom"
app_email = "dev@enfono.com"
app_license = "mit"

# Includes in <head>
app_include_css = ["/assets/desert_stom/css/measurement.css"]
# DocType JS
doctype_js = {
	"Sales Order": "public/js/sales_order.js",
}

doctype_list_js = {
	"Sales Order": "public/js/sales_order_list.js",
}

# Installation
after_install = "desert_stom.install.after_install"

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
		"filters": [["module", "=", "Desert Stom"]],
	},
	{
		"dt": "Property Setter",
		"filters": [
			["name", "in", [
				"Sales Order-main-default_print_format",
				"Sales Invoice-main-default_print_format",
				"Customer-main-search_fields",
				"Sales Order Item-uom-in_list_view",
			]],
		],
	},
	{
		"dt": "Garment Type",
	},
	{
		"dt": "Style Option",
	},
]

# Dashboard overrides
override_doctype_dashboards = {
	"Sales Order": "desert_stom.overrides.sales_order_dashboard.get_data",
}

# Document Events
doc_events = {
	"Sales Order": {
		"on_submit": "desert_stom.events.sales_order.on_submit",
	},
	"Payment Entry": {
		"on_submit": "desert_stom.events.payment_entry.update_so_advance",
		"on_cancel": "desert_stom.events.payment_entry.update_so_advance",
	},
}
