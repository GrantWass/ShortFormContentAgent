# NYT Article → TikTok Generator

A multi-agent LangGraph pipeline that converts New York Times articles into TikTok-ready vertical videos.

## Architecture

This system uses LangGraph to orchestrate multiple specialized agents:

1. **Article Ingest Agent** - Fetches and cleans NYT articles
2. **Script Agent** - Generates conversational TikTok scripts (30-60s)
3. **Prompt Agent** - Converts narration into visual prompts
4. **Visual Strategy Router** - Routes to appropriate visual generation method
5. **Visual Generation Agents** - Stock footage, AI video, or image slideshow
6. **Voiceover Agent** - Converts script to speech
7. **Caption Generator** - Auto-generates subtitles
8. **Video Assembly Agent** - Assembles final vertical video

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `env.example.template` to `.env` and fill in your API keys:
```bash
cp env.example.template .env
# Then edit .env and add your API keys
```

3. Run an example:
```bash
python main.py --url "https://www.nytimes.com/2024/01/01/example.html"
```

## Configuration

The system supports multiple visual generation strategies:
- **Stock Footage**: Fast, cost-effective, uses Pexels/Pixabay
- **AI Video**: Abstract topics, uses Runway/Pika/Luma
- **Image Slideshow**: Fallback, uses DALL·E/Midjourney

Routing is automatic based on article characteristics, but can be manually overridden.

## Output

Produces vertical videos (1080×1920) optimized for TikTok with:
- Synchronized voiceover
- Auto-generated captions
- Background music
- Visual assets matched to narration
