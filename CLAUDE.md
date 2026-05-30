# Asafat Tailoring — ERPNext Custom App

> **READ `skills/` BEFORE ANY OPERATION.** Every skill document exists because something broke in production.

---

## Skill Index

| Skill | Path | Read When |
|-------|------|-----------|
| **Safety** | `skills/safety/SKILL.md` | BEFORE touching any code — hard rules, decision matrix, checklist |
| **Architecture** | `skills/architecture/SKILL.md` | To understand the system — files, APIs, data flow, doctypes |
| **Operations** | `skills/operations/SKILL.md` | To build, deploy, rollback, or debug — commands and workflows |
| **Troubleshooting** | `skills/troubleshooting/SKILL.md` | When something breaks — 12 known bug patterns with fixes |
| **Session Logs** | `skills/session-logs/` | To see what was done previously — decisions, changes, open items |

---

## Top 5 Rules (Prevents 90% of Production Issues)

### 1. ALWAYS call `calculate_taxes_and_totals()` before `save()` on submitted documents
Without this, SO totals won't include new items. Grand total, net total, tax totals all stay stale.

### 2. ALWAYS set ALL 14 fields when appending items to a submitted SO
Missing `conversion_factor` → UOM error. Missing `base_rate`/`net_amount` → commission TypeError. See `skills/safety/SKILL.md` for the complete field list.

### 3. NEVER use dict format for Number Card `filters_json`
Use `[["Sales Order","docstatus","=",1]]` (list-of-lists). Dict format silently kills all number cards.

### 4. ALWAYS handle BOTH submit and cancel for Payment Entry hooks
Advance tracking breaks if cancel isn't handled. The PE hook recalculates from SQL, not increment/decrement.

### 5. ALWAYS run the full deploy sequence after changes
```bash
bench build --app asafat_tailoring && bench --site mysite.local migrate && bench --site mysite.local clear-cache
```

---

## Project Overview
Custom ERPNext v15 / Frappe v15 app for **Asafat Sahran Tailoring** shop.
GitHub: https://github.com/sayanthns/asafat_tailoring (private)

## Tech Stack
- Frappe v15.68.1 / ERPNext v15.61.1
- Site: mysite.local
- Bench path: /Users/sayanthns/frappe-bench
- App path: /Users/sayanthns/frappe-bench/apps/asafat_tailoring

## App Structure
```
asafat_tailoring/
  api.py                    # 6 whitelisted APIs (advance, invoice, complete, stats, return, prev measurements)
  hooks.py                  # App config, doc_events, fixtures, doctype_js
  install.py                # Post-install setup (custom fields, stock settings, extras group, number cards)
  setup_print_formats.py    # 4 custom print formats (Measurement Card, Tailoring Order, Invoice, Delivery Slip)
  events/
    sales_order.py          # on_submit: set default stitching_status
    payment_entry.py        # on_submit/on_cancel: recalculate advance_collected on linked SOs
  overrides/
    sales_order_dashboard.py # Adds Tailoring Measurement to SO dashboard
  public/
    js/sales_order.js       # SO form: status buttons, measurement dialog, advance, complete, return (~850 lines)
    js/sales_order_list.js  # List view: color-coded stitching_status indicators (~37 lines)
    css/measurement.css     # Measurement form styling (~1000+ lines)
  www/
    user-guide.html         # Public user guide page at /user-guide
    user-guide.py           # Context file for user guide
  asafat_tailoring/
    doctype/
      tailoring_measurement/  # Main measurement doctype (submittable, ~180 lines Python, ~612 lines JS)
      measurement_item/       # Child table for SO items in measurement
      measurement_extra_item/ # Child table for extras/add-ons
    report/
      daily_sales_collection/       # Script report: daily invoice/payment breakdown
      sales_order_profit_status/    # Script report: per-order profitability
    workspace/
      asafat_tailoring/             # Workspace with 4 number cards, shortcuts, links
  fixtures/
    custom_field.json       # 13 custom fields (12 on Sales Order, 1 on Customer)
    print_format.json       # 3 print formats
    property_setter.json    # Default print format assignments
  skills/                   # Agent handoff documentation
    safety/SKILL.md         # Hard rules, decision matrix, code changes checklist
    architecture/SKILL.md   # System design, file reference, API docs
    operations/SKILL.md     # Build/deploy, rollback, console operations
    troubleshooting/SKILL.md # 12 known bug patterns with fixes
    session-logs/           # Per-session change logs
```

## Key Custom Fields on Sales Order
- stitching_status (Select: Order/Measurement/Job Order/Processing/Process Completed/Ready for Delivery/Delivered)
- advance_collected (Currency, read_only)
- outstanding_amount (Currency, read_only)
- measurement_count (Int, read_only)
- Profit section: item_cost, stitching_cost, total_cost, revenue, estimated_profit

## Key Custom Fields on Customer
- custom_phone (Data/Phone, searchable)

## Workflow
1. Sales Order created (status: Order)
2. Tailoring Measurement submitted (status: Measurement, extras added to SO)
3. Advance payment collected (status: Job Order, WhatsApp sent)
4. Manual status transitions: Processing → Process Completed → Ready for Delivery (WhatsApp sent)
5. Complete Order dialog creates SI/PE/DN (status: Delivered)
6. Optional: Sales Return creates Credit Note + refund

## Important Patterns
- `flags.ignore_validate_update_after_submit = True` for modifying submitted SO items
- `so.calculate_taxes_and_totals()` MUST be called before `so.save()` when modifying SO items
- Per-item measurement JSON storage with cloth_name switcher
- Stitching cost = 35 SAR per item qty (hardcoded)
- UOM filtering via Stock Settings `allow_uom_with_conversion_rate_defined_in_item`
- Number cards have `show_percentage_stats` disabled (Frappe bug workaround)
- Payment Entry hook recalculates advance via SQL sum on submit/cancel

## Build & Deploy
```bash
cd /Users/sayanthns/frappe-bench
bench build --app asafat_tailoring
bench --site mysite.local migrate
bench --site mysite.local clear-cache
bench restart  # if Python changes
```

## Common Issues
See `skills/troubleshooting/SKILL.md` for the complete list. Quick reference:
- UOM error → set `conversion_factor: 1` on appended items
- Commission TypeError → set all base_*/net_* fields on appended items
- Number cards gone → fix `filters_json` format, disable `show_percentage_stats`
- Totals wrong → call `calculate_taxes_and_totals()` before save
- Advance wrong → recalculate via `_recalculate_advance()` in bench console
