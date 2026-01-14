import requests
import time
import random
import logging
import os
import urllib.parse
from requests.exceptions import ConnectionError, Timeout, HTTPError
from typing import Optional

from config import settings
from scraper import pipeline

# Configure logging
logger = logging.getLogger(__name__)

# Initialize session
session = requests.Session()
session.headers.update({
    "User-Agent": settings.user_agent,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
})

def extract_slug(url: str) -> str:
    """Extract article slug from URL."""
    # Handle full URL or path
    path = urllib.parse.urlparse(url).path
    if path.startswith('/wiki/'):
        return path.replace('/wiki/', '')
    return path

def fetch_with_retry(url: str, max_retries: int = settings.max_retries) -> requests.Response:
    backoff = settings.initial_backoff
    
    # Ensure URL is absolute if it's a path
    if url.startswith('/'):
        url = settings.base_url + url
        
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=settings.request_timeout)
            response.raise_for_status()
            return response
        except (ConnectionError, Timeout, HTTPError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {url}")
                raise
            
            should_retry = True
            if isinstance(e, HTTPError) and e.response.status_code not in [429, 503]:
                # Don't retry client errors (404, etc) unless it's a rate limit
                should_retry = False
            
            if should_retry:
                wait_time = min(backoff, settings.max_backoff)
                increment_backoff = True
                
                # Check for Retry-After header
                if isinstance(e, HTTPError) and e.response.status_code in [429, 503]:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                            logger.warning(f"Server requested wait of {wait_time}s via Retry-After")
                            increment_backoff = False
                        except ValueError:
                            pass # Fallback to standard backoff

                logger.warning(f"Error fetching {url}: {e}. Retrying in {wait_time}s")
                time.sleep(wait_time)
                
                if increment_backoff:
                    backoff *= 2
            else:
                raise
    raise Exception("Unreachable code") 

def fetch_article(url: str) -> Optional[str]:
    """
    Download article and save to raw file.
    Returns path to saved file.
    """
    article_slug = extract_slug(url)
    raw_path = os.path.join(settings.output_dirs['raw'], f"{article_slug}.html")
    
    # Skip if already downloaded
    if os.path.exists(raw_path):
        logger.info(f"Skipping {article_slug} (already downloaded)")
        return raw_path
    
    # Download with retry logic
    try:
        response = fetch_with_retry(url)
        
        # Save raw HTML
        pipeline.save_html(raw_path, response.text)
        logger.info(f"Downloaded {article_slug}")
        
        # Rate limit
        time.sleep(random.uniform(settings.min_delay, settings.max_delay))
        
        return raw_path
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
