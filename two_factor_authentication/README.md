# Two-Factor Authentication (2FA / OTP) Module

> **Integration Guide & Academic Architecture Reference**  
> This directory is the designated placeholder module for the **2-Step Verification / OTP System** as required by the PBL project specifications.

---

## 📌 Architecture Overview

The system uses a **Two-Stage Authentication Pipeline**:

```
[User Login Form]
       │
       ▼
[Stage 1: Primary Verification]
  - Validate Email & Bcrypt Password Hash in Database
       │
       ├──> If Invalid: Return HTTP 401 Unauthorized
       └──> If Valid: Check `is_2fa_required_for_user(user)`
                 │
                 ├──> If 2FA Disabled (Current State):
                 │      Issue Auth JWT Session Token & Complete Login
                 │
                 └──> If 2FA Enabled:
                        Issue Temporary Pre-Auth Token
                        Return Status: "2FA_REQUIRED"
                        Prompt User for 6-Digit Verification Code
                             │
                             ▼
                      [Stage 2: 2FA Verification]
                        Validate OTP / TOTP Token
                        Issue Final Auth Session Token
```

---

## 🚀 How to Implement 2-Factor Authentication

You can implement either **Option A (Google Authenticator TOTP)** or **Option B (Email / SMS OTP)** using the instructions below:

### Option A: Google Authenticator (TOTP - Recommended)

1. **Install `pyotp` and `qrcode`**:
   ```bash
   pip install pyotp qrcode pillow
   ```

2. **Add Secret to Database**:
   Add a `totp_secret` column to the `users` table:
   ```sql
   ALTER TABLE users ADD COLUMN totp_secret TEXT;
   ```

3. **Update `two_factor_authentication/totp_service.py`**:
   ```python
   import pyotp

   class TwoFactorAuthService:
       @staticmethod
       def generate_secret_key():
           return pyotp.random_base32()

       @staticmethod
       def generate_provisioning_uri(user_email, secret_key):
           totp = pyotp.TOTP(secret_key)
           return totp.provisioning_uri(name=user_email, issuer_name="SmartFood Intelligence")

       @classmethod
       def verify_otp_token(cls, user_identifier, token_code, secret_key=None):
           if not secret_key:
               return False
           totp = pyotp.TOTP(secret_key)
           return totp.verify(token_code, valid_window=1)
   ```

4. **Activate 2FA in `config.py`**:
   ```python
   TWO_FACTOR_ENABLED = True
   ```

---

### Option B: 6-Digit Email OTP (Simple & Effective)

1. Use Python's built-in `smtplib` or `Flask-Mail`:
   ```python
   import secrets
   import time

   otp_cache = {}

   def send_email_otp(recipient_email):
       code = f"{secrets.randbelow(1000000):06d}"
       otp_cache[recipient_email] = {"code": code, "expires": time.time() + 300}
       # Send via your SMTP server:
       # server.sendmail(...)
       return code
   ```

2. Verify in `verify_otp_token`:
   ```python
   def verify_email_otp(recipient_email, submitted_code):
       entry = otp_cache.get(recipient_email)
       if entry and entry["code"] == submitted_code and time.time() <= entry["expires"]:
           del otp_cache[recipient_email]
           return True
       return False
   ```

---

## 🔗 Key Integration Points in Codebase

| File | Purpose | Lines / Symbol |
| :--- | :--- | :--- |
| `config.py` | Global 2FA Enable Flag | `TWO_FACTOR_ENABLED` |
| `auth/auth_service.py` | Login pipeline check | `is_2fa_required_for_user()` |
| `two_factor_authentication/hooks.py` | Challenge generator | `initiate_2fa_challenge()` |
| `two_factor_authentication/totp_service.py` | Core token validation | `TwoFactorAuthService.verify_otp_token()` |
