
Update (T04b, step 1): Push Notification using Auth0 Guardian enabled in Security > Multi-factor Auth, app option "Auth0 Guardian". The factor card carries an ENTERPRISE MFA badge, so it is available only because of the trial. Other factors left disabled. Nothing paid.

MFA page review (2026-10-22 19:24): only Push (Auth0 Guardian) enabled; MFA policy "Never"; Adaptive MFA risk assessment off; trusted-browser skip on (7-day idle, 30-day max). No changes saved on that page.

T04b (2026-10-23): test user created in the dashboard (database connection); email verified through the Auth0 verification email; enrollment invitation sent from User > Details > Multi-Factor Authentication; the invitation page showed a QR code that was scanned with the Guardian app. The dashboard lists the device as "Enrolled using Push Notification and TOTP" and the user attribute multifactor shows ["guardian"]. A recovery code was issued and stored outside the repository.
Not yet proven at this point: a real push approval request reaching the phone (CIBA end to end).
