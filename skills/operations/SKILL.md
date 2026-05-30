# Operations — Day-to-Day Workflows

> How to build, deploy, debug, and maintain the Asafat Tailoring app.

---

## Environment Setup

### Prerequisites
- Python ≥3.10
- Node.js (for asset compilation)
- MariaDB 10.x
- Redis
- Frappe Bench CLI

### Key Paths
```
Bench:     /Users/sayanthns/frappe-bench
App:       /Users/sayanthns/frappe-bench/apps/asafat_tailoring
Site:      /Users/sayanthns/frappe-bench/sites/mysite.local
Assets:    /Users/sayanthns/frappe-bench/sites/assets/asafat_tailoring
Logs:      /Users/sayanthns/frappe-bench/logs/
```

---

## Build & Deploy

### Standard Deploy (after code changes)

```bash
cd /Users/sayanthns/frappe-bench

# 1. Build frontend assets (JS/CSS)
bench build --app asafat_tailoring

# 2. Run database migrations (if doctype/field changes)
bench --site mysite.local migrate

# 3. Clear all caches
bench --site mysite.local clear-cache

# 4. Restart services (if Python changes)
bench restart
```

### Quick Deploy (CSS/JS only — no Python changes)

```bash
cd /Users/sayanthns/frappe-bench
bench build --app asafat_tailoring
bench --site mysite.local clear-cache
# No restart needed — browser hard-refresh (Ctrl+Shift+R) loads new assets
```

### Quick Deploy (Python only — no JS/CSS changes)

```bash
cd /Users/sayanthns/frappe-bench
bench restart
# Or for development: bench will auto-reload if using `bench start`
```

---

## Fixture Management

### Export fixtures (after changing custom fields, print formats, property setters)

```bash
cd /Users/sayanthns/frappe-bench

# Export all fixtures defined in hooks.py
bench --site mysite.local export-fixtures --app asafat_tailoring
```

This exports to `asafat_tailoring/fixtures/`:
- `custom_field.json` — all custom fields tagged to this app
- `print_format.json` — print formats from "Asafat Tailoring" module
- `property_setter.json` — property setters for Sales Order and Sales Invoice

### Import fixtures (on new site or after migration)

```bash
bench --site mysite.local migrate
# Fixtures auto-import during migrate if defined in hooks.py
```

### Manual fixture import

```bash
bench --site mysite.local import-doc asafat_tailoring/fixtures/custom_field.json
```

---

## Install on New Site

```bash
cd /Users/sayanthns/frappe-bench

# 1. Get the app
bench get-app https://github.com/sayanthns/asafat_tailoring.git

# 2. Install on site
bench --site mysite.local install-app asafat_tailoring

# 3. This triggers after_install() which:
#    - Creates custom fields on Sales Order and Customer
#    - Removes deprecated fields
#    - Sets up search fields
#    - Enables UOM filtering in Stock Settings
#    - Creates "Extras" item group
#    - Creates 4 Number Cards for workspace dashboard

# 4. Build assets
bench build --app asafat_tailoring

# 5. Set up print formats (if not created by fixtures)
bench --site mysite.local console
>>> from asafat_tailoring.setup_print_formats import setup_print_formats
>>> setup_print_formats()
>>> frappe.db.commit()
```

---

## Accessing Logs

### Bench logs (all services)
```bash
# Real-time logs during development
cd /Users/sayanthns/frappe-bench
bench start
# Logs appear in terminal

# Or check log files
tail -f /Users/sayanthns/frappe-bench/logs/web.log
tail -f /Users/sayanthns/frappe-bench/logs/worker.log
```

### Frappe error logs (in-app)
```
Browser → URL bar → /app/error-log
# Or
bench --site mysite.local console
>>> frappe.get_all("Error Log", limit=10, order_by="creation desc")
```

### MariaDB query log
```bash
bench --site mysite.local mariadb
MariaDB> SHOW VARIABLES LIKE 'general_log%';
```

---

## Bench Console (Python REPL)

```bash
cd /Users/sayanthns/frappe-bench
bench --site mysite.local console
```

### Common console operations

```python
# Check a Sales Order
so = frappe.get_doc("Sales Order", "SO-2026-00001")
print(so.stitching_status, so.advance_collected, so.outstanding_amount)

# Fix wrong advance_collected
from asafat_tailoring.events.payment_entry import _recalculate_advance
_recalculate_advance("SO-2026-00001")
frappe.db.commit()

# Fix number card filter format
card = frappe.get_doc("Number Card", "Total Orders")
card.filters_json = '[["Sales Order","docstatus","=",1]]'
card.show_percentage_stats = 0
card.save()
frappe.db.commit()

# Check all custom fields
fields = frappe.get_all("Custom Field",
    filters={"module": "Asafat Tailoring"},
    fields=["name", "dt", "fieldname", "fieldtype"])
for f in fields:
    print(f"{f.dt}.{f.fieldname} ({f.fieldtype})")

# Re-run post-install setup
from asafat_tailoring.install import after_install
after_install()
frappe.db.commit()

# Recreate print formats
from asafat_tailoring.setup_print_formats import setup_print_formats
setup_print_formats()
frappe.db.commit()
```

---

## Rollback a Bad Deploy

### If migration broke something:

```bash
cd /Users/sayanthns/frappe-bench

# 1. Revert code
git -C apps/asafat_tailoring log --oneline -5   # find the good commit
git -C apps/asafat_tailoring checkout <good-commit-hash>

# 2. Re-migrate (applies rollback patches if any)
bench --site mysite.local migrate

# 3. Rebuild and restart
bench build --app asafat_tailoring
bench --site mysite.local clear-cache
bench restart
```

### If custom fields were corrupted:

```bash
bench --site mysite.local console
>>> # Delete and recreate
>>> frappe.db.delete("Custom Field", {"module": "Asafat Tailoring"})
>>> frappe.db.commit()
>>> from asafat_tailoring.install import after_install
>>> after_install()
>>> frappe.db.commit()
```

### If number cards disappeared:

```bash
bench --site mysite.local console
>>> # Delete and recreate
>>> for name in ["Total Orders", "Orders Under Processing", "Ready to Deliver", "Orders Completed"]:
...     if frappe.db.exists("Number Card", name):
...         frappe.delete_doc("Number Card", name)
>>> frappe.db.commit()
>>> from asafat_tailoring.install import _setup_number_cards
>>> _setup_number_cards()
>>> frappe.db.commit()
```

---

## Common Workflows

### Adding a new custom field to Sales Order

1. Define it in `install.py:get_custom_fields()` function
2. Run `after_install()` via bench console to create it
3. Export fixtures: `bench --site mysite.local export-fixtures --app asafat_tailoring`
4. If it needs `allow_on_submit`: set that property in the field definition
5. Build and clear cache

### Adding a new API endpoint

1. Add function to `api.py` with `@frappe.whitelist()` decorator
2. Call from JS: `frappe.call({ method: "asafat_tailoring.api.your_function", args: {...} })`
3. Restart bench (Python change)

### Adding a new document event hook

1. Create handler in `events/` directory
2. Register in `hooks.py` under `doc_events`
3. Restart bench

### Modifying a print format

1. Edit the HTML template in `setup_print_formats.py`
2. Run via bench console:
   ```python
   from asafat_tailoring.setup_print_formats import setup_print_formats
   setup_print_formats()
   frappe.db.commit()
   ```
3. Export fixtures: `bench --site mysite.local export-fixtures --app asafat_tailoring`

### Modifying the workspace

1. Edit workspace in browser: `/app/workspace/Asafat Tailoring`
2. Or modify JSON directly: `workspace/asafat_tailoring/asafat_tailoring.json`
3. If modified in browser, export: `bench --site mysite.local export-fixtures --app asafat_tailoring`

---

## Environment Variables

This app does not use custom environment variables. All configuration is via:

- **Site config:** `/Users/sayanthns/frappe-bench/sites/mysite.local/site_config.json`
- **ERPNext Settings:** Stock Settings, Company defaults, Mode of Payment accounts
- **Hardcoded constants:** Stitching cost (35 SAR), naming series pattern, WhatsApp URL format

---

## Git Workflow

```bash
cd /Users/sayanthns/frappe-bench/apps/asafat_tailoring

# Check status
git status

# Stage and commit
git add -A
git commit -m "description of changes"

# Push to GitHub
git push origin main
```

### Before committing:
1. Ensure fixtures are exported if custom fields/print formats changed
2. Run `bench build --app asafat_tailoring` to verify no build errors
3. Test the full workflow on local site

---

## Monitoring & Health Checks

### Quick health check after deploy:

1. Open workspace: `/app/asafat-tailoring` — verify 4 number cards appear
2. Open any Sales Order — verify stitching_status indicator shows
3. Open a submitted SO — verify custom buttons appear (Add Measurement, Collect Advance, etc.)
4. Create a test measurement — verify extras are added to SO with correct totals
5. Check print preview — verify Measurement Card renders
6. Check error log: `/app/error-log` — should be clean

### Verify custom fields exist:
```bash
bench --site mysite.local console
>>> len(frappe.get_all("Custom Field", filters={"dt": "Sales Order", "module": "Asafat Tailoring"}))
# Should return 12
```
