"""Script Agent - Generates conversational TikTok scripts from articles."""
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class ScriptAgent:
    """Generates spoken TikTok scripts (30-60 seconds, conversational)."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a TikTok script writer. Your job is to convert news articles into engaging, conversational scripts for short-form video.

CRITICAL RULES:
1. Script must be 60 seconds when spoken at ~180 words per minute
2. Write in a conversational, engaging tone - like you're talking to a friend
3. NO direct quotes from the article
4. NO attribution ("NYT says...", "According to...")
5. NO brand names or logos mentioned
6. Transform the content - make it your own voice
7. Focus on the most interesting/engaging aspects
8. Use simple, clear language
9. Start with a hook
9. End with a question or call to action

Output format (JSON):
{{
  "script": "Full script text here...",
  "sentences": ["Sentence 1.", "Sentence 2.", "Sentence 3."]
}}

Each sentence should be a complete thought that can be visualized."""),
            ("human", "Article:\n\n{article_text}\n\nGenerate a TikTok script:")
        ])
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate script from article text."""
        logger.info("✍️  [Script Agent] Starting script generation...")
        article_text = state.get("article_text", "")
        if not article_text:
            logger.error("✍️  [Script Agent] Error: article_text is required")
            raise ValueError("article_text is required")
        
        logger.info(f"✍️  [Script Agent] Article text length: {len(article_text)} characters")
        
        # Truncate if too long (keep first ~2000 chars for context)
        truncated_text = article_text[:2000] + "..." if len(article_text) > 2000 else article_text
        logger.info(f"✍️  [Script Agent] Calling LLM to generate script (using {self.config.OPENAI_MODEL})...")
        
        chain = self.prompt_template | self.llm
        response = chain.invoke({"article_text": truncated_text})
        
        # Parse JSON response
        content = response.content.strip()
        logger.debug(f"✍️  [Script Agent] LLM response received, length: {len(content)} characters")
        
        # Try to extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(content)
            state["script"] = result.get("script", "")
            state["sentences"] = result.get("sentences", [])
            logger.info(f"✍️  [Script Agent] Generated script: {len(state['script'])} characters, {len(state['sentences'])} sentences")
        except json.JSONDecodeError:
            logger.warning("✍️  [Script Agent] Failed to parse JSON, using fallback sentence splitting")
            # Fallback: treat entire response as script and split by sentences
            state["script"] = content
            state["sentences"] = self._split_into_sentences(content)
            logger.info(f"✍️  [Script Agent] Fallback script: {len(state['script'])} characters, {len(state['sentences'])} sentences")
        
        logger.info("✍️  [Script Agent] ✅ Script generation complete")
        return state
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences (simple heuristic)."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() + "." for s in sentences if s.strip()]
