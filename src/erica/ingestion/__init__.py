"""Data ingestion module for Erica AI Tutor."""

from erica.ingestion.processor import chunk_text, process_pdf, process_slides
from erica.ingestion.scraper import scrape_course_website

__all__ = ["scrape_course_website", "process_pdf", "process_slides", "chunk_text"]
