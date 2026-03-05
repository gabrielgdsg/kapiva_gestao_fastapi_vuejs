# test_gmail.py — Run after setting .env (step 6). Delete after testing.
import os
import sys
from pathlib import Path

# Load .env from backend/ (strip quotes and \r so values are clean)
BACKEND_DIR = Path(__file__).resolve().parent
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip().replace("\r", "")
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip("'\"").strip()
                os.environ.setdefault(k.strip(), v)

def test():
    import imaplib
    if not os.environ.get("GMAIL_ADDRESS"):
        print("✗ Erro: GMAIL_ADDRESS não está definido no .env.")
        print("  Adicione no backend/.env a linha:")
        print('  GMAIL_ADDRESS=seu_email@gmail.com')
        print("  (use o mesmo e-mail da conta que você autorizou no auth.py)")
        return
    from gmail.oauth2 import get_oauth2_string

    def auth_callback(response):
        # response is bytes (server challenge). Empty = initial; non-empty = e.g. 401 error.
        if response:
            return b""  # ack error challenge with empty response
        return get_oauth2_string()  # raw SASL string as bytes; imaplib will base64-encode it

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.authenticate("XOAUTH2", auth_callback)
        mail.select("inbox")
        _, uids = mail.uid("search", None, 'SUBJECT "pedido"')
        count = len(uids[0].split()) if uids and uids[0] else 0
        print(f"✓ Conexão OK — {count} e-mails com 'pedido' encontrados")
        mail.logout()
    except Exception as e:
        print(f"✗ Erro: {e}")

if __name__ == "__main__":
    test()
