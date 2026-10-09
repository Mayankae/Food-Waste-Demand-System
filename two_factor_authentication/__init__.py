# ==============================================================================
# TWO-FACTOR AUTHENTICATION (2FA / OTP) PLACEHOLDER MODULE
# ==============================================================================
# IMPORTANT NOTICE:
# As required, the final 2-step OTP/TOTP authentication mechanism is intentionally
# left as a placeholder so that you (the developer/student) can implement your
# preferred 2-factor authentication provider (e.g., Google Authenticator TOTP,
# Twilio SMS OTP, or SMTP Email OTP).
#
# All hooks, function signatures, and integration points are ready in:
# - two_factor_authentication/totp_service.py
# - two_factor_authentication/hooks.py
# - auth/auth_service.py (marked with [2FA INTEGRATION POINT])
#
# Please read two_factor_authentication/README.md for step-by-step instructions.
# ==============================================================================

from .hooks import (
    is_2fa_required_for_user,
    initiate_2fa_challenge,
    validate_2fa_challenge
)

__all__ = [
    "is_2fa_required_for_user",
    "initiate_2fa_challenge",
    "validate_2fa_challenge"
]
