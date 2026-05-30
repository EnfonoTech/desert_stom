/* ═══════════════════════════════════════════════════════════
   Asafat Tailoring — Tailoring Measurement Form
   Per-item measurements with cloth_name switcher
   ═══════════════════════════════════════════════════════════ */

var PER_ITEM_FIELDS = [
	"length", "shoulder", "sleeve_length", "loose_1", "loose_2",
	"bottom", "bottom_size", "sleeve_loose", "shoulder_alt", "sleeve_alt",
	"collar_style", "collar_type", "neck_style", "neck_type",
	"hip", "hip_type", "special_button"
];


frappe.ui.form.on("Tailoring Measurement", {
	refresh(frm) {
		$(frm.wrapper).attr("data-doctype", "Tailoring Measurement");
		$(frm.wrapper).find(".form-layout").attr("data-doctype", "Tailoring Measurement");

		// Force reload latest CSS (bust browser cache)
		var oldCss = document.querySelector('link[href*="measurement.css"]');
		if (oldCss) {
			var freshHref = '/assets/asafat_tailoring/css/measurement.css?v=' + (frappe.boot.build_version || Date.now());
			if (oldCss.href.indexOf(freshHref) === -1) {
				oldCss.href = freshHref;
			}
		}

		// Filter extra items to only show "Extras" item group
		frm.set_query("item_code", "extra_items", function() {
			return { filters: { item_group: "Extras" } };
		});

		// Clean up old elements
		$(".sticky-action-bar, .meas-right-panel, #sticky-action-bar, .visual-option-grid").remove();
		$(".meas-summary-banner, .thobe-diagram-card, #meas-progress-wrap, .meas-item-indicator").remove();

		inject_badges(frm);
		inject_summary_banner(frm);
		inject_thobe_diagram(frm);
		inject_progress_bar(frm);
		update_progress(frm);
		update_cloth_name_options(frm);
		setup_visual_popups(frm);

		// Auto-select first cloth if none selected
		if (!frm.doc.cloth_name && frm.doc.measurement_items && frm.doc.measurement_items.length) {
			var firstName = frm.doc.measurement_items[0].item_name || frm.doc.measurement_items[0].item_code;
			if (firstName) {
				frm.set_value("cloth_name", firstName);
			}
		}

		// Load current item's measurements from JSON
		load_from_json(frm);
		frm._previous_cloth = frm.doc.cloth_name || "";

		// Show item indicator
		inject_item_indicator(frm);
	},

	before_save(frm) {
		save_current_to_json(frm);
	},

	cloth_name(frm) {
		// Save previous item's measurements
		save_current_to_json(frm);

		// Load new item's measurements
		load_from_json(frm);

		// Update tracker
		frm._previous_cloth = frm.doc.cloth_name || "";

		// Refresh visual elements
		update_progress(frm);
		update_diagram_labels(frm);
		inject_item_indicator(frm);
	},

	sales_order(frm) {
		if (frm.doc.sales_order) {
			frappe.db.get_value("Sales Order", frm.doc.sales_order,
				["customer_phone", "delivery_date"], function(r) {
				if (r) {
					if (r.customer_phone && !frm.doc.phone_no) {
						frm.set_value("phone_no", r.customer_phone);
					}
					if (r.delivery_date) {
						if (!frm.doc.promise_date) frm.set_value("promise_date", r.delivery_date);
						if (!frm.doc.delivery_date) frm.set_value("delivery_date", r.delivery_date);
					}
				}
			});
		}
	},

	length(frm) { update_progress(frm); update_diagram_labels(frm); },
	shoulder(frm) { update_progress(frm); update_diagram_labels(frm); },
	sleeve_length(frm) { update_progress(frm); update_diagram_labels(frm); },
	loose_1(frm) { update_progress(frm); update_diagram_labels(frm); },
	loose_2(frm) { update_progress(frm); update_diagram_labels(frm); },
	collar_style(frm) { update_progress(frm); },
	special_button(frm) { update_progress(frm); },
	bottom(frm) { update_progress(frm); update_diagram_labels(frm); },
	sleeve_loose(frm) { update_progress(frm); },
});


/* ═══════════════════════════════════════════════════════════
   PER-ITEM MEASUREMENT SWITCHER (JSON storage)
   ═══════════════════════════════════════════════════════════ */

function save_current_to_json(frm) {
	var key = frm._previous_cloth || frm.doc.cloth_name;
	if (!key) return;

	var data;
	try {
		data = JSON.parse(frm.doc.measurements_json || "{}");
	} catch(e) {
		data = {};
	}

	var item_data = {};
	for (var i = 0; i < PER_ITEM_FIELDS.length; i++) {
		item_data[PER_ITEM_FIELDS[i]] = frm.doc[PER_ITEM_FIELDS[i]] || "";
	}
	data[key] = item_data;
	frm.doc.measurements_json = JSON.stringify(data);
}

function load_from_json(frm) {
	var key = frm.doc.cloth_name;
	if (!key) return;

	var data;
	try {
		data = JSON.parse(frm.doc.measurements_json || "{}");
	} catch(e) {
		data = {};
	}

	var item_data = data[key] || {};

	for (var i = 0; i < PER_ITEM_FIELDS.length; i++) {
		var field = PER_ITEM_FIELDS[i];
		var val = item_data[field];
		if (val !== undefined && val !== null) {
			frm.doc[field] = val;
		} else {
			var df = frm.fields_dict[field] && frm.fields_dict[field].df;
			if (df && (df.fieldtype === "Float" || df.fieldtype === "Int" || df.fieldtype === "Currency")) {
				frm.doc[field] = 0;
			} else {
				frm.doc[field] = "";
			}
		}
	}
	frm.refresh_fields();
}


/* ═══════════════════════════════════════════════════════════
   ITEM INDICATOR — shows which item is being edited
   ═══════════════════════════════════════════════════════════ */

function inject_item_indicator(frm) {
	$(".meas-item-indicator").remove();

	if (!frm.doc.cloth_name) return;

	var opts = (frm.fields_dict.cloth_name.df.options || "").split("\n").filter(Boolean);
	var idx = opts.indexOf(frm.doc.cloth_name) + 1;
	var total = opts.length;

	if (total <= 0) return;

	var label = 'Editing: <strong>' + frm.doc.cloth_name + '</strong>';
	if (total > 1) {
		label += ' <span class="mii-count">(' + idx + ' of ' + total + ')</span>';
	}

	// Show "Copy from first item" button if this is not the first item
	var copy_btn = "";
	if (total > 1 && idx > 1) {
		copy_btn = ' <button class="btn btn-xs btn-default mii-copy-btn" style="margin-left:12px;">'
			+ '<i class="fa fa-copy"></i> Copy from ' + opts[0]
			+ '</button>';
	}

	var $section = $(frm.fields_dict.measurements_section.wrapper);
	$section.find(".section-head").after(
		'<div class="meas-item-indicator">' + label + copy_btn + '</div>'
	);

	// Bind copy button
	$section.find(".mii-copy-btn").on("click", function() {
		_copy_from_first_item(frm, opts[0]);
	});
}

function _copy_from_first_item(frm, first_key) {
	var data;
	try {
		data = JSON.parse(frm.doc.measurements_json || "{}");
	} catch(e) {
		data = {};
	}

	var source = data[first_key];
	if (!source || !Object.keys(source).length) {
		frappe.show_alert({ message: __("No measurements saved for {0} yet.", [first_key]), indicator: "orange" }, 3);
		return;
	}

	for (var i = 0; i < PER_ITEM_FIELDS.length; i++) {
		var field = PER_ITEM_FIELDS[i];
		var val = source[field];
		if (val !== undefined && val !== null && val !== "") {
			frm.doc[field] = val;
		}
	}
	frm.refresh_fields();
	frm.dirty();
	frappe.show_alert({ message: __("Measurements copied from {0}. Adjust as needed.", [first_key]), indicator: "blue" }, 4);
}


/* ═══ MEASUREMENT ITEMS CHILD TABLE EVENTS ═══ */
frappe.ui.form.on("Measurement Item", {
	item_code(frm) { update_cloth_name_options(frm); },
	measurement_items_add(frm) { update_cloth_name_options(frm); },
	measurement_items_remove(frm) { update_cloth_name_options(frm); },
});

function update_cloth_name_options(frm) {
	var options = [""];
	var name_count = {};
	var rows = frm.doc.measurement_items || [];

	// First pass: count occurrences of each item name
	rows.forEach(function(row) {
		var name = row.item_name || row.item_code;
		if (name) {
			name_count[name] = (name_count[name] || 0) + 1;
		}
	});

	// Second pass: build unique labels (append #N for duplicates)
	var name_seen = {};
	rows.forEach(function(row) {
		var name = row.item_name || row.item_code;
		if (!name) return;
		name_seen[name] = (name_seen[name] || 0) + 1;

		var label;
		if (name_count[name] > 1) {
			label = name + " #" + name_seen[name];
		} else {
			label = name;
		}
		if (options.indexOf(label) === -1) {
			options.push(label);
		}
	});

	frm.set_df_property("cloth_name", "options", options.join("\n"));
}


/* ═══ BADGES ═══ */
function inject_badges(frm) {
	$(frm.page.main).find(".meas-badges").remove();
	var badges = [];
	if (frm.doc.delivery_type === "Urgent") badges.push('<span class="badge-urgent">Urgent</span>');
	if (frm.doc.thobe) badges.push('<span class="badge-saudi">' + frm.doc.thobe + '</span>');
	if (badges.length) {
		$(frm.page.main).find(".page-head .title-area")
			.append('<div class="meas-badges" style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;">' + badges.join("") + '</div>');
	}
}


/* ═══ SUMMARY BANNER — full width, before first section ═══ */
function inject_summary_banner(frm) {
	$(".meas-summary-banner").remove();

	var $formLayout = $(frm.wrapper).find(".form-layout");
	var $firstSection = $formLayout.find(".form-section").first();

	var html = '<div class="meas-summary-banner">'
		+ '<div class="msb-section"><div class="msb-label">Invoice</div><div class="msb-value mono">' + (frm.doc.name || "-") + '</div></div>'
		+ '<div class="msb-divider"></div>'
		+ '<div class="msb-section"><div class="msb-label">Customer</div><div class="msb-value">' + (frm.doc.customer_name || "-") + '</div></div>'
		+ '<div class="msb-divider"></div>'
		+ '<div class="msb-section"><div class="msb-label">Phone</div><div class="msb-value mono">' + (frm.doc.phone_no||"-") + '</div></div>'
		+ '<div class="msb-divider"></div>'
		+ '<div class="msb-section"><div class="msb-label">Length</div><div class="msb-value highlight">' + (frm.doc.length||"-") + '</div></div>'
		+ '<div class="msb-section"><div class="msb-label">Shoulder</div><div class="msb-value">' + (frm.doc.shoulder||"-") + '</div></div>'
		+ '<div class="msb-section"><div class="msb-label">Sleeve</div><div class="msb-value highlight">' + (frm.doc.sleeve_length||"-") + '</div></div>'
		+ '</div>';

	if ($firstSection.length) {
		$firstSection.before(html);
	}
}


/* ═══ THOBE DIAGRAM — injected into the right column of the header section ═══ */
function inject_thobe_diagram(frm) {
	$(".thobe-diagram-card").remove();

	var svg = '<svg viewBox="0 0 240 360" xmlns="http://www.w3.org/2000/svg">'
		+ '<path d="M95 20 C95 10,145 10,145 20 L148 30 L190 50 L210 95 L195 100 L175 65 L175 320 C175 335,120 340,120 340 C120 340,65 335,65 320 L65 65 L45 100 L30 95 L50 50 L92 30Z" fill="#EFF6FF" stroke="#2563EB" stroke-width="1.5" stroke-linejoin="round"/>'
		+ '<ellipse cx="120" cy="22" rx="22" ry="8" fill="none" stroke="#2563EB" stroke-width="1" stroke-dasharray="4,2"/>'
		+ '<line x1="120" y1="30" x2="120" y2="200" stroke="#2563EB" stroke-width="0.5" stroke-dasharray="3,3" opacity="0.3"/>'
		+ '<rect x="90" y="110" width="22" height="18" rx="2" fill="none" stroke="#2563EB" stroke-width="0.8" opacity="0.4"/>'
		+ '<line x1="185" y1="22" x2="185" y2="330" stroke="#DC2626" stroke-width="1"/><line x1="180" y1="22" x2="190" y2="22" stroke="#DC2626" stroke-width="0.8"/><line x1="180" y1="330" x2="190" y2="330" stroke="#DC2626" stroke-width="0.8"/><text x="193" y="180" fill="#DC2626" font-size="8" font-weight="600">L</text>'
		+ '<line x1="65" y1="52" x2="175" y2="52" stroke="#2563EB" stroke-width="1"/><line x1="65" y1="48" x2="65" y2="56" stroke="#2563EB" stroke-width="0.8"/><line x1="175" y1="48" x2="175" y2="56" stroke="#2563EB" stroke-width="0.8"/><text x="108" y="48" fill="#2563EB" font-size="8" font-weight="600">S</text>'
		+ '<line x1="32" y1="95" x2="65" y2="62" stroke="#D97706" stroke-width="1"/><text x="22" y="108" fill="#D97706" font-size="8" font-weight="600">SL</text>'
		+ '<line x1="65" y1="100" x2="175" y2="100" stroke="#7C3AED" stroke-width="0.8" stroke-dasharray="4,2"/><text x="100" y="96" fill="#7C3AED" font-size="7" font-weight="600">L1</text>'
		+ '<line x1="65" y1="220" x2="175" y2="220" stroke="#059669" stroke-width="0.8" stroke-dasharray="4,2"/><text x="100" y="216" fill="#059669" font-size="7" font-weight="600">L2</text>'
		+ '<line x1="65" y1="325" x2="175" y2="325" stroke="#6B7280" stroke-width="0.8" stroke-dasharray="4,2"/><text x="105" y="338" fill="#6B7280" font-size="7" font-weight="600">B</text>'
		+ '</svg>';

	var diagramHtml = '<div class="thobe-diagram-card">'
		+ '<div class="diagram-title">Kathoora Measurements</div>' + svg
		+ '<div class="diagram-labels">'
		+ '<div class="dlbl"><span class="dot" style="background:#DC2626"></span>Length<span class="dval" id="dlbl-length">'+(frm.doc.length||"-")+'</span></div>'
		+ '<div class="dlbl"><span class="dot" style="background:#2563EB"></span>Shoulder<span class="dval" id="dlbl-shoulder">'+(frm.doc.shoulder||"-")+'</span></div>'
		+ '<div class="dlbl"><span class="dot" style="background:#D97706"></span>Sleeve<span class="dval" id="dlbl-sleeve">'+(frm.doc.sleeve_length||"-")+'</span></div>'
		+ '<div class="dlbl"><span class="dot" style="background:#7C3AED"></span>Loose 1<span class="dval" id="dlbl-loose1">'+(frm.doc.loose_1||"-")+'</span></div>'
		+ '<div class="dlbl"><span class="dot" style="background:#059669"></span>Loose 2<span class="dval" id="dlbl-loose2">'+(frm.doc.loose_2||"-")+'</span></div>'
		+ '<div class="dlbl"><span class="dot" style="background:#6B7280"></span>Bottom<span class="dval" id="dlbl-bottom">'+(frm.doc.bottom||"-")+'</span></div>'
		+ '</div></div>';

	// Insert into the 3rd column of the header section, after delivery_date
	var $deliveryDate = $(frm.fields_dict.delivery_date.wrapper);
	if ($deliveryDate.length) {
		$deliveryDate.after(diagramHtml);
	}
}

function update_diagram_labels(frm) {
	var m = { "dlbl-length": frm.doc.length, "dlbl-shoulder": frm.doc.shoulder, "dlbl-sleeve": frm.doc.sleeve_length,
		"dlbl-loose1": frm.doc.loose_1, "dlbl-loose2": frm.doc.loose_2, "dlbl-bottom": frm.doc.bottom };
	for (var id in m) { var el = document.getElementById(id); if (el) el.textContent = m[id] || "-"; }
}


/* ═══ PROGRESS BAR — compact, after the summary banner ═══ */
function inject_progress_bar(frm) {
	if (document.getElementById("meas-progress-wrap")) return;

	var $banner = $(".meas-summary-banner");
	if ($banner.length) {
		$banner.after(
			'<div id="meas-progress-wrap">'
			+ '<div class="progress-header"><span>Form Completion</span><span id="meas-pct">0%</span></div>'
			+ '<div class="progress-track"><div class="progress-fill" id="meas-fill" style="width:0%;"></div></div>'
			+ '</div>'
		);
	}
}

function update_progress(frm) {
	var fields = ["length","shoulder","sleeve_length","loose_1","loose_2","collar_style","special_button"];
	var skip = ["Select Button","Select Style","Select Type","Select Pocket","Select Patty"];
	var filled = 0;
	for (var i = 0; i < fields.length; i++) {
		var v = frm.doc[fields[i]];
		if (v && v !== 0 && skip.indexOf(v) === -1) filled++;
	}
	var pct = Math.round((filled / fields.length) * 100);
	var pe = document.getElementById("meas-pct");
	var fe = document.getElementById("meas-fill");
	if (pe) pe.textContent = pct + "%";
	if (fe) fe.style.width = pct + "%";
}


/* ═══════════════════════════════════════════════════════════
   VISUAL POPUP SELECTORS
   Show image cards in a popup when dropdown is clicked
   ═══════════════════════════════════════════════════════════ */

function setup_visual_popups(frm) {
	var isReadOnly = frm.doc.docstatus === 1 || frm.doc.docstatus === 2;
	if (isReadOnly) return;

	var fields = [
		{ fieldname: "collar_style", title: "Select Collar Style", icon_fn: make_collar_svg, compact: true },
		{ fieldname: "special_button", title: "Select Button Type", icon_fn: make_button_svg, compact: false },
		{ fieldname: "thobe", title: "Select Thobe Model", icon_fn: make_thobe_svg, compact: false },
	];

	for (var i = 0; i < fields.length; i++) {
		bind_popup_trigger(frm, fields[i]);
	}
}

function bind_popup_trigger(frm, config) {
	var field = frm.fields_dict[config.fieldname];
	if (!field) return;

	var $select = $(field.wrapper).find("select");
	if (!$select.length) return;

	$select.addClass("vo-select-trigger");

	$select.off("mousedown.vo").on("mousedown.vo", function(e) {
		e.preventDefault();
		e.stopPropagation();
		show_visual_popup(frm, config);
		return false;
	});
}


function show_visual_popup(frm, config) {
	$(".vo-popup-overlay").remove();

	var field = frm.fields_dict[config.fieldname];
	if (!field) return;

	var options = (field.df.options || "").split("\n").filter(function(o) { return o.trim(); });
	var skip = ["Select Button","Select Style","Select Type","Select Pocket","Select Patty"];
	var currentVal = frm.doc[config.fieldname] || "";

	var cardsHtml = '';
	for (var i = 0; i < options.length; i++) {
		var opt = options[i].trim();
		if (!opt || skip.indexOf(opt) !== -1) continue;

		var isSelected = (opt === currentVal);
		var svgIcon = config.icon_fn(opt, i);

		cardsHtml += '<div class="vo-popup-card' + (isSelected ? ' selected' : '') + '" data-value="' + opt.replace(/"/g, '&quot;') + '">'
			+ '<div class="vo-icon">' + svgIcon + '</div>'
			+ '<div class="vo-label">' + opt + '</div>'
			+ '</div>';
	}

	var popupHtml = '<div class="vo-popup-overlay">'
		+ '<div class="vo-popup-panel">'
		+ '<div class="vo-popup-header">'
		+ '<div class="vo-popup-title">' + config.title + '</div>'
		+ '<button class="vo-popup-close">&times;</button>'
		+ '</div>'
		+ '<div class="vo-popup-body">'
		+ '<div class="vo-popup-grid' + (config.compact ? ' compact' : '') + '">'
		+ cardsHtml
		+ '</div></div></div></div>';

	var $popup = $(popupHtml);
	$("body").append($popup);

	$popup.find(".vo-popup-close").on("click", function() { $popup.remove(); });
	$popup.on("click", function(e) {
		if ($(e.target).hasClass("vo-popup-overlay")) $popup.remove();
	});
	$popup.find(".vo-popup-card").on("click", function() {
		var val = $(this).data("value");
		frm.set_value(config.fieldname, val);
		$popup.remove();
	});
	$(document).one("keydown.vo", function(e) {
		if (e.key === "Escape") $popup.remove();
	});
}


/* ═══════════════════════════════════════════════════════════
   SVG ICON GENERATORS
   ═══════════════════════════════════════════════════════════ */

function make_collar_svg(label) {
	var L = label.toUpperCase();
	if (L === "NONE") {
		return '<svg viewBox="0 0 64 64"><rect x="8" y="8" width="48" height="48" rx="8" fill="#F9FAFB" stroke="#D1D5DB" stroke-width="1.5"/>'
			+ '<line x1="18" y1="18" x2="46" y2="46" stroke="#D1D5DB" stroke-width="2"/><line x1="46" y1="18" x2="18" y2="46" stroke="#D1D5DB" stroke-width="2"/></svg>';
	}
	if (L.indexOf("SHAPE") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<path d="M8 48 L8 20 Q32 2 56 20 L56 48" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5" stroke-linejoin="round"/>'
			+ '<path d="M14 42 Q32 24 50 42" fill="#EFF6FF" stroke="#2563EB" stroke-width="1.2"/>'
			+ '<path d="M20 38 Q32 28 44 38" fill="none" stroke="#93C5FD" stroke-width="0.8" stroke-dasharray="3,2"/>'
			+ '<line x1="32" y1="32" x2="32" y2="48" stroke="#2563EB" stroke-width="0.8" stroke-dasharray="2,2"/>'
			+ '<circle cx="32" cy="46" r="2" fill="#2563EB"/></svg>';
	}
	if (L.indexOf("SAADA") !== -1 || L.indexOf("SADA") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<path d="M8 48 L8 18 L20 10 L44 10 L56 18 L56 48" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5" stroke-linejoin="round"/>'
			+ '<path d="M16 40 L32 26 L48 40" fill="#FFFBEB" stroke="#D97706" stroke-width="1.2"/>'
			+ '<line x1="32" y1="10" x2="32" y2="26" stroke="#D97706" stroke-width="0.8"/>'
			+ '<rect x="29" y="12" width="6" height="4" rx="1" fill="none" stroke="#F59E0B" stroke-width="0.6"/>'
			+ '<circle cx="32" cy="44" r="2" fill="#D97706"/></svg>';
	}
	if (L.indexOf("FRANCY") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<path d="M8 48 Q12 8 32 4 Q52 8 56 48" fill="#EDE9FE" stroke="#7C3AED" stroke-width="1.5" stroke-linejoin="round"/>'
			+ '<path d="M18 38 Q32 20 46 38" fill="#F5F3FF" stroke="#7C3AED" stroke-width="1.2"/>'
			+ '<circle cx="32" cy="14" r="3.5" fill="#7C3AED" opacity="0.2" stroke="#7C3AED" stroke-width="0.8"/>'
			+ '<path d="M24 30 Q28 24 32 26 Q36 24 40 30" fill="none" stroke="#A78BFA" stroke-width="0.8"/>'
			+ '<circle cx="32" cy="44" r="2" fill="#7C3AED"/>'
			+ '<line x1="32" y1="20" x2="32" y2="38" stroke="#7C3AED" stroke-width="0.6" stroke-dasharray="2,2"/></svg>';
	}
	if (L.indexOf("MALAKI") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<rect x="6" y="8" width="52" height="36" rx="6" fill="#FEE2E2" stroke="#DC2626" stroke-width="1.5"/>'
			+ '<path d="M18 28 L32 16 L46 28" fill="#FFF1F2" stroke="#DC2626" stroke-width="1.2"/>'
			+ '<rect x="22" y="34" width="20" height="12" rx="2" fill="none" stroke="#F87171" stroke-width="0.8"/>'
			+ '<line x1="32" y1="34" x2="32" y2="46" stroke="#F87171" stroke-width="0.6"/>'
			+ '<circle cx="26" cy="12" r="1.5" fill="#DC2626" opacity="0.3"/><circle cx="38" cy="12" r="1.5" fill="#DC2626" opacity="0.3"/></svg>';
	}
	return '<svg viewBox="0 0 64 64">'
		+ '<path d="M10 48 Q10 14 32 8 Q54 14 54 48" fill="#F0FDF4" stroke="#059669" stroke-width="1.5"/>'
		+ '<path d="M18 40 Q32 26 46 40" fill="#ECFDF5" stroke="#059669" stroke-width="1"/>'
		+ '<circle cx="32" cy="44" r="2" fill="#059669"/></svg>';
}

function make_button_svg(label) {
	var L = label.toUpperCase();
	if (L.indexOf("SPECIAL") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<rect x="4" y="4" width="56" height="56" rx="8" fill="#FFFBEB" stroke="#D97706" stroke-width="0.5"/>'
			+ '<circle cx="32" cy="18" r="7" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>'
			+ '<path d="M28 18 L36 18 M32 14 L32 22" stroke="#D97706" stroke-width="1"/>'
			+ '<circle cx="32" cy="38" r="7" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>'
			+ '<path d="M28 38 L36 38 M32 34 L32 42" stroke="#D97706" stroke-width="1"/></svg>';
	}
	if (L.indexOf("NORMAL") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<rect x="4" y="4" width="56" height="56" rx="8" fill="#EFF6FF" stroke="#2563EB" stroke-width="0.5"/>'
			+ '<circle cx="32" cy="18" r="7" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>'
			+ '<circle cx="29" cy="16" r="1.2" fill="#2563EB"/><circle cx="35" cy="16" r="1.2" fill="#2563EB"/>'
			+ '<circle cx="29" cy="20" r="1.2" fill="#2563EB"/><circle cx="35" cy="20" r="1.2" fill="#2563EB"/>'
			+ '<circle cx="32" cy="38" r="7" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>'
			+ '<circle cx="29" cy="36" r="1.2" fill="#2563EB"/><circle cx="35" cy="36" r="1.2" fill="#2563EB"/>'
			+ '<circle cx="29" cy="40" r="1.2" fill="#2563EB"/><circle cx="35" cy="40" r="1.2" fill="#2563EB"/></svg>';
	}
	if (L.indexOf("GAFIT") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<rect x="4" y="4" width="56" height="56" rx="8" fill="#F0FDF4" stroke="#059669" stroke-width="0.5"/>'
			+ '<rect x="18" y="12" width="28" height="10" rx="3" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>'
			+ '<rect x="26" y="14" width="12" height="6" rx="1.5" fill="#059669" opacity="0.2"/>'
			+ '<rect x="18" y="36" width="28" height="10" rx="3" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>'
			+ '<rect x="26" y="38" width="12" height="6" rx="1.5" fill="#059669" opacity="0.2"/></svg>';
	}
	if (L.indexOf("NO") !== -1) {
		return '<svg viewBox="0 0 64 64">'
			+ '<rect x="4" y="4" width="56" height="56" rx="8" fill="#F9FAFB" stroke="#D1D5DB" stroke-width="0.5"/>'
			+ '<circle cx="32" cy="32" r="16" fill="none" stroke="#D1D5DB" stroke-width="1.5"/>'
			+ '<line x1="20" y1="20" x2="44" y2="44" stroke="#D1D5DB" stroke-width="2"/></svg>';
	}
	return '<svg viewBox="0 0 64 64"><rect x="4" y="4" width="56" height="56" rx="8" fill="#F9FAFB" stroke="#D1D5DB" stroke-width="1"/>'
		+ '<text x="32" y="36" text-anchor="middle" fill="#9CA3AF" font-size="14" font-weight="600">?</text></svg>';
}

function make_thobe_svg(label) {
	var L = label.toLowerCase();
	var fills = { saudi: ["#EFF6FF","#2563EB"], gulf: ["#FEF3C7","#D97706"], kuwait: ["#F0FDF4","#059669"], other: ["#F9FAFB","#6B7280"] };
	var c = fills[L] || fills.other;

	var body = '<path d="M22 10 C22 5,42 5,42 10 L44 16 L56 24 L62 40 L56 42 L48 28 L48 58 C48 60,32 62,32 62 C32 62,16 60,16 58 L16 28 L8 42 L2 40 L8 24 L20 16Z" fill="'+c[0]+'" stroke="'+c[1]+'" stroke-width="1.2" stroke-linejoin="round"/>';
	var collar = '<ellipse cx="32" cy="11" rx="8" ry="3.5" fill="none" stroke="'+c[1]+'" stroke-width="0.8"/>';

	var details = '';
	if (L === "saudi") {
		details = '<line x1="32" y1="16" x2="32" y2="45" stroke="'+c[1]+'" stroke-width="0.5" stroke-dasharray="2,2"/>'
			+ '<rect x="24" y="28" width="7" height="5" rx="1" fill="none" stroke="'+c[1]+'" stroke-width="0.5"/>';
	} else if (L === "gulf") {
		details = '<path d="M28 12 Q32 8 36 12" fill="none" stroke="'+c[1]+'" stroke-width="0.8"/>'
			+ '<rect x="23" y="26" width="8" height="7" rx="1" fill="none" stroke="'+c[1]+'" stroke-width="0.5"/>'
			+ '<line x1="23" y1="29" x2="31" y2="29" stroke="'+c[1]+'" stroke-width="0.4"/>';
	} else if (L === "kuwait") {
		details = '<line x1="26" y1="12" x2="38" y2="12" stroke="'+c[1]+'" stroke-width="1"/>'
			+ '<line x1="32" y1="12" x2="32" y2="40" stroke="'+c[1]+'" stroke-width="0.4" stroke-dasharray="2,2"/>'
			+ '<line x1="16" y1="48" x2="16" y2="56" stroke="'+c[1]+'" stroke-width="0.6"/>'
			+ '<line x1="48" y1="48" x2="48" y2="56" stroke="'+c[1]+'" stroke-width="0.6"/>';
	} else {
		details = '<text x="32" y="40" text-anchor="middle" fill="'+c[1]+'" font-size="8" font-weight="600">?</text>';
	}

	return '<svg viewBox="0 0 64 64">' + body + collar + details + '</svg>';
}


/* ═══ EXTRAS CHILD TABLE — auto-calculate amount ═══ */
frappe.ui.form.on("Measurement Extra Item", {
	qty(frm, cdt, cdn) {
		_calc_extra_amount(cdt, cdn);
		frm.refresh_field("extra_items");
	},
	rate(frm, cdt, cdn) {
		_calc_extra_amount(cdt, cdn);
		frm.refresh_field("extra_items");
	},
	item_code(frm, cdt, cdn) {
		// rate is fetched automatically; recalc after fetch completes
		setTimeout(function() {
			_calc_extra_amount(cdt, cdn);
			frm.refresh_field("extra_items");
		}, 500);
	},
});

function _calc_extra_amount(cdt, cdn) {
	var row = locals[cdt][cdn];
	row.amount = flt(row.qty) * flt(row.rate);
}
