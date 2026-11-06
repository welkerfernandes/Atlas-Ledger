"""Infrastructure boundary: database ownership and tenant authentication."""
import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from fastapi import Header, HTTPException


def tenant(x_api_key: str = Header(default='')) -> str:
    # Credentials map to identities; a caller cannot select another tenant by header.
    credentials = json.loads(os.getenv('API_KEYS', '{"local-alpha":"alpha","local-beta":"beta"}'))
    for key, identity in credentials.items():
        if hmac.compare_digest(key, x_api_key):
            return identity
    raise HTTPException(401, 'Invalid API key')


@contextmanager
def database(path):
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
