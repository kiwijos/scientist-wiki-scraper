import argparse
import logging
import sys
import os
from bs4 import BeautifulSoup

from config import settings
from scraper.crawler import Crawler
from scraper import fetcher, parser, pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.output_dirs['logs'], 'scraper.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def is_scientist_article(html_path: str) -> bool:
    """
    Heuristic to check if article is about a person/scientist.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
            
        # Check categories
        cat_links = soup.find('div', {'id': 'mw-normal-catlinks'})
        if cat_links:
            text = cat_links.get_text().lower()
            keywords = ['scientist', 'physicist', 'chemist', 'biologist', 
                       'astronomer', 'mathematician', 'nobel', 'fellow', 'academic',
                       'researcher']
            if any(k in text for k in keywords):
                return True
        
        # Check infobox for "Born" to see if it's a person
        infobox = soup.find('table', {'class': 'infobox'})
        if not infobox:
            return False
        
        text = infobox.get_text().lower()
        if 'born' in text:
            return True
                
        return False
    except Exception as e:
        logger.warning(f"Error checking if scientist {html_path}: {e}")
        return False

def get_collected_count() -> int:
    """Count number of successfully processed articles."""
    try:
        return len([name for name in os.listdir(settings.output_dirs['words']) if not name.startswith('.')])
    except FileNotFoundError:
        return 0

def main() -> None:
    parser_args = argparse.ArgumentParser(description="Wikipedia Scientist Scraper")
    parser_args.add_argument('--count', type=int, default=settings.target_article_count, help='Number of articles to collect in this run')
    args = parser_args.parse_args()

    pipeline.create_directories()
    crawler = Crawler()
    
    session_target: int = args.count
    session_collected: int = 0

    total_collected = get_collected_count()
    
    logger.info(f"Starting crawl. Target for this session: {session_target} articles.")

    try:
        while True:
            if session_collected >= session_target:
                logger.info(f"Reached session target {session_target}. Stopping.")
                break
                
            url = crawler.get_next_url()
            if not url:
                logger.info("Queue empty. Stopping.")
                break
                
            logger.info(f"Processing {url}")
            
            try:
                # Fetch
                raw_path = fetcher.fetch_article(url)
                if not raw_path:
                    crawler.log_failure(url, "Download failed")
                    crawler.mark_completed(url)
                    continue
                    
                # Check if Scientist
                if not is_scientist_article(raw_path):
                    logger.debug(f"Skipping {url} - does not appear to be a scientist.")
                    # We mark as completed (visited) so we don't try again
                    crawler.mark_completed(url)
                    
                    # If it's not a scientist, delete it.
                    try:
                        os.remove(raw_path)
                    except OSError as e:
                        logger.warning(f"Could not delete non-scientist file {raw_path}: {e}")
                    continue
                    
                # Parse
                words, links = parser.parse_article(raw_path)
                
                # Save Processed
                article_slug = fetcher.extract_slug(url)
                pipeline.save_processed_data(article_slug, words, links)
                
                # Update Crawler
                crawler.add_urls(links)
                crawler.mark_completed(url)
                
                session_collected += 1
                total_collected += 1
                logger.info(f"Completed {url}. Session: {session_collected}/{session_target} (Total saved: {total_collected})")

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                crawler.log_failure(url, str(e))
                crawler.mark_completed(url) # Mark tried

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        crawler.save_progress()
        logger.info(f"Saved progress. Collected {session_collected} articles this session.")

if __name__ == "__main__":
    main()
