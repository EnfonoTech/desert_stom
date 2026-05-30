frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		// Hide standard fields not needed for tailoring
		frm.toggle_display("po_no", false);
		frm.toggle_display("po_date", false);
		frm.toggle_display("order_type", false);
		frm.toggle_display("accounting_dimensions_section", false);
		frm.toggle_display("currency_and_price_list", false);

		// Show phone number below customer field
		if (frm.doc.customer_phone) {
			$(frm.fields_dict.customer_phone.wrapper).find(".like-disabled-input, .control-value").css({
				"font-weight": "600",
				"color": "#2563EB",
			});
		}

		// Relocate selling_price_list above items table
		if (frm.fields_dict.selling_price_list && frm.fields_dict.items) {
			var $pl = $(frm.fields_dict.selling_price_list.wrapper);
			var $items = $(frm.fields_dict.items.wrapper);
			if (!$pl.closest(".price-list-relocated").length) {
				var $wrap = $('<div class="price-list-relocated" style="margin-bottom:10px;"></div>');
				$pl.detach().appendTo($wrap);
				$items.before($wrap);
				$pl.show();
			}
		}

		// Color indicator for stitching status
		const colors = {
			Order: "blue",
			Measurement: "purple",
			"Job Order": "orange",
			Processing: "yellow",
			"Process Completed": "light-blue",
			"Ready for Delivery": "green",
			Delivered: "darkgrey",
		};
		if (frm.doc.stitching_status) {
			frm.page.set_indicator(frm.doc.stitching_status, colors[frm.doc.stitching_status] || "gray");
		}

		// Remove unwanted Create options added by ERPNext core
		if (frm.doc.docstatus === 1) {
			setTimeout(() => {
				const unwanted = [
					"Pick List", "Work Order", "Material Request",
					"Request for Raw Materials", "Purchase Order", "Project",
				];
				unwanted.forEach((label) => {
					frm.page.remove_inner_button(__(label), __("Create"));
				});
			}, 500);
		}

		// Submitted SO actions
		if (frm.doc.docstatus === 1) {
			// Add Measurement button
			frm.add_custom_button(__("Add Measurement"), () => {
				show_measurement_dialog(frm);
			}, __("Measurements"));

			// Show measurement count and calculate profit/loss
			frappe.call({
				method: "desert_stom.api.get_so_stats",
				args: { so_name: frm.doc.name },
				async: false,
				callback(r) {
					if (r.message) {
						const s = r.message;
						// Update doc values (already persisted by API)
						frm.doc.measurement_count = s.measurement_count;
						frm.doc.item_cost = s.item_cost;
						frm.doc.stitching_cost = s.stitching_cost;
						frm.doc.total_cost = s.total_cost;
						frm.doc.revenue = s.revenue;
						frm.doc.estimated_profit = s.estimated_profit;
						frm.refresh_fields();
						// Clear dirty state (values already persisted by API)
						frm.doc.__unsaved = 0;
						frm.page.clear_indicator();
						// Restore stitching status indicator
						if (frm.doc.stitching_status) {
							frm.page.set_indicator(frm.doc.stitching_status, colors[frm.doc.stitching_status] || "gray");
						}

						// Color the profit field green/red
						setTimeout(() => {
							if (frm.fields_dict.estimated_profit) {
								$(frm.fields_dict.estimated_profit.wrapper)
									.find(".like-disabled-input, .control-value")
									.css({
										"font-weight": "700",
										"font-size": "14px",
										"color": s.estimated_profit >= 0 ? "#10B981" : "#EF4444",
									});
							}
						}, 300);
					}
				},
			});

			// Status transition buttons based on current status
			var st = frm.doc.stitching_status;

			// Manual status buttons (Processing, Process Completed, Ready for Delivery are manual)
			if (st === "Job Order") {
				frm.add_custom_button(__("Processing"), () => {
					update_stitching_status(frm, "Processing");
				}, __("Status"));
			}
			if (st === "Processing") {
				frm.add_custom_button(__("Process Completed"), () => {
					update_stitching_status(frm, "Process Completed");
				}, __("Status"));
			}
			if (st === "Process Completed") {
				frm.add_custom_button(__("Ready for Delivery"), () => {
					update_stitching_status(frm, "Ready for Delivery", true);
				}, __("Status"));
			}

			// Collect Advance button (before Job Order)
			if (["Order", "Measurement"].includes(st)) {
				frm.add_custom_button(__("Collect Advance"), () => {
					show_advance_dialog(frm);
				}, __("Payments"));
			}

			// Complete Order button (only when Ready for Delivery)
			if (st === "Ready for Delivery") {
				frm.add_custom_button(__("Complete Order"), () => {
					show_completion_dialog(frm);
				});
				frm.$wrapper
					.find(".btn-custom[data-label='Complete%20Order']")
					.addClass("btn-primary");
			}

			// Return button (only when Delivered and has Sales Invoice)
			if (st === "Delivered") {
				frm.add_custom_button(__("Sales Return"), () => {
					show_return_dialog(frm);
				});
			}
		}
	},
});


function show_measurement_dialog(frm) {
	// Build item checkbox fields — each SO row gets its own checkbox
	// even if the same item_code appears multiple times
	const item_fields = (frm.doc.items || []).map((item, idx) => ({
		fieldname: `item_${idx}`,
		fieldtype: "Check",
		label: `Row ${idx + 1}: ${item.item_code} — ${item.item_name || ""} (Qty: ${item.qty})`,
		default: 1,
	}));

	const d = new frappe.ui.Dialog({
		title: __("Create Measurement"),
		fields: [
			{
				fieldname: "items_section",
				fieldtype: "Section Break",
				label: __("Select Items for this Measurement"),
			},
			...item_fields,
			{
				fieldname: "previous_section",
				fieldtype: "Section Break",
				label: __("Previous Measurements"),
			},
			{
				fieldname: "copy_previous",
				fieldtype: "Check",
				label: __("Copy from latest measurement"),
				default: 0,
			},
			{
				fieldname: "previous_info",
				fieldtype: "HTML",
				options: '<p class="text-muted">Checking for previous measurements...</p>',
			},
		],
		primary_action_label: __("Create Measurement"),
		primary_action(values) {
			// Gather selected items (each SO row separately)
			const selected = [];
			(frm.doc.items || []).forEach((item, idx) => {
				if (values[`item_${idx}`]) {
					selected.push({
						item_code: item.item_code,
						item_name: item.item_name,
						qty: item.qty,
						so_detail: item.name,
					});
				}
			});
			if (!selected.length) {
				frappe.msgprint(__("Please select at least one item"));
				return;
			}

			// Collect previous measurement data if copy was checked
			var prev_data = null;
			if (values.copy_previous && d._previous_measurement) {
				prev_data = d._previous_measurement;
			}

			d.hide();

			// Only pass basic link/routing params via URL (these work reliably)
			frappe.new_doc("Tailoring Measurement", {
				sales_order: frm.doc.name,
				customer: frm.doc.customer,
				phone_no: frm.doc.customer_phone || "",
				promise_date: frm.doc.delivery_date,
				delivery_date: frm.doc.delivery_date,
			});

			// After routing, populate child table + copy previous measurements
			var _populate_done = false;
			var _populate = function() {
				if (_populate_done) return;
				if (cur_frm && cur_frm.doctype === "Tailoring Measurement" && cur_frm.is_new()) {
					_populate_done = true;

					// 1. Populate measurement_items child table
					selected.forEach((s) => {
						let row = cur_frm.add_child("measurement_items");
						row.item_code = s.item_code;
						row.item_name = s.item_name;
						row.qty = s.qty;
						row.sales_order_item = s.so_detail;
					});

					// 2. Build cloth_name options first so we can set cloth_name
					//    before copying previous measurements
					var _per_item_fields = [
						"length", "shoulder", "sleeve_length",
						"loose_1", "loose_2", "bottom", "bottom_size",
						"sleeve_loose", "shoulder_alt", "sleeve_alt",
						"collar_style", "collar_type",
						"neck_style", "neck_type",
						"hip", "hip_type", "special_button",
					];

					// Build options and auto-select first item
					var _name_count = {};
					selected.forEach((s) => {
						var n = s.item_name || s.item_code;
						_name_count[n] = (_name_count[n] || 0) + 1;
					});
					var _name_seen = {};
					var _options = [""];
					selected.forEach((s) => {
						var n = s.item_name || s.item_code;
						_name_seen[n] = (_name_seen[n] || 0) + 1;
						var label = _name_count[n] > 1 ? n + " #" + _name_seen[n] : n;
						_options.push(label);
					});

					// Set cloth_name to first item
					var first_item = _options[1] || "";
					cur_frm.doc.cloth_name = first_item;

					// 3. Copy previous measurement values
					if (prev_data) {
						// Set values on the form fields
						_per_item_fields.forEach((key) => {
							if (prev_data[key] !== null && prev_data[key] !== undefined && prev_data[key] !== "") {
								cur_frm.doc[key] = prev_data[key];
							}
						});
						// Also copy thobe and delivery_type
						if (prev_data.thobe) cur_frm.doc.thobe = prev_data.thobe;
						if (prev_data.delivery_type) cur_frm.doc.delivery_type = prev_data.delivery_type;

						// Save into measurements_json so load_from_json won't clear them
						// Store same values for ALL items (customer's measurements apply to all)
						var json_data = {};
						var item_vals = {};
						_per_item_fields.forEach((key) => {
							item_vals[key] = cur_frm.doc[key] || "";
						});
						_options.forEach((opt) => {
							if (opt) json_data[opt] = Object.assign({}, item_vals);
						});
						cur_frm.doc.measurements_json = JSON.stringify(json_data);
					}

					// Set _previous_cloth tracker before refresh
					cur_frm._previous_cloth = first_item;

					cur_frm.refresh_fields();
					// Trigger cloth_name options update after items are populated
					cur_frm.trigger("refresh");
				}
			};

			// Try multiple approaches for reliable first-load
			frappe.after_ajax(() => {
				setTimeout(_populate, 300);
				setTimeout(_populate, 800);
				setTimeout(_populate, 1500);
			});

			// Also listen for page change
			$(document).one("page-change", function() {
				setTimeout(_populate, 500);
			});
		},
	});

	// Check for previous customer measurements
	frappe.call({
		method: "desert_stom.api.get_previous_measurements",
		args: { customer: frm.doc.customer },
		callback(r) {
			if (r.message && r.message.name) {
				d._previous_measurement = r.message;
				d.fields_dict.previous_info.$wrapper.html(
					`<p class="text-muted">Found previous measurement:
					<a href="/app/tailoring-measurement/${r.message.name}" target="_blank">${r.message.name}</a>
					(${r.message.measurement_date || ""})</p>`,
				);
			} else {
				d.fields_dict.previous_info.$wrapper.html(
					'<p class="text-muted">No previous measurements found for this customer.</p>',
				);
				d.set_df_property("copy_previous", "hidden", 1);
			}
		},
	});

	d.show();
}


function show_advance_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Collect Advance Payment"),
		fields: [
			{
				fieldname: "amount",
				fieldtype: "Currency",
				label: __("Amount"),
				reqd: 1,
			},
			{
				fieldname: "mode_of_payment",
				fieldtype: "Link",
				label: __("Mode of Payment"),
				options: "Mode of Payment",
				reqd: 1,
				default: "Cash",
			},
			{
				fieldname: "reference_no",
				fieldtype: "Data",
				label: __("Reference No"),
			},
		],
		primary_action_label: __("Create Payment"),
		primary_action(values) {
			frappe.call({
				method: "desert_stom.api.create_advance_payment",
				args: {
					so_name: frm.doc.name,
					amount: values.amount,
					mode_of_payment: values.mode_of_payment,
					reference_no: values.reference_no || "",
				},
				callback(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Payment Entry {0} created", [r.message]),
							indicator: "green",
						});
						d.hide();
						frm.reload_doc();
					}
				},
			});
		},
	});
	d.show();
}


function show_completion_dialog(frm) {
	// Build item checkboxes
	const item_fields = (frm.doc.items || []).map((item, idx) => ({
		fieldname: `item_${idx}`,
		fieldtype: "Check",
		label: `${item.item_name || item.item_code} (Qty: ${item.qty})`,
		default: 1,
	}));

	const d = new frappe.ui.Dialog({
		title: __("Complete Order"),
		size: "large",
		fields: [
			{
				fieldname: "mode_section",
				fieldtype: "Section Break",
				label: __("Billing Mode"),
			},
			{
				fieldname: "billing_mode",
				fieldtype: "Select",
				label: __("Mode"),
				options: "Full Billing\nInvoice Only\nDelivery Only\nPayment Only",
				default: "Full Billing",
				reqd: 1,
				onchange() {
					const mode = d.get_value("billing_mode");
					d.set_value("create_si", mode === "Full Billing" || mode === "Invoice Only" ? 1 : 0);
					d.set_value("create_pe", mode === "Full Billing" || mode === "Payment Only" ? 1 : 0);
					d.set_value("create_dn", mode === "Full Billing" || mode === "Delivery Only" ? 1 : 0);
				},
			},
			{
				fieldname: "items_section",
				fieldtype: "Section Break",
				label: __("Items"),
			},
			...item_fields,
			{
				fieldname: "discount_section",
				fieldtype: "Section Break",
				label: __("Discount"),
			},
			{
				fieldname: "discount_type",
				fieldtype: "Select",
				label: __("Discount Type"),
				options: "None\nPercentage\nAmount",
				default: "None",
				onchange() {
					const dtype = d.get_value("discount_type");
					d.set_df_property("discount_percentage", "hidden", dtype !== "Percentage");
					d.set_df_property("discount_amount", "hidden", dtype !== "Amount");
					// Recalculate payment amount
					recalc_payment();
				},
			},
			{
				fieldname: "discount_percentage",
				fieldtype: "Float",
				label: __("Discount (%)"),
				default: 0,
				hidden: 1,
				onchange() { recalc_payment(); },
			},
			{
				fieldname: "cb_disc",
				fieldtype: "Column Break",
			},
			{
				fieldname: "discount_amount",
				fieldtype: "Currency",
				label: __("Discount Amount"),
				default: 0,
				hidden: 1,
				onchange() { recalc_payment(); },
			},
			{
				fieldname: "payment_section",
				fieldtype: "Section Break",
				label: __("Payment"),
			},
			{
				fieldname: "total_amount",
				fieldtype: "Currency",
				label: __("Total Amount"),
				default: frm.doc.grand_total,
				read_only: 1,
			},
			{
				fieldname: "advance_paid",
				fieldtype: "Currency",
				label: __("Advance Paid"),
				default: frm.doc.advance_collected || 0,
				read_only: 1,
			},
			{
				fieldname: "cb_pay",
				fieldtype: "Column Break",
			},
			{
				fieldname: "payment_amount",
				fieldtype: "Currency",
				label: __("Payment Amount Now"),
				default: (frm.doc.grand_total || 0) - (frm.doc.advance_collected || 0),
			},
			{
				fieldname: "mode_of_payment",
				fieldtype: "Link",
				label: __("Mode of Payment"),
				options: "Mode of Payment",
				default: "Cash",
			},
			{
				fieldname: "options_section",
				fieldtype: "Section Break",
				label: __("Document Options"),
			},
			{
				fieldname: "create_si",
				fieldtype: "Check",
				label: __("Create Sales Invoice"),
				default: 1,
			},
			{
				fieldname: "create_pe",
				fieldtype: "Check",
				label: __("Create Payment Entry"),
				default: 1,
			},
			{
				fieldname: "create_dn",
				fieldtype: "Check",
				label: __("Create Delivery Note"),
				default: 1,
			},
			{
				fieldname: "cb_opt",
				fieldtype: "Column Break",
			},
			{
				fieldname: "print_after",
				fieldtype: "Select",
				label: __("Print After Create"),
				options: "None\nInvoice\nDelivery Note\nBoth",
				default: "Invoice",
			},
		],
		primary_action_label: __("Complete"),
		primary_action(values) {
			// Collect selected item indices
			const selected_items = [];
			(frm.doc.items || []).forEach((item, idx) => {
				if (values[`item_${idx}`]) {
					selected_items.push(item.name);
				}
			});

			frappe.call({
				method: "desert_stom.api.complete_order",
				args: {
					so_name: frm.doc.name,
					values: {
						selected_items: selected_items,
						payment_amount: values.payment_amount || 0,
						mode_of_payment: values.mode_of_payment,
						create_si: values.create_si,
						create_pe: values.create_pe,
						create_dn: values.create_dn,
						print_after: values.print_after,
						discount_type: values.discount_type || "None",
						discount_percentage: values.discount_percentage || 0,
						discount_amount: values.discount_amount || 0,
					},
				},
				freeze: true,
				freeze_message: __("Creating documents..."),
				callback(r) {
					if (r.message) {
						let msg_parts = [];
						if (r.message.si) msg_parts.push(__("Sales Invoice: {0}", [r.message.si]));
						if (r.message.pe) msg_parts.push(__("Payment Entry: {0}", [r.message.pe]));
						if (r.message.dn) msg_parts.push(__("Delivery Note: {0}", [r.message.dn]));

						frappe.msgprint({
							title: __("Order Completed"),
							indicator: "green",
							message: msg_parts.join("<br>"),
						});
						d.hide();
						frm.reload_doc();

						// Handle print after create
						if (values.print_after && values.print_after !== "None") {
							if (
								(values.print_after === "Invoice" || values.print_after === "Both") &&
								r.message.si
							) {
								const print_url = frappe.urllib.get_full_url(
									"/printview?doctype=Sales%20Invoice&name=" + encodeURIComponent(r.message.si) + "&format=Tailoring%20Invoice"
								);
								window.open(print_url, "_blank");
							}
							if (
								(values.print_after === "Delivery Note" || values.print_after === "Both") &&
								r.message.dn
							) {
								const print_url = frappe.urllib.get_full_url(
									"/printview?doctype=Delivery%20Note&name=" + encodeURIComponent(r.message.dn) + "&format=Delivery%20Slip"
								);
								window.open(print_url, "_blank");
							}
						}
					}
				},
			});
		},
	});

	// Helper to recalculate payment amount when discount changes
	function recalc_payment() {
		const grand = frm.doc.grand_total || 0;
		const advance = frm.doc.advance_collected || 0;
		const dtype = d.get_value("discount_type");
		let disc = 0;
		if (dtype === "Percentage") {
			disc = grand * (d.get_value("discount_percentage") || 0) / 100;
		} else if (dtype === "Amount") {
			disc = d.get_value("discount_amount") || 0;
		}
		const payable = Math.max(0, grand - disc - advance);
		d.set_value("total_amount", grand - disc);
		d.set_value("payment_amount", payable);
	}

	d.show();
}


function update_stitching_status(frm, new_status, send_whatsapp) {
	frm.set_value("stitching_status", new_status);
	frm.save("Update").then(() => {
		frappe.show_alert({
			message: __("Status updated to {0}", [new_status]),
			indicator: "green",
		});
		if (send_whatsapp) {
			send_status_whatsapp(frm, new_status);
		}
	});
}


function send_status_whatsapp(frm, status) {
	var phone = frm.doc.customer_phone;
	if (!phone) {
		frappe.msgprint(__("No phone number found for this customer. WhatsApp message not sent."));
		return;
	}

	// Clean phone number (remove spaces, dashes)
	phone = phone.replace(/[\s\-()]/g, "");
	// Add country code if not present
	if (!phone.startsWith("+") && !phone.startsWith("00")) {
		phone = "966" + phone.replace(/^0/, "");
	}
	phone = phone.replace(/^00/, "").replace(/^\+/, "");

	var customer = frm.doc.customer_name || frm.doc.customer;
	var so = frm.doc.name;
	var msg = "";

	if (status === "Job Order") {
		msg = "Dear " + customer + ",\n\n"
			+ "Thank you for your order (" + so + "). "
			+ "We have received your advance payment and your order is now confirmed.\n"
			+ "We will notify you once your garment is ready.\n\n"
			+ "Desert Stom Tailoring";
	} else if (status === "Ready for Delivery") {
		msg = "Dear " + customer + ",\n\n"
			+ "Your order (" + so + ") is ready for delivery! "
			+ "Please visit our shop to collect your garment.\n\n"
			+ "Desert Stom Tailoring";
	}

	if (msg) {
		var url = "https://wa.me/" + phone + "?text=" + encodeURIComponent(msg);
		window.open(url, "_blank");
	}
}


function show_return_dialog(frm) {
	// Build item checkboxes with qty for return
	const item_fields = [];
	(frm.doc.items || []).forEach((item, idx) => {
		item_fields.push({
			fieldname: `return_item_${idx}`,
			fieldtype: "Check",
			label: `${item.item_name || item.item_code} (Qty: ${item.qty}, Rate: ${item.rate})`,
			default: 1,
		});
		item_fields.push({
			fieldname: `return_qty_${idx}`,
			fieldtype: "Float",
			label: __("Return Qty"),
			default: item.qty,
			depends_on: `eval:doc.return_item_${idx}`,
		});
		if (idx < (frm.doc.items || []).length - 1) {
			item_fields.push({ fieldtype: "Section Break" });
		}
	});

	const d = new frappe.ui.Dialog({
		title: __("Sales Return"),
		fields: [
			{
				fieldname: "return_reason",
				fieldtype: "Small Text",
				label: __("Return Reason"),
			},
			{
				fieldname: "items_section",
				fieldtype: "Section Break",
				label: __("Select Items to Return"),
			},
			...item_fields,
			{
				fieldname: "refund_section",
				fieldtype: "Section Break",
				label: __("Refund"),
			},
			{
				fieldname: "create_credit_note",
				fieldtype: "Check",
				label: __("Create Credit Note"),
				default: 1,
			},
			{
				fieldname: "create_refund",
				fieldtype: "Check",
				label: __("Create Refund Payment"),
				default: 0,
			},
			{
				fieldname: "mode_of_payment",
				fieldtype: "Link",
				label: __("Mode of Payment"),
				options: "Mode of Payment",
				default: "Cash",
				depends_on: "eval:doc.create_refund",
			},
		],
		primary_action_label: __("Process Return"),
		primary_action(values) {
			// Collect selected return items
			const return_items = [];
			(frm.doc.items || []).forEach((item, idx) => {
				if (values[`return_item_${idx}`]) {
					return_items.push({
						item_code: item.item_code,
						item_name: item.item_name,
						qty: values[`return_qty_${idx}`] || item.qty,
						rate: item.rate,
						so_detail: item.name,
					});
				}
			});

			if (!return_items.length) {
				frappe.msgprint(__("Please select at least one item to return"));
				return;
			}

			frappe.call({
				method: "desert_stom.api.process_sales_return",
				args: {
					so_name: frm.doc.name,
					return_items: return_items,
					return_reason: values.return_reason || "",
					create_credit_note: values.create_credit_note,
					create_refund: values.create_refund,
					mode_of_payment: values.mode_of_payment || "Cash",
				},
				freeze: true,
				freeze_message: __("Processing return..."),
				callback(r) {
					if (r.message) {
						let msg_parts = [];
						if (r.message.credit_note) {
							msg_parts.push(__("Credit Note: {0}", [r.message.credit_note]));
						}
						if (r.message.refund) {
							msg_parts.push(__("Refund Payment: {0}", [r.message.refund]));
						}
						frappe.msgprint({
							title: __("Return Processed"),
							indicator: "green",
							message: msg_parts.join("<br>"),
						});
						d.hide();
						frm.reload_doc();
					}
				},
			});
		},
	});

	d.show();
}
