import os
from typing import List
from config import settings

def create_directories() -> None:
    """Create all necessary directories defined in config."""
    for path in settings.output_dirs.values():
        os.makedirs(path, exist_ok=True)

def save_html(path: str, content: str) -> None:
    """Save raw HTML content to file."""
    # Ensure directory exists just in case
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_processed_data(article_slug: str, words: str, links: List[str]) -> None:
    """Save processed words and links."""
    words_path = os.path.join(settings.output_dirs['words'], article_slug)
    links_path = os.path.join(settings.output_dirs['links'], article_slug)
    
    # Save words (single line)
    with open(words_path, 'w', encoding='utf-8') as f:
        f.write(words)
    
    # Save links (one per line)
    with open(links_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(links))

def extract_slug_from_path(path: str) -> str:
    """Helper to get slug if full path is passed, though usually we pass slug."""
    # This might not be needed if we pass slug directly, but keeping it simple.
    return os.path.basename(path).replace('.html', '')
