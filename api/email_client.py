from __future__ import annotations

import logging
import os

logger = logging.getLogger("jiba.email")


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Sends the reset link via SendGrid. Without SENDGRID_API_KEY set, logs
    the link instead of raising — so registration/login/reset flows all work
    in local dev and CI without needing the user's real SendGrid account,
    and the exact same code path goes live the moment the key is added."""
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "no-reply@jiba-ktu-buddy.example")

    if not api_key:
        logger.info(
            "SENDGRID_API_KEY not set — skipping real email send. "
            "Password reset link for %s: %s",
            to_email,
            reset_link,
        )
        return

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject="Reset your JIBA password",
        html_content=(
            f"<p>Click the link below to reset your JIBA password. "
            f"This link expires in 30 minutes.</p>"
            f'<p><a href="{reset_link}">{reset_link}</a></p>'
            f"<p>If you didn't request this, you can safely ignore this email.</p>"
        ),
    )

    try:
        SendGridAPIClient(api_key).send(message)
    except Exception:
        # A delivery failure shouldn't 500 the /auth/forgot-password
        # response — that endpoint deliberately never reveals send status
        # to the client — but it must still be visible server-side.
        logger.exception("Failed to send password reset email to %s", to_email)
