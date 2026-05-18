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

    # Visual prompts (short-form)
    prompts: NotRequired[list[str]]

    # Visual strategy (short-form)
    visual_strategy: NotRequired[Literal["stock", "ai_video", "slideshow"]]
    enable_ai_video: NotRequired[bool]
    visual_assets: NotRequired[list[str]]  # Paths to video/image files

    # Audio
    voiceover_path: NotRequired[str]
    timestamps: NotRequired[list[dict[str, float]]]  # [{"start": 0.0, "end": 2.5}, ...]

    # Captions
    captions: NotRequired[list[dict]]  # [{"start": 0.0, "end": 2.5, "text": "..."}, ...]

    # Final output
    final_video_path: NotRequired[str]

    # YouTube long-form fields
    youtube_mode: NotRequired[bool]
    video_title: NotRequired[str]
    video_description: NotRequired[str]
    chapters: NotRequired[list[dict]]  # [{title, content, sentences, image_queries}, ...]

    # Metadata
    source_files: NotRequired[list[str]]  # Input file paths that were combined
    current_date: NotRequired[str]        # Execution date passed to LLMs (e.g. "May 18, 2026")
    errors: NotRequired[list[str]]
    metadata: NotRequired[dict]
