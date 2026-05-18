"""Wikimedia Visual Agent - Fetches public domain images from Wikimedia Commons."""
import requests
from pathlib import Path
from typing import Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "ShortFormContentAgent/1.0 (educational use)"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class WikimediaVisualAgent:
    """Fetches public domain / CC-licensed images from Wikimedia Commons."""

    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "visuals" / "wikimedia"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def __call__(self, state: VideoState) -> VideoState:
        queries = self._collect_queries(state)
        if not queries:
            raise ValueError("wikimedia_visual requires either chapters (YouTube) or prompts (short-form)")

        logger.info(f"🖼️  [Wikimedia] Fetching {len(queries)} images...")
        visual_assets: list[str] = []

        for idx, query in enumerate(queries):
            logger.info(f"🖼️  [Wikimedia] [{idx + 1}/{len(queries)}] Searching: {query[:60]}...")
            path = self._fetch_best_image(query, 0, idx)
            if path:
                visual_assets.append(str(path))
                logger.info(f"🖼️  [Wikimedia]   ✅ {path.name}")
            else:
                logger.warning(f"🖼️  [Wikimedia]   ⚠️  No image found for: {query}")

        logger.info(f"🖼️  [Wikimedia] ✅ Downloaded {len(visual_assets)}/{len(queries)} images")
        state["visual_assets"] = visual_assets
        return state

    def _collect_queries(self, state: VideoState) -> list[str]:
        """Build a flat list of search queries from chapters (YouTube) or prompts (short-form)."""
        chapters = state.get("chapters", [])
        if chapters:
            queries = []
            for ch_idx, chapter in enumerate(chapters):
                chapter_queries = chapter.get("image_queries", [])
                logger.info(f"🖼️  [Wikimedia] Chapter {ch_idx + 1} '{chapter.get('title', '')}': {len(chapter_queries)} queries")
                queries.extend(chapter_queries)
            return queries

        # Short-form fallback: use visual prompts as search terms
        prompts = state.get("prompts", [])
        if prompts:
            logger.info(f"🖼️  [Wikimedia] Short-form mode: using {len(prompts)} visual prompts as queries")
        return prompts

    def _fetch_best_image(self, query: str, ch_idx: int, q_idx: int) -> Optional[Path]:
        """Search Commons and download the best matching image."""
        titles = self._search_commons(query)
        for title in titles:
            url = self._get_image_url(title)
            if url:
                filename = f"wiki_c{ch_idx:02d}_q{q_idx:02d}.jpg"
                path = self._download(url, filename)
                if path:
                    return path
        return None

    def _search_commons(self, query: str) -> list[str]:
        """Return a list of File: titles matching the query."""
        try:
            resp = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srnamespace": "6",  # File namespace
                    "srlimit": "8",
                    "format": "json",
                },
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("query", {}).get("search", [])
            titles = []
            for r in results:
                title = r.get("title", "")
                ext = Path(title).suffix.lower()
                if title.startswith("File:") and ext in IMAGE_EXTENSIONS:
                    titles.append(title)
            return titles
        except Exception as e:
            logger.debug(f"🖼️  [Wikimedia] Search error for '{query}': {e}")
            return []

    def _get_image_url(self, title: str) -> Optional[str]:
        """Resolve a File: title to a direct download URL (max 1920px wide)."""
        try:
            resp = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|size",
                    "iiurlwidth": "1920",
                    "format": "json",
                },
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                info = page.get("imageinfo", [{}])[0]
                # Prefer the resized thumb (bandwidth-friendly), fall back to original
                return info.get("thumburl") or info.get("url")
        except Exception as e:
            logger.debug(f"🖼️  [Wikimedia] URL resolve error for '{title}': {e}")
        return None

    def _download(self, url: str, filename: str) -> Optional[Path]:
        """Download an image file to the output directory."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
            resp.raise_for_status()
            path = self.output_dir / filename
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except Exception as e:
            logger.debug(f"🖼️  [Wikimedia] Download error: {e}")
            return None
