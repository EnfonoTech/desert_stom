from frappe import _


def get_data(data):
	# Add Tailoring Measurement to the connections
	data["transactions"].append(
		{
			"label": _("Tailoring"),
			"items": ["Tailoring Measurement"],
		}
	)
	return data
