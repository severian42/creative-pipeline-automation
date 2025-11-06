# Creative Automation Pipeline - Blueprint

## 1. High-Level Architecture

### Application Flow

1. **User opens Gradio UI** (`http://127.0.0.1:7860`) in browser

2. **User uploads** `campaign_brief.yaml` and optionally selects local folder with existing assets

3. **User clicks "Generate Campaign"** button

4. **Gradio triggers FastAPI backend** via HTTP POST to `/api/v1/campaigns/generate`

5. **FastAPI Orchestrator begins execution:**
   - a. Parse YAML brief and validate structure
   - b. Call `ComplianceAgent` (Gemini Flash) to validate campaign message against Patagonia brand guidelines and legal requirements
   - c. If compliance fails → return error logs to Gradio UI, stop
   - d. If compliance passes → proceed to asset processing

6. **For each product in brief:**
   - a. `StorageManager` searches for matching asset (using `asset_filename` from YAML)
   - b. Searches in Dropbox (`/apps/creative_automation_poc/assets/`) OR local `./assets/` (fallback)
   - c. If asset found → use as base image
   - d. If asset NOT found → call `ImageGenerator` (gemini-2.5-flash-image) to generate new product image
   - e. `CreativeEngine` processes base image:
     - Generates 3 aspect ratios (1:1, 9:16, 16:9)
     - Resizes/crops using PIL
     - Adds campaign message text overlay with professional styling
   - f. `StorageManager` saves 3 final creatives to output location

7. **Post-generation brand compliance** (optional second check on generated images)

8. **Logs streamed to Gradio UI** in real-time via SSE or polling

9. **Final gallery displayed** with all generated creatives and download links

### Component Architecture

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

---

## 2. Project File Structure

```
backend/
├── .env.example                    # Template for environment variables
├── .gitignore                      # Git ignore (includes .env, output/, __pycache__)
├── app.py                          # FastAPI backend application
├── gradio_ui.py                    # Gradio frontend application
├── config.py                       # Configuration management and validation
├── campaign_brief_patagonia.yaml   # Example Patagonia campaign brief
├── requirements.txt                # Python dependencies (UV compatible)
├── README.md                       # Comprehensive documentation
│
├── modules/
│   ├── __init__.py                 # Module exports
│   ├── orchestrator.py             # Main campaign execution controller
│   ├── storage_manager.py          # Dropbox/local file abstraction
│   ├── image_generator.py          # Gemini 2.5 Flash Image wrapper
│   ├── creative_engine.py          # PIL image operations (resize, text overlay)
│   └── compliance_agent.py         # Gemini Flash agentic QA/compliance
│
├── assets/                         # Local asset storage (fallback)
│   └── patagonia_better_sweater/
│       └── product_1.jpg
│   └── patagonia_baggies_shorts/
│       └── product_1.jpg
│
└── output/                         # Generated campaign outputs (local fallback)
    └── patagonia-q4-2025-launch/
        ├── patagonia_better_sweater/
        │   ├── 1x1.jpg
        │   ├── 9x16.jpg
        │   └── 16x9.jpg
        └── patagonia_baggies_shorts/
            ├── 1x1.jpg
            ├── 9x16.jpg
            └── 16x9.jpg
```

---

## 3. Data Model: campaign_brief_patagonia.yaml

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
    description: "Durable, quick-drying shorts made from 100% recycled nylon with a DWR (durable water repellent) finish. Perfect for water and land."
    asset_filename: "patagonia_baggies_shorts"
```

**Schema Validation Requirements:**
- `campaign_id`: string (required, alphanumeric with hyphens)
- `target_region`: string (required)
- `target_audience`: string (required)
- `campaign_message`: string (required, max 200 chars)
- `products`: list (required, min 2 items)
  - `name`: string (required)
  - `description`: string (required)
  - `asset_filename`: string (required, used for asset lookup)

---

## 4. Module Specifications

### 4.1 `config.py`

**Purpose:** Load, validate, and manage all environment variables and application configuration.

**Key Dependencies:** `os`, `pathlib`, `pydantic`

**Class: `AppConfig`**

- `__init__(self)`:
  - Loads `.env` file using `dotenv.load_dotenv()`
  - Reads `GEMINI_API_KEY` (required, raises error if missing)
  - Reads `DROPBOX_ACCESS_TOKEN` (optional)
  - Reads `DROPBOX_APP_KEY` (optional)
  - Reads `DROPBOX_APP_SECRET` (optional)
  - Sets `DROPBOX_BASE_PATH = "/apps/creative_automation_poc"`
  - Sets `LOCAL_ASSETS_DIR = "./assets"`
  - Sets `LOCAL_OUTPUT_DIR = "./output"`
  - Validates that paths exist or creates them

- `has_dropbox_credentials(self) -> bool`:
  - Returns True if all Dropbox tokens are present and non-empty
  - Returns False otherwise

- `get_storage_mode(self) -> str`:
  - Returns "dropbox" or "local" based on credential availability

- `get_patagonia_brand_guidelines(self) -> dict`:
  - Returns hardcoded Patagonia brand guidelines as dict
  - Used by `ComplianceAgent`

**Global Instance:**

```python
config = AppConfig()
```

---

### 4.2 `modules/storage_manager.py`

**Purpose:** Abstract all file system operations, automatically routing to Dropbox or local storage.

**Key Dependencies:** `dropbox`, `PIL.Image`, `io`, `pathlib`, `config`

**Class: `StorageManager`**

- `__init__(self, config: AppConfig)`:
  - Stores reference to config
  - If `config.has_dropbox_credentials()`:
    - Initialize `dropbox.Dropbox(oauth2_refresh_token=..., app_key=..., app_secret=...)`
    - Set `self.mode = "dropbox"`
    - Log success: "StorageManager initialized in DROPBOX mode"
  - Else:
    - Set `self.mode = "local"`
    - Set `self.dbx = None`
    - Log warning: "StorageManager initialized in LOCAL mode (Dropbox credentials not found)"

- `find_asset(self, asset_filename: str) -> Image.Image | None`:
  - Takes clean asset filename like `"patagonia_better_sweater"`
  - **If `self.mode == "dropbox"`:**
    - Search in `/apps/creative_automation_poc/assets/{asset_filename}/`
    - Look for `.jpg`, `.jpeg`, `.png` extensions
    - Use `dbx.files_list_folder()` to list files
    - Use `dbx.files_download()` to get first matching file
    - Return PIL Image or None
  - **If `self.mode == "local"`:**
    - Search in `./assets/{asset_filename}/`
    - Use `Path.glob("*.jpg")`, `Path.glob("*.png")`, etc.
    - Open with `Image.open()` and return first match or None
  - Log result: "Asset found: {path}" or "Asset not found: {asset_filename}"

- `upload_creative(self, campaign_id: str, product_name: str, aspect_ratio: str, image: Image.Image) -> str`:
  - Generates structured path: `{campaign_id}/{product_name}/{aspect_ratio}.jpg`
  - **If `self.mode == "dropbox"`:**
    - Full path: `/apps/creative_automation_poc/output/{campaign_id}/{product_name}/{aspect_ratio}.jpg`
    - Ensure parent folder exists using `dbx.files_create_folder_v2()` (catch already_exists error)
    - Convert PIL Image to bytes buffer (JPEG, quality=95)
    - Upload using `dbx.files_upload(mode=WriteMode.overwrite)`
    - Return Dropbox path
  - **If `self.mode == "local"`:**
    - Full path: `./output/{campaign_id}/{product_name}/{aspect_ratio}.jpg`
    - Create parent directories with `Path.mkdir(parents=True, exist_ok=True)`
    - Save image using `image.save()`
    - Return local path
  - Log: "Creative uploaded: {path}"

- `upload_user_assets(self, local_folder_path: str) -> dict`:
  - Takes local folder path from user's desktop
  - Scans for image files recursively
  - **If `self.mode == "dropbox"`:**
    - Upload all images to `/apps/creative_automation_poc/assets/`
    - Preserve folder structure
  - **If `self.mode == "local"`:**
    - Copy files to `./assets/`
  - Returns dict: `{"uploaded_count": int, "files": [list of paths]}`

---

### 4.3 `modules/image_generator.py`

**Purpose:** Wrap Gemini 2.5 Flash Image API for generating product images.

**Key Dependencies:** `google.genai`, `PIL.Image`, `io`, `mimetypes`, `config`

**Class: `ImageGenerator`**

- `__init__(self, config: AppConfig)`:
  - Stores config reference
  - Initialize `genai.Client(api_key=config.GEMINI_API_KEY)`
  - Set `self.model = "gemini-2.5-flash-image"`

- `generate_product_image(self, product_name: str, product_description: str, aspect_ratio: str) -> Image.Image`:
  - Takes product details and ONE aspect ratio ("1:1", "9:16", or "16:9")
  - Constructs prompt:
    ```
    "Professional product photography of {product_name}. {product_description}.
    High-quality commercial advertising style. Clean background. Studio lighting.
    Photorealistic."
    ```
  - Creates Gemini API request:
    - `model = "gemini-2.5-flash-image"`
    - `response_modalities = ["IMAGE"]`
    - `image_config = ImageConfig(aspect_ratio=aspect_ratio, image_size="1K")`
  - Streams response chunks
  - Extracts first `inline_data` chunk with image bytes
  - Converts bytes to PIL Image using `Image.open(io.BytesIO(data))`
  - Returns PIL Image
  - Log: "Generated image for {product_name} at {aspect_ratio}"
  - If generation fails, raise Exception with details

- `generate_all_aspect_ratios(self, product_name: str, product_description: str) -> dict[str, Image.Image]`:
  - Loops through ["1:1", "9:16", "16:9"]
  - Calls `generate_product_image()` for each
  - Returns dict: `{"1:1": Image, "9:16": Image, "16:9": Image}`
  - This allows parallel or sequential generation

---

### 4.4 `modules/creative_engine.py`

**Purpose:** Perform PIL/Pillow image operations (resize, crop, text overlay).

**Key Dependencies:** `PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`, `pathlib`

**Class: `CreativeEngine`**

- `__init__(self)`:
  - Defines target sizes:
    ```python
    self.aspect_ratios = {
        "1:1": (1080, 1080),
        "9:16": (1080, 1920),
        "16:9": (1920, 1080)
    }
    ```
  - Loads default font (try system fonts, fallback to PIL default)

- `resize_to_aspect_ratio(self, image: Image.Image, aspect_ratio: str) -> Image.Image`:
  - Takes source image and target aspect ratio key ("1:1", "9:16", "16:9")
  - Gets target size from `self.aspect_ratios`
  - Calculate source aspect ratio
  - If wider than target: fit by height, then center-crop width
  - If taller than target: fit by width, then center-crop height
  - Use `Image.resize()` with `LANCZOS` resampling
  - Use `Image.crop()` to get exact dimensions
  - Return resized/cropped image

- `add_text_overlay(self, image: Image.Image, campaign_message: str, product_name: str) -> Image.Image`:
  - Create copy of image
  - Create semi-transparent black overlay at bottom (30% of height)
  - Use `Image.alpha_composite()` for professional look
  - Add campaign message in white text (centered in overlay)
  - Add product name in smaller white text at top-left corner
  - Use word wrapping if message is long
  - Font size responsive to image dimensions
  - Return final image with text

- `process_creative(self, base_image: Image.Image, aspect_ratio: str, campaign_message: str, product_name: str) -> Image.Image`:
  - Combines resize + text overlay
  - Calls `resize_to_aspect_ratio()`
  - Calls `add_text_overlay()`
  - Returns final creative-ready image

---

### 4.5 `modules/compliance_agent.py`

**Purpose:** Use Gemini Flash LLM to perform brand and legal compliance checks.

**Key Dependencies:** `google.genai`, `config`

**Class: `ComplianceAgent`**

- `__init__(self, config: AppConfig)`:
  - Stores config reference
  - Initialize `genai.Client(api_key=config.GEMINI_API_KEY)`
  - Set `self.model = "gemini-flash-latest"`
  - Load Patagonia brand guidelines from config

- `check_legal_compliance(self, campaign_message: str) -> tuple[bool, str]`:
  - Constructs prompt:
    ```
    You are a legal compliance checker for advertising content.
    Review this campaign message for legal issues:
    "{campaign_message}"
    
    Check for:
    - Discriminatory language
    - Harmful or violent terms
    - False claims or scammy language
    - Misleading statements
    
    Respond in JSON format:
    {"compliant": true/false, "reason": "explanation"}
    ```
  - Calls Gemini Flash with prompt
  - Parses JSON response
  - Returns (bool, str): (is_compliant, reason)
  - Log result

- `check_brand_compliance(self, campaign_message: str, target_audience: str) -> tuple[bool, str]`:
  - Constructs prompt with Patagonia brand guidelines:
    ```
    You are a brand compliance checker for Patagonia.
    Brand Guidelines:
    {patagonia_guidelines}
    
    Campaign Message: "{campaign_message}"
    Target Audience: "{target_audience}"
    
    Check if the message:
    1. Aligns with Patagonia's environmental mission
    2. Avoids prohibited language (guaranteed, miracle, buy now, etc.)
    3. Focuses on quality, durability, and responsibility
    4. Matches the brand voice (authentic, not salesy)
    
    Respond in JSON format:
    {"compliant": true/false, "reason": "explanation"}
    ```
  - Calls Gemini Flash
  - Parses JSON response
  - Returns (bool, str)
  - Log result

- `validate_campaign(self, campaign_data: dict) -> tuple[bool, str]`:
  - Runs both `check_legal_compliance()` and `check_brand_compliance()`
  - If either fails, returns (False, reason)
  - If both pass, returns (True, "Campaign compliant")
  - This is the main entry point called by Orchestrator

---

### 4.6 `modules/orchestrator.py`

**Purpose:** Main controller that executes the entire campaign generation workflow.

**Key Dependencies:** All other modules, `yaml`, `pathlib`, `typing`

**Class: `CampaignOrchestrator`**

- `__init__(self, config: AppConfig)`:
  - Initialize all sub-components:
    - `self.storage_manager = StorageManager(config)`
    - `self.image_generator = ImageGenerator(config)`
    - `self.creative_engine = CreativeEngine()`
    - `self.compliance_agent = ComplianceAgent(config)`
  - Set `self.config = config`

- `execute_campaign(self, brief_data: dict, log_callback: callable) -> dict`:
  - Main orchestration method
  - `log_callback` is a function to send real-time logs to Gradio UI
  - **Step 1: Validation**
    - Validate YAML structure
    - Check that at least 2 products exist
    - log_callback("Campaign validated")
  - **Step 2: Compliance Check**
    - Call `compliance_agent.validate_campaign(brief_data)`
    - If fails: log error and return failure dict
    - log_callback("Compliance passed")
  - **Step 3: Process Each Product**
    - Loop through `brief_data["products"]`
    - For each product:
      - log_callback(f"Processing {product.name}")
      - Call `storage_manager.find_asset(product.asset_filename)`
      - If asset found:
        - Use existing asset as base
        - log_callback(f"Using existing asset for {product.name}")
      - If asset NOT found:
        - Call `image_generator.generate_all_aspect_ratios()`
        - log_callback(f"Generated new images for {product.name}")
      - For each aspect ratio:
        - If using existing asset: resize it using `creative_engine`
        - Add text overlay with `creative_engine.add_text_overlay()`
        - Call `storage_manager.upload_creative()`
        - log_callback(f"Saved {aspect_ratio} creative")
  - **Step 4: Return Results**
    - Compile dict with all output paths, status, logs
    - Return to FastAPI endpoint

---

### 4.7 `app.py` (FastAPI Backend)

**Purpose:** HTTP API server for campaign generation.

**Key Dependencies:** `fastapi`, `pydantic`, `config`, `orchestrator`

**Main Components:**

- Initialize FastAPI app with CORS
- Create global instances: `config`, `orchestrator`
- Define Pydantic models:
  - `ProductRequest`: name, description, asset_filename
  - `CampaignRequest`: campaign_id, target_region, target_audience, campaign_message, products
  - `CampaignResponse`: campaign_id, status, logs, output_paths

**Endpoint: `POST /api/v1/campaigns/generate`**

- Request body: `CampaignRequest`
- Converts to dict format
- Calls `orchestrator.execute_campaign(brief_data, log_callback)`
- Log callback appends to response logs list
- Returns `CampaignResponse` with status="completed" or status="failed"

**Endpoint: `GET /api/v1/health`**

- Returns `{"status": "healthy", "storage_mode": config.get_storage_mode()}`

**Endpoint: `GET /api/v1/campaigns/{campaign_id}/outputs`**

- Lists all output files for a campaign
- Returns file paths and download URLs

---

### 4.8 `gradio_ui.py` (Gradio Frontend)

**Purpose:** User interface for campaign generation.

**Key Dependencies:** `gradio`, `requests`, `yaml`, `pathlib`

**UI Components:**

```python
with gr.Blocks(title="Creative Automation Pipeline - Patagonia Demo") as app:
    gr.Markdown("## Creative Automation Pipeline (Patagonia Demo)")
    gr.Markdown("Upload campaign brief and assets to generate social media creatives.")

    with gr.Row():
        with gr.Column():
            brief_file = gr.File(
                label="Upload Campaign Brief (.yaml)",
                file_types=[".yaml", ".yml"]
            )
            assets_folder = gr.File(
                label="Upload Asset Images (optional)",
                file_count="multiple",
                file_types=["image"]
            )
            generate_btn = gr.Button("Generate Campaign", variant="primary")

        with gr.Column():
            log_output = gr.Textbox(
                label="Campaign Logs",
                interactive=False,
                lines=20,
                max_lines=30
            )

    with gr.Row():
        gallery = gr.Gallery(
            label="Generated Creatives",
            show_label=True,
            columns=3,
            height="auto"
        )

    # Event handler
    generate_btn.click(
        fn=run_campaign,
        inputs=[brief_file, assets_folder],
        outputs=[log_output, gallery]
    )
```

**Function: `run_campaign(brief_file, assets_files)`**

- Parse YAML brief from uploaded file
- If assets_files provided:
  - Send to FastAPI backend storage endpoint for upload
- Make POST request to `http://localhost:8000/api/v1/campaigns/generate`
- Poll for logs every 500ms and update `log_output` textbox
- When complete, fetch output images
- Return logs and gallery of images
- Handle errors gracefully with user-friendly messages

**Launch:**

```python
if __name__ == "__main__":
    app.launch(server_port=7860, server_name="127.0.0.1")
```

---

## 5. Requirements.txt

```txt
# Web Frameworks
fastapi==0.115.0
uvicorn[standard]==0.30.0
gradio==5.0.0

# GenAI
google-genai==1.0.0

# Image Processing
Pillow==10.4.0

# Cloud Storage
dropbox==12.0.2

# Configuration & Data
pyyaml==6.0.2
python-dotenv==1.0.1
pydantic==2.9.0

# Utilities
requests==2.32.0
```

---

## 6. .env.example

```env
# Required: Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Dropbox Configuration (if not set, will use local storage)
DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
```

---

## 7. README.md Content Structure

### Title & Status

- Project name and POC disclaimer
- Badge/note about assessment demo

### Demo Section

- Placeholder for 2-3 minute video/GIF

### Features

- YAML-based campaign briefs
- Gemini 2.5 Flash Image generation
- Dual storage (Dropbox/local)
- 3 aspect ratios (1:1, 9:16, 16:9)
- Agentic compliance checks
- Real-time logging
- Modern Gradio UI

### Tech Stack

- **Frontend:** Gradio 5.0
- **Backend:** FastAPI
- **GenAI:** Google Gemini (Flash + 2.5 Flash Image)
- **Storage:** Dropbox SDK (with local fallback)
- **Image Processing:** Pillow
- **Config:** YAML, Python UV

### Setup & Installation (UV)

```bash
# Clone repository
git clone <repo-url>
cd backend

# Create virtual environment with UV
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

- Detail `.env` variables
- Explain Dropbox setup (optional)
- Link to Gemini API key instructions

### How to Run

```bash
# Terminal 1: Start FastAPI backend
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Gradio UI
source .venv/bin/activate
python gradio_ui.py
```

- Open `http://127.0.0.1:7860`

### How to Use

1. Upload `campaign_brief_patagonia.yaml`
2. (Optional) Upload existing product images
3. Click "Generate Campaign"
4. View logs in real-time
5. Download creatives from gallery

### Key Design Decisions

**Gradio + FastAPI Architecture:**

- Gradio provides rapid prototyping with professional UI
- FastAPI backend enables modular, testable business logic
- Separation allows easy scaling or integration with other frontends

**Dropbox Abstraction Layer:**

- `StorageManager` encapsulates all I/O operations
- Automatic fallback to local storage for demo robustness
- Production-ready pattern for cloud storage integration
- Normalizes paths and handles errors gracefully

**Agentic Compliance with Gemini Flash:**

- Demonstrates "nice-to-have" features as required capabilities
- LLM-based validation more flexible than regex/keyword matching
- Checks both legal requirements and brand voice alignment
- Returns structured feedback for user transparency

**YAML over JSON:**

- More human-readable for campaign briefs
- Better commenting support for complex briefs
- Industry-standard for configuration files

**Multi-Aspect Ratio Strategy:**

- Generate once, format three times approach
- Efficient use of GenAI credits
- PIL operations (resize/crop) are deterministic and fast

### Assumptions & Limitations

**Asset Naming:**

- Assumes assets match `asset_filename` in brief
- Searches for common extensions (.jpg, .png)
- Takes first match if multiple files exist

**Image Generation:**

- Gemini output is non-deterministic
- Generation takes 5-10 seconds per image
- Rate limits may apply to API

**Text Overlay:**

- Fixed positioning (bottom overlay)
- English language only in demo
- Font fallback to PIL default if system fonts unavailable

**Storage:**

- Dropbox requires one-time OAuth setup
- Local fallback sufficient for single-user demo
- No authentication on FastAPI endpoints (demo only)

### Example Campaign Brief

Include the full Patagonia YAML example

### Future Enhancements

- Multi-language support
- A/B testing variants
- Performance analytics dashboard
- Batch processing
- Advanced brand color extraction
- Dynamic layout templates

---

## Implementation Order

1. **Setup & Config** (config.py, .env.example, requirements.txt)
2. **Storage Layer** (storage_manager.py)
3. **Image Generation** (image_generator.py)
4. **Creative Engine** (creative_engine.py)
5. **Compliance Agent** (compliance_agent.py)
6. **Orchestrator** (orchestrator.py)
7. **FastAPI Backend** (app.py)
8. **Gradio UI** (gradio_ui.py)
9. **Documentation** (README.md)
10. **Testing** (manual workflow test with Patagonia brief)

