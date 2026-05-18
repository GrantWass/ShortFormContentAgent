"""YouTube Script Agent - Generates structured 10-12 minute video scripts."""
import json
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger
from prompts import YOUTUBE_SCRIPT_SYSTEM


class YouTubeScriptAgent:
    """Generates long-form YouTube scripts with chapters and Wikimedia image queries."""

    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY,
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", YOUTUBE_SCRIPT_SYSTEM),
            ("human", "Today's date: {current_date}\n\nArticle:\n\n{article_text}\n\nGenerate the YouTube script:"),
        ])

    def __call__(self, state: VideoState) -> VideoState:
        logger.info("🎬 [YouTube Script] Generating 10-12 minute script...")
        article_text = state.get("article_text", "")
        if not article_text:
            raise ValueError("article_text is required")

        # Use up to 4000 chars of article for richer long-form content
        truncated = article_text[:4000] + "..." if len(article_text) > 4000 else article_text
        logger.info(f"🎬 [YouTube Script] Using {len(truncated)} chars of article text")

        chain = self.prompt_template | self.llm
        response = chain.invoke({
            "article_text": truncated,
            "current_date": state.get("current_date", "unknown"),
        })

        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("🎬 [YouTube Script] JSON parse failed, using recovery fallback")
            result = self._recover(content)

        state["video_title"] = result.get("video_title", "YouTube Video")
        state["video_description"] = result.get("video_description", "")
        state["chapters"] = result.get("chapters", [])
        state["script"] = result.get("full_script", "")

        # Flatten all chapter sentences into state["sentences"] for the caption agent
        all_sentences = []
        for chapter in state["chapters"]:
            all_sentences.extend(chapter.get("sentences", []))
        state["sentences"] = all_sentences

        logger.info(f"🎬 [YouTube Script] ✅ Title: '{state['video_title']}'")
        logger.info(f"🎬 [YouTube Script] {len(state['chapters'])} chapters, "
                    f"{len(state['sentences'])} sentences, "
                    f"{len(state['script'].split())} words")
        return state

    def _recover(self, content: str) -> dict:
        """Best-effort fallback when JSON parsing fails."""
        sentences = [s.strip() + "." for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]
        n = max(1, len(sentences))
        queries_per_chapter = max(1, n // 3)
        return {
            "video_title": "YouTube Video",
            "video_description": "",
            "chapters": [
                {
                    "title": "Full Video",
                    "content": content,
                    "sentences": sentences,
                    "image_queries": ["documentary footage history"] * queries_per_chapter,
                }
            ],
            "full_script": content,
        }
