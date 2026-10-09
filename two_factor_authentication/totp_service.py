"""
================================================================================
TWO-STEP AUTHENTICATION SERVICE (OTP)
================================================================================
Fully implemented 2-step verification system with:
- 6-digit cryptographic OTP generation
- Expiration tracking (5 minutes)
- Attempt protection (Maximum 5 attempts per session)
- Invalidation on success or attempt exhaustion
================================================================================
"""

import time
import secrets
import logging

logger = logging.getLogger(__name__)

class TwoFactorAuthService:
    """
    Active OTP-based Two-Factor Authentication Service.
    """

    # In-memory store for active OTP verification sessions
    # Schema: { email: { 'code': str, 'expires_at': float, 'attempts': int, 'max_attempts': int } }
    _active_otps = {}
    OTP_EXPIRY_SECONDS = 300  # 5 minutes
    MAX_ATTEMPTS = 5

    @classmethod
    def generate_login_otp(cls, user_email):
        """
        Generate a secure 6-digit OTP code for the user login session.
        """
        # Cryptographically secure 6-digit number between 100000 and 999999
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = time.time() + cls.OTP_EXPIRY_SECONDS

        cls._active_otps[user_email] = {
            "code": code,
            "expires_at": expires_at,
            "attempts": 0,
            "max_attempts": cls.MAX_ATTEMPTS
        }

        logger.info(f"[2FA] OTP generated for '{user_email}': {code} (Expires in 5 minutes)")
        print(f"\n==========================================")
        print(f" [2FA OTP CODE] For user: {user_email}")
        print(f" >>> CODE: {code} <<< (Valid for 5 mins)")
        print(f"==========================================\n")

        return code, cls.OTP_EXPIRY_SECONDS

    @classmethod
    def verify_otp_token(cls, user_email, token_code):
        """
        Verify the OTP entered by the user.
        Enforces expiration check and attempt limiting.
        Returns: (is_valid: bool, message: str)
        """
        if not user_email or user_email not in cls._active_otps:
            return False, "No active OTP request found. Please sign in again."

        record = cls._active_otps[user_email]

        # 1. Check expiration
        now = time.time()
        if now > record["expires_at"]:
            del cls._active_otps[user_email]
            return False, "OTP has expired. Please sign in again to request a new code."

        # 2. Check attempt protection
        record["attempts"] += 1
        if record["attempts"] > record["max_attempts"]:
            del cls._active_otps[user_email]
            return False, "Maximum verification attempts exceeded. For security, please sign in again."

        # 3. Check code match
        submitted_clean = str(token_code).strip()
        expected_code = str(record["code"]).strip()

        if submitted_clean == expected_code:
            # Successfully verified: clean up active session
            del cls._active_otps[user_email]
            logger.info(f"[2FA] OTP verified successfully for '{user_email}'.")
            return True, "Verification successful."
        else:
            remaining = record["max_attempts"] - record["attempts"]
            return False, f"Incorrect verification code. {remaining} attempt(s) remaining."

    @classmethod
    def get_active_otp_hint(cls, user_email):
        """Helper for demo/evaluation environment to retrieve active OTP."""
        record = cls._active_otps.get(user_email)
        if record and time.time() <= record["expires_at"]:
            return record["code"]
        return None
