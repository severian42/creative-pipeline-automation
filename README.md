# Creative Automation Pipeline POC

> **Note:** This is a technical assessment proof-of-concept demonstrating automated creative generation for social media campaigns.

**Project Context:** This POC Demo was created under a strict 3hr time limit to fit a 'deadline scenario' where the client needed a quick turn around to see that their brief and pain points could be addressed. The use of a coding assistant was very much a part of the process to ensure that the rapid prototype would be functional and demoed. You can see my planning and prompts in the `Plans_For_Assistant` folder to give more insight into how I approached this project under the deadline.

All components are functional, yet not fully production ready. Tests currently pass the 80% coverage and functionality.

---

**Demo Video:** [Watch the demo](https://docs.google.com/videos/d/1OWNQq3kOzGgR8axxYk-luLv8pLAi4RVXp50GIw2thdQ/edit?usp=sharing)

## Features

- **YAML-Based Campaign Briefs:** Human-readable configuration format for campaign specifications
- **Gemini 2.5 Flash Image Generation:** AI-powered product image generation when assets are unavailable
- **Dual Storage System:** Seamless Dropbox integration with automatic local fallback
- **Multi-Aspect Ratio Support:** Generate creatives for 1:1 (Instagram), 9:16 (Stories/TikTok), and 16:9 (YouTube/Facebook)
- **LLM Compliance Checks:** AI-powered legal and brand compliance validation using Gemini Flash
- **Auto-Fix Compliance Issues:** Automatically rewrites non-compliant messages using LLM team (up to 5 attempts with smart retry logic)
- **Multi-Language Support:** Generate campaigns in multiple languages with locale-specific messages. Both AI models (Image Generation & Compliance) are locale-aware and will adapt their output to the selected language.
- **A/B Testing:** Test multiple message variants within a single campaign for optimization
- **Real-Time Streaming:** Live logs and progress updates streamed to UI as they happen (0.5s polling)
- **Demo Gradio UI:** Professional web interface for easy campaign management

---

## Tech Stack

- **Frontend:** Gradio 5.0 (Web UI)
- **Backend:** FastAPI (REST API)
- **GenAI:** Google Gemini
  - Gemini 2.5 Flash Image (image generation)
  - Gemini Flash (compliance checking)
- **Storage:** Dropbox SDK with local filesystem fallback
- **Image Processing:** Pillow (PIL)
- **Configuration:** YAML, Python dotenv
- **Dependency Management:** Python UV

---

## Prerequisites

- Python 3.10 or higher
- [Python UV](https://github.com/astral-sh/uv) installed
- Gemini API key ([Get one here](https://ai.google.dev/))
- (Optional) Dropbox app credentials for cloud storage

---

## Setup & Installation

You can run this application either locally with Python or using Docker.

### Option 1: Docker (Recommended for Quick Start)

**Prerequisites:**
- Docker and Docker Compose installed

**Quick Start:**
```bash
# 1. Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 2. Start the application
docker-compose up -d

# 3. Access the UI
# Gradio UI: http://localhost:7860
# FastAPI: http://localhost:8000
# API Docs: http://localhost:8000/docs

# 4. View logs
docker-compose logs -f

# 5. Stop the application
docker-compose down
```

### Option 2: Local Installation with Python UV

**Prerequisites:**
- Python 3.10+ and [Python UV](https://github.com/astral-sh/uv) installed
- Gemini API key ([Get one here](https://ai.google.dev/))

#### 1. Clone Repository

```bash
git clone https://github.com/severian42/creative-pipeline-automation
```

#### 2. Create Virtual Environment with UV

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

#### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required: GEMINI_API_KEY
# Optional: BACKEND_URL (default: http://localhost:8000)
# Optional: DROPBOX_ACCESS_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET
```

**Getting a Gemini API Key:**
1. Visit [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key"
3. Copy your key and add to `.env`

**Setting up Dropbox (Optional):**
1. Create a Dropbox app at [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Select "Scoped access" and "Full Dropbox" access
3. Generate an OAuth2 refresh token
4. Add credentials to `.env`

---

## How to Run

### Method 1: Docker (Simplest)

```bash
# Start both services with one command
docker-compose up -d

# Access the UI
open http://localhost:7860
```

### Method 2: Two Terminals (Local Development)

**Terminal 1 - Start FastAPI Backend:**
```bash
source .venv/bin/activate
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Gradio UI:**
```bash
source .venv/bin/activate
uv run python gradio_ui.py
```

Then open your browser to: `http://127.0.0.1:7860`

### Method 3: API Only

If you prefer to interact via API:

```bash
# Local
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000

# Or Docker
docker-compose up -d
```

API documentation available at: `http://localhost:8000/docs`

---

## How to Use

### Using the Gradio UI

1. **Upload Campaign Brief**
   - Click "Campaign Brief (.yaml)" and select `campaign_brief_patagonia.yaml`
   - The brief defines products, target audience, and campaign message

2. **(Optional) Upload Assets**
   - Click "Asset Images (optional)" to upload existing product photos
   - Name files to match `asset_filename` in the brief (e.g., `patagonia_better_sweater.jpg`)
   - If no assets provided, AI will generate images

3. **Generate Campaign**
   - Click "🚀 Generate Campaign" button
   - Monitor real-time logs in the Campaign Logs panel
   - Wait for compliance checks and creative generation

4. **View Results**
   - Generated creatives appear in the gallery
   - Files are saved to `./output/<campaign_id>/` (local mode) or Dropbox (cloud mode)
   - Each product has 3 creatives (1:1, 9:16, 16:9 aspect ratios)

### Using the API

```bash
curl -X POST http://localhost:8000/api/v1/campaigns/generate \
  -H "Content-Type: application/json" \
  -d @campaign_brief.json
```

See API documentation at `http://localhost:8000/docs` for full endpoint details.

---

## Multi-Language & A/B Testing

### Multi-Language Support

The system supports generating campaigns in multiple languages with full AI awareness:

**How it works:**
1. Define locales in your campaign brief:
   ```yaml
   locales:
     - language: "en"
       region: "US"
       message: "Built to endure..."
     - language: "es"
       region: "ES"
       message: "Construido para durar..."
     - language: "fr"
       region: "FR"
       message: "Conçu pour durer..."
   ```

2. Select a locale from the dropdown in the Gradio UI

3. **Both AI models are locale-aware:**
   - **Image Generator (Gemini 2.5 Flash Image):** Generates images with context for the target language/market
   - **Compliance Agent (Gemini Flash):** Validates and fixes messages in the selected language

4. All generated content (images, text overlays, compliance checks) respects the selected locale

**Supported Languages:**
- English (en), Spanish (es), French (fr) 
- Can be easily extended to: German (de), Italian (it), Portuguese (pt), Japanese (ja), Chinese (zh), Korean (ko), Arabic (ar)

### A/B Testing

Test multiple message variants to optimize campaign performance:

**How it works:**
1. Enable A/B testing in your campaign brief:
   ```yaml
   ab_testing:
     enabled: true
     variants:
       - name: "variant_a"
         message: "Built to endure. Designed to be repaired."
       - name: "variant_b"
         message: "Quality that lasts. Repair, don't replace."
   ```

2. Select a variant from the dropdown in the Gradio UI

3. The system generates creatives with the selected variant message

**Priority:** A/B variant takes precedence over locale if both are selected.

---

## Architecture

### High-Level Flow

```
┌─────────────────┐
│   Gradio UI     │ (Port 7860)
│  - Upload forms │
│  - Log viewer   │
│  - Gallery      │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │ (Port 8000)
│  ┌───────────────────────────┐  │
│  │   Orchestrator            │  │
│  │  (main business logic)    │  │
│  └──────────┬────────────────┘  │
│             │                    │
│    ┌────────┴────────┐          │
│    ▼        ▼        ▼          │
│  ┌────┐  ┌────┐  ┌────┐        │
│  │Comp│  │Stor│  │Img │        │
│  │lnce│  │age │  │Gen │        │
│  └────┘  └────┘  └────┘        │
│    │        │        │          │
│    │        │        └──────────┼─► Gemini 2.5 Flash Image
│    └────────┼───────────────────┼─► Gemini Flash (Agentic)
│             │                   │
│             ▼                   │
│      ┌──────────────┐           │
│      │  Dropbox API │           │
│      │  (or local)  │           │
│      └──────────────┘           │
└─────────────────────────────────┘
```

### Component Responsibilities

- **Gradio UI:** User interface for campaign management
- **FastAPI Backend:** RESTful API with campaign orchestration
- **Orchestrator:** Coordinates workflow between all components
- **Storage Manager:** Abstracts Dropbox/local file operations
- **Image Generator:** Wraps Gemini 2.5 Flash Image API
- **Creative Engine:** PIL-based image processing and text overlay
- **Compliance Agent:** Agentic validation using Gemini Flash

---

## Key Design Decisions

### Gradio + FastAPI Architecture

**Why two separate applications?**
- **Gradio:** Provides rapid prototyping with a professional, production-ready UI
- **FastAPI:** Enables modular, testable business logic with clear API contracts
- **Separation Benefits:** 
  - Easy to scale backend independently
  - Can integrate with other frontends (mobile app, CLI, etc.)
  - Better testability and maintainability

### Dropbox Abstraction Layer

**Why the `StorageManager` pattern?**
- **Flexibility:** Single interface for multiple storage backends
- **Robustness:** Automatic fallback to local storage for demo reliability
- **Production-Ready:** Pattern used in enterprise applications for cloud abstraction
- **Developer Experience:** No Dropbox account required to test the application

The `StorageManager` class:
- Detects credential availability at startup
- Normalizes paths across storage systems
- Handles errors gracefully with detailed logging

### Agentic Compliance with Auto-Fix

**Why use an LLM for compliance checking?**
- **Flexibility:** Adapts to nuanced brand voice better than keyword matching
- **Auto-Fix:** Automatically rewrites non-compliant messages using Gemini Flash
- **Multi-Attempt:** Tries up to 5 times with intelligent retry logic to achieve compliance
- **Transparency:** Returns structured explanations for all changes
- **Dual Validation:** Checks both legal requirements AND brand alignment

The compliance agent validates:
- Legal issues (discriminatory language, false claims, unsubstantiated claims)
- Brand voice alignment (Patagonia's environmental mission)
- Forbidden terms (e.g., "buy now", "limited time")
- Authentic messaging vs. aggressive sales language

**Auto-Fix Workflow:**
1. Check message for compliance issues (legal + brand)
2. If issues found → Use Gemini Flash to rewrite message
3. Re-check fixed message for compliance
4. If fix fails → Retry with new LLM generation
5. Repeat up to 5 times with smart retry logic until compliant
6. Log all fix attempts, explanations, and final compliant message
7. Continue campaign generation with fixed message

### YAML over JSON

**Why YAML for campaign briefs?**
- More human-readable and editable
- Better commenting support for documentation
- Industry standard for configuration files
- Easier for non-technical stakeholders to work with

### Multi-Aspect Ratio Strategy

**Two approaches implemented:**

1. **With Existing Assets:**
   - Load single asset
   - Resize/crop to each ratio using PIL
   - Add text overlay
   - Fast and deterministic

2. **Without Assets:**
   - Generate images at each ratio using Gemini
   - Add text overlay
   - Produces native aspect ratio content

This hybrid approach optimizes cost (fewer API calls when reusing assets) while maintaining quality.

---

## Assumptions & Limitations

### Asset Naming
- Assets must be organized in folders matching `asset_filename` from brief
- System searches for common image extensions (.jpg, .png, .jpeg, .webp)
- Takes first match if multiple files exist in folder

### Image Generation
- Gemini output is non-deterministic (same prompt may produce different images)
- Generation typically takes 5-10 seconds per image
- Rate limits may apply based on your Gemini API tier

### Text Overlay
- Fixed positioning with semi-transparent overlay at bottom
- English language only in current implementation
- Font fallback to PIL default if system fonts unavailable
- Responsive sizing based on image dimensions

### Storage
- Dropbox requires one-time OAuth2 setup
- Local fallback stores files in `./output/` directory
- No authentication on FastAPI endpoints (demo-only configuration)

### Compliance
- LLM-based validation may have false positives/negatives
- Requires active internet connection for Gemini API
- Falls back to "pass" on API errors to avoid blocking legitimate campaigns

---

## Project Structure

```
backend/
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── app.py                          # FastAPI backend
├── gradio_ui.py                    # Gradio frontend
├── config.py                       # Configuration management
├── campaign_brief_patagonia.yaml   # Example campaign
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── modules/
│   ├── __init__.py                 # Module exports
│   ├── orchestrator.py             # Campaign controller
│   ├── storage_manager.py          # Storage abstraction
│   ├── image_generator.py          # Gemini image API
│   ├── creative_engine.py          # Image processing
│   └── compliance_agent.py         # Compliance validation
│
├── assets/                         # Local asset storage
│   └── [product_folders]/
│       └── [images]
│
└── output/                         # Generated outputs
    └── [campaign_id]/
        └── [product_name]/
            ├── 1x1.jpg
            ├── 9x16.jpg
            └── 16x9.jpg
```

---

## Example Campaign Brief

```yaml
campaign_id: "patagonia-q4-2025-launch"
target_region: "Global (English)"
target_audience: "Eco-conscious consumers, outdoor enthusiasts, and individuals (ages 25-55) who value quality, durability, and corporate responsibility."
campaign_message: "Built to endure. Designed to be repaired. Better for our home planet."

products:
  - name: "Patagonia Better Sweater"
    description: "A warm, low-bulk full-zip jacket made of 100% recycled polyester fleece. Fair Trade Certified™ sewn."
    asset_filename: "patagonia_better_sweater"
    
  - name: "Patagonia Baggies Shorts"
    description: "Durable, quick-drying shorts made from 100% recycled nylon with a DWR finish. Perfect for water and land."
    asset_filename: "patagonia_baggies_shorts"
```

---

## Future Enhancements

- **Analytics Dashboard:** Track campaign performance metrics
- **Batch Processing:** Handle multiple campaigns simultaneously
- **Advanced Brand Color Extraction:** Ensure color palette compliance
- **Dynamic Layout Templates:** Support for various creative formats
- **Video Generation:** Extend to short-form video content
- **Approval Workflows:** Multi-stakeholder review and approval system

---

## Disclaimer

This is a technical assessment proof-of-concept.
