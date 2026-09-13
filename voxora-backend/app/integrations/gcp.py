"""
Voxora Backend — Google Cloud Platform Credentials Helper.

Loads service account credentials from multiple environment variable formats,
supporting raw JSON strings, multiline strings, escaped newlines, base64 strings,
and local file paths across serverless (Vercel) and local environments.
"""

import base64
import json
import logging
import os
from typing import Any
from google.oauth2 import service_account

from app.config import get_settings

logger = logging.getLogger(__name__)

_cached_credentials: service_account.Credentials | None = None


def get_gcp_credentials() -> service_account.Credentials | None:
    """
    Safely load Google Cloud service account credentials.
    Returns None if no valid credentials can be loaded.
    """
    global _cached_credentials
    if _cached_credentials is not None:
        return _cached_credentials

    settings = get_settings()

    # 1. Candidate environment variables containing JSON
    candidate_json_strings = [
        os.environ.get("GOOGLE_CREDENTIALS_JSON"),
        os.environ.get("GCP_SERVICE_ACCOUNT_JSON"),
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
        getattr(settings, "gcp_service_account_json", None),
    ]

    # Also check if GOOGLE_APPLICATION_CREDENTIALS itself contains JSON
    raw_gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if raw_gac.startswith("{") and raw_gac.endswith("}"):
        candidate_json_strings.append(raw_gac)

    for raw_val in candidate_json_strings:
        if not raw_val or not isinstance(raw_val, str):
            continue
        val = raw_val.strip()
        if not val:
            continue

        # Strip outer quotes if any
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1].strip()

        cred_info: dict[str, Any] | None = None

        # Attempt 1: direct JSON parse
        try:
            cred_info = json.loads(val)
        except Exception:
            pass

        # Attempt 2: strict=False (allows unescaped control characters/newlines)
        if not cred_info or not isinstance(cred_info, dict):
            try:
                cred_info = json.loads(val, strict=False)
            except Exception:
                pass

        # Attempt 3: unescape double-escaped newlines with strict=False
        if not cred_info or not isinstance(cred_info, dict):
            try:
                cred_info = json.loads(val.replace(r"\n", "\n"), strict=False)
            except Exception:
                pass

        # Attempt 4: unicode-escape
        if not cred_info or not isinstance(cred_info, dict):
            try:
                cred_info = json.loads(val.encode("utf-8").decode("unicode_escape"), strict=False)
            except Exception:
                pass

        # Attempt 5: base64 decode
        if not cred_info or not isinstance(cred_info, dict):
            try:
                decoded = base64.b64decode(val).decode("utf-8")
                cred_info = json.loads(decoded, strict=False)
            except Exception:
                pass

        if cred_info and isinstance(cred_info, dict) and "type" in cred_info:
            # Fix private_key newlines if escaped
            if "private_key" in cred_info and isinstance(cred_info["private_key"], str):
                if r"\n" in cred_info["private_key"]:
                    cred_info["private_key"] = cred_info["private_key"].replace(r"\n", "\n")

            try:
                creds = service_account.Credentials.from_service_account_info(
                    cred_info,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                _cached_credentials = creds
                logger.info("Successfully loaded GCP credentials from JSON environment variable")
                return creds
            except Exception as e:
                logger.error("Failed to construct Credentials from JSON info: %s", e)

    # 2. File path fallback (local development)
    file_candidates = [
        getattr(settings, "google_application_credentials", None),
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    ]
    for file_path in file_candidates:
        if file_path and isinstance(file_path, str) and not (file_path.strip().startswith("{")):
            path = file_path.strip()
            if os.path.exists(path):
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        path,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                    _cached_credentials = creds
                    logger.info("Successfully loaded GCP credentials from file: %s", path)
                    return creds
                except Exception as e:
                    logger.error("Failed to load credentials from file %s: %s", path, e)

    logger.warning("No valid GCP credentials found in environment or filesystem")
    return None
