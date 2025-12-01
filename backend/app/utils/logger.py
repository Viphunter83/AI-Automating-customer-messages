import json
import logging
import re
from datetime import datetime

from pythonjsonlogger import jsonlogger

# Patterns for secrets that should be masked
SECRET_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{10,})["\']?',
    r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{10,})["\']?',
    r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\'<>]{3,})["\']?',
    r'(?i)(token)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{10,})["\']?',
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API keys
    r"Bearer\s+[a-zA-Z0-9\-_]{20,}",  # Bearer tokens
]


def mask_secrets(text: str) -> str:
    """Mask secrets in log messages"""
    if not text:
        return text

    masked = text
    for pattern in SECRET_PATTERNS:
        if ":" in pattern or "=" in pattern:
            # Pattern with key-value format
            masked = re.sub(
                pattern,
                lambda m: m.group(0).replace(
                    m.group(2) if len(m.groups()) > 1 else m.group(1), "***MASKED***"
                ),
                masked,
                flags=re.IGNORECASE,
            )
        else:
            # Direct pattern match (like API keys)
            masked = re.sub(pattern, "***MASKED***", masked, flags=re.IGNORECASE)

    return masked


class SecretMaskingFilter(logging.Filter):
    """Filter to mask secrets in log records"""

    def filter(self, record):
        # Mask secrets in log message
        if hasattr(record, "msg") and record.msg:
            record.msg = mask_secrets(str(record.msg))

        # Mask secrets in args
        if hasattr(record, "args") and record.args:
            record.args = tuple(
                mask_secrets(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )

        # Mask secrets in extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if isinstance(value, str) and any(
                    pattern_keyword in key.lower()
                    for pattern_keyword in [
                        "key",
                        "secret",
                        "password",
                        "token",
                        "auth",
                    ]
                ):
                    record.__dict__[key] = mask_secrets(value)

        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Mask any secrets in the log record
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = mask_secrets(value)


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration with secret masking"""

    # Console handler with JSON format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomJsonFormatter())
    console_handler.addFilter(SecretMaskingFilter())

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger
