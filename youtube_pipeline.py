"""YouTube long-form video pipeline (10-12 min, 1920x1080, Wikimedia images)."""
from langgraph.graph import StateGraph, END
from state import VideoState
from config import Config
from logger import logger

from agents.article_ingest import ArticleIngestAgent
from agents.youtube_script_agent import YouTubeScriptAgent
from agents.wikimedia_visual import WikimediaVisualAgent
from agents.voiceover_agent import VoiceoverAgent
from agents.caption_agent import CaptionAgent
from agents.youtube_video_assembly import YouTubeVideoAssemblyAgent


def create_youtube_pipeline(config: Config) -> StateGraph:
    """Build and compile the YouTube long-form LangGraph pipeline."""
    article_ingest = ArticleIngestAgent(config)
    youtube_script = YouTubeScriptAgent(config)
    wikimedia_visual = WikimediaVisualAgent(config)
    voiceover_agent = VoiceoverAgent(config)
    caption_agent = CaptionAgent(config)
    youtube_assembly = YouTubeVideoAssemblyAgent(config)

    workflow = StateGraph(VideoState)
    workflow.add_node("article_ingest", article_ingest)
    workflow.add_node("youtube_script", youtube_script)
    workflow.add_node("voiceover_agent", voiceover_agent)
    workflow.add_node("wikimedia_visual", wikimedia_visual)
    workflow.add_node("caption_agent", caption_agent)
    workflow.add_node("youtube_assembly", youtube_assembly)

    workflow.set_entry_point("article_ingest")
    workflow.add_edge("article_ingest", "youtube_script")
    # Voiceover runs before wikimedia so timestamps are available for clip timing
    workflow.add_edge("youtube_script", "voiceover_agent")
    workflow.add_edge("voiceover_agent", "wikimedia_visual")
    workflow.add_edge("wikimedia_visual", "caption_agent")
    workflow.add_edge("caption_agent", "youtube_assembly")
    workflow.add_edge("youtube_assembly", END)

    return workflow.compile()


def run_youtube_pipeline(
    config: Config,
    article_url: str = None,
    article_text: str = None,
) -> VideoState:
    """Run the YouTube pipeline and return the final state."""
    pipeline = create_youtube_pipeline(config)
    initial_state: VideoState = {
        "article_text": article_text or "",
        "article_url": article_url or "",
        "youtube_mode": True,
    }
    return pipeline.invoke(initial_state)
