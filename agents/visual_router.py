"""Visual Strategy Router - Routes to appropriate visual generation method."""
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger
from prompts import VISUAL_ROUTER_SYSTEM


class VisualStrategyRouter:
    """Routes to stock footage, AI video, or image slideshow based on article characteristics."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=0.3,  # Lower temperature for routing decisions
            api_key=config.OPENAI_API_KEY
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", VISUAL_ROUTER_SYSTEM),
            ("human", "Article title: {title}\nArticle text (first 500 chars): {text}\n\nChoose strategy:"),
        ])
    
    def __call__(self, state: VideoState) -> VideoState:
        """Route to appropriate visual strategy."""
        logger.info("🔀 [Visual Router] Determining visual strategy...")
        
        # Check if AI video is enabled
        enable_ai_video = state.get("enable_ai_video", False)
        if not enable_ai_video:
            logger.info("🔀 [Visual Router] AI video generation is disabled")
        
        # Allow manual override
        if "visual_strategy" in state and state["visual_strategy"]:
            strategy = state["visual_strategy"]
            # Validate that ai_video is only used if enabled
            if strategy == "ai_video" and not enable_ai_video:
                logger.warning("🔀 [Visual Router] AI video strategy requested but disabled, falling back to stock footage")
                strategy = "stock"
            logger.info(f"🔀 [Visual Router] Using manual override: {strategy}")
            state["visual_strategy"] = strategy
            return state
        
        article_text = state.get("article_text", "")
        article_title = state.get("article_title", "")
        
        # Simple heuristic-based routing (can be overridden by LLM)
        strategy = self._heuristic_route(article_text, article_title, enable_ai_video)
        logger.info(f"🔀 [Visual Router] Heuristic routing suggests: {strategy}")
        
        # Optionally use LLM for more nuanced routing
        if self.config.OPENAI_API_KEY:
            try:
                logger.debug("🔀 [Visual Router] Using LLM for routing decision...")
                chain = self.prompt_template | self.llm
                response = chain.invoke({
                    "title": article_title or "Untitled",
                    "text": article_text[:500]
                })
                llm_strategy = response.content.strip().lower()
                # Filter out ai_video if disabled
                if llm_strategy == "ai_video" and not enable_ai_video:
                    logger.debug("🔀 [Visual Router] LLM suggested ai_video but it's disabled, using heuristic instead")
                    llm_strategy = strategy
                if llm_strategy in ["stock", "ai_video", "slideshow"]:
                    strategy = llm_strategy
                    logger.info(f"🔀 [Visual Router] LLM routing selected: {strategy}")
            except Exception as e:
                logger.warning(f"🔀 [Visual Router] LLM routing failed, using heuristic: {e}")
        
        state["visual_strategy"] = strategy
        logger.info(f"🔀 [Visual Router] ✅ Selected strategy: {strategy}")
        return state
    
    def _heuristic_route(self, text: str, title: str, enable_ai_video: bool = False) -> Literal["stock", "wikimedia", "ai_video", "slideshow"]:
        """Simple heuristic-based routing."""
        text_lower = (text + " " + title).lower()

        # Breaking news — stock footage is fastest and most relevant
        breaking_keywords = ["breaking", "urgent", "latest", "just in", "developing"]
        if any(kw in text_lower for kw in breaking_keywords):
            return "stock"

        # Historical or documentary-style content — Wikimedia has better imagery
        historical_keywords = [
            "history", "historical", "war", "battle", "century", "ancient", "revolution",
            "president", "prime minister", "government", "election", "congress", "senate",
            "treaty", "founded", "discovered", "invented", "assassination", "empire",
        ]
        if any(kw in text_lower for kw in historical_keywords):
            return "wikimedia"

        # Abstract/futuristic topics — only route to ai_video if enabled
        abstract_keywords = ["future", "ai", "technology", "virtual", "digital", "metaverse", "quantum"]
        if any(kw in text_lower for kw in abstract_keywords) and enable_ai_video:
            return "ai_video"

        # Data/analysis topics
        data_keywords = ["data", "study", "research", "analysis", "statistics", "survey"]
        if any(kw in text_lower for kw in data_keywords):
            return "slideshow"

        # Default to stock footage
        return "stock"
