# Copyright (c) 2023, Albashq Alshwmy and contributors
# For license information, please see license.txt

import frappe
import datetime
from datetime import timedelta 
from frappe import _
from frappe.utils import flt, nowdate,getdate
from frappe.model.document import Document

class IncentiveCalculation(Document):
    def validate(self):	
        filters = frappe._dict()	
        filters["branch"] = self.branch
        filters["department"] = self.department
        filters["designation"] = self.designation
        filters["cost_center"] = self.cost_center
        filters["month"] = self.month	 
        filters["first_month"] = self.first_month	 
        filters["last_month"] = self.last_month	 

        emps_details = self.get_emp_list(filters)
        self.set('employees',[])		  		
        for emp in emps_details:					 
            self.append('employees',emp)
                         
    def validate_month(self):
        count =frappe.db.sql("""
                    SELECT COUNT(`tabIncentive Calculation`.name) AS count
                    FROM `tabIncentive Calculation`
                    JOIN `tabIncentive Employee` 
                    ON `tabIncentive Calculation`.name = `tabIncentive Employee`.parent
                    WHERE `tabIncentive Calculation`.docstatus = 1
                    AND `tabIncentive Calculation`.first_month BETWEEN %s AND %s and
                    """, (self.first_month, self.last_month), as_dict=True)	
        if int(count[0].count)>0:
            frappe.throw(_("There are incentives for this month already {}".format(count[0].count))) 
    
    def on_submit(self):
        self.create_journal_entry()
    
    def on_cancel(self):
        juo = frappe.db.sql_list(
                """SELECT `tabJournal Entry`.name 
                FROM 
                    `tabJournal Entry`
                JOIN 
                    `tabJournal Entry Account` 
                ON 
                    `tabJournal Entry`.name = `tabJournal Entry Account`.parent
                WHERE   `tabJournal Entry`.docstatus = 1 AND `tabJournal Entry Account`.reference_type='Incentive Calculation' AND `tabJournal Entry Account`.reference_name='{0}' """.format( self.name)		
            )
        for r  in juo : 
            frappe.get_doc("Journal Entry",r).cancel()
            
        # frappe.msgprint(_("This has been cancelled") + "{}".format(juo))

        frappe.db.sql("""
            UPDATE `tabGL Entry`
            SET 
                against_voucher_type = NULL,
                against_voucher = NULL
            WHERE against_voucher = %s
        """, (self.name,))

        frappe.db.commit()
        
    def get_emp_list(self, filters):
        cond = ""
        for f in ["branch", "designation"]:
            if filters.get(f):
                cond += " and `tabEmployee`." + f + " = " + frappe.db.escape(filters.get(f))

        for f in ["cost_center", "department"]:
            if filters.get(f):
                cond += " and `tabEmployee Incentive`." + f + " = " + frappe.db.escape(filters.get(f))	 
        # frappe.msgprint("{}".format(cond))
        return frappe.db.sql("""
            SELECT
                `tabEmployee Incentive`.employee, 
                `tabEmployee Incentive`.employee_name, 
                `tabEmployee Incentive`.incentive_amount AS amount,
                `tabEmployee Incentive`.custom_tax AS tax,
                `tabEmployee Incentive`.custom_net_amount AS net_amount,
                `tabEmployee Incentive`.cost_center,
                `tabEmployee Incentive`.department 
            FROM
                `tabEmployee Incentive`
            JOIN
                `tabEmployee` 
            ON	
                `tabEmployee Incentive`.employee = `tabEmployee`.name
            WHERE
                `tabEmployee Incentive`.docstatus = 1
                AND `tabEmployee Incentive`.first_month BETWEEN %s AND %s
                {0}
        """.format(cond), (self.first_month, self.last_month), as_dict=True)
        
    def create_journal_entry(self):
        if not self.total_amount:
            frappe.throw(_("The value is zero and the value is zero")) 

        # First Journal Entry
        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.posting_date
        je.voucher_type = "Bank Entry"
        je.company = self.company
        je.mode_of_payment = self.mode_of_payment
        je.cheque_no = self.name
        je.cheque_date = self.posting_date
        je.user_remark = "Payment against Incentive Calculation:" + " " + self.name + _("Month") + " " + self.month 

        if self.total_amount and self.expense_account:
            je.append("accounts", {
                "account": self.expense_account,
                "debit_in_account_currency":  self.total_amount,
                "debit":  self.total_amount,					 
                "reference_type": "Incentive Calculation",
                "reference_name": self.name,			 
                "cost_center": self.cost_center,			 
                "is_advance": "Yes",
            })

        if self.total_net_amount and self.payable:
            je.append("accounts", {
                "account": self.payable,
                "credit_in_account_currency": self.total_net_amount,
                "credit": self.total_net_amount,					 
                "reference_type": "Incentive Calculation",
                "reference_name": self.name,			 
                "cost_center": self.cost_center,			 
                "is_advance": "Yes",
            })

        if self.total_tax and self.tax:
            je.append("accounts", {
                "account": self.tax,
                "credit_in_account_currency": self.total_tax,
                "credit": self.total_tax,					 
                "reference_type": "Incentive Calculation",
                "reference_name": self.name,			 
                "cost_center": self.cost_center,			 
                "is_advance": "Yes",
            })

        je.save()

@frappe.whitelist()
def make_bank_entry(dt, dn):
    doc = frappe.get_doc(dt, dn)

    if doc.bank_entry:
        frappe.throw(
            _("Bank Entry <a href='/app/journal-entry/{0}' style='font-weight: bold;'>{0}</a> already exists.").format(doc.bank_entry),
            title=_("Bank Entry Exists")
        )

    # Make Bank Entry
    je = frappe.new_doc("Journal Entry")
    je.posting_date = doc.posting_date
    je.voucher_type = "Bank Entry"
    je.company = doc.company
    je.mode_of_payment = doc.mode_of_payment
    je.cheque_no = doc.name
    je.cheque_date = doc.posting_date
    je.user_remark = "Payment against Incentive Calculation:" + " " + doc.name + _("Month") + " " + doc.month 

    if doc.total_net_amount and doc.payable:
        je.append("accounts", {
            "account": doc.payable,
            "debit_in_account_currency": doc.total_net_amount,
            "debit": doc.total_net_amount,					 
            "reference_type": "Incentive Calculation",
            "reference_name": doc.name,			 
            "cost_center": doc.cost_center,			 
            "is_advance": "Yes",
        })

    if doc.total_net_amount and doc.receivable:
        je.append("accounts", {
            "account": doc.receivable,
            "credit_in_account_currency": doc.total_net_amount,
            "credit": doc.total_net_amount,					 
            "reference_type": "Incentive Calculation",
            "reference_name": doc.name,			 
            "cost_center": doc.cost_center,			 
            "is_advance": "Yes",
        })

    je.save()
    # je.submit()

    # Show success message with clickable link
    frappe.msgprint(
        _("Bank Entry created: <a href='/app/journal-entry/{0}' target='_blank'>{0}</a>").format(je.name)
    )

    frappe.db.sql("""
        UPDATE `tabIncentive Calculation`
        SET bank_entry = %s
        WHERE name = %s
    """, (je.name, doc.name))
    frappe.db.commit()