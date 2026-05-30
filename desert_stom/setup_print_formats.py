import frappe


def create_print_formats():
	"""Create all print formats for Asafat Tailoring."""

	# 1. Measurement Card
	measurement_card_html = """
<style>
	.print-format { font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
	.mc-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #D4A84B; padding-bottom: 10px; margin-bottom: 15px; }
	.mc-title { font-size: 20px; font-weight: 700; color: #1a1a2e; }
	.mc-subtitle { font-size: 12px; color: #666; margin-top: 4px; }
	.mc-badge-urgent { background: #C0392B; color: white; padding: 4px 14px; border-radius: 4px; font-size: 12px; font-weight: 600; }
	.mc-badge-normal { background: #95a5a6; color: white; padding: 4px 14px; border-radius: 4px; font-size: 12px; }
	.mc-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px; }
	.mc-info-row { display: flex; gap: 8px; font-size: 12px; }
	.mc-info-label { color: #888; min-width: 80px; }
	.mc-info-value { font-weight: 600; color: #1a1a2e; }
	.mc-section-title { font-size: 13px; font-weight: 700; text-transform: uppercase; color: #D4A84B; border-bottom: 1px solid #eee; padding-bottom: 4px; margin: 15px 0 10px; letter-spacing: 0.05em; }
	.mc-meas-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0; border: 1px solid #ddd; border-radius: 6px; overflow: hidden; }
	.mc-meas-cell { padding: 8px 12px; border-right: 1px solid #eee; border-bottom: 1px solid #eee; }
	.mc-meas-cell:nth-child(3n) { border-right: none; }
	.mc-meas-label { font-size: 9px; text-transform: uppercase; color: #888; letter-spacing: 0.08em; }
	.mc-meas-value { font-size: 16px; font-weight: 600; font-family: 'Courier New', monospace; color: #1a1a2e; }
	.mc-meas-unit { font-size: 9px; color: #aaa; }
	.mc-key-cell { background: #FFF8E7; }
	.mc-key-cell .mc-meas-value { color: #B8892A; }
	.mc-options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
	.mc-opt-row { font-size: 11px; display: flex; gap: 6px; }
	.mc-opt-label { color: #888; min-width: 100px; }
	.mc-opt-value { font-weight: 500; }
	.mc-note-box { border: 1px solid #D4A84B; border-radius: 6px; padding: 10px 14px; background: #FFFDF5; margin-top: 15px; font-size: 12px; color: #333; min-height: 40px; }
	.mc-signature { margin-top: 30px; display: flex; justify-content: space-between; }
	.mc-sig-line { border-top: 1px solid #ccc; width: 200px; padding-top: 4px; font-size: 10px; color: #888; text-align: center; }
</style>

<div class="print-format">
	<div class="mc-header">
		<div>
			<div class="mc-title">Measurement Card &mdash; {{ doc.name }}</div>
			<div class="mc-subtitle">Asafat Sahran Tailoring</div>
		</div>
		<div>
			{% if doc.delivery_type == "Urgent" %}
				<span class="mc-badge-urgent">URGENT</span>
			{% else %}
				<span class="mc-badge-normal">Normal</span>
			{% endif %}
		</div>
	</div>

	<div class="mc-info-grid">
		<div class="mc-info-row"><span class="mc-info-label">Customer</span><span class="mc-info-value">{{ doc.customer_name or "" }}</span></div>
		<div class="mc-info-row"><span class="mc-info-label">Phone</span><span class="mc-info-value">{{ doc.phone_no or "" }}</span></div>
		<div class="mc-info-row"><span class="mc-info-label">Date</span><span class="mc-info-value">{{ frappe.format(doc.measurement_date, {"fieldtype": "Date"}) }}</span></div>
		<div class="mc-info-row"><span class="mc-info-label">Promise Date</span><span class="mc-info-value">{{ frappe.format(doc.promise_date, {"fieldtype": "Date"}) if doc.promise_date else "-" }}</span></div>
		<div class="mc-info-row"><span class="mc-info-label">Cloth</span><span class="mc-info-value">{{ doc.cloth_name or "" }}</span></div>
		<div class="mc-info-row"><span class="mc-info-label">Model</span><span class="mc-info-value">{{ doc.stitching_model or "-" }} / {{ doc.thobe or "-" }}</span></div>
	</div>

	<div class="mc-section-title">Body Measurements</div>
	<div class="mc-meas-grid">
		<div class="mc-meas-cell mc-key-cell">
			<div class="mc-meas-label">Length</div>
			<div class="mc-meas-value">{{ doc.length or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Shoulder</div>
			<div class="mc-meas-value">{{ doc.shoulder or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell mc-key-cell">
			<div class="mc-meas-label">Sleeve Length</div>
			<div class="mc-meas-value">{{ doc.sleeve_length or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Loose 1</div>
			<div class="mc-meas-value">{{ doc.loose_1 or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Loose 2</div>
			<div class="mc-meas-value">{{ doc.loose_2 or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Bottom</div>
			<div class="mc-meas-value">{{ doc.bottom or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Sleeve Loose</div>
			<div class="mc-meas-value">{{ doc.sleeve_loose or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Shoulder Alt</div>
			<div class="mc-meas-value">{{ doc.shoulder_alt or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
		<div class="mc-meas-cell">
			<div class="mc-meas-label">Sleeve Alt</div>
			<div class="mc-meas-value">{{ doc.sleeve_alt or "-" }}</div>
			<div class="mc-meas-unit">cm</div>
		</div>
	</div>

	<div class="mc-section-title">Garment Options</div>
	<div class="mc-options-grid">
		<div class="mc-opt-row"><span class="mc-opt-label">Collar Style</span><span class="mc-opt-value">{{ doc.collar_style or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Collar Type</span><span class="mc-opt-value">{{ doc.collar_type or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Neck Style</span><span class="mc-opt-value">{{ doc.neck_style or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Neck Type</span><span class="mc-opt-value">{{ doc.neck_type or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Hip</span><span class="mc-opt-value">{{ doc.hip or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Hip Type</span><span class="mc-opt-value">{{ doc.hip_type or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Front Patty</span><span class="mc-opt-value">{{ doc.front_patty or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Front Pocket</span><span class="mc-opt-value">{{ doc.front_pocket or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Kally Piece</span><span class="mc-opt-value">{{ doc.kally_piece or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Side Pocket</span><span class="mc-opt-value">{{ doc.side_pocket_type or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label">Jawal Pocket</span><span class="mc-opt-value">{{ doc.jawal_pocket or "-" }}</span></div>
		<div class="mc-opt-row"><span class="mc-opt-label"><strong>Special Button</strong></span><span class="mc-opt-value"><strong>{{ doc.special_button or "-" }}</strong></span></div>
	</div>

	{% if doc.description_note %}
	<div class="mc-section-title">Notes</div>
	<div class="mc-note-box">{{ doc.description_note }}</div>
	{% endif %}

	<div class="mc-signature">
		<div class="mc-sig-line">Stitcher Signature</div>
		<div class="mc-sig-line">Date</div>
	</div>
</div>
"""

	# 2. Tailoring Invoice (Sales Invoice)
	tailoring_invoice_html = """
<style>
	.print-format { font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
	.ti-header { text-align: center; border-bottom: 2px solid #D4A84B; padding-bottom: 12px; margin-bottom: 15px; }
	.ti-title { font-size: 22px; font-weight: 700; color: #1a1a2e; }
	.ti-sub { font-size: 12px; color: #888; }
	.ti-info { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 15px; font-size: 12px; }
	.ti-label { color: #888; }
	.ti-val { font-weight: 600; }
	.ti-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
	.ti-table th { background: #f5f5f5; font-size: 11px; text-transform: uppercase; padding: 8px; border: 1px solid #ddd; text-align: left; }
	.ti-table td { padding: 8px; border: 1px solid #eee; font-size: 12px; }
	.ti-tax-table { width: 60%; margin-left: auto; margin-bottom: 15px; border-collapse: collapse; }
	.ti-tax-table td { padding: 6px 8px; font-size: 12px; border-bottom: 1px solid #eee; }
	.ti-tax-table .ti-tax-label { color: #888; }
	.ti-tax-table .ti-tax-amount { text-align: right; font-weight: 500; }
	.ti-summary { border: 1px solid #D4A84B; border-radius: 6px; padding: 12px; background: #FFFDF5; }
	.ti-sum-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
	.ti-sum-total { font-weight: 700; font-size: 15px; border-top: 1px solid #D4A84B; padding-top: 6px; margin-top: 6px; }
	.ti-so-ref { font-size: 11px; color: #888; margin-bottom: 10px; }
	.ti-footer { margin-top: 30px; display: flex; justify-content: space-between; }
	.ti-sig-line { border-top: 1px solid #ccc; width: 180px; padding-top: 4px; font-size: 10px; color: #888; text-align: center; }
	.ti-thank-you { text-align: center; margin-top: 25px; font-size: 13px; color: #D4A84B; font-weight: 600; }
</style>

<div class="print-format">
	<div class="ti-header">
		<div class="ti-title">Tailoring Invoice</div>
		<div class="ti-sub">Asafat Sahran &mdash; {{ doc.name }}</div>
	</div>

	<div class="ti-info">
		<div><span class="ti-label">Customer: </span><span class="ti-val">{{ doc.customer_name or doc.customer }}</span></div>
		<div><span class="ti-label">Invoice #: </span><span class="ti-val">{{ doc.name }}</span></div>
		<div><span class="ti-label">Phone: </span><span class="ti-val">{{ doc.contact_mobile or doc.contact_phone or "-" }}</span></div>
		<div><span class="ti-label">Date: </span><span class="ti-val">{{ frappe.format(doc.posting_date, {"fieldtype": "Date"}) }}</span></div>
		{% if doc.items and doc.items[0].sales_order %}
		<div><span class="ti-label">Sales Order: </span><span class="ti-val">{{ doc.items[0].sales_order }}</span></div>
		{% endif %}
		<div><span class="ti-label">Due Date: </span><span class="ti-val">{{ frappe.format(doc.due_date, {"fieldtype": "Date"}) if doc.due_date else "-" }}</span></div>
	</div>

	<table class="ti-table">
		<thead>
			<tr>
				<th style="width:30px;">#</th>
				<th>Item</th>
				<th style="width:50px;">Qty</th>
				<th style="width:90px;">Rate</th>
				<th style="width:100px; text-align:right;">Amount</th>
			</tr>
		</thead>
		<tbody>
			{% for item in doc.items %}
			<tr>
				<td>{{ loop.index }}</td>
				<td>{{ item.item_name or item.item_code }}</td>
				<td>{{ item.qty }}</td>
				<td>{{ frappe.format(item.rate, {"fieldtype": "Currency"}) }}</td>
				<td style="text-align:right;">{{ frappe.format(item.amount, {"fieldtype": "Currency"}) }}</td>
			</tr>
			{% endfor %}
		</tbody>
	</table>

	{% if doc.taxes %}
	<table class="ti-tax-table">
		<tr>
			<td class="ti-tax-label">Net Total</td>
			<td class="ti-tax-amount">{{ frappe.format(doc.net_total, {"fieldtype": "Currency"}) }}</td>
		</tr>
		{% for tax in doc.taxes %}
		<tr>
			<td class="ti-tax-label">{{ tax.description }}</td>
			<td class="ti-tax-amount">{{ frappe.format(tax.tax_amount, {"fieldtype": "Currency"}) }}</td>
		</tr>
		{% endfor %}
	</table>
	{% endif %}

	<div class="ti-summary">
		<div class="ti-sum-row"><span>Grand Total</span><span>{{ frappe.format(doc.grand_total, {"fieldtype": "Currency"}) }}</span></div>
		{% if doc.total_advance %}
		<div class="ti-sum-row"><span>Advance Paid</span><span>- {{ frappe.format(doc.total_advance, {"fieldtype": "Currency"}) }}</span></div>
		{% endif %}
		<div class="ti-sum-row ti-sum-total"><span>Outstanding</span><span>{{ frappe.format(doc.outstanding_amount, {"fieldtype": "Currency"}) }}</span></div>
	</div>

	<div class="ti-thank-you">Thank you for choosing Asafat Sahran!</div>

	<div class="ti-footer">
		<div class="ti-sig-line">Customer Signature</div>
		<div class="ti-sig-line">Date</div>
	</div>
</div>
"""

	# 3. Delivery Slip
	delivery_slip_html = """
<style>
	.print-format { font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
	.ds-header { border-bottom: 2px solid #2DD4BF; padding-bottom: 10px; margin-bottom: 15px; }
	.ds-title { font-size: 20px; font-weight: 700; color: #1a1a2e; }
	.ds-sub { font-size: 12px; color: #888; }
	.ds-info { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 15px; font-size: 12px; }
	.ds-label { color: #888; }
	.ds-val { font-weight: 600; }
	.ds-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
	.ds-table th { background: #f0faf8; font-size: 11px; text-transform: uppercase; padding: 8px; border: 1px solid #ddd; }
	.ds-table td { padding: 8px; border: 1px solid #eee; font-size: 12px; }
	.ds-sig { display: flex; justify-content: space-between; margin-top: 40px; }
	.ds-sig-block { text-align: center; }
	.ds-sig-line { border-top: 1px solid #ccc; width: 180px; margin-top: 50px; padding-top: 4px; font-size: 10px; color: #888; }
</style>

<div class="print-format">
	<div class="ds-header">
		<div class="ds-title">Delivery Slip &mdash; {{ doc.name }}</div>
		<div class="ds-sub">Asafat Sahran Tailoring</div>
	</div>

	<div class="ds-info">
		<div><span class="ds-label">Customer: </span><span class="ds-val">{{ doc.customer_name or doc.customer }}</span></div>
		<div><span class="ds-label">Date: </span><span class="ds-val">{{ frappe.format(doc.posting_date, {"fieldtype": "Date"}) }}</span></div>
	</div>

	<table class="ds-table">
		<thead>
			<tr>
				<th>#</th>
				<th>Item</th>
				<th>Qty</th>
			</tr>
		</thead>
		<tbody>
			{% for item in doc.items %}
			<tr>
				<td>{{ loop.index }}</td>
				<td>{{ item.item_name or item.item_code }}</td>
				<td>{{ item.qty }}</td>
			</tr>
			{% endfor %}
		</tbody>
	</table>

	<div class="ds-sig">
		<div class="ds-sig-block">
			<div class="ds-sig-line">Customer Signature</div>
		</div>
		<div class="ds-sig-block">
			<div class="ds-sig-line">Date</div>
		</div>
	</div>
</div>
"""

	# 4. Tailoring Order (Sales Order)
	tailoring_order_html = """
<style>
	.print-format { font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
	.so-header { text-align: center; border-bottom: 2px solid #D4A84B; padding-bottom: 12px; margin-bottom: 15px; }
	.so-title { font-size: 22px; font-weight: 700; color: #1a1a2e; }
	.so-sub { font-size: 12px; color: #888; }
	.so-info { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 15px; font-size: 12px; }
	.so-label { color: #888; }
	.so-val { font-weight: 600; }
	.so-badge { display: inline-block; padding: 3px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; color: white; }
	.so-badge-order { background: #3B82F6; }
	.so-badge-stitching { background: #F59E0B; }
	.so-badge-completed { background: #10B981; }
	.so-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
	.so-table th { background: #f5f5f5; font-size: 11px; text-transform: uppercase; padding: 8px; border: 1px solid #ddd; text-align: left; }
	.so-table td { padding: 8px; border: 1px solid #eee; font-size: 12px; }
	.so-tax-table { width: 60%; margin-left: auto; margin-bottom: 15px; border-collapse: collapse; }
	.so-tax-table td { padding: 6px 8px; font-size: 12px; border-bottom: 1px solid #eee; }
	.so-tax-table .so-tax-label { color: #888; }
	.so-tax-table .so-tax-amount { text-align: right; font-weight: 500; }
	.so-summary { border: 1px solid #D4A84B; border-radius: 6px; padding: 12px; background: #FFFDF5; }
	.so-sum-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
	.so-sum-total { font-weight: 700; font-size: 15px; border-top: 1px solid #D4A84B; padding-top: 6px; margin-top: 6px; }
	.so-terms { margin-top: 15px; font-size: 11px; color: #666; border: 1px solid #eee; border-radius: 6px; padding: 10px; }
	.so-terms-title { font-weight: 600; color: #1a1a2e; margin-bottom: 4px; font-size: 12px; }
	.so-footer { margin-top: 30px; display: flex; justify-content: space-between; }
	.so-sig-line { border-top: 1px solid #ccc; width: 180px; padding-top: 4px; font-size: 10px; color: #888; text-align: center; }
	.so-thank-you { text-align: center; margin-top: 25px; font-size: 13px; color: #D4A84B; font-weight: 600; }
</style>

<div class="print-format">
	<div class="so-header">
		<div class="so-title">Sales Order</div>
		<div class="so-sub">Asafat Sahran &mdash; {{ doc.name }}</div>
	</div>

	<div class="so-info">
		<div><span class="so-label">Customer: </span><span class="so-val">{{ doc.customer_name or doc.customer }}</span></div>
		<div><span class="so-label">Order #: </span><span class="so-val">{{ doc.name }}</span></div>
		<div><span class="so-label">Phone: </span><span class="so-val">{{ doc.customer_phone or "-" }}</span></div>
		<div><span class="so-label">Order Date: </span><span class="so-val">{{ frappe.format(doc.transaction_date, {"fieldtype": "Date"}) }}</span></div>
		<div>
			<span class="so-label">Status: </span>
			{% if doc.stitching_status == "Stitching" %}
				<span class="so-badge so-badge-stitching">Stitching</span>
			{% elif doc.stitching_status == "Completed" %}
				<span class="so-badge so-badge-completed">Completed</span>
			{% else %}
				<span class="so-badge so-badge-order">Order</span>
			{% endif %}
		</div>
		<div><span class="so-label">Delivery Date: </span><span class="so-val">{{ frappe.format(doc.delivery_date, {"fieldtype": "Date"}) if doc.delivery_date else "-" }}</span></div>
	</div>

	<table class="so-table">
		<thead>
			<tr>
				<th style="width:30px;">#</th>
				<th>Item</th>
				<th style="width:50px;">Qty</th>
				<th style="width:90px;">Rate</th>
				<th style="width:100px; text-align:right;">Amount</th>
			</tr>
		</thead>
		<tbody>
			{% for item in doc.items %}
			<tr>
				<td>{{ loop.index }}</td>
				<td>{{ item.item_name or item.item_code }}</td>
				<td>{{ item.qty }}</td>
				<td>{{ frappe.format(item.rate, {"fieldtype": "Currency"}) }}</td>
				<td style="text-align:right;">{{ frappe.format(item.amount, {"fieldtype": "Currency"}) }}</td>
			</tr>
			{% endfor %}
		</tbody>
	</table>

	{% if doc.taxes %}
	<table class="so-tax-table">
		<tr>
			<td class="so-tax-label">Net Total</td>
			<td class="so-tax-amount">{{ frappe.format(doc.net_total, {"fieldtype": "Currency"}) }}</td>
		</tr>
		{% for tax in doc.taxes %}
		<tr>
			<td class="so-tax-label">{{ tax.description }}</td>
			<td class="so-tax-amount">{{ frappe.format(tax.tax_amount, {"fieldtype": "Currency"}) }}</td>
		</tr>
		{% endfor %}
	</table>
	{% endif %}

	<div class="so-summary">
		<div class="so-sum-row"><span>Grand Total</span><span>{{ frappe.format(doc.grand_total, {"fieldtype": "Currency"}) }}</span></div>
		{% if doc.advance_paid %}
		<div class="so-sum-row"><span>Advance Paid</span><span>- {{ frappe.format(doc.advance_paid, {"fieldtype": "Currency"}) }}</span></div>
		{% endif %}
		{% if doc.advance_collected %}
		<div class="so-sum-row"><span>Advance Collected</span><span>- {{ frappe.format(doc.advance_collected, {"fieldtype": "Currency"}) }}</span></div>
		{% endif %}
		<div class="so-sum-row so-sum-total">
			<span>Balance Due</span>
			<span>{{ frappe.format((doc.grand_total or 0) - (doc.advance_paid or 0), {"fieldtype": "Currency"}) }}</span>
		</div>
	</div>

	{% if doc.terms %}
	<div class="so-terms">
		<div class="so-terms-title">Terms &amp; Conditions</div>
		{{ doc.terms }}
	</div>
	{% endif %}

	<div class="so-thank-you">Thank you for choosing Asafat Sahran!</div>

	<div class="so-footer">
		<div class="so-sig-line">Customer Signature</div>
		<div class="so-sig-line">Date</div>
	</div>
</div>
"""

	print_formats = [
		{
			"name": "Measurement Card",
			"doc_type": "Tailoring Measurement",
			"module": "Asafat Tailoring",
			"html": measurement_card_html,
			"standard": "No",
			"print_format_type": "Jinja",
			"custom_format": 1,
		},
		{
			"name": "Tailoring Invoice",
			"doc_type": "Sales Invoice",
			"module": "Asafat Tailoring",
			"html": tailoring_invoice_html,
			"standard": "No",
			"print_format_type": "Jinja",
			"custom_format": 1,
		},
		{
			"name": "Delivery Slip",
			"doc_type": "Delivery Note",
			"module": "Asafat Tailoring",
			"html": delivery_slip_html,
			"standard": "No",
			"print_format_type": "Jinja",
			"custom_format": 1,
		},
		{
			"name": "Tailoring Order",
			"doc_type": "Sales Order",
			"module": "Asafat Tailoring",
			"html": tailoring_order_html,
			"standard": "No",
			"print_format_type": "Jinja",
			"custom_format": 1,
		},
	]

	for pf_data in print_formats:
		if frappe.db.exists("Print Format", pf_data["name"]):
			pf = frappe.get_doc("Print Format", pf_data["name"])
			pf.html = pf_data["html"]
			pf.save()
		else:
			pf = frappe.new_doc("Print Format")
			pf.update(pf_data)
			pf.insert(ignore_permissions=True)

	# Set default print formats
	_set_default_print_formats()

	frappe.db.commit()
	print("Print formats created successfully!")


def _set_default_print_formats():
	"""Set default print formats for Sales Order and Sales Invoice using Property Setter."""
	defaults = {
		"Sales Order": "Tailoring Order",
		"Sales Invoice": "Tailoring Invoice",
	}

	for dt, pf_name in defaults.items():
		ps_name = f"{dt}-main-default_print_format"
		if frappe.db.exists("Property Setter", ps_name):
			frappe.db.set_value("Property Setter", ps_name, "value", pf_name)
		else:
			ps = frappe.new_doc("Property Setter")
			ps.doctype_or_field = "DocType"
			ps.doc_type = dt
			ps.property = "default_print_format"
			ps.property_type = "Data"
			ps.value = pf_name
			ps.insert(ignore_permissions=True)
