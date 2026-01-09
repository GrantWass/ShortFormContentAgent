"""Main LangGraph pipeline definition."""
from typing import Literal
from langgraph.graph import StateGraph, END
from state import VideoState
from config import Config
from logger import logger

# Import agents
from agents.article_ingest import ArticleIngestAgent
from agents.script_agent import ScriptAgent
from agents.prompt_agent import PromptAgent
from agents.visual_router import VisualStrategyRouter
from agents.visual_stock import StockFootageAgent
from agents.visual_ai_video import AIVideoAgent
from agents.visual_slideshow import ImageSlideshowAgent
from agents.voiceover_agent import VoiceoverAgent
from agents.caption_agent import CaptionAgent
from agents.video_assembly import VideoAssemblyAgent


def create_pipeline(config: Config) -> StateGraph:
    """Create the LangGraph pipeline."""
    
    # Initialize agents
    article_ingest = ArticleIngestAgent(config)
    script_agent = ScriptAgent(config)
    prompt_agent = PromptAgent(config)
    visual_router = VisualStrategyRouter(config)
    stock_agent = StockFootageAgent(config)
    ai_video_agent = AIVideoAgent(config)
    slideshow_agent = ImageSlideshowAgent(config)
    voiceover_agent = VoiceoverAgent(config)
    caption_agent = CaptionAgent(config)
    video_assembly = VideoAssemblyAgent(config)
    
    # Create graph
    workflow = StateGraph(VideoState)
    
    # Add nodes
    workflow.add_node("article_ingest", article_ingest)
    workflow.add_node("script_agent", script_agent)
    workflow.add_node("prompt_agent", prompt_agent)
    workflow.add_node("visual_router", visual_router)
    workflow.add_node("stock_footage", stock_agent)
    workflow.add_node("ai_video", ai_video_agent)
    workflow.add_node("image_slideshow", slideshow_agent)
    workflow.add_node("voiceover_agent", voiceover_agent)
    workflow.add_node("caption_agent", caption_agent)
    workflow.add_node("video_assembly", video_assembly)
    
    # Define edges
    workflow.set_entry_point("article_ingest")
    
    workflow.add_edge("article_ingest", "script_agent")
    workflow.add_edge("script_agent", "prompt_agent")
    workflow.add_edge("prompt_agent", "visual_router")
    
    # Conditional routing based on visual strategy
    def route_visuals(state: VideoState) -> Literal["stock_footage", "ai_video", "image_slideshow"]:
        strategy = state.get("visual_strategy", "stock")
        if strategy == "ai_video":
            logger.info("🔀 [Pipeline] Routing to AI Video generation")
            return "ai_video"
        elif strategy == "slideshow":
            logger.info("🔀 [Pipeline] Routing to Image Slideshow generation")
            return "image_slideshow"
        else:
            logger.info("🔀 [Pipeline] Routing to Stock Footage generation")
            return "stock_footage"
    
    workflow.add_conditional_edges(
        "visual_router",
        route_visuals,
        {
            "stock_footage": "stock_footage",
            "ai_video": "ai_video",
            "image_slideshow": "image_slideshow"
        }
    )
    
    # All visual paths converge
    workflow.add_edge("stock_footage", "voiceover_agent")
    workflow.add_edge("ai_video", "voiceover_agent")
    workflow.add_edge("image_slideshow", "voiceover_agent")
    
    workflow.add_edge("voiceover_agent", "caption_agent")
    workflow.add_edge("caption_agent", "video_assembly")
    workflow.add_edge("video_assembly", END)
    
    return workflow.compile()


def run_pipeline(config: Config, article_url: str = None, article_text: str = None) -> VideoState:
    """Run the pipeline with given input."""
    pipeline = create_pipeline(config)
    
    initial_state: VideoState = {
        "article_text": article_text or "",
        "article_url": article_url or "",
    }
    
    # Run pipeline
    final_state = pipeline.invoke(initial_state)
    
    return final_state
