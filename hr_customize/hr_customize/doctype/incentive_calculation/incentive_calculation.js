// Copyright (c) 2023, Albashq Alshwmy and contributors
// For license information, please see license.txt
frappe.ui.form.on("Incentive Calculation", {
    get_incentive_employee: function (frm) {
        frm.events.get_employees(frm);
    },
    get_employees: function (frm) {
        return frappe
            .call({
                doc: frm.doc,
                method: "get_employees",
                freeze: true,
            })
            .then((r) => {
                if (r.docs && r.docs[0].employees) {
                    frm.dirty();
                    frm.save();
                    frm.refresh();
                }
            });
    },
    refresh: (frm) => {
        if (frm.doc.docstatus == 1 && !frm.doc.bank_entry)
            frm.add_custom_button(__("Make Bank Entry"), function () {
                frm.events.make_payment_entry(frm);
            });

        frm.set_query("cost_center", function () {
            return {
                filters: {
                    is_group: 0,
                    // "root_type":['in',["Cash","Bank"]],
                    company: frm.doc.company,
                },
            };
        });
        frm.set_query("department", function () {
            return {
                filters: {
                    is_group: 0,
                },
            };
        });
        frm.set_query("form_account", function () {
            return {
                filters: {
                    is_group: 0,
                    // "root_type":"Payable",
                    company: frm.doc.company,
                },
            };
        });
        frm.set_query("to_account", function () {
            return {
                filters: {
                    is_group: 0,
                    // "root_type":"Payable",
                    company: frm.doc.company,
                },
            };
        });
        frm.set_query("receivable", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    account_type: ["in", ["Cash", "Bank"]],
                    is_group: 0,
                },
            };
        });
        frm.set_query("form_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Expense",
                    account_type: "Expense Account",
                    is_group: 0,
                },
            };
        });
        frm.set_query("to_account", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    root_type: "Liability",
                    is_group: 0,
                },
            };
        });
    },
    validate: function (frm) {
        var total_amount = 0;
        var total_tax = 0;
        var total_net_amount = 0;

        $.each(frm.doc.employees || [], function (i, d) {
            total_amount += d.amount || 0;
            total_tax += d.tax || 0;
            total_net_amount += d.net_amount || 0;
        });
        frm.set_value("total_amount", total_amount);
        frm.set_value("total_tax", total_tax);
        frm.set_value("total_net_amount", total_net_amount);
    },
    make_payment_entry: function (frm) {
        var method =
            "hr_customize.hr_customize.doctype.incentive_calculation.incentive_calculation.make_bank_entry";

        return frappe.call({
            method: method,
            args: {
                dt: frm.doc.doctype,
                dn: frm.doc.name,
            },
            callback: function (r) {
                var doclist = frappe.model.sync(r.message);
                frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
            },
        });
    },
    first_month: function (frm) {
        frappe.call({
            method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date",
            args: {
                frequency: "Monthly",
                start_date: frm.doc.first_month,
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value("last_month", r.message.end_date);
                }
            },
        });
    },
});
