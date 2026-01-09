"""Example usage of the TikTok generator."""
from config import Config
from pipeline import run_pipeline


def example_with_url():
    """Example: Generate video from NYT article URL."""
    config = Config()
    
    # Example NYT article URL (replace with actual article)
    article_url = "https://www.nytimes.com/2024/01/01/example.html"
    
    print("Running pipeline with URL...")
    final_state = run_pipeline(config, article_url=article_url)
    
    print(f"\nVideo saved to: {final_state.get('final_video_path', 'N/A')}")


def example_with_text():
    """Example: Generate video from raw article text."""
    config = Config()
    
    # Example article text
    article_text = """
    Scientists have made a breakthrough in renewable energy technology. 
    A new solar panel design has achieved record efficiency levels, 
    potentially revolutionizing how we generate clean electricity. 
    The innovation could help accelerate the transition away from fossil fuels.
    """
    
    print("Running pipeline with text...")
    final_state = run_pipeline(config, article_text=article_text)
    
    print(f"\nVideo saved to: {final_state.get('final_video_path', 'N/A')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "text":
        example_with_text()
    else:
        example_with_url()
