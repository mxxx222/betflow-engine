import os
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from .oidc_config import OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_AUTHORITY, OIDC_REDIRECT_URI, OIDC_SCOPE

app = FastAPI(title="Sealed Share")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SEALED_SHARE_SESSION_SECRET", "devsecret"))

oauth = OAuth()
oauth.register(
    name='oidc',
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
    server_metadata_url=f"{OIDC_AUTHORITY}/.well-known/openid-configuration",
    client_kwargs={
        'scope': OIDC_SCOPE
    }
)

# In-memory store for demo (replace with DB in production)
SHARES = {}

class ShareRequest(BaseModel):
    recipient_email: EmailStr
    expires_in_minutes: int = 60
    watermark: Optional[str] = None
    filename: str
    content: str  # base64 or text for demo

class ShareAccessRequest(BaseModel):
    token: str
    recipient_email: EmailStr

@app.post("/share")
def create_share(req: ShareRequest):
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=req.expires_in_minutes)
    SHARES[token] = {
        "recipient_email": req.recipient_email,
        "expires_at": expires_at,
        "filename": req.filename,
        "content": req.content,
        "watermark": req.watermark,
        "accessed": False
    }
    # Send magic link to recipient_email
    magic_link = f"{os.getenv('SEALED_SHARE_MAGIC_LINK_BASE', 'http://localhost:8080')}/magic/{token}"
    send_magic_link_email(req.recipient_email, magic_link, req.filename, expires_at)
    return {"token": token, "expires_at": expires_at.isoformat()}


def send_magic_link_email(recipient_email: str, magic_link: str, filename: str, expires_at: datetime):
    smtp_host = os.getenv("SEALED_SHARE_SMTP_HOST")
    smtp_port = int(os.getenv("SEALED_SHARE_SMTP_PORT", "587"))
    smtp_user = os.getenv("SEALED_SHARE_SMTP_USER")
    smtp_pass = os.getenv("SEALED_SHARE_SMTP_PASS")
    sender = os.getenv("SEALED_SHARE_FROM", smtp_user)
    if not all([smtp_host, smtp_user, smtp_pass, sender]):
        print("[WARN] SMTP config missing, not sending email.")
        return
    msg = EmailMessage()
    msg["Subject"] = f"Sealed Share: Sinulle jaettu tiedosto {filename}"
    msg["From"] = sender
    msg["To"] = recipient_email
    msg.set_content(f"Hei!\n\nSinulle on jaettu tiedosto Sealed Share -palvelussa. Voit avata sen vain sinulle tarkoitetulla linkillä. Linkki vanhenee {expires_at} UTC.\n\nAvaa tiedosto: {magic_link}\n\nTerveisin, Sealed Share")
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[INFO] Magic link sent to {recipient_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send magic link: {e}")

@app.post("/access")
def access_share(req: ShareAccessRequest):
    share = SHARES.get(req.token)
    if not share:
        raise HTTPException(status_code=404, detail="Not found")
    if share["recipient_email"] != req.recipient_email:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if datetime.utcnow() > share["expires_at"]:
        raise HTTPException(status_code=410, detail="Expired")
    if share["accessed"]:
        raise HTTPException(status_code=403, detail="Already accessed")
    share["accessed"] = True
    # TODO: Apply watermark to file if needed
    # For demo, just return content
    return {
        "filename": share["filename"],
        "content": share["content"],
        "watermark": share["watermark"]
    }


# OIDC login endpoints
@app.get("/oidc/login")
async def oidc_login(request: Request):
    redirect_uri = OIDC_REDIRECT_URI
    return await oauth.oidc.authorize_redirect(request, redirect_uri)

@app.get("/oidc/callback")
async def oidc_callback(request: Request):
    token = await oauth.oidc.authorize_access_token(request)
    user = await oauth.oidc.parse_id_token(request, token)
    request.session['user'] = dict(user)
    return RedirectResponse(url="/oidc/userinfo")

@app.get("/oidc/userinfo")
async def oidc_userinfo(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url="/oidc/login")
    return user
