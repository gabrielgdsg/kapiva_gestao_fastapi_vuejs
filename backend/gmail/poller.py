# gmail/poller.py — Fetch emails (pedidos / NF-e) via IMAP XOAUTH2
import email
import imaplib
import logging
import os
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def _ensure_env(settings=None):
    """Set GOOGLE_* and GMAIL_ADDRESS in os.environ from settings if given."""
    if settings is None:
        return
    for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN", "GMAIL_ADDRESS"):
        val = getattr(settings, key, None) or os.environ.get(key)
        if val:
            os.environ[key] = str(val)


def fetch_emails(
    subject_keywords: List[str],
    since_uid: Optional[int] = None,
    max_messages: int = 50,
    settings=None,
    since_date: Optional[str] = None,
) -> List[dict]:
    """
    Fetch emails whose subject contains any of subject_keywords.
    since_date: YYYY-MM-DD for IMAP SINCE (e.g. backfill).
    Returns list of { uid, subject, date, from_addr, pdf_attachments: [ { filename, content: bytes } ] }.
    """
    _ensure_env(settings)
    from gmail.oauth2 import get_oauth2_string

    def auth_callback(response):
        if response:
            return b""
        return get_oauth2_string()

    results = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.authenticate("XOAUTH2", auth_callback)
        # Try INBOX first; if 0 results, try [Gmail]/All Mail (labels as folders)
        since_imap = None
        if since_date:
            try:
                from datetime import datetime
                dt = datetime.strptime(since_date, "%Y-%m-%d")
                since_imap = dt.strftime("%d-%b-%Y")
            except Exception:
                pass

        keywords = [k.strip() for k in subject_keywords if k.strip()]
        if not keywords:
            logger.warning("No subject keywords provided")
            return []

        def search_folder(folder: str):
            mail.select(folder)
            all_uids = set()
            for kw in keywords:
                # One search per keyword (avoids IMAP OR syntax); merge UIDs. Gmail: SUBJECT "x" [SINCE date]
                if since_imap:
                    q = f'SINCE {since_imap} SUBJECT "{kw}"'
                else:
                    q = f'SUBJECT "{kw}"'
                typ, data = mail.uid("search", None, q)
                if typ == "OK" and data and data[0]:
                    all_uids.update(data[0].split())
            return sorted(all_uids, key=int)

        chosen_folder = "INBOX"
        uids = search_folder("INBOX")
        if not uids:
            try:
                uids = search_folder("[Gmail]/All Mail")
                if uids:
                    chosen_folder = "[Gmail]/All Mail"
                    logger.info("Found %s message(s) in All Mail (INBOX had 0)", len(uids))
            except Exception as e:
                logger.debug("All Mail not available: %s", e)

        if not uids:
            mail.logout()
            return []

        mail.select(chosen_folder)
        if since_uid is not None:
            uids = [u for u in uids if int(u) > since_uid]
        uids = uids[-max_messages:]  # newest first, limit

        for uid in uids:
            uid = int(uid)
            typ, msg_data = mail.uid("fetch", str(uid).encode(), "(RFC822)")
            if typ != "OK" or not msg_data:
                continue
            try:
                raw = msg_data[0][1]
                if isinstance(raw, bytes):
                    msg = email.message_from_bytes(raw)
                else:
                    msg = email.message_from_string(raw)
            except Exception as e:
                logger.warning("Parse email uid %s: %s", uid, e)
                continue

            subject = str(msg.get("Subject") or "")
            date_str = msg.get("Date", "")
            from_addr = msg.get("From", "")
            try:
                dt = parsedate_to_datetime(date_str) if date_str else None
                date_iso = dt.isoformat() if dt else None
            except Exception:
                date_iso = None

            pdf_attachments = []
            for part in msg.walk():
                if part.get_content_disposition() != "attachment":
                    continue
                fname = part.get_filename()
                if not fname:
                    continue
                if fname.lower().endswith(".pdf"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        pdf_attachments.append({"filename": fname, "content": payload})

            results.append({
                "uid": uid,
                "subject": subject,
                "date": date_iso,
                "from_addr": from_addr,
                "pdf_attachments": pdf_attachments,
            })

        mail.logout()
    except Exception as e:
        logger.exception("Gmail fetch failed: %s", e)
    return results
