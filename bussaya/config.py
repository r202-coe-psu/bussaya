"""Settings for standalone scripts (e.g. bussaya-controller) that don't run
inside the Flask app and so can't read ``app.config``.

Values come from environment variables, loaded from a ``.env`` file via
python-dotenv if one is present, falling back to the same defaults as
bussaya.default_settings.
"""

import os

from dotenv import load_dotenv

from bussaya import default_settings

# (env var name, default value) - default's type decides how the env
# var string gets cast.
_SETTINGS = [
    ("MONGODB_DB", default_settings.MONGODB_DB),
    ("MONGODB_HOST", "localhost"),
    ("MONGODB_PORT", 27017),
    ("MONGODB_USERNAME", ""),
    ("MONGODB_PASSWORD", ""),
    ("MAIL_ENABLED", default_settings.MAIL_ENABLED),
    ("MAIL_HOST", default_settings.MAIL_HOST),
    ("MAIL_PORT", default_settings.MAIL_PORT),
    ("MAIL_USE_TLS", default_settings.MAIL_USE_TLS),
    ("MAIL_USERNAME", default_settings.MAIL_USERNAME),
    ("MAIL_PASSWORD", default_settings.MAIL_PASSWORD),
    ("MAIL_SENDER", default_settings.MAIL_SENDER),
    ("MAIL_SENDER_NAME", default_settings.MAIL_SENDER_NAME),
    ("SITE_BASE_URL", default_settings.SITE_BASE_URL),
]


def _cast(raw, default):
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        return int(raw)
    return raw


def load_settings():
    """Build a plain settings dict from the environment / .env file."""

    load_dotenv()

    settings = {}
    for name, default in _SETTINGS:
        raw = os.environ.get(name)
        settings[name] = _cast(raw, default) if raw is not None else default

    return settings
