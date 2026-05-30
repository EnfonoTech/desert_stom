# Troubleshooting — Known Issues & Fixes

> Every bug pattern encountered during development, with exact diagnosis and fix steps.

---

## Quick Reference: "If You See X, Check Y"

| Error / Symptom | Check This First |
|-----------------|-----------------|
| "UOM Conversion Factor" error on measurement submit | `conversion_factor` missing in `_add_extras_to_sales_order()` |
| `TypeError: unsupported operand type(s) for +: 'float' and 'NoneType'` | Missing `base_rate`, `base_amount`, `net_rate`, `net_amount` on appended SO items |
| Number cards blank on workspace | `filters_json` format (must be list-of-lists, not dict) or `show_percentage_stats` enabled |
| `TypeError: 'NoneType' object is not callable` in number card | Disable `show_percentage_stats` on the number card |
| SO totals not including extras | `calculate_taxes_and_totals()` not called before `save()` |
| Advance not updating on PE cancel | Check `events/payment_entry.py` hook is registered in `hooks.py` |
| Extras amount showing 0.00 in SO | Rate derivation missing: `rate = amount / qty` when rate is 0 |
| Wrong items removed on measurement cancel | Items were reordered manually — extras must stay at end of SO items |
| Dirty form indicator after API stat update | Missing `frm.dirty(false)` after `frm.set_value()` calls |
| Measurement dialog fields not populating | setTimeout delays too short for slow connections |
| Print format not rendering | Run `setup_print_formats()` and `frappe.db.commit()` in bench console |
| Custom buttons not appearing on SO | Check `docstatus === 1` and `stitching_status` value |
| WhatsApp not opening | Phone number format — needs `966` prefix for Saudi numbers |
| Report showing wrong SO reference | First SI item (`idx=1`) doesn't have `sales_order` linked |
| Revenue showing 0 in stats | No submitted Sales Invoice linked to SO items |

---

## Bug Pattern #1: UOM Conversion Factor Error

### Symptom
Error when submitting a Tailoring Measurement that has extra items:
```
Sales Order Item Row #2: Value missing for: UOM Conversion Factor
```

### Root Cause
When appending items to a submitted Sales Order, ERPNext requires `conversion_factor` to be explicitly set. The field doesn't default to 1 for programmatically added rows.

### Diagnosis
1. Check `tailoring_measurement.py:_add_extras_to_sales_order()`
2. Look at the dict being passed to `so.append("items", {...})`
3. Verify `conversion_factor`, `uom`, and `stock_uom` are all present

### Fix
```python
so.append("items", {
    # ... other fields ...
    "uom": "Nos",
    "stock_uom": "Nos",
    "conversion_factor": 1,  # ← THIS MUST BE SET
})
```

### Prevention
Always include `conversion_factor: 1` when programmatically appending items to any submitted document with UOM fields.

---

## Bug Pattern #2: Commission Calculation TypeError

### Symptom
```
TypeError: unsupported operand type(s) for +: 'float' and 'NoneType'
```
Occurs when saving a Sales Order that has extras appended from measurement submission.

### Root Cause
ERPNext's commission calculation iterates over all SO items and adds up `base_amount`, `net_amount`, etc. When these fields are `None` (not set), Python can't add `float + None`.

### Diagnosis
1. Open the SO in question
2. Check the extras rows — inspect `base_rate`, `base_amount`, `net_rate`, `net_amount`, `base_net_rate`, `base_net_amount`
3. If any are `None` or missing, this is the cause

### Fix
Set ALL monetary fields when appending items:
```python
item_data = {
    "rate": rate,
    "amount": amount,
    "base_rate": rate,
    "base_amount": amount,
    "net_rate": rate,
    "net_amount": amount,
    "base_net_rate": rate,
    "base_net_amount": amount,
}
```

### Prevention
See Safety SKILL.md — Hard Rule #1 lists all 14 required fields.

---

## Bug Pattern #3: Number Cards Disappear

### Symptom
The workspace dashboard shows empty space where number cards should be. No visible error in browser.

### Root Cause (Variant A)
`filters_json` is in dict format `{"docstatus": 1}` instead of list-of-lists `[["Sales Order", "docstatus", "=", 1]]`.

### Root Cause (Variant B)
`show_percentage_stats` is enabled (set to 1), triggering Frappe's `get_percentage_difference()` function which fails on custom fields with `TypeError: 'NoneType' object is not callable`.

### Diagnosis
```bash
bench --site mysite.local console
>>> card = frappe.get_doc("Number Card", "Total Orders")
>>> print(card.filters_json)    # Should be list-of-lists
>>> print(card.show_percentage_stats)  # Should be 0
```

Also check bench console output / `Error Log` for:
```
TypeError: 'NoneType' object is not callable
File ".../frappe/desk/doctype/number_card/number_card.py", line XX, in get_percentage_difference
```

### Fix
```python
# bench console
for name in ["Total Orders", "Orders Under Processing", "Ready to Deliver", "Orders Completed"]:
    card = frappe.get_doc("Number Card", name)
    card.show_percentage_stats = 0
    # Ensure filters are list-of-lists format
    card.save()
frappe.db.commit()
```

### Prevention
In `install.py`, always:
1. Use list-of-lists for `filters_json`
2. Set `show_percentage_stats = 0` for cards that filter on custom fields

---

## Bug Pattern #4: SO Totals Not Updated After Extras

### Symptom
After submitting a measurement with extras:
- SO `Total Quantity` shows only original items (e.g., 1 instead of 2)
- SO `Total (SAR)` doesn't include extras amount
- SO `Grand Total` is wrong

### Root Cause
When modifying a submitted SO with `ignore_validate_update_after_submit`, calling `so.save()` alone does NOT trigger the standard `calculate_taxes_and_totals()` method. The new items exist in the database but totals are stale.

### Diagnosis
1. Open the SO after measurement with extras
2. Check if `Total Quantity` matches actual item count
3. Check if `Grand Total` includes extras amounts
4. If totals are stale, this is the issue

### Fix
Add `so.calculate_taxes_and_totals()` before `so.save()`:
```python
so.flags.ignore_validate_update_after_submit = True
so.flags.ignore_mandatory = True
# ... append items ...
so.calculate_taxes_and_totals()  # ← ADD THIS
so.save()
so.reload()
```

### Prevention
ALWAYS call `calculate_taxes_and_totals()` before saving any document where you've modified child table items.

---

## Bug Pattern #5: Advance Not Updating on PE Cancel

### Symptom
When a Payment Entry linked to a Sales Order is cancelled, the SO's `advance_collected` and `outstanding_amount` fields don't update.

### Root Cause
Originally, only `api.py:create_advance_payment()` updated the advance fields (on creation). There was no hook for PE cancellation. The fix was to add `events/payment_entry.py` with a proper recalculation hook.

### Diagnosis
1. Cancel a Payment Entry linked to an SO
2. Reload the SO
3. Check if `advance_collected` still shows the old amount

### Fix (Already Applied)
The `events/payment_entry.py:update_so_advance()` hook handles both submit and cancel. It recalculates by summing ALL submitted PE allocations via SQL:

```sql
SELECT COALESCE(SUM(per.allocated_amount), 0)
FROM `tabPayment Entry Reference` per
JOIN `tabPayment Entry` pe ON pe.name = per.parent
WHERE per.reference_doctype = 'Sales Order'
    AND per.reference_name = %s
    AND pe.docstatus = 1
```

If still broken, verify `hooks.py` has:
```python
"Payment Entry": {
    "on_submit": "asafat_tailoring.events.payment_entry.update_so_advance",
    "on_cancel": "asafat_tailoring.events.payment_entry.update_so_advance",
},
```

### Prevention
Never create payment-related hooks without handling BOTH submit and cancel events.

---

## Bug Pattern #6: Extras Rate Shows 0.00

### Symptom
Extra items appended to SO show `Rate: 0.00` and `Amount: 0.00` even though the measurement extra item had values.

### Root Cause
In the Measurement Extra Item child table, the user might enter only the `amount` field (not `rate`). When the code copies `rate` directly, it gets 0 because rate was never set — only amount was.

### Diagnosis
1. Check the Tailoring Measurement's `extra_items` table
2. Compare `rate` vs `amount` — if rate is 0 but amount has a value, this is the issue

### Fix (Already Applied)
Rate derivation logic in `_add_extras_to_sales_order()`:
```python
rate = flt(extra.rate)
amount = flt(extra.amount)
if rate == 0 and amount > 0 and flt(extra.qty) > 0:
    rate = amount / flt(extra.qty)
```

### Prevention
Always derive rate from amount/qty as a fallback when rate is 0.

---

## Bug Pattern #7: Dirty Form After Stats Refresh

### Symptom
After opening a submitted SO, the form shows "Not Saved" indicator even though the user made no changes.

### Root Cause
The `get_so_stats` API call updates multiple SO fields (`measurement_count`, `item_cost`, etc.) via `frm.set_value()` in JavaScript. Each `set_value()` call marks the form as dirty.

### Diagnosis
Open any submitted SO → check if "Not Saved" indicator appears immediately.

### Fix
After all `set_value()` calls in the stats callback, clear the dirty flag:
```javascript
frappe.call({
    method: "asafat_tailoring.api.get_so_stats",
    args: { so_name: frm.doc.name },
    callback: function(r) {
        // ... set values ...
        frm.dirty(false);  // ← Clear dirty state
    }
});
```

### Prevention
Always call `frm.dirty(false)` after programmatically setting field values that the user didn't change.

---

## Bug Pattern #8: Measurement Dialog Population Failure

### Symptom
When clicking "Add Measurement" on SO, the new Tailoring Measurement form opens but fields (items, measurements from previous record) are not populated.

### Root Cause
`sales_order.js:show_measurement_dialog()` uses `setTimeout` with delays of 300ms, 800ms, and 1500ms to set field values after Frappe loads the new form. On slow connections or heavy pages, these delays may not be sufficient.

### Diagnosis
1. Open browser developer console
2. Click "Add Measurement"
3. Watch for console errors about fields not found
4. Check if measurement_items table and measurements_json are populated

### Workaround
The code has a page-change event listener as a fallback, but it's timing-dependent. If fields are missing:
1. User can manually select items and enter measurements
2. Or reload the measurement form and try the "Copy from Latest" option

### Potential Fix
Replace setTimeout with `frappe.after_ajax()` or `frm.events.onload_post_render` hook for more reliable timing.

---

## Bug Pattern #9: Revenue Shows Wrong Amount

### Symptom
In Profit & Loss section of SO, `Revenue` shows the SO's grand total instead of the actual invoiced amount (which may differ due to discounts).

### Root Cause
`api.py:get_so_stats()` uses a fallback: if no submitted Sales Invoice is found linked to the SO items, it uses `so.grand_total` as revenue. This is by design but can be confusing if:
- Invoices exist but are in Draft status
- Invoices were created outside the app's workflow
- Partial invoicing was done

### Diagnosis
```python
# bench console
si_total = frappe.db.sql("""
    SELECT COALESCE(SUM(si.grand_total), 0)
    FROM `tabSales Invoice` si
    JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
    WHERE sii.sales_order = %s AND si.docstatus = 1
""", "SO-2026-00001")[0][0]
print(f"SI total: {si_total}")
```

If result is 0 but invoices exist, they're either in Draft or not linked to the SO.

---

## Bug Pattern #10: Print Format Not Rendering

### Symptom
Print preview shows default ERPNext format instead of custom Tailoring format, or shows raw HTML/Jinja errors.

### Root Cause
Print formats might not have been created (if `setup_print_formats.py` wasn't run) or the property setter assigning defaults might be missing.

### Diagnosis
```python
# bench console
# Check if print formats exist
for name in ["Measurement Card", "Tailoring Order", "Tailoring Invoice", "Delivery Slip"]:
    exists = frappe.db.exists("Print Format", name)
    print(f"{name}: {'EXISTS' if exists else 'MISSING'}")

# Check property setters
for dt in ["Sales Order", "Sales Invoice"]:
    pf = frappe.db.get_value("Property Setter",
        {"doc_type": dt, "property": "default_print_format"}, "value")
    print(f"{dt} default: {pf}")
```

### Fix
```python
# bench console
from asafat_tailoring.setup_print_formats import setup_print_formats
setup_print_formats()
frappe.db.commit()
```

---

## Bug Pattern #11: WhatsApp Message Not Sent

### Symptom
Clicking status transition buttons that should send WhatsApp doesn't open WhatsApp, or opens with wrong number.

### Root Cause
Phone number normalization in `sales_order.js:send_status_whatsapp()` may fail for:
- Numbers without country code
- Numbers with unexpected format (e.g., `+1-555-1234`)
- Empty `customer_phone` field

### Diagnosis
1. Check SO's `customer_phone` field value
2. Open browser console
3. Click the status button
4. Check if `window.open()` was called with correct URL

### Fix
Ensure customer has `custom_phone` set in the correct format. The normalization logic:
- Strips spaces, dashes, parentheses
- If no `+` or `00` prefix, prepends `966` (Saudi)
- If starts with `0`, removes leading `0` and prepends `966`

---

## Bug Pattern #12: Complete Order Creates Wrong Payment Amount

### Symptom
The Payment Entry created during "Complete Order" has wrong amount — either too much or too little.

### Root Cause
The payment calculation in `show_completion_dialog()` is:
```
payment_amount = grand_total - discount - advance_paid
```

If the SO's `advance_collected` is stale (not recalculated after PE cancellation), the payment amount will be wrong.

### Diagnosis
1. Check SO's `advance_collected` against actual submitted PEs
2. Run advance recalculation:
   ```python
   from asafat_tailoring.events.payment_entry import _recalculate_advance
   _recalculate_advance("SO-2026-00001")
   frappe.db.commit()
   ```

---

## System-Level Issues

### Bench won't start
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Check if MariaDB is running
mysql -u root -p -e "SELECT 1"

# Check for port conflicts
lsof -i :8000  # Frappe web
lsof -i :9000  # Socketio
```

### Build fails
```bash
# Clear node modules and rebuild
cd /Users/sayanthns/frappe-bench
rm -rf node_modules
yarn install
bench build --app asafat_tailoring
```

### Migration fails
```bash
# Check for syntax errors in Python files
cd /Users/sayanthns/frappe-bench/apps/asafat_tailoring
python -m py_compile asafat_tailoring/api.py
python -m py_compile asafat_tailoring/install.py
python -m py_compile asafat_tailoring/events/payment_entry.py
python -m py_compile asafat_tailoring/events/sales_order.py

# If doctype JSON is corrupted, re-export from site
bench --site mysite.local export-doc "DocType" "Tailoring Measurement"
```

### Custom fields missing after migration
```bash
bench --site mysite.local console
>>> from asafat_tailoring.install import after_install
>>> after_install()
>>> frappe.db.commit()
```
