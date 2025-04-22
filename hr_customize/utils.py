import frappe
# Letter Head
from frappe import _
@frappe.whitelist()
def get_leave_app(name):	
	data2 = frappe.db.sql( """ select  sum(total_leave_days)  as total,status from `tabLeave Application` t where t.employee=%s  group by status""" ,name,as_dict=1)
	data1 = frappe.db.sql( """ select  leave_type,from_date ,to_date,total_leave_days  as total,status,description from `tabLeave Application` t where t.employee=%s  order by from_date""" ,name,as_dict=1)
	return {'data1':data1,'data2':data2 }