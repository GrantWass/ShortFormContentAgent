"""Main entry point for the TikTok generator."""
import argparse
import sys
from pathlib import Path
from config import Config
from pipeline import run_pipeline
from logger import setup_logging


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Convert NYT articles to TikTok videos")
    parser.add_argument("--url", type=str, help="NYT article URL")
    parser.add_argument("--text", type=str, help="Raw article text (alternative to URL)")
    parser.add_argument("--output-dir", type=str, help="Output directory (overrides config)")
    parser.add_argument("--strategy", type=str, choices=["stock", "ai_video", "slideshow"],
                       help="Force visual strategy (overrides auto-routing)")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--log-file", type=str, help="Optional log file path")
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    logger = setup_logging(log_level=args.log_level, log_file=log_file)
    
    # Load config
    config = Config()
    
    # Override output dir if provided
    if args.output_dir:
        from pathlib import Path
        config.OUTPUT_DIR = Path(args.output_dir)
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Validate config
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Check input
    if not args.url and not args.text:
        parser.error("Either --url or --text must be provided")
    
    # Prepare initial state
    article_url = args.url
    article_text = args.text
    
    # Create initial state with optional strategy override
    initial_state = {
        "article_text": article_text or "",
        "article_url": article_url or "",
    }
    
    if args.strategy:
        initial_state["visual_strategy"] = args.strategy
    
    logger.info("="*60)
    logger.info("Starting TikTok Generator Pipeline")
    logger.info("="*60)
    logger.info(f"Input type: {'URL' if article_url else 'Text'}")
    if article_url:
        logger.info(f"Article URL: {article_url}")
    if args.strategy:
        logger.info(f"Visual strategy: {args.strategy} (forced)")
    logger.info(f"Output directory: {config.OUTPUT_DIR}")
    
    try:
        # Run pipeline
        from pipeline import create_pipeline
        pipeline = create_pipeline(config)
        final_state = pipeline.invoke(initial_state)
        
        # Print results
        logger.info("="*60)
        logger.info("Pipeline completed successfully!")
        logger.info("="*60)
        
        if "final_video_path" in final_state:
            logger.info(f"✅ Video saved to: {final_state['final_video_path']}")
        else:
            logger.warning("⚠️  Video generation may have failed - no final_video_path in state")
        
        if "errors" in final_state and final_state["errors"]:
            logger.warning("Errors encountered during processing:")
            for error in final_state["errors"]:
                logger.warning(f"  - {error}")
        
        # Print metadata
        if "script" in final_state:
            logger.info(f"Script length: {len(final_state['script'])} characters")
        if "visual_assets" in final_state:
            logger.info(f"Visual assets generated: {len(final_state['visual_assets'])} files")
        if "visual_strategy" in final_state:
            logger.info(f"Visual strategy used: {final_state['visual_strategy']}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
