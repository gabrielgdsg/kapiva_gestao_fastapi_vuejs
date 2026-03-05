# gmail/auth.py — Run once to get tokens, then add them to .env
from pathlib import Path
import sys

# Allow running as: python gmail/auth.py (from backend/) or python -m gmail.auth (from backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRET = BACKEND_DIR / "client_secret.json"

if not CLIENT_SECRET.exists():
    print(f"Coloque o arquivo client_secret.json em: {BACKEND_DIR}")
    sys.exit(1)

def authorize():
    import json
    from google_auth_oauthlib.flow import InstalledAppFlow

    with open(CLIENT_SECRET) as f:
        secrets = json.load(f)
    client_data = secrets.get("installed", secrets.get("web", {}))

    # IMAP/POP/SMTP require https://mail.google.com/ (gmail.readonly is for REST API only)
    SCOPES = ["https://mail.google.com/"]
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), scopes=SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n✓ Autorizado com sucesso!\n")
    print("Adicione estas linhas ao seu .env (em backend/):\n")
    print(f"GOOGLE_CLIENT_ID={client_data.get('client_id', '')}")
    print(f"GOOGLE_CLIENT_SECRET={client_data.get('client_secret', '')}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")

if __name__ == "__main__":
    authorize()
