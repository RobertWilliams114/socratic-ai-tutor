"""Web scraping and data collection utilities."""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from socratic.config import settings
from socratic.models import Resource, ResourceType

logger = logging.getLogger(__name__)


def scrape_course_website(
    base_url: str | None = None, max_depth: int = 3, save_dir: Path | str | None = None
) -> list[Resource]:
    """Scrape course website and extract content.

    Args:
        base_url: Base URL to scrape (defaults to settings)
        max_depth: Maximum depth for recursive scraping
        save_dir: Directory to save raw HTML (Path or str)

    Returns:
        List of Resource objects
    """
    base_url = base_url or settings.course_website_url
    save_dir = Path(save_dir) if save_dir else settings.data_dir / "web"
    save_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    resources = []
    manifest = {"base_url": base_url, "urls": []}

    def crawl(url: str, depth: int = 0):
        if depth > max_depth or url in visited:
            return

        try:
            visited.add(url)
            logger.info(f"Scraping: {url} (depth {depth})")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract main content
            content_areas = soup.find_all(["article", "main", "div"], class_=["content"])
            if not content_areas:
                content_areas = [soup.find("body")]

            text_content = "\n\n".join(
                [area.get_text(strip=True, separator="\n") for area in content_areas if area]
            )

            # Save raw HTML
            url_hash = str(abs(hash(url)))
            html_file = save_dir / f"{url_hash}.html"
            html_file.write_text(response.text, encoding="utf-8")

            # Create resource
            resource = Resource(
                id=f"web_{url_hash}",
                type=ResourceType.WEB,
                url=url,
                title=soup.title.string if soup.title else url,
                content=text_content,
                metadata={"depth": depth, "html_file": str(html_file)},
            )
            resources.append(resource)
            manifest["urls"].append({"url": url, "depth": depth, "title": resource.title})

            # Find links to follow
            if depth < max_depth:
                for link in soup.find_all("a", href=True):
                    next_url = urljoin(url, link["href"])
                    # Only follow links within the same domain
                    if urlparse(next_url).netloc == urlparse(base_url).netloc:
                        crawl(next_url, depth + 1)

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

    crawl(base_url)

    # Save manifest
    manifest_file = save_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Scraped {len(resources)} web pages. Manifest saved to {manifest_file}")

    return resources


