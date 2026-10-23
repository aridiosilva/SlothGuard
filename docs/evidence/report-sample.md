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
- Source: fallback

User U001 holds both 'Vendor_Master_Maintain' and 'Payment_Release', which conflicts with rule SOD-001 (Vendor maintenance vs. payment release). Severity: high. Review whether both roles are needed.

### SOD-002 | U002
- Severity: High
- Roles: Purchase_Requester + Purchase_Approver
- Source: fallback

User U002 holds both 'Purchase_Requester' and 'Purchase_Approver', which conflicts with rule SOD-002 (Purchase request vs. purchase approval). Severity: high. Review whether both roles are needed.

### SOD-003 | U003
- Severity: High
- Roles: Journal_Entry_Create + Journal_Entry_Approve
- Source: fallback

User U003 holds both 'Journal_Entry_Create' and 'Journal_Entry_Approve', which conflicts with rule SOD-003 (Journal entry creation vs. approval). Severity: high. Review whether both roles are needed.

### SOD-006 | U004
- Severity: High
- Roles: User_Admin + Audit_Log_Admin
- Source: fallback

User U004 holds both 'User_Admin' and 'Audit_Log_Admin', which conflicts with rule SOD-006 (User administration vs. audit log administration). Severity: high. Review whether both roles are needed.

### SOD-004 | U010
- Severity: High
- Roles: Payroll_Maintain + Payroll_Approve
- Source: fallback

User U010 holds both 'Payroll_Maintain' and 'Payroll_Approve', which conflicts with rule SOD-004 (Payroll maintenance vs. payroll approval). Severity: high. Review whether both roles are needed.

### SOD-005 | U007
- Severity: Medium
- Roles: Bank_Reconcile + Payment_Release
- Source: fallback

User U007 holds both 'Bank_Reconcile' and 'Payment_Release', which conflicts with rule SOD-005 (Bank reconciliation vs. payment release). Severity: medium. Review whether both roles are needed.

### SOD-007 | U008
- Severity: Medium
- Roles: Dev_Commit + Prod_Deploy
- Source: fallback

User U008 holds both 'Dev_Commit' and 'Prod_Deploy', which conflicts with rule SOD-007 (Code development vs. production deploy). Severity: medium. Review whether both roles are needed.

### SOD-008 | U009
- Severity: Low
- Roles: Inventory_Adjust + Inventory_Count_Approve
- Source: fallback

User U009 holds both 'Inventory_Adjust' and 'Inventory_Count_Approve', which conflicts with rule SOD-008 (Inventory adjustment vs. inventory count approval). Severity: low. Review whether both roles are needed.

