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

Holding both the Vendor\_Master\_Maintain and Payment\_Release roles creates a significant risk because a single user has the ability to create a vendor and then process payments for that vendor. This conflict violates the Separation of Duties (SOD-001) principle, allowing for potential fraud, such as creating fictitious vendors and issuing payments. To mitigate this, review the access controls to ensure that the authority to maintain vendor master data is strictly separated from the authority to release payments. Consider restricting the Payment\_Release role to only payments against existing, approved vendors.

### SOD-002 | U002
- Severity: High
- Roles: Purchase_Requester + Purchase_Approver
- Source: model

Holding both the Purchase\_Requester and Purchase\_Approver roles for user U002 presents a significant risk related to segregation of duties (SOD-002). This configuration allows the same individual to initiate a purchase request and subsequently approve it, bypassing necessary independent review. This overlap creates a high risk for unauthorized or fraudulent spending. Therefore, review should focus on whether this dual role is necessary or if the roles should be split to enforce proper separation of duties.

### SOD-003 | U003
- Severity: High
- Roles: Journal_Entry_Create + Journal_Entry_Approve
- Source: model

Holding both the `Journal_Entry_Create` and `Journal_Entry_Approve` roles presents a significant segregation of duties (SoD) risk as the same user can independently initiate and authorize accounting entries. This allows for the potential for unauthorized transactions or fraudulent entries to pass through without independent oversight. You must review if this dual responsibility is absolutely necessary for U003's job function. Consider reassigning one of the conflicting roles to mitigate this high-severity risk.

### SOD-006 | U004
- Severity: High
- Roles: User_Admin + Audit_Log_Admin
- Source: model

Holding both User\_Admin and Audit\_Log\_Admin roles for user U004 presents a significant risk as it violates the principle of separation of duties. This combination allows the user to both grant access permissions and subsequently erase the audit trail of those actions, effectively concealing unauthorized changes. The rule SOD-006 is explicitly designed to prevent this conflict where one person controls both the action and the evidence of that action. Review should focus on immediately segregating these responsibilities to ensure that no single individual has the power to both manage user access and control audit logs.

### SOD-004 | U010
- Severity: High
- Roles: Payroll_Maintain + Payroll_Approve
- Source: model

Holding both the Payroll\_Maintain and Payroll\_Approve roles creates a significant segregation of duties (SoD) risk under SOD-004. This combination allows User U010 to both modify sensitive pay data and authorize its final execution, enabling unauthorized changes or fraudulent payments. This dual access increases the potential for error or malicious activity without independent oversight. You must review the necessity of User U010 holding both roles and determine if the functions can be split between two separate users.

### SOD-005 | U007
- Severity: Medium
- Roles: Bank_Reconcile + Payment_Release
- Source: model

Holding both the Bank\_Reconcile and Payment\_Release roles for User U007 creates a significant conflict of interest. This combination allows an individual to initiate a payment and subsequently conceal it within the bank reconciliation process, bypassing necessary oversight. This increases the risk of unauthorized transactions or fraudulent activity going undetected. You should review the necessity of this dual role and determine if the separation of duties can be enforced or if one of the roles needs to be reassigned.

### SOD-007 | U008
- Severity: Medium
- Roles: Dev_Commit + Prod_Deploy
- Source: model

Holding both the `Dev_Commit` and `Prod_Deploy` roles creates a significant risk under SOD-007. This combination allows User U008 to write code and directly deploy it to the production environment without any required separation of duties or review process. This bypasses a critical control designed to prevent unreviewed changes from reaching production. Therefore, you must review the necessity of this dual assignment and investigate if one role can be restricted or if a separate deployment role is required.

### SOD-008 | U009
- Severity: Low
- Roles: Inventory_Adjust + Inventory_Count_Approve
- Source: model

Holding both the Inventory\_Adjust and Inventory\_Count\_Approve roles creates a conflict of interest under SOD-008. This allows User U009 to potentially manipulate inventory records without independent oversight, increasing the risk of undetected errors or fraud. The ability to both perform the adjustment and approve the count bypasses necessary segregation of duties. Therefore, review the necessity of U009 holding both roles and consider reassigning one of the permissions.

