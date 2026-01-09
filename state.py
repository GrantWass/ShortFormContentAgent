"""State schema for LangGraph pipeline."""
from typing import TypedDict, Literal, Optional
from typing_extensions import NotRequired


class VideoState(TypedDict):
    """Shared state passed between LangGraph nodes."""
    
    # Article data
    article_url: NotRequired[str]
    article_text: str
    article_title: NotRequired[str]
    
    # Script data
    script: NotRequired[str]
    sentences: NotRequired[list[str]]
    
    # Visual prompts
    prompts: NotRequired[list[str]]
    
    # Visual strategy
    visual_strategy: NotRequired[Literal["stock", "ai_video", "slideshow"]]
    visual_assets: NotRequired[list[str]]  # Paths to video/image files
    
    # Audio
    voiceover_path: NotRequired[str]
    timestamps: NotRequired[list[dict[str, float]]]  # [{"start": 0.0, "end": 2.5}, ...]
    
    # Captions
    captions: NotRequired[list[dict]]  # [{"start": 0.0, "end": 2.5, "text": "..."}, ...]
    
    # Final output
    final_video_path: NotRequired[str]
    
    # Metadata
    errors: NotRequired[list[str]]
    metadata: NotRequired[dict]
