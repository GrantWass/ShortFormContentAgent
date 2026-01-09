"""Article Ingest Agent - Fetches and cleans NYT articles."""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class ArticleIngestAgent:
    """Fetches and cleans article text from NYT URLs or raw text."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def __call__(self, state: VideoState) -> VideoState:
        """Process article input and extract clean text."""
        logger.info("📰 [Article Ingest] Starting article ingestion...")
        
        if "article_text" in state and state["article_text"]:
            # Already have text, just ensure it's clean
            logger.info("📰 [Article Ingest] Cleaning provided article text...")
            state["article_text"] = self._clean_text(state["article_text"])
            logger.info(f"📰 [Article Ingest] Cleaned text length: {len(state['article_text'])} characters")
            return state
        
        if "article_url" in state and state["article_url"]:
            # Fetch from URL
            logger.info(f"📰 [Article Ingest] Fetching article from URL: {state['article_url']}")
            text, title = self._fetch_from_url(state["article_url"])
            logger.info(f"📰 [Article Ingest] Fetched article, cleaning text...")
            state["article_text"] = self._clean_text(text)
            if title:
                state["article_title"] = title
                logger.info(f"📰 [Article Ingest] Article title: {title}")
            logger.info(f"📰 [Article Ingest] Cleaned text length: {len(state['article_text'])} characters")
        else:
            logger.error("📰 [Article Ingest] Error: Either article_text or article_url must be provided")
            raise ValueError("Either article_text or article_url must be provided")
        
        logger.info("📰 [Article Ingest] ✅ Article ingestion complete")
        return state
    
    def _fetch_from_url(self, url: str) -> tuple[str, Optional[str]]:
        """Fetch article from NYT URL."""
        try:
            # Try NYT API first if key is available
            if self.config.NYT_API_KEY and "nytimes.com" in url:
                article_id = self._extract_nyt_article_id(url)
                if article_id:
                    return self._fetch_from_nyt_api(article_id)
        except Exception as e:
            logger.warning(f"📰 [Article Ingest] NYT API fetch failed, falling back to scraping: {e}")
        
        # Fallback to web scraping
        logger.info("📰 [Article Ingest] Scraping article from web page...")
        return self._scrape_article(url)
    
    def _extract_nyt_article_id(self, url: str) -> Optional[str]:
        """Extract article ID from NYT URL."""
        match = re.search(r'/(\d{4}/\d{2}/\d{2}/[^/]+)\.html', url)
        return match.group(1) if match else None
    
    def _fetch_from_nyt_api(self, article_id: str) -> tuple[str, Optional[str]]:
        """Fetch article using NYT API."""
        # This is a placeholder - NYT API structure varies
        # In practice, you'd use the NYT Article Search or Archive API
        raise NotImplementedError("NYT API integration requires specific API endpoint")
    
    def _scrape_article(self, url: str) -> tuple[str, Optional[str]]:
        """Scrape article content from web page."""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main article content
        article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile("article|content|story"))
        
        if article:
            text = article.get_text(separator=" ", strip=True)
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
        else:
            # Fallback: get all text
            text = soup.get_text(separator=" ", strip=True)
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
        
        return text, title
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize article text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common metadata patterns
        text = re.sub(r'By\s+[A-Z][a-z]+\s+[A-Z][a-z]+.*?\.', '', text)  # Author bylines
        text = re.sub(r'Published\s+[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}', '', text)  # Dates
        text = re.sub(r'Updated\s+[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Normalize whitespace again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
