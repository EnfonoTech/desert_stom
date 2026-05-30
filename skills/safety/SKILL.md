# Safety — Precautions, Dos and Don'ts

> Read this BEFORE touching any code. Every rule here exists because we broke something in production.

---

## Hard Rules — NEVER Do These

### 1. NEVER append items to a submitted Sales Order without setting ALL amount fields

**Why:** ERPNext validates every currency field on submitted documents. Missing fields cause `TypeError: unsupported operand type(s) for +: 'float' and 'NoneType'` in commission calculations and tax computations.

**What happens if you do:** The SO save will either throw a 500 error or silently corrupt totals. The user sees a broken order they can't fix without bench console.

**Required fields when appending to SO items:**
```python
so.append("items", {
    "item_code": ...,
    "item_name": ...,
    "qty": ...,
    "rate": ...,
    "amount": ...,
    "base_rate": ...,        # MUST SET — causes TypeError if None
    "base_amount": ...,      # MUST SET
    "net_rate": ...,         # MUST SET
    "net_amount": ...,       # MUST SET
    "base_net_rate": ...,    # MUST SET
    "base_net_amount": ...,  # MUST SET
    "uom": "Nos",
    "stock_uom": "Nos",
    "conversion_factor": 1,  # MUST SET — causes UOM Conversion Factor error
    "delivery_date": ...,
    "warehouse": ...,
})
```

**File:** `tailoring_measurement.py:_add_extras_to_sales_order()` (~line 80)

---

### 2. NEVER call `so.save()` without `so.calculate_taxes_and_totals()` first

**Why:** When modifying a submitted SO with `ignore_validate_update_after_submit`, the standard save does NOT recalculate totals. Your new items will exist in the child table but Total Quantity, Net Total, and Grand Total will remain stale.

**What happens if you do:** SO shows wrong totals. The "Total (SAR)" field won't include the extras. Outstanding amount will be wrong. Invoices created from this SO will have incorrect amounts.

**Correct pattern:**
```python
so.flags.ignore_validate_update_after_submit = True
so.flags.ignore_mandatory = True
# ... modify items ...
so.calculate_taxes_and_totals()   # ← THIS LINE IS CRITICAL
so.save()
so.reload()
```

**Files affected:** `tailoring_measurement.py` — both `_add_extras_to_sales_order()` and `_remove_extras_from_sales_order()`

---

### 3. NEVER use dict format for Number Card `filters_json`

**Why:** Frappe's `get_percentage_difference()` function expects list-of-lists format. Dict format triggers `TypeError: 'NoneType' object is not callable` which silently kills all number cards on the workspace.

**Wrong:** `{"docstatus": 1}`
**Right:** `[["Sales Order", "docstatus", "=", 1]]`

**What happens if you do:** The entire workspace dashboard goes blank. Number cards disappear with no visible error — only traceback in bench console.

**File:** `install.py:_setup_number_cards()` (~line 140)

---

### 4. NEVER delete or reorder SO items manually when extras have been added

**Why:** The `_remove_extras_from_sales_order()` function removes extras by iterating in reverse from the end of the items list. It assumes extras are always the last items.

**What happens if you do:** Cancelling a measurement will remove the wrong items from the SO, potentially deleting the customer's original order items.

**File:** `tailoring_measurement.py:_remove_extras_from_sales_order()` (~line 120)

---

### 5. NEVER modify `advance_collected` or `outstanding_amount` directly via frappe.db.set_value outside the proper hooks

**Why:** There are TWO places that update these fields: `api.py:create_advance_payment()` and `events/payment_entry.py:update_so_advance()`. The PE hook recalculates from ALL submitted PEs via SQL. If you manually set values, the next PE submit/cancel will overwrite your changes.

**What happens if you do:** Advance amounts become inconsistent. Customer may be shown wrong outstanding balance.

---

### 6. NEVER enable `show_percentage_stats` on Number Cards that filter on custom fields

**Why:** Known Frappe v15 bug. The percentage calculation fails when filters reference custom fields like `stitching_status`.

**Fix if accidentally enabled:**
```python
# bench console
card = frappe.get_doc("Number Card", "Card Name")
card.show_percentage_stats = 0
card.save()
frappe.db.commit()
```

---

## ALWAYS Do These

### Before modifying submitted documents:
1. Set `doc.flags.ignore_validate_update_after_submit = True`
2. Set `doc.flags.ignore_mandatory = True`
3. Call `doc.calculate_taxes_and_totals()` before save
4. Call `doc.reload()` after save

### Before creating Payment Entries programmatically:
1. Verify the Mode of Payment account exists: `frappe.get_value("Mode of Payment Account", ...)`
2. If no account found, throw a clear error — don't let it silently fail
3. Use `ignore_permissions=True` since these are system-generated
4. Always set `reference_doctype` and `reference_name` in allocations

### Before creating Sales Invoices programmatically:
1. Call `si.set_advances()` to auto-allocate existing advance payments
2. Copy taxes from SO to SI (they don't auto-populate)
3. Set `update_stock=1` if no separate Delivery Note will be created

### Before deploying any change:
1. Run `bench build --app desert_stom`
2. Run `bench --site mysite.local migrate`
3. Run `bench --site mysite.local clear-cache`
4. Test the full workflow: SO → Measurement → Advance → Status transitions → Complete Order
5. Verify number cards still appear on workspace
6. Verify print formats still render

---

## Decision Matrix

| Situation | Do This | Don't Do This |
|-----------|---------|---------------|
| Need to add items to submitted SO | Use `_add_extras_to_sales_order()` pattern with ALL fields | Don't use `so.append("items", {...})` with minimal fields |
| Need to update SO totals after item change | Call `calculate_taxes_and_totals()` then `save()` | Don't call `save()` alone — totals won't update |
| Need to track advance payments | Use PE hook in `events/payment_entry.py` | Don't manually increment/decrement `advance_collected` |
| Need to change stitching_status | Use `doc.db_set("stitching_status", value)` on submitted doc | Don't use `doc.stitching_status = value; doc.save()` — triggers full validation |
| Need to create Number Cards | Use list-of-lists for filters_json | Don't use dict format for filters |
| Need to remove extras from SO | Cancel the Tailoring Measurement (triggers `_remove_extras_from_sales_order()`) | Don't manually delete SO item rows |
| Need to fix wrong advance_collected | Cancel and re-submit the Payment Entry | Don't manually set the field — PE hook will overwrite |
| Rate is 0 but amount has value | Derive rate: `rate = amount / qty` | Don't leave rate as 0 — SO line will show 0.00 |
| Need to query revenue for SO | Sum `grand_total` from linked submitted Sales Invoices | Don't use SO `grand_total` if invoices exist (may have discounts) |
| Customer phone needs formatting | Strip spaces/dashes, add 966 prefix for Saudi numbers | Don't assume all numbers have country code |

---

## Code Changes Checklist

Before deploying ANY change, verify:

- [ ] All SO item append operations include ALL 14 required fields (see Hard Rule #1)
- [ ] Every `so.save()` on submitted docs is preceded by `so.calculate_taxes_and_totals()`
- [ ] Number Card filters use `[["DocType", "field", "operator", "value"]]` format
- [ ] No direct SQL writes to `advance_collected` or `outstanding_amount`
- [ ] `conversion_factor: 1` is set on all programmatically added items
- [ ] `bench build --app desert_stom` completes without errors
- [ ] `bench --site mysite.local migrate` runs clean
- [ ] Workspace number cards render after deployment
- [ ] Full workflow test passes (SO → Measurement with extras → Advance → Complete)
- [ ] Print formats render for: Measurement Card, Tailoring Order, Tailoring Invoice, Delivery Slip
- [ ] Payment Entry submit AND cancel both update advance_collected correctly
- [ ] Measurement cancel removes extras AND reverts SO status
- [ ] No Python `None` values in any currency field calculations

---

## Common Pitfalls That Cause Production Issues

### 1. The "Dirty Form" Trap
**Symptom:** After API calls update SO fields (stats, advance), the form shows unsaved changes indicator.
**Why:** Setting field values via `frm.set_value()` marks the form dirty.
**Fix:** Call `frm.dirty(false)` after programmatic field updates. See `sales_order.js` refresh handler.

### 2. The "setTimeout" Fragility
**Symptom:** Measurement dialog sometimes doesn't populate fields on the new Tailoring Measurement form.
**Why:** `sales_order.js:show_measurement_dialog()` uses `setTimeout(300ms, 800ms, 1500ms)` to set values after Frappe form renders. Slow connections may need longer delays.
**Impact:** Medium — user can manually fill fields, but it's annoying.
**File:** `sales_order.js:show_measurement_dialog()` (~line 200)

### 3. The "First Item" Revenue Assumption
**Symptom:** Daily Sales Collection report shows wrong SO reference for some invoices.
**Why:** Report LEFT JOINs on `idx=1` (first SI item) to get `sales_order` reference. If first item has no SO link, the reference is empty.
**File:** `daily_sales_collection.py` (~line 40)

### 4. The "Extras at End" Assumption
**Symptom:** Wrong items removed when measurement is cancelled.
**Why:** `_remove_extras_from_sales_order()` removes from end of list in reverse. If items were manually reordered, wrong items get removed.
**File:** `tailoring_measurement.py:_remove_extras_from_sales_order()`
