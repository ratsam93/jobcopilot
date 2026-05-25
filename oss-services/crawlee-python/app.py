from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
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
    warnings: list[str] = []


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
    warnings: list[str] = []

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
                url=context.request.url,
                title=soup.title.string.strip() if soup.title and soup.title.string else None,
                text_preview=text[:1000],
                links=links,
            )
        )

    @crawler.failed_request_handler
    async def handle_failed_request(context: BeautifulSoupCrawlingContext) -> None:
        warnings.append(f"Crawlee failed to process {context.request.url}")

    await crawler.run(urls)

    if not pages:
        warnings.append("Crawlee returned no handled pages; used direct HTTP fallback.")
        pages = await _fallback_fetch(urls[:max_pages])

    return CrawlResponse(
        status="success",
        requested_urls=urls,
        pages_crawled=len(pages),
        max_pages=max_pages,
        pages=pages,
        warnings=warnings,
    )


async def _fallback_fetch(urls: list[str]) -> list[CrawlPage]:
    pages: list[CrawlPage] = []
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "JobCopilot-Crawlee-Service/0.1"},
    ) as client:
        for url in urls:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                pages.append(CrawlPage(url=url, title=None, text_preview=f"HTTP fallback failed: {exc}", links=[]))
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            text = " ".join(soup.get_text(" ", strip=True).split())
            links = [str(anchor.get("href", "")).strip() for anchor in soup.find_all("a", href=True)]
            pages.append(
                CrawlPage(
                    url=str(response.url),
                    title=soup.title.string.strip() if soup.title and soup.title.string else None,
                    text_preview=text[:1000],
                    links=[link for link in links if link][:20],
                )
            )
    return pages
