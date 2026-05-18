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
            ("system", """You are a YouTube script writer specializing in long-form educational and news content. Convert the provided article into a structured 10-12 minute YouTube video script.

REQUIREMENTS:
- Total word count: 1,800-2,000 words (spoken at 150 WPM = ~12 minutes)
- Structure: Hook (30s) → Introduction (2min) → 3-5 content chapters (6-8min) → Conclusion/CTA (1min)
- Tone: Engaging, informative, authoritative but accessible
- NO direct quotes, NO attribution ("according to...", "the article says...")
- Transform content into your own voice
- Each chapter must be self-contained and clearly titled

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "video_title": "Compelling YouTube title (max 70 chars)",
  "video_description": "Full YouTube description with chapter timestamps (use 00:00, 02:30, etc. as placeholders)\\n\\nChapters:\\n00:00 Introduction\\n02:30 Chapter 1 Title\\n...",
  "chapters": [
    {{
      "title": "Chapter title",
      "content": "Full narration text for this chapter (2-4 paragraphs, 200-400 words)",
      "sentences": ["Complete sentence 1.", "Complete sentence 2.", "..."],
      "image_queries": ["specific Wikimedia Commons search term", "another specific term", "..."]
    }}
  ],
  "full_script": "Complete concatenated script from all chapters"
}}

RULES FOR image_queries:
- Provide one query per 2-3 sentences in the chapter
- Be highly specific: "Napoleon Bonaparte portrait 1812" not just "Napoleon"
- Target real subjects: historical figures, places, maps, paintings, artifacts, events
- These must exist as real images on Wikimedia Commons
- Include context: "French Revolution guillotine illustration", "Roman Colosseum aerial view", "World War 2 soldiers Normandy"
"""),
            ("human", "Article:\n\n{article_text}\n\nGenerate the YouTube script:"),
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
        response = chain.invoke({"article_text": truncated})

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
