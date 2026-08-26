"""Data ingestion module for Socratic AI Tutor."""

from socratic.ingestion.processor import chunk_text, process_pdf, process_slides
from socratic.ingestion.scraper import scrape_course_website

__all__ = ["scrape_course_website", "process_pdf", "process_slides", "chunk_text"]
