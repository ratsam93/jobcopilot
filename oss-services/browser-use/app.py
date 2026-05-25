from __future__ import annotations

import importlib.metadata
import os
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field


app = FastAPI(title="JobCopilot Browser Use Service", version="0.1.0")


class InspectTitleRequest(BaseModel):
    url: str = Field(min_length=1)


class InspectTitleResponse(BaseModel):
    status: str
    url: str
    title: str
    browser_use_installed: bool
    browser_use_version: str | None


def _allowed_hosts() -> set[str]:
    value = os.getenv("BROWSER_USE_ALLOWED_HOSTS", "example.com")
    return {host.strip().lower() for host in value.split(",") if host.strip()}


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail=f"Only absolute http/https URLs are supported: {url}")
    host = parsed.hostname.lower() if parsed.hostname else ""
    if host not in _allowed_hosts():
        raise HTTPException(status_code=403, detail=f"Host is not allowlisted: {host}")
    return url


def _browser_use_version() -> str | None:
    try:
        return importlib.metadata.version("browser-use")
    except importlib.metadata.PackageNotFoundError:
        return None


@app.get("/health")
def health() -> dict[str, object]:
    version = _browser_use_version()
    return {
        "status": "ok",
        "service": "browser-use",
        "browser_use_installed": version is not None,
        "browser_use_version": version,
        "allowed_hosts": sorted(_allowed_hosts()),
    }


@app.post("/inspect-title", response_model=InspectTitleResponse)
async def inspect_title(payload: InspectTitleRequest) -> InspectTitleResponse:
    url = _validate_url(payload.url)
    version = _browser_use_version()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        title = await page.title()
        final_url = page.url
        await browser.close()

    return InspectTitleResponse(
        status="success",
        url=final_url,
        title=title,
        browser_use_installed=version is not None,
        browser_use_version=version,
    )
