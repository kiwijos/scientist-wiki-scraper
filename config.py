from typing import Dict
from pydantic_settings import BaseSettings
from pydantic import model_validator, Field

class Settings(BaseSettings):
    # Wikipedia Settings
    base_url: str = Field(default="https://en.wikipedia.org", description="Base URL for Wikipedia")
    starting_category: str = "/wiki/Category:Scientists"
    target_article_count: int = 200

    # Request Settings
    user_agent: str = "ScientistScraper/1.0 (https://gitlab.lnu.se/2dv515/student/al227qz/project; al227qz@student.lnu.se)"
    request_timeout: int = 10  # seconds
    min_delay: float = 1.5     # seconds
    max_delay: float = 3.0     # seconds

    # Retry Settings
    max_retries: int = 5
    initial_backoff: int = 2   # seconds
    max_backoff: int = 32      # seconds

    # Output Directories
    output_dirs: Dict[str, str] = {
        'raw': 'data/Raw/Scientists',
        'words': 'data/Words/Scientists',
        'links': 'data/Links/Scientists',
        'logs': 'logs',
    }

    # Parser Settings
    remove_stopwords: bool = False
    deduplicate_links: bool = True

settings = Settings()
