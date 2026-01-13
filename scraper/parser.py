from bs4 import BeautifulSoup
import re
import logging
from typing import List, Tuple, Optional, Any

from config import settings

logger = logging.getLogger(__name__)

def clean_content(soup: BeautifulSoup) -> Optional[Any]:
    """
    Find main content container and remove unwanted elements.
    Returns the cleaned soup element (or selection of elements).
    """
    # Main Content Container
    # "Wikipedia uses <div class="mw-parser-output"> for the main article content"
    # Note: scraping shows multiple mw-parser-output divs (e.g. in indicators).
    # We must prioritize the one inside #mw-content-text
    
    content = None
    mw_content_text = soup.find('div', {'id': 'mw-content-text'})
    
    if mw_content_text:
        content = mw_content_text.find('div', {'class': 'mw-parser-output'})
    
    # Fallback if not inside mw-content-text or if mw-content-text missing
    if not content:
        # Heuristic: find all and take the one with the most paragraphs
        divs = soup.find_all('div', {'class': 'mw-parser-output'})
        if divs:
            content = max(divs, key=lambda d: len(d.find_all('p', recursive=False))) # Using recursive=False might be safer for strict structure or True for nested
            # Actually, just most p tags generally
            if not content.find('p'):
                 content = max(divs, key=lambda d: len(d.find_all('p')))
    
    if not content:
        # Final fallback to mw-content-text direct
        content = mw_content_text
        
    if not content:
        return None

    # Remove unwanted elements
    # "Table of Contents: <div id="vector-toc"> with class vector-toc"
    # "Infoboxes: Tables and divs with class infobox"
    # "Navigation boxes: Divs with class navbox"
    # "Reference sections: Divs with class reflist or references"
    # "Side panels: Divs with class sidebar"
    
    unwanted_classes = [
        'vector-toc', 'infobox', 'navbox', 'reflist', 'references', 'sidebar', 
        'mw-editsection', 'noprint', 'IPA', 'rt-comment'
    ]
    
    # Remove by class
    for css_class in unwanted_classes:
        for tag in content.find_all(class_=css_class):
            tag.decompose()
            
    # Remove specific tags that are usually metadata/noise
    for tag in content.find_all(['style', 'script', 'noscript', 'meta', 'link']):
        tag.decompose()
        
    return content

def extract_words(content: Any) -> str:
    """
    Extract clean words from soup content.
    Returns space-delimited string.
    Strategies:
    - Focus on <p> tags for main content.
    """
    if not content:
        return ""
        
    text_parts = []
    
    # Focus on <p> (paragraph) tags for main content
    # We iterate over paragraphs to avoid getting text from random divs/tables/etc
    paragraphs = content.find_all('p', recursive=True)
    
    for p in paragraphs:
        # Get text
        text = p.get_text(separator=' ')
        # Clean: Lowercase 
        text_lower = text.lower()
        
        # Remove punctuation AND specific phonetic symbols that might slip through \w
        # \w matches unicode letters, including modifier letters used in IPA (ˈ, ː, etc)
        # We explicitly remove them here.
        cleaned = re.sub(r'[^\w\s]', '', text_lower)
        
        # Additional cleanup for phonetic modifiers if not removed by class exclusion
        # ˈ (U+02C8), ː (U+02D0), ˌ (U+02CC)
        cleaned = re.sub(r'[ˈːˌ]', '', cleaned)
        
        if cleaned.strip():
            text_parts.append(cleaned)
            
    full_text = ' '.join(text_parts)
    
    # Normalize whitespace (single space-delimited)
    return ' '.join(full_text.split())

def extract_links(content: Any) -> List[str]:
    """
    Extract internal Wikipedia links.
    Returns list of link paths (e.g. /wiki/Article).
    """
    if not content:
        return []

    links = []
    
    # Focus on <p> (paragraph) tags for main content
    # This (hopefully) ensures only contextually relevant links are captured
    paragraphs = content.find_all('p', recursive=True)
    
    for p in paragraphs:
        for a in p.find_all('a', href=True):
            href = a['href']
            
            # Handle fragments: "Should strip fragments but keep the base article link"
            if '#' in href:
                href = href.split('#')[0]
                
            # Skip empty links after split
            if not href:
                continue

            # Only internal Wikipedia article links
            if href.startswith('/wiki/') and ':' not in href:
                # Exclude special pages (redundant check if : is excluded, but explicit is good)
                # "Special pages (EXCLUDE): /wiki/Special:*, /wiki/Help:*, /wiki/Wikipedia:*"
                # "Categories (EXCLUDE): /wiki/Category:*"
                # "Files (EXCLUDE): /wiki/File:*"
                if not any(x in href for x in ['File:', 'Category:', 'Help:', 'Special:', 'Wikipedia:']):
                    links.append(href)
    
    if settings.deduplicate_links:
        # Deduplicate while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        return unique_links
        
    return links

def parse_article(html_path: str) -> Tuple[str, List[str]]:
    """
    Parse HTML file and return (words, links).
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Clean and prepare content
        content = clean_content(soup)
        
        if not content:
            logger.warning(f"Could not find valid content in {html_path}")
            return "", []

        # Extract words
        words = extract_words(content)
        
        # Extract links
        links = extract_links(content)
        
        return words, links
    except Exception as e:
        logger.error(f"Error parsing {html_path}: {e}")
        return "", []
