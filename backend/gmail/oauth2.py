# gmail/oauth2.py — Helper for IMAP XOAUTH2 (refreshes token automatically)
import base64
import os

def get_oauth2_string() -> bytes:
    """
    Return the raw SASL string as bytes for IMAP.
    imaplib will base64-encode this before sending — do NOT pre-encode.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    user = (os.environ.get("GMAIL_ADDRESS") or "").strip()
    if not user:
        raise ValueError("GMAIL_ADDRESS não definido no .env — use o e-mail da conta que você autorizou")
    token = (creds.token or "").strip()
    # Gmail IMAP XOAUTH2: base64(user=email\x01auth=Bearer token\x01\x01). imaplib does the base64.
    raw = f"user={user}\x01auth=Bearer {token}\x01\x01"
    return raw.encode("ascii")
