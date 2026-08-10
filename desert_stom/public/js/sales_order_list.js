// Override Sales Order list view to show Stitching Status
// Loaded via doctype_list_js hook (after ERPNext's list settings)

var settings = frappe.listview_settings["Sales Order"];
if (settings) {
	// Add stitching_status to fetched fields
	settings.add_fields = settings.add_fields || [];
	if (!settings.add_fields.includes("stitching_status")) {
		settings.add_fields.push("stitching_status");
	}
	if (!settings.add_fields.includes("return_reason")) {
		settings.add_fields.push("return_reason");
	}

	// Wrap ERPNext's get_indicator
	var _orig = settings.get_indicator;

	settings.get_indicator = function (doc) {
		if (doc.docstatus === 1 && doc.stitching_status) {
			var colors = {
				Order: "blue",
				Measurement: "purple",
				"Job Order": "orange",
				Processing: "yellow",
				"Process Completed": "light-blue",
				"Ready for Delivery": "green",
				Delivered: "darkgrey",
			};
			var label = doc.stitching_status;
			if (doc.return_reason && ["Job Order", "Processing"].includes(doc.stitching_status)) {
				label = doc.stitching_status + " (Returned)";
			}
			return [
				__(label),
				colors[doc.stitching_status] || "gray",
				"stitching_status,=," + doc.stitching_status,
			];
		}
		if (_orig) {
			return _orig(doc);
		}
	};
}
