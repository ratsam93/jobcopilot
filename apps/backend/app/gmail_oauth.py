from __future__ import annotations

from apps.backend.app.config import settings


class GmailOAuthConfig:
    client_id = settings.gmail_oauth_client_id
    client_secret = settings.gmail_oauth_client_secret
    redirect_uri = settings.gmail_oauth_redirect_uri


gmail_oauth = GmailOAuthConfig()
