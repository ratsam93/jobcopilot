from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from crawlee import Request
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="JobCopilot Crawlee Service", version="0.1.0")


class CrawlRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=10)
    max_pages: int | None = Field(default=None, ge=1, le=25)


class CrawlPage(BaseModel):
    url: str
    title: str | None = None
    text_preview: str
    links: list[str]


class CrawlResponse(BaseModel):
    status: str
    requested_urls: list[str]
    pages_crawled: int
    max_pages: int
    pages: list[CrawlPage]


def _validate_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail=f"Only absolute http/https URLs are supported: {url}")
    return url


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "crawlee-python"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(payload: CrawlRequest) -> CrawlResponse:
    urls = [_validate_http_url(url) for url in payload.urls]
    configured_limit = int(os.getenv("CRAWLEE_MAX_PAGES", "3"))
    max_pages = min(payload.max_pages or configured_limit, 25)
    pages: list[CrawlPage] = []

    crawler = BeautifulSoupCrawler(max_requests_per_crawl=max_pages)

    @crawler.router.default_handler
    async def handle_page(context: BeautifulSoupCrawlingContext) -> None:
        soup: BeautifulSoup = context.soup
        text = " ".join(soup.get_text(" ", strip=True).split())
        links = []
        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href", "")).strip()
            if href and len(links) < 20:
                links.append(href)
        pages.append(
            CrawlPage(
                url=context.request.loaded_url or context.request.url,
                title=soup.title.string.strip() if soup.title and soup.title.string else None,
                text_preview=text[:1000],
                links=links,
            )
        )

    await crawler.run([Request.from_url(url) for url in urls])

    return CrawlResponse(
        status="success",
        requested_urls=urls,
        pages_crawled=len(pages),
        max_pages=max_pages,
        pages=pages,
    )
