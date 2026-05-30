# Architecture — System Design & Structure

> Complete technical reference for the Asafat Tailoring ERPNext custom app.

---

## System Overview

**Asafat Tailoring** is a Frappe v15 / ERPNext v15 custom app that adds a tailoring-specific workflow on top of ERPNext's standard Sales Order → Invoice → Delivery pipeline. It introduces body measurement capture, stitching status tracking, advance payment management, profit analysis, and WhatsApp notifications.

**Business Flow:**
```
Customer walks in → Sales Order created → Measurement taken → Advance collected
→ Stitching progresses (4 status steps) → Order completed (Invoice + Payment + Delivery)
→ Optional: Sales Return with Credit Note
```

---

## Tech Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Frappe Framework | v15.68.1 | Python backend + Jinja templates |
| ERPNext | v15.61.1 | ERP modules (Selling, Accounts, Stock) |
| MariaDB | 10.x | Database |
| Redis | — | Cache, queue, socketio |
| Node.js | — | Asset compilation |
| Python | ≥3.10 | Runtime |

**Bench path:** `/Users/sayanthns/frappe-bench`
**App path:** `/Users/sayanthns/frappe-bench/apps/asafat_tailoring`
**Site:** `mysite.local`
**GitHub:** https://github.com/sayanthns/asafat_tailoring (private)

---

## File-by-File Reference

### Core Configuration

| File | Purpose | Key Details |
|------|---------|-------------|
| `hooks.py` | App registration & configuration | CSS/JS includes, doc_events, fixtures, dashboard overrides, after_install hook |
| `install.py` | Post-install setup | Creates custom fields, stock settings, "Extras" item group, 4 number cards, search field config |
| `setup_print_formats.py` | 4 Jinja print format templates | Measurement Card, Tailoring Order, Tailoring Invoice, Delivery Slip |
| `modules.txt` | Module declaration | Single module: "Asafat Tailoring" |
| `patches.txt` | Migration patches | Currently empty |

### Backend Logic (Python)

| File | Purpose | Functions |
|------|---------|-----------|
| `api.py` | 6 whitelisted API endpoints | `create_advance_payment`, `create_sales_invoice`, `complete_order`, `get_so_stats`, `process_sales_return`, `get_previous_measurements` |
| `events/sales_order.py` | SO on_submit hook | Sets default `stitching_status = "Order"` |
| `events/payment_entry.py` | PE on_submit/on_cancel hook | Recalculates `advance_collected` and `outstanding_amount` on linked SOs via SQL sum |
| `overrides/sales_order_dashboard.py` | Dashboard override | Adds "Tailoring Measurement" link to SO dashboard |
| `tailoring_measurement.py` | Measurement doctype controller | `before_save` (JSON sync), `on_submit` (add extras, update status), `on_cancel` (remove extras, revert status), `validate` (JSON check) |

### Frontend (JavaScript)

| File | Purpose | Lines |
|------|---------|-------|
| `public/js/sales_order.js` | SO form customization | ~850 lines: status buttons, 4 dialog functions, stat refresh, WhatsApp, field hiding, DOM manipulation |
| `public/js/sales_order_list.js` | SO list view | ~37 lines: color-coded stitching_status indicators |
| `tailoring_measurement.js` | Measurement form | ~612 lines: summary banner, SVG thobe diagram, progress bar, visual popups, per-item JSON switching, cloth_name dropdown |

### Styling (CSS)

| File | Purpose | Lines |
|------|---------|-------|
| `public/css/measurement.css` | Tailoring Measurement form styling | ~1000+ lines: card-based sections, monospace inputs, SVG diagram, visual popups, progress bar, summary banner |

### Reports (Script Reports)

| File | Purpose | Columns |
|------|---------|---------|
| `report/daily_sales_collection/` | Daily invoice + payment breakdown | Date, Invoice, Customer, SO, Amount, PE, Mode, Collected, Outstanding |
| `report/sales_order_profit_status/` | Per-order profitability | SO, Date, Customer, Status, Grand Total, Item Cost, Stitching Cost, Total Cost, Profit, Advance, Outstanding, Measurements |

### Fixtures (JSON)

| File | Contents |
|------|----------|
| `fixtures/custom_field.json` | 13 custom fields (12 on Sales Order, 1 on Customer) |
| `fixtures/print_format.json` | 3 print formats (Measurement Card, Tailoring Invoice, Delivery Slip) |
| `fixtures/property_setter.json` | 2 default print format assignments (SO → Tailoring Order, SI → Tailoring Invoice) |

### Website

| File | Purpose |
|------|---------|
| `www/user-guide.html` | Public user documentation at `/user-guide` |
| `www/user-guide.py` | Context: removes sidebar/header, no_cache=1 |

---

## Custom Doctypes

### 1. Tailoring Measurement (Submittable)

**Naming:** `MEAS-.YYYY.-.#####` (e.g., MEAS-2026-00001)

**Linked to:** Sales Order (required), Customer (required)

**Field Groups:**
- **Header:** sales_order, customer, customer_name, phone_no, measurement_date, promise_date, delivery_date
- **Measurement Items:** child table of SO items being measured
- **Cloth Details:** cloth_name (select switcher), cloth_no, qty, stitching_model, thobe, delivery_type
- **Body Measurements:** length, shoulder, sleeve_length, loose_1, loose_2, bottom (all required Float), plus optional: bottom_size, sleeve_loose, shoulder_alt, sleeve_alt
- **Collar & Neck:** collar_style (25 options), collar_type, neck_style (25 options), neck_type
- **Hip & Button:** hip, hip_type, special_button
- **Extras:** child table of add-on items (buttons, thread, etc.)
- **Notes:** description_note

**Critical Architecture: Per-Item Measurement JSON**

The `measurements_json` field stores measurement values for EACH item in the SO, keyed by cloth_name:

```json
{
  "White Thobe": {
    "length": 58, "shoulder": 22, "sleeve_length": 24,
    "loose_1": 50, "loose_2": 48, "bottom": 24,
    "collar_style": "SHAPE 2.5\" INSIDE PLASTIC",
    "collar_type": "Option 1", ...
  },
  "White Thobe #2": {
    "length": 60, "shoulder": 23, ...
  }
}
```

When user switches `cloth_name` dropdown, JS saves current fields to JSON and loads the selected item's values.

### 2. Measurement Item (Child Table)
Fields: item_code, item_name, qty, sales_order_item (hidden reference)

### 3. Measurement Extra Item (Child Table)
Fields: item_code, item_name, qty, rate (fetched from standard_rate), amount (calculated)

---

## Custom Fields on Standard Doctypes

### Sales Order (12 fields)

| Field | Type | Purpose | Special |
|-------|------|---------|---------|
| `customer_phone` | Data/Phone | Fetched from customer.custom_phone | in_standard_filter, search_index |
| `stitching_status` | Select | 7-stage workflow status | allow_on_submit, default="Order" |
| `advance_collected` | Currency | Cumulative advance payments received | read_only, allow_on_submit |
| `outstanding_amount` | Currency | grand_total - advance_collected | read_only, allow_on_submit |
| `measurement_count` | Int | Count of linked measurements | read_only, allow_on_submit |
| `item_cost` | Currency | Sum of valuation_rate × qty | read_only, in collapsible Profit section |
| `stitching_cost` | Currency | total_qty × 35 SAR | read_only |
| `total_cost` | Currency | item_cost + stitching_cost | read_only, bold |
| `revenue` | Currency | From linked Sales Invoices | read_only |
| `estimated_profit` | Currency | revenue - total_cost | read_only, bold |

### Customer (1 field)

| Field | Type | Purpose |
|-------|------|---------|
| `custom_phone` | Data/Phone | Additional searchable phone |

---

## Stitching Status Workflow

```
Order ──[Measurement submitted]──→ Measurement
  │                                    │
  └──[Advance collected]──→ Job Order ←┘
                               │
                    [Manual button click]
                               │
                          Processing
                               │
                    [Manual button click]
                               │
                      Process Completed
                               │
                    [Manual button click + WhatsApp]
                               │
                    Ready for Delivery
                               │
                    [Complete Order dialog]
                               │
                          Delivered
                               │
                    [Sales Return button]
                               │
                     Credit Note created
```

**Color coding (list view and form indicator):**
- Order → blue
- Measurement → purple
- Job Order → orange
- Processing → yellow
- Process Completed → light-blue
- Ready for Delivery → green
- Delivered → darkgrey

---

## API Endpoints Detail

### 1. `create_advance_payment(so_name, amount, mode_of_payment, reference_no="")`
- Creates Payment Entry type "Receive"
- Links to SO via Payment Entry Reference child table
- Updates `advance_collected` and `outstanding_amount` on SO
- Auto-transitions status to "Job Order" if currently "Order" or "Measurement"
- **Dependency:** Mode of Payment must have an account configured for the company

### 2. `create_sales_invoice(so_name, selected_items=None, update_stock=1)`
- Creates SI from SO items (all or selected subset)
- Copies tax rows from SO → SI
- Calls `si.set_advances()` to auto-allocate existing advance payments
- **Dependency:** SO must be submitted

### 3. `complete_order(so_name, values)`
- All-in-one completion: creates SI, PE, DN based on flags in `values`
- Supports discount: `discount_type` ("Percentage" or "Amount"), applies to SI
- Payment amount = grand_total - discount - advance_paid
- Sets `stitching_status = "Delivered"`
- **Returns:** `{"si": "SI-00001", "pe": "PE-00001", "dn": "DN-00001"}`

### 4. `get_so_stats(so_name)`
- Calculates: measurement_count, item_cost, stitching_cost, total_cost, revenue, estimated_profit
- Revenue = sum of linked submitted SI grand_totals, OR SO grand_total if no SI exists
- Persists values to SO fields with `update_modified=False`

### 5. `process_sales_return(so_name, return_items, return_reason, create_credit_note, create_refund, mode_of_payment)`
- Finds original SI via `Sales Invoice Item` with `sales_order` filter
- Creates Credit Note: SI with `is_return=1`, `return_against=original_si`, negative quantities
- Optional refund PE: type "Pay", negative `allocated_amount`

### 6. `get_previous_measurements(customer)`
- Returns latest submitted Tailoring Measurement for the customer
- Used by measurement dialog to pre-fill values

---

## Document Event Hooks

| DocType | Event | Handler | What It Does |
|---------|-------|---------|--------------|
| Sales Order | on_submit | `events.sales_order.on_submit` | Sets `stitching_status = "Order"` if not set |
| Payment Entry | on_submit | `events.payment_entry.update_so_advance` | Recalculates `advance_collected` via SQL sum of all submitted PE allocations |
| Payment Entry | on_cancel | `events.payment_entry.update_so_advance` | Same — recalculates after cancel (cancelled PE excluded by docstatus filter) |

---

## External Integrations

### WhatsApp (via wa.me URLs)
- **Not an API integration** — opens WhatsApp Web in browser
- Phone normalization: strips spaces/dashes, adds `966` prefix for Saudi numbers
- Two message templates:
  1. "Job Order" — order confirmation with SO number
  2. "Ready for Delivery" — pickup notification
- **File:** `sales_order.js:send_status_whatsapp()` (~line 750)

---

## Database Queries (Direct SQL)

### 1. Revenue calculation (`api.py:get_so_stats`)
```sql
SELECT COALESCE(SUM(si.grand_total), 0)
FROM `tabSales Invoice` si
JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
WHERE sii.sales_order = %s AND si.docstatus = 1
```

### 2. Advance recalculation (`events/payment_entry.py:_recalculate_advance`)
```sql
SELECT COALESCE(SUM(per.allocated_amount), 0)
FROM `tabPayment Entry Reference` per
JOIN `tabPayment Entry` pe ON pe.name = per.parent
WHERE per.reference_doctype = 'Sales Order'
    AND per.reference_name = %s
    AND pe.docstatus = 1
    AND pe.party_type = 'Customer'
```

### 3. Daily Sales Collection report — joins SI with PE via references

### 4. Sales Order Profit Status report — fetches items and valuation rates

---

## Credentials & Configuration Locations

| Item | Location | Notes |
|------|----------|-------|
| Site config | `/Users/sayanthns/frappe-bench/sites/mysite.local/site_config.json` | DB credentials, Redis URLs |
| Common config | `/Users/sayanthns/frappe-bench/sites/common_site_config.json` | Shared settings |
| GitHub repo | https://github.com/sayanthns/asafat_tailoring | Private — needs SSH key or token |
| Stock settings | ERPNext → Stock Settings | `allow_uom_with_conversion_rate_defined_in_item` must be enabled |
| Mode of Payment accounts | ERPNext → Mode of Payment → Account table | Must have account for company — PE creation fails without it |
| Company default accounts | ERPNext → Company → Default Accounts | Used for PE debit/credit accounts |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (Client)                         │
│                                                                 │
│  sales_order.js          tailoring_measurement.js               │
│  sales_order_list.js     measurement.css                        │
│  (4 dialogs, status      (summary banner, SVG diagram,         │
│   buttons, stat refresh)  visual popups, progress bar)          │
└────────────────────────────┬────────────────────────────────────┘
                             │ frappe.call() / frappe.xcall()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRAPPE SERVER (Python)                      │
│                                                                 │
│  api.py (6 @whitelist endpoints)                                │
│  events/sales_order.py (on_submit hook)                         │
│  events/payment_entry.py (on_submit/on_cancel hook)             │
│  tailoring_measurement.py (before_save, on_submit, on_cancel)   │
│  overrides/sales_order_dashboard.py                             │
│  install.py (post-install setup)                                │
│  setup_print_formats.py (Jinja templates)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ frappe.db / raw SQL
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MariaDB (Database)                         │
│                                                                 │
│  tabSales Order (+ 12 custom fields)                            │
│  tabCustomer (+ 1 custom field)                                 │
│  tabTailoring Measurement                                       │
│  tabMeasurement Item                                            │
│  tabMeasurement Extra Item                                      │
│  tabSales Invoice, tabPayment Entry, tabDelivery Note           │
│  tabNumber Card (4 dashboard cards)                             │
│  tabPrint Format (3 custom formats)                             │
│  tabProperty Setter (2 default assignments)                     │
│  tabCustom Field (13 field definitions)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Constants

| Constant | Value | Location | Purpose |
|----------|-------|----------|---------|
| Stitching cost rate | 35 SAR per qty | `api.py:get_so_stats()`, `sales_order_profit_status.py` | Hardcoded stitching cost per item |
| Naming series | `MEAS-.YYYY.-.#####` | `tailoring_measurement.json` | Measurement document naming |
| Extras item group | "Extras" | `install.py:_setup_extras_item_group()` | Parent group for add-on items |
| Default UOM | "Nos" | Used in `_add_extras_to_sales_order()` | Standard UOM for extras |
| WhatsApp base URL | `https://wa.me/` | `sales_order.js:send_status_whatsapp()` | WhatsApp Web deep link |
| Saudi country code | `966` | `sales_order.js:send_status_whatsapp()` | Default phone prefix |
