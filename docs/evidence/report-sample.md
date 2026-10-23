# SoD Review Report

Generated on: 2026-10-23

## Summary

- High: 5
- Medium: 2
- Low: 1

## Findings

### SOD-001 | U001
- Severity: High
- Roles: Vendor_Master_Maintain + Payment_Release
- Source: model

Holding both the Vendor\_Master\_Maintain and Payment\_Release roles creates a significant risk because a single user has the ability to both create vendor records and authorize payments. This combination allows for the potential to create a fictitious vendor and subsequently release payments to that entity. This violates the principle of segregation of duties, directly contradicting SOD-001. Review should focus on immediately removing the Payment\_Release role from U001 or implementing stricter controls to limit access to vendor creation.

### SOD-002 | U002
- Severity: High
- Roles: Purchase_Requester + Purchase_Approver
- Source: model

Holding both the Purchase\_Requester and Purchase\_Approver roles for user U002 creates a significant conflict of interest as they could independently initiate and authorize a purchase. This violates the segregation of duties principle outlined in SOD-002, increasing the risk of unauthorized or improper spending. You must review U002's role assignments to determine if this dual responsibility is necessary for their job function. Consider removing one of these conflicting roles to enforce proper segregation of duties.

### SOD-003 | U003
- Severity: High
- Roles: Journal_Entry_Create + Journal_Entry_Approve
- Source: model

Holding both the Journal Entry Create and Approve roles for user U003 presents a significant risk under SOD-003. This dual access allows the user to initiate and then approve their own journal entries, bypassing necessary segregation of duties. This conflict increases the potential for unauthorized or fraudulent accounting transactions. You must review if this combination of roles is strictly necessary for U003's job function.

### SOD-006 | U004
- Severity: High
- Roles: User_Admin + Audit_Log_Admin
- Source: model

Holding both User\_Admin and Audit\_Log\_Admin roles for user U004 presents a significant risk because this user has the power to both grant access and subsequently erase the evidence of those actions. This violates the principle of separation of duties by allowing a single individual to perform both the administrative function and the oversight function. To mitigate this, review the necessity of U004 holding both permissions and determine if these roles can be separated to enforce proper segregation of duties.

### SOD-004 | U010
- Severity: High
- Roles: Payroll_Maintain + Payroll_Approve
- Source: model

Holding both the Payroll_Maintain and Payroll_Approve roles for user U010 creates a significant risk because the user has the ability to both alter pay data and authorize the payroll run. This combination violates the segregation of duties principle outlined in SOD-004. A single individual could potentially make unauthorized changes and then approve those changes, leading to financial misstatements or fraudulent payroll activities. Review should focus on separating these functions to ensure that maintenance and approval tasks are performed by different individuals.

### SOD-005 | U007
- Severity: Medium
- Roles: Bank_Reconcile + Payment_Release
- Source: model

Holding both the Bank\_Reconcile and Payment\_Release roles presents a significant risk as it creates a conflict of interest. This combination allows a single user (U007) to potentially release a payment and then obscure that transaction within the reconciliation process. This bypasses necessary segregation of duties, increasing the risk of fraudulent activity going undetected. We must review the necessity of U007 holding both roles and implement controls to separate these functions.

### SOD-007 | U008
- Severity: Medium
- Roles: Dev_Commit + Prod_Deploy
- Source: model

Holding both the `Dev_Commit` and `Prod_Deploy` roles for user U008 presents a significant risk under SOD-007. This combination allows the user to write code in development and subsequently deploy it directly to production without necessary review or separation of duties. This bypasses critical safeguards designed to prevent unauthorized or unreviewed production changes. Therefore, access should be reviewed to ensure these roles are separated according to the principle of least privilege.

### SOD-008 | U009
- Severity: Low
- Roles: Inventory_Adjust + Inventory_Count_Approve
- Source: model

Holding both the Inventory_Adjust and Inventory_Count_Approve roles creates a conflict of interest as the same user can both modify inventory levels and approve the resulting count. This violates the segregation of duties principle outlined in SOD-008, increasing the risk of undetected inventory manipulation. You should review the necessity of this combined access and determine if these functions truly need to be separated. Consider revoking one role or implementing compensating controls to ensure proper separation.

