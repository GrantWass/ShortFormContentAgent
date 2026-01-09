"""Prompt Agent - Converts narration sentences into visual prompts."""
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class PromptAgent:
    """Converts script sentences into abstract visual prompts."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=0.8,  # Higher creativity for visual prompts
            api_key=config.OPENAI_API_KEY
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a visual prompt generator for video production. Convert spoken narration into abstract, reusable visual prompts.

RULES:
1. One prompt per sentence
2. Prompts should be abstract and cinematic, not literal
3. NO logos, text, or brand references
4. NO specific people or locations (unless abstract)
5. Focus on mood, atmosphere, and visual concepts
6. Think in terms of stock footage, B-roll, or abstract visuals
7. Prompts should work for both video clips and images

Examples:
- "Breaking news alert" → "cinematic city skyline at night, newsroom atmosphere"
- "Economic data shows growth" → "animated data visualization, upward trending graphs"
- "People are concerned" → "diverse crowd reaction shots, worried expressions"
- "Technology is advancing" → "futuristic tech interfaces, glowing circuits"

Output format: JSON array of strings
["prompt 1", "prompt 2", "prompt 3", ...]"""),
            ("human", "Sentences:\n{sentences}\n\nGenerate visual prompts (one per sentence):")
        ])
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate visual prompts from sentences."""
        logger.info("🎨 [Prompt Agent] Starting visual prompt generation...")
        sentences = state.get("sentences", [])
        if not sentences:
            logger.error("🎨 [Prompt Agent] Error: sentences are required")
            raise ValueError("sentences are required")
        
        logger.info(f"🎨 [Prompt Agent] Generating prompts for {len(sentences)} sentences...")
        sentences_text = "\n".join(f"- {s}" for s in sentences)
        
        chain = self.prompt_template | self.llm
        logger.debug("🎨 [Prompt Agent] Calling LLM to generate visual prompts...")
        response = chain.invoke({"sentences": sentences_text})
        
        content = response.content.strip()
        
        # Extract JSON array
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        elif content.startswith("["):
            pass  # Already JSON
        else:
            # Try to find array in text
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                content = match.group(0)
        
        import json
        try:
            prompts = json.loads(content)
            if isinstance(prompts, list):
                state["prompts"] = prompts
                logger.info(f"🎨 [Prompt Agent] Generated {len(prompts)} visual prompts")
            else:
                logger.warning("🎨 [Prompt Agent] LLM response not a list, using fallback")
                # Fallback: create one prompt per sentence
                state["prompts"] = self._fallback_prompts(sentences)
        except json.JSONDecodeError:
            logger.warning("🎨 [Prompt Agent] Failed to parse JSON, using fallback prompts")
            state["prompts"] = self._fallback_prompts(sentences)
        
        logger.info("🎨 [Prompt Agent] ✅ Visual prompt generation complete")
        return state
    
    def _fallback_prompts(self, sentences: list[str]) -> list[str]:
        """Generate simple fallback prompts."""
        return [f"cinematic visual for: {s[:50]}" for s in sentences]
