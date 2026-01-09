# Quick Start Guide

## Installation

1. **Clone and navigate to the project:**
```bash
cd ShortFormContentAgent
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp env.example.template .env
# Edit .env and add your API keys
```

## Required API Keys

**Minimum required:**
- `OPENAI_API_KEY` - For LLM (script generation) and TTS (voiceover)

**Optional but recommended:**
- `ELEVENLABS_API_KEY` - Better quality voiceover (alternative to OpenAI TTS)
- `PEXELS_API_KEY` - Stock footage (get free key at https://www.pexels.com/api/)
- `PIXABAY_API_KEY` - Stock footage backup (get free key at https://pixabay.com/api/docs/)

**For AI video generation:**
- `RUNWAY_API_KEY` - AI video generation
- `PIKA_API_KEY` - AI video generation
- `LUMA_API_KEY` - AI video generation

## Usage

### Basic Usage (URL)
```bash
python main.py --url "https://www.nytimes.com/2024/01/01/example.html"
```

### Basic Usage (Text)
```bash
python main.py --text "Your article text here..."
```

### Force Visual Strategy
```bash
python main.py --url "..." --strategy stock
python main.py --url "..." --strategy ai_video
python main.py --url "..." --strategy slideshow
```

### Custom Output Directory
```bash
python main.py --url "..." --output-dir ./my_outputs
```

## Pipeline Flow

1. **Article Ingest** - Fetches and cleans article text
2. **Script Agent** - Generates 60s conversational script
3. **Prompt Agent** - Converts sentences to visual prompts
4. **Visual Router** - Chooses strategy (stock/ai_video/slideshow)
5. **Visual Generation** - Fetches/generates visuals
6. **Voiceover Agent** - Converts script to speech
7. **Caption Agent** - Generates subtitles
8. **Video Assembly** - Assembles final video

## Output Structure

```
outputs/
├── audio/
│   └── voiceover.mp3
├── visuals/
│   ├── stock/
│   ├── ai_video/
│   └── slideshow/
└── videos/
    └── final_video.mp4
```

## Troubleshooting

**Issue: Import errors**
- Make sure you're running from the project root directory
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Issue: API key errors**
- Check your `.env` file has the correct keys
- Verify keys are valid and have proper permissions

**Issue: Video generation fails**
- Ensure FFmpeg is installed: `brew install ffmpeg` (Mac) or `apt-get install ffmpeg` (Linux)
- For Windows, download from https://ffmpeg.org/

**Issue: No visuals generated**
- Check that at least one visual API key is configured
- The system will create placeholder images if APIs are unavailable

## Next Steps

- Customize prompt templates in each agent
- Add retry logic for API failures
- Implement caching for expensive operations
- Add batch processing for multiple articles
- Enhance video assembly with better transitions and effects
