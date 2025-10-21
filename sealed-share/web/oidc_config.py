# OIDC configuration for Sealed Share
import os

OIDC_CLIENT_ID = os.getenv("SEALED_SHARE_OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.getenv("SEALED_SHARE_OIDC_CLIENT_SECRET", "")
OIDC_AUTHORITY = os.getenv("SEALED_SHARE_OIDC_AUTHORITY", "https://accounts.google.com")
OIDC_REDIRECT_URI = os.getenv("SEALED_SHARE_OIDC_REDIRECT_URI", "http://localhost:8080/oidc/callback")
OIDC_SCOPE = os.getenv("SEALED_SHARE_OIDC_SCOPE", "openid email profile")
