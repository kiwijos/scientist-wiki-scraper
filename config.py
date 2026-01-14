from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Wikipedia Settings
    base_url: str = Field(default="https://en.wikipedia.org", description="Base URL for Wikipedia")
    starting_category: str = "/wiki/Category:Scientists"
    target_article_count: int = 200

    # Request Settings
    # User-Agent is required and must be set by the user (via env var or .env file)
    user_agent: str = Field(description="User-Agent string adhering to Wikimedia policy")
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

    @field_validator('user_agent')
    @classmethod
    def validate_user_agent(cls, v: str) -> str:
        if len(v) < 10:
             raise ValueError("User-Agent is too short. It must be descriptive.")
        if '@' not in v and 'http' not in v:
            raise ValueError("User-Agent must contain contact information (email or website) to comply with Wikimedia policy.")
        return v

settings = Settings()
