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

Holding both the Vendor_Master_Maintain and Payment_Release roles creates a significant conflict of interest under SOD-001. This combination allows a single user (U001) to create unauthorized vendors and subsequently release payments for those fictitious entities. This violates the principle of segregation of duties by combining creation and payment authorization functions. Review should focus on immediately separating these two roles to ensure proper control over vendor lifecycle management and financial disbursement.

### SOD-002 | U002
- Severity: High
- Roles: Purchase_Requester + Purchase_Approver
- Source: model

Holding both the Purchase_Requester and Purchase_Approver roles creates a significant conflict under SOD-002. This configuration allows User U002 to bypass necessary segregation of duties by independently initiating and approving a purchase. This increases the risk of fraudulent spending or unauthorized transactions. You must review the necessity of this dual role assignment and consider restricting one of the permissions.

### SOD-003 | U003
- Severity: High
- Roles: Journal_Entry_Create + Journal_Entry_Approve
- Source: model

Holding both the Journal_Entry_Create and Journal_Entry_Approve roles for user U003 creates a significant risk under SOD-003. This combination allows the user to unilaterally post and approve accounting entries, bypassing necessary segregation of duties. This grants the user the ability to create fraudulent entries and then approve them without independent oversight. Review should focus on whether this dual responsibility is absolutely necessary for U003's job function.

### SOD-006 | U004
- Severity: High
- Roles: User_Admin + Audit_Log_Admin
- Source: model

Holding both User_Admin and Audit_Log_Admin roles for user U004 creates a significant conflict of interest. This combination grants the user the ability to both grant permissions and simultaneously erase the records of those actions. This violates the principle of segregation of duties by allowing a single entity to control both access provisioning and accountability. You must immediately review the necessity of this dual assignment and determine if the roles can be separated.

### SOD-004 | U010
- Severity: High
- Roles: Payroll_Maintain + Payroll_Approve
- Source: model

Holding both the Payroll_Maintain and Payroll_Approve roles creates a significant conflict of interest under SOD-004. This combination allows a single user to both alter sensitive pay data and authorize the final payroll execution, bypassing necessary segregation of duties. This increases the risk of unauthorized or erroneous financial changes going undetected. Review should focus on whether U010 genuinely requires both permissions or if they can be split into separate roles.

### SOD-005 | U007
- Severity: Medium
- Roles: Bank_Reconcile + Payment_Release
- Source: model

Holding both the Bank_Reconcile and Payment_Release roles for user U007 creates a significant conflict of interest. This dual access allows the user to potentially release a payment and subsequently conceal the transaction within the bank reconciliation process. This circumvents segregation of duties designed to prevent fraudulent activity. Review should focus on whether these roles are truly necessary for the user's daily responsibilities and if a split of duties is feasible.

### SOD-007 | U008
- Severity: Medium
- Roles: Dev_Commit + Prod_Deploy
- Source: model

Holding both the Dev_Commit and Prod_Deploy roles for user U008 creates a significant risk under SOD-007. This configuration allows the user to write code and directly deploy it to production without an independent review process. This bypasses necessary separation of duties, increasing the likelihood of unauthorized or untested code reaching the live environment. Review should focus on removing one of these roles to enforce segregation between development and production responsibilities.

### SOD-008 | U009
- Severity: Low
- Roles: Inventory_Adjust + Inventory_Count_Approve
- Source: model

Holding both the Inventory_Adjust and Inventory_Count_Approve roles creates a conflict of interest. This combination allows a single user to both make inventory adjustments and subsequently approve the resulting count, bypassing necessary segregation of duties. This violates the principle of preventing one person from controlling both the transaction and the approval. Therefore, review the need for this user to possess both roles and consider separating these responsibilities.

