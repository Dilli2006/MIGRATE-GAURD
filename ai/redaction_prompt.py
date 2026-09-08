"""PII redaction - deterministic regex-based (no LLM needed)."""

from __future__ import annotations

import re


def redact(text: str) -> str:
    """Redact PII and sensitive data from text using regex patterns.

    Covers: emails, IPs, AWS keys, connection strings, passwords in env vars.
    """
    if not text:
        return text

    # Email addresses
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[REDACTED_EMAIL]", text)
    # IPv4 addresses
    text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", text)
    # AWS access keys
    text = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]", text)
    # Connection strings
    text = re.sub(r"postgresql://[^\s]+", "[REDACTED_CONNECTION_STRING]", text)
    text = re.sub(r"mysql://[^\s]+", "[REDACTED_CONNECTION_STRING]", text)
    text = re.sub(r"mongodb://[^\s]+", "[REDACTED_CONNECTION_STRING]", text)
    # Passwords in env vars or config
    text = re.sub(
        r"(?i)(password|passwd|secret|token|api_key|apikey)\s*[=:]\s*\S+",
        r"\1=[REDACTED]",
        text,
    )

    return text

