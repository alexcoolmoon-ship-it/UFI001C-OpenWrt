#!/usr/bin/env python3
"""Summarize a stock radio (modem) partition for compatibility checks.

Used by stock_install.py radio_preflight() and check_backup().
"""
import hashlib
import re

# Firmware labels are version identifiers like 'UFI001BC 20211121'.
# Only UFI-prefixed labels are reported; other ASCII bytes in the image
# (which may sit next to private data) are never included in the report.
_LABEL_RE = re.compile(rb'UFI[A-Z0-9][A-Z0-9 ._\-]{2,40}')


def summarize(radio_bytes, profile):
    """Return a JSON-serializable report about the radio partition.

    radio_bytes: raw bytes of the stock 'modem' partition.
    profile: stock profile dict with 'stock_modem_sha256' (str or list).
    """
    digest = hashlib.sha256(radio_bytes).hexdigest()
    expected = profile.get('stock_modem_sha256')
    if isinstance(expected, str):
        expected = [expected]
    expected = list(expected or [])
    labels = []
    for match in _LABEL_RE.finditer(radio_bytes):
        label = match.group().decode('ascii').strip()
        if label not in labels:
            labels.append(label)
    return {
        'radio_bytes': len(radio_bytes),
        'radio_sha256': digest,
        'stock_modem_sha256': digest,
        'stock_modem_hash_matches': digest in expected,
        'known_stock_hashes': expected,
        'firmware_labels': labels,
    }
