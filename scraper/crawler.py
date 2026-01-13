import json
import os
import logging
from collections import deque
from typing import Set, Deque, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

class FailedUrl(BaseModel):
    url: str
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class CrawlStatistics(BaseModel):
    total_completed: int = 0
    total_queued: int = 0
    total_failed: int = 0

class CrawlState(BaseModel):
    completed: Set[str] = set()
    queued: Deque[str] = deque()
    failed: List[FailedUrl] = []
    statistics: CrawlStatistics = CrawlStatistics()

class Crawler:
    def __init__(self, progress_file: str = 'progress.json'):
        self.progress_file = progress_file
        self.state = CrawlState()
        self.seed_urls = ["/wiki/Albert_Einstein", "/wiki/Marie_Curie", "/wiki/Isaac_Newton", "/wiki/Charles_Darwin"]
        
        self._load_progress()
        
        # Seed if empty
        if not self.state.queued and not self.state.completed:
            for url in self.seed_urls:
                self._add_url(url)

    def _load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle potential malformed data or empty file
                    if data:
                        self.state = CrawlState(**data)
                logger.info(f"Loaded progress: {len(self.state.completed)} completed, {len(self.state.queued)} queued")
            except Exception as e:
                logger.error(f"Failed to load progress: {e}")
                # Fallback to empty state if load fails
                self.state = CrawlState()

    def save_progress(self):
        # Update statistics before saving
        self.state.statistics.total_completed = len(self.state.completed)
        self.state.statistics.total_queued = len(self.state.queued)
        self.state.statistics.total_failed = len(self.state.failed)
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                f.write(self.state.model_dump_json(indent=4))
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def get_next_url(self) -> Optional[str]:
        if not self.state.queued:
            return None
        return self.state.queued.popleft()

    def _add_url(self, url: str):
        if url not in self.state.completed and url not in self.state.queued:
            self.state.queued.append(url)

    def add_urls(self, urls: List[str]):
        for url in urls:
            self._add_url(url)
            
    def mark_completed(self, url: str):
        self.state.completed.add(url)
        
    def log_failure(self, url: str, reason: str):
        self.state.failed.append(FailedUrl(url=url, reason=str(reason)))

