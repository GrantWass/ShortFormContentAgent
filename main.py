"""Main entry point for the content generator."""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from config import Config
from logger import setup_logging


def load_files(paths: list[str], logger) -> tuple[str, list[str]]:
    """Read one or more article files and combine them into a single text block."""
    articles = []
    resolved = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            logger.error(f"File not found: {raw}")
            sys.exit(1)
        content = p.read_text(encoding="utf-8").strip()
        if not content:
            logger.warning(f"File is empty, skipping: {raw}")
            continue
        articles.append((p.name, content))
        resolved.append(str(p.resolve()))

    if not articles:
        logger.error("All provided files are empty.")
        sys.exit(1)

    if len(articles) == 1:
        return articles[0][1], resolved

    # Multiple articles — combine with clear separators so the LLM can
    # identify each source and synthesize them into one unified script.
    parts = [f"=== ARTICLE {i} ({name}) ===\n{text}" for i, (name, text) in enumerate(articles, 1)]
    return "\n\n".join(parts), resolved


def main():
    parser = argparse.ArgumentParser(
        description="Convert articles to short-form TikTok or long-form YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Single file (TikTok)
  python main.py input/1.txt

  # Multiple files synthesized into one video (TikTok)
  python main.py input/1.txt input/2.txt input/3.txt

  # YouTube long-form
  python main.py input/1.txt input/2.txt --youtube

  # URL fallback
  python main.py --url "https://example.com/article"
  python main.py --url "https://example.com/article" --youtube
        """,
    )

    # Primary input: one or more text files
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="One or more article text files (e.g. input/1.txt input/2.txt)",
    )

    # Secondary input: URL
    parser.add_argument(
        "--url",
        type=str,
        help="Article URL (used when no files are provided)",
    )

    parser.add_argument("--output-dir", type=str, help="Output directory (overrides config)")
    parser.add_argument(
        "--youtube",
        action="store_true",
        help="Generate a long-form YouTube video (10-12 min, 1920x1080, Wikimedia images)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["stock", "ai_video", "slideshow"],
        help="Force visual strategy for short-form (overrides auto-routing)",
    )
    parser.add_argument(
        "--enable-ai-video",
        action="store_true",
        help="Enable AI video generation for short-form (disabled by default)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--log-file", type=str, help="Optional log file path")

    args = parser.parse_args()
    log_file = Path(args.log_file) if args.log_file else None
    logger = setup_logging(log_level=args.log_level, log_file=log_file)

    # Validate input — files take priority, URL is fallback
    if not args.files and not args.url:
        parser.error("Provide one or more article files (e.g. input/1.txt) or --url")

    if args.files and args.url:
        logger.warning("Both files and --url provided; files take priority, --url ignored.")

    # Load config
    config = Config()
    if args.output_dir:
        config.OUTPUT_DIR = Path(args.output_dir)
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    errors = config.validate()
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        sys.exit(1)

    # Resolve article text and source list
    source_files: list[str] = []
    if args.files:
        article_text, source_files = load_files(args.files, logger)
        article_url = ""
    else:
        article_text = ""
        article_url = args.url

    current_date = datetime.now().strftime("%B %d, %Y")

    # Build initial pipeline state
    initial_state = {
        "article_text": article_text,
        "article_url": article_url,
        "enable_ai_video": args.enable_ai_video,
        "youtube_mode": args.youtube,
        "source_files": source_files,
        "current_date": current_date,
    }

    if not args.youtube and args.strategy:
        initial_state["visual_strategy"] = args.strategy
        if args.strategy == "ai_video" and not args.enable_ai_video:
            logger.warning("⚠️  ai_video strategy requires --enable-ai-video; enabling automatically.")
            initial_state["enable_ai_video"] = True

    # Log run summary
    mode = "YouTube Long-Form" if args.youtube else "TikTok Short-Form"
    logger.info("=" * 60)
    logger.info(f"Starting {mode} Pipeline")
    logger.info("=" * 60)
    if source_files:
        logger.info(f"Input files ({len(source_files)}): {', '.join(Path(f).name for f in source_files)}")
    else:
        logger.info(f"Input URL: {article_url}")
    if not args.youtube and args.strategy:
        logger.info(f"Visual strategy: {args.strategy} (forced)")
    logger.info(f"Output directory: {config.OUTPUT_DIR}")

    try:
        if args.youtube:
            from youtube_pipeline import create_youtube_pipeline
            pipeline = create_youtube_pipeline(config)
        else:
            from pipeline import create_pipeline
            pipeline = create_pipeline(config)

        final_state = pipeline.invoke(initial_state)

        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)

        if "final_video_path" in final_state:
            logger.info(f"✅ Video saved to: {final_state['final_video_path']}")
        else:
            logger.warning("⚠️  No final_video_path in state — assembly may have failed.")

        if final_state.get("errors"):
            for e in final_state["errors"]:
                logger.warning(f"  - {e}")

        if "script" in final_state:
            words = len(final_state["script"].split())
            logger.info(f"Script: {words} words (~{words // 150} min)")
        if args.youtube and "video_title" in final_state:
            logger.info(f"YouTube title: {final_state['video_title']}")
        if "visual_assets" in final_state:
            logger.info(f"Visual assets: {len(final_state['visual_assets'])} files")
        if not args.youtube and "visual_strategy" in final_state:
            logger.info(f"Visual strategy: {final_state['visual_strategy']}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
