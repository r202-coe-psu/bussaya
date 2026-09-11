import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

logger = logging.getLogger(__name__)


class Mailer:
    """Thin SMTP wrapper driven by Flask app config. Disabled (no-op) unless
    MAIL_ENABLED is set, so the reminder job is safe to run in dev/test
    environments without SMTP credentials configured."""

    def __init__(self, config):
        self.enabled = bool(config.get("MAIL_ENABLED", False))
        self.host = config.get("MAIL_HOST", "localhost")
        self.port = int(config.get("MAIL_PORT", 587))
        self.use_tls = bool(config.get("MAIL_USE_TLS", True))
        self.username = config.get("MAIL_USERNAME", "")
        self.password = config.get("MAIL_PASSWORD", "")
        self.sender = config.get("MAIL_SENDER") or self.username
        self.sender_name = config.get("MAIL_SENDER_NAME", "")

    def send(self, to_email, subject, body):
        if not self.enabled:
            logger.debug("Mail disabled, skipping send to %s: %s", to_email, subject)
            return False

        if not to_email:
            logger.debug("No recipient email, skipping send: %s", subject)
            return False

        sender = self.sender
        if self.sender_name:
            sender = formataddr((self.sender_name, self.sender))

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to_email
        message.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(self.host, self.port, timeout=15)
            try:
                if self.use_tls:
                    server.starttls()
                if self.username:
                    server.login(self.username, self.password)
                server.sendmail(self.sender, [to_email], message.as_string())
            finally:
                server.quit()
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False

        return True
