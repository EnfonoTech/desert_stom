import frappe


def on_submit(doc, method):
	if not doc.stitching_status:
		doc.db_set("stitching_status", "Order")
