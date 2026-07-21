"""
Reusable HTML email builders for the Patient Record System.

All emails use inline CSS for maximum email-client compatibility.
Each function returns a tuple of (plain_text, html) suitable for
passing to django.core.mail.send_mail() as message and html_message.
"""

from django.conf import settings


# ── Shared brand styles ───────────────────────────────────────────────

BRAND_COLOR = "#0078d4"
BRAND_NAME = "Patient Record System"
BRAND_TAGLINE = "NORSU Medical Dental Clinic"


def _base_html(body_html, title=None):
    """Wrap inner HTML in a full email template with header & footer."""
    title_block = f"<h1 style=\"font-size:24px;font-weight:700;color:#1a1a2e;margin:0 0 8px;letter-spacing:-0.3px;\">{title}</h1>" if title else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f0f4ff;font-family:'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f4ff;padding:28px 16px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;">
          <!-- Brand header -->
          <tr>
            <td style="padding-bottom:20px;text-align:center;">
              <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
                <tr>
                  <td style="vertical-align:middle;">
                    <span style="font-size:15px;font-weight:700;color:#1a1a2e;letter-spacing:-0.2px;">{BRAND_NAME}</span>
                    <br><span style="font-size:10px;color:#6b7280;">{BRAND_TAGLINE}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Card -->
          <tr>
            <td style="background:#ffffff;border-radius:16px;padding:36px 32px 32px;box-shadow:0 1px 3px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.06);">
              {title_block}
              {body_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding-top:20px;text-align:center;font-size:11px;color:#9ca3af;line-height:1.6;">
              Negros Oriental State University — Medical Clinic
              <br>{BRAND_NAME}
              <br><span style="color:#d1d5db;">&copy; 2026 All rights reserved.</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ── OTP emails ────────────────────────────────────────────────────────


def otp_email(otp: str, purpose: str, recipient_name: str = "") -> tuple:
    """
    Build a branded OTP email.

    Args:
        otp: The 6-digit one-time password.
        purpose: Short descriptor e.g. 'registration' or 'password reset'.
        recipient_name: Optional greeting name.

    Returns:
        (plain_text, html) tuple.
    """
    greeting = f"Hi {recipient_name}," if recipient_name else "Hi there,"
    action_label = {
        'registration': 'complete your registration',
        'password reset': 'reset your password',
    }.get(purpose, 'verify your account')

    plain = (
        f"{greeting}\n\n"
        f"Your One-Time Password (OTP) for {purpose} is:\n\n"
        f"   {otp}\n\n"
        f"This code expires in 3 minutes. Please do not share it with anyone.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"— {BRAND_NAME}\n{BRAND_TAGLINE}"
    )

    html = _base_html(f"""
      <p style="font-size:14px;color:#4b5563;margin:0 0 20px;line-height:1.6;">
        {greeting.replace(',', ',<br>')}
      </p>
      <p style="font-size:13px;color:#6b7280;margin:0 0 16px;">
        Use the code below to <strong>{action_label}</strong>:
      </p>
      <!-- OTP box -->
      <table cellpadding="0" cellspacing="0" style="margin:0 auto 20px;">
        <tr>
          <td style="background:#f0f4ff;border-radius:12px;padding:18px 32px;border:1.5px dashed #0078d4;text-align:center;">
            <span style="font-size:36px;font-weight:800;letter-spacing:8px;color:#1a1a2e;font-variant-numeric:tabular-nums;">{otp}</span>
          </td>
        </tr>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin:0 0 4px;">
        <strong>&#9200; Expires in 3 minutes</strong>
      </p>
      <p style="font-size:11px;color:#9ca3af;margin:0 0 20px;">
        Please do not share this code with anyone.
      </p>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:20px 0;">
      <p style="font-size:12px;color:#9ca3af;margin:0;line-height:1.5;">
        If you did not request this code, you can safely ignore this email.
      </p>
    """, title="Your OTP Code")

    return plain, html


def account_notification_email(
    subject: str,
    greeting: str,
    body_lines: list,
    cta_text: str = None,
    cta_url: str = None,
) -> tuple:
    """
    Build a branded transactional email (e.g. password reset, account created).

    Args:
        subject: Email subject line.
        greeting: Opening greeting (e.g. "Hi Bradi,").
        body_lines: List of paragraph strings.
        cta_text: Optional call-to-action button text.
        cta_url: Optional call-to-action button URL.

    Returns:
        (plain_text, html) tuple.
    """
    plain_body = "\n\n".join(body_lines)
    plain = f"{greeting}\n\n{plain_body}\n\n— {BRAND_NAME}\n{BRAND_TAGLINE}"
    if cta_text and cta_url:
        plain += f"\n\n{cta_text}: {cta_url}"

    html_paragraphs = "".join(
        f'<p style="font-size:14px;color:#4b5563;margin:0 0 12px;line-height:1.6;">{p}</p>'
        for p in body_lines
    )

    cta_html = ""
    if cta_text and cta_url:
        cta_html = f"""
        <table cellpadding="0" cellspacing="0" style="margin:20px auto 8px;">
          <tr>
            <td style="background:{BRAND_COLOR};border-radius:10px;padding:0;">
              <a href="{cta_url}" style="display:inline-block;padding:12px 28px;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:10px;">{cta_text}</a>
            </td>
          </tr>
        </table>
        <p style="font-size:11px;color:#9ca3af;margin:0 0 16px;text-align:center;">
          Or copy this link: <span style="color:{BRAND_COLOR};">{cta_url}</span>
        </p>
        """

    html = _base_html(f"""
      <p style="font-size:14px;color:#4b5563;margin:0 0 16px;line-height:1.6;">
        {greeting.replace(',', ',<br>')}
      </p>
      {html_paragraphs}
      {cta_html}
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:20px 0;">
      <p style="font-size:12px;color:#9ca3af;margin:0;line-height:1.5;">
        This is an automated message from {BRAND_NAME}. Please do not reply directly.
      </p>
    """, title=subject)

    return plain, html


def temp_password_email(temp_password: str, username: str, recipient_name: str = "") -> tuple:
    """
    Build an email for admin-reset or walk-in temp password notification.

    Returns:
        (plain_text, html) tuple.
    """
    greeting = f"Hi {recipient_name}," if recipient_name else "Hi there,"

    plain = (
        f"{greeting}\n\n"
        f"An administrator has created or reset your account.\n\n"
        f"Username: {username}\n"
        f"Temporary password: {temp_password}\n\n"
        f"You will be required to change this password on your next login.\n\n"
        f"Please visit the system to log in.\n\n"
        f"— {BRAND_NAME}\n{BRAND_TAGLINE}"
    )

    html = _base_html(f"""
      <p style="font-size:14px;color:#4b5563;margin:0 0 16px;line-height:1.6;">
        {greeting.replace(',', ',<br>')}
      </p>
      <p style="font-size:13px;color:#6b7280;margin:0 0 16px;">
        An administrator has created or reset your account credentials.
      </p>
      <table cellpadding="10" cellspacing="0" style="margin:0 auto 20px;background:#f9fafb;border-radius:12px;width:100%;">
        <tr>
          <td style="padding:12px 20px;">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="font-size:12px;font-weight:600;color:#6b7280;padding-bottom:4px;">Username</td>
              </tr>
              <tr>
                <td style="font-size:16px;font-weight:700;color:#1a1a2e;padding-bottom:12px;">{username}</td>
              </tr>
              <tr>
                <td style="font-size:12px;font-weight:600;color:#6b7280;padding-bottom:4px;">Temporary password</td>
              </tr>
              <tr>
                <td style="font-size:16px;font-weight:700;color:#1a1a2e;font-family:'Courier New',monospace;letter-spacing:2px;">{temp_password}</td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
      <p style="font-size:12px;color:#dc2626;margin:0 0 16px;font-weight:500;">
        &#9888; You will be required to change this password on your next login.
      </p>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:20px 0;">
      <p style="font-size:12px;color:#9ca3af;margin:0;line-height:1.5;">
        Please visit the system to log in. If you did not expect this, contact the clinic.
      </p>
    """, title="Your Account Credentials")

    return plain, html


