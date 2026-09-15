"""
Shared field validators.

Imported by accounts.forms, patients.forms, patients.models, and
consultations.forms — deliberately placed in `core` (which has no
dependencies on any other app) to avoid circular imports.
"""
import re

from django.core.exceptions import ValidationError

# ── Philippine mobile number validation / normalization ────────────────────
# Accepts the common PH mobile formats (10 digits after the prefix; all
# Philippine mobile prefixes currently start with '9'):
#     09171234567          local format
#     +639171234567        international format
#     9171234567           prefix omitted
# Separators (spaces, dashes, dots, parentheses) are ignored.
PH_MOBILE_RE = re.compile(r'^(?:\+63|0)?9\d{9}$')

PHONE_ERROR_MESSAGE = (
    'Enter a valid Philippine mobile number '
    '(09XXXXXXXXX or +639XXXXXXXXX).'
)


def _clean_phone_digits(value):
    """Strip separators, keeping only a leading '+'."""
    value = str(value).strip()
    cleaned = re.sub(r'[\s\-\(\)\.]', '', value)
    # Reject any '+' that is not the leading character
    if '+' in cleaned[1:]:
        return ''
    return cleaned


def validate_phone(value):
    """Strict Philippine mobile number validator (model + form level)."""
    cleaned = _clean_phone_digits(value)
    if not PH_MOBILE_RE.match(cleaned):
        raise ValidationError(PHONE_ERROR_MESSAGE)


def normalize_phone(value):
    """Validate a PH mobile number and return it canonically as +63XXXXXXXXXX.

    Raises ValidationError when the value is not a valid PH mobile number.
    Forms call this in clean_<field> so the database always stores one
    consistent format.
    """
    cleaned = _clean_phone_digits(value)
    if not PH_MOBILE_RE.match(cleaned):
        raise ValidationError(PHONE_ERROR_MESSAGE)
    if cleaned.startswith('+63'):
        return cleaned
    if cleaned.startswith('0'):
        return '+63' + cleaned[1:]
    return '+63' + cleaned  # bare 9XXXXXXXXX
