from frappe import _
 
def get_data():
	return {
		"fieldname": "incentive_calculation",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
			"Payment Entry": "reference_name",
		},
		"transactions": [{"items": ["Journal Entry"]}],
	}