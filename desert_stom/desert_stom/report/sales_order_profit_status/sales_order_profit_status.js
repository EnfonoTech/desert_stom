frappe.query_reports["Sales Order Profit Status"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "stitching_status",
			label: __("Stitching Status"),
			fieldtype: "Select",
			options: "\nOrder\nMeasurement\nJob Order\nProcessing\nProcess Completed\nReady for Delivery\nDelivered",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "estimated_profit" && data) {
			if (data.estimated_profit < 0) {
				value = "<span style='color:red;font-weight:bold;'>" + value + "</span>";
			} else if (data.estimated_profit > 0) {
				value = "<span style='color:green;font-weight:bold;'>" + value + "</span>";
			}
		}
		if (column.fieldname === "stitching_status" && data) {
			var colors = {
				Order: "#3B82F6",
				Measurement: "#8B5CF6",
				"Job Order": "#F59E0B",
				Processing: "#EAB308",
				"Process Completed": "#06B6D4",
				"Ready for Delivery": "#10B981",
				Delivered: "#6B7280",
			};
			var color = colors[data.stitching_status] || "#6B7280";
			value = "<span style='color:" + color + ";font-weight:600;'>" + value + "</span>";
		}
		return value;
	},
};
