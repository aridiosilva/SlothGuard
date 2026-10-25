# SoD Review Report

Generated on: 2026-10-25

## Summary

- High: 5
- Medium: 2
- Low: 1

## Findings

### SOD-001 | U001
- Severity: High
- Roles: Vendor_Master_Maintain + Payment_Release
- Source: model

Holding both the Vendor_Master_Maintain and Payment_Release roles creates a high risk because the user has the ability to both create vendors and authorize payments. This presents a clear opportunity for fraud, specifically allowing an individual to create a fictitious vendor and subsequently release payment for it. Review should focus on whether this dual responsibility is strictly necessary for user U001's function. Consider segregating these duties to enforce the separation required by SOD-001.

### SOD-002 | U002
- Severity: High
- Roles: Purchase_Requester + Purchase_Approver
- Source: model

Holding both the Purchase_Requester and Purchase_Approver roles for user U002 creates a significant risk as it violates the segregation of duties principle outlined in SOD-002. This dual role allows the user to independently initiate and approve their own purchase requests, bypassing necessary independent review. This configuration increases the potential for unauthorized spending or fraudulent transactions. Review should focus on separating the request and approval functions so that no single user can perform both actions.

### SOD-003 | U003
- Severity: High
- Roles: Journal_Entry_Create + Journal_Entry_Approve
- Source: model

Holding both the Journal_Entry_Create and Journal_Entry_Approve roles creates a significant risk under SOD-003 because it allows a single user to both initiate and authorize financial transactions. This combination bypasses necessary segregation of duties, increasing the potential for unauthorized or erroneous entries to go undetected. You must review the necessity of this dual access for User U003. Consider removing one of the conflicting roles to enforce proper separation of duties.

### SOD-006 | U004
- Severity: High
- Roles: User_Admin + Audit_Log_Admin
- Source: model

Holding both User_Admin and Audit_Log_Admin roles for user U004 presents a high risk because this user has the capability to both grant access and subsequently erase the audit trail of those actions. This dual capability violates the principle of separation of duties, creating a significant vulnerability for unauthorized or malicious changes. Review should focus on whether these combined permissions are strictly necessary for U004's job function. Consider immediately restricting one of these roles to mitigate the risk of data manipulation without oversight.

### SOD-004 | U010
- Severity: High
- Roles: Payroll_Maintain + Payroll_Approve
- Source: model

Holding both the Payroll_Maintain and Payroll_Approve roles for user U010 poses a significant risk because it violates the segregation of duties principle (SOD-004). This combination allows an individual to both modify sensitive pay data and authorize the final payroll execution, creating an opportunity for unauthorized or erroneous changes to go undetected. This overlap increases the potential for fraud or significant errors in compensation. Therefore, review should focus on whether this dual responsibility is strictly necessary for U010's job function.

### SOD-005 | U007
- Severity: Medium
- Roles: Bank_Reconcile + Payment_Release
- Source: model

Holding both the Bank_Reconcile and Payment_Release roles presents a significant risk because a single user could potentially release a payment and then conceal the transaction within the bank reconciliation process. This creates a control bypass where an unauthorized action (payment release) can be masked by a subsequent action (reconciliation). You must review the segregation of duties between these two functions to ensure that the individual performing payment releases is separate from the individual performing reconciliations. Consider implementing controls to ensure that payment release actions are independently verified or require a secondary approval independent of the reconciliation function.

### SOD-007 | U008
- Severity: Medium
- Roles: Dev_Commit + Prod_Deploy
- Source: model

Holding both the Dev_Commit and Prod_Deploy roles creates a significant risk under SOD-007 because the same user can write and directly deploy code to production without necessary review. This violates the principle of separation of duties, increasing the likelihood of unauthorized or unreviewed changes reaching the live environment. To mitigate this, you must review the necessity of U008 holding both permissions simultaneously. Consider separating these responsibilities into distinct roles to enforce proper governance.

### SOD-008 | U009
- Severity: Low
- Roles: Inventory_Adjust + Inventory_Count_Approve
- Source: model

Holding both the Inventory_Adjust and Inventory_Count_Approve roles creates a conflict of interest under SOD-008. This combination allows a single user to both modify inventory levels and approve the resulting count, bypassing necessary segregation of duties. This increases the risk of unauthorized inventory manipulation or inaccurate reporting. You should review why U009 requires both permissions and determine if these roles can be split.

