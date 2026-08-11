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
			["dt", "in", ["Sales Order", "Customer", "Tailoring Measurement"]],
			["fieldname", "in", [
				"stitching_status", "return_reason", "advance_collected",
				"outstanding_amount", "measurement_count",
				"customer_phone", "custom_phone",
				"profit_loss_section", "item_cost", "stitching_cost",
				"total_cost", "profit_cb", "revenue", "estimated_profit",
				"custom_pocket_style", "custom_cuff_type", "custom_stitching_type_",
				"custom_patty_model", "custom_patty_type",
				"custom_front_pocket_type", "custom_front_pocket_accessories_if_any",
				"custom_side_pocket_type_", "custom_side_pocket_accessories_if_any",
				"custom_kally_piece_", "custom_cuff_length",
				"custom_sleeve_loose_2", "custom_sleeve_loose_3", "custom_sleeve_loose_3_copy",
				"custom_collar_length", "custom_neck_width", "custom_patty_length",
				"custom_front_pocket_line_length", "custom_front_pocket_width",
				"custom_side_pocket_line_length_", "custom_side_pocket_length_",
				"custom_sleeves_col_break",
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
				"Tailoring Measurement-bottom_size-label",
				"Tailoring Measurement-bottom-label",
				"Tailoring Measurement-sleeve_loose-label",
				"Tailoring Measurement-main-field_order",
			]],
		],
	},
	{
		"dt": "Garment Type",
	},
	{
		"dt": "Style Option",
	}
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
