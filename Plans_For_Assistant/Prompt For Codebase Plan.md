**Your Role:** You are a Principal Staff Engineer. Your task is to create a detailed, pedantic, and production-grade codebase plan (a "blueprint") for a technical assessment demo app. The resulting plan must be so clear that a junior engineer could implement it perfectly. The plan must be 100% traceable, modular, and defensible, adhering to all constraints.

**The Objective:** Build a "Creative Automation Pipeline" Proof-of-Concept (POC). This application will accept a campaign brief and product details, reuse existing assets if available, or generate new ones using GenAI, and then produce a set of final creative assets (images with text overlays) for different social media aspect ratios.

**The Ground Truth:** The app must fulfill all minimum requirements from the "FDE Take-Home Exercise" specification provided below in \<Specification\>.

**The design must adhere strictly to the following Mandatory Tech Stack:**

1. **UI / Application Server:** **Gradio**. The app must run as a local Gradio web app. This will be the *only* interface. No separate FastAPI backend.  
2. **Configuration Format:** **YAML**. All campaign briefs will be ingested as .yaml files, not .json.  
3. **Dependency Management:** **Python UV**. The README.md must provide all setup and run instructions using uv.  
4. **File Storage:** **Dropbox** (as the primary production-grade storage) with a **local filesystem fallback**. The app must check for a DROPBOX\_ACCESS\_TOKEN environment variable.  
   * If the token is present, all asset lookups and final output uploads *must* go to a specified Dropbox folder (e.g., /apps/creative\_automation\_poc/).  
   * If the token is *missing*, the app must gracefully fall back to using local folders (e.g., ./assets/ for lookups, ./output/ for saves) and log a warning.  
5. **Image Generation:** **gemini-2.5-flash-image**. This is the *only* model to be used for *new* asset generation. You must generate all three required aspect ratios.  
6. **Agentic QA & Compliance:** **Gemini Flash**. This model will be used as an "agent" to perform "nice-to-have" checks (which are *required* for this "production-grade" demo). It will:  
   * Perform legal/content moderation checks on the campaign message.  
   * Perform brand compliance checks on the campaign message and audience description against provided brand guidelines.

**The Demo Campaign:** The example campaign we will use for the demo is for the retailer **Patagonia**.

---

### **\<Specification\> (FDE Take-Home Exercise)**

* **Goal:** Demonstrate a working proof-of-concept that automates creative asset generation for social ad campaigns using GenAI.  
* **Requirements (minimum):**  
  * Accept a campaign brief (in **YAML**) with:  
    * Product(s) – at least two different products.  
    * Target region/market.  
    * Target audience.  
    * Campaign message.  
  * Accept input assets (from **Dropbox** or a local folder) and reuse them when available.  
  * When assets are missing, generate new ones using a **GenAI image model**.  
  * Produce creatives for at least **three aspect ratios** (1:1, 9:16, 16:9).  
  * Display **campaign message** on the final campaign posts.  
  * Run locally (as a **Gradio app**).  
  * Save generated outputs to **Dropbox** (or a local folder), clearly organized by campaign, product, and aspect ratio.  
  * Include basic documentation (**README.md**) explaining:  
    * How to run it (using **Python UV**).  
    * Example input and output.  
    * Key design decisions.  
    * Any assumptions or limitations.  
* **Nice to Have (Required for this POC):**  
  * Brand compliance checks.  
  * Simple legal content checks.  
  * Logging or reporting of results (to the Gradio UI).

---

### **\<Patagonia\_Brand\_Guidelines\> (For the Compliance Agent)**

* **Quality:** Build the best product, provide the best service, and constantly improve everything we do. The best product is useful, versatile, long-lasting, repairable, and recyclable.  
* **Integrity:** Examine our practices openly and honestly, learn from our mistakes, and meet our commitments.  
* **Environmentalism:** Protect our home planet. We’re all part of nature. We work to reduce our impact, share solutions, and embrace regenerative practices. Address the deep connections between environmental destruction and social justice.  
* **Justice:** Be just, equitable, and antiracist as a company and in our community. We embrace the work necessary to create equity for historically marginalized people.  
* **Not bound by convention:** Do it our way. Our success lies in developing new ways to do things.  
* **Forbidden Content:**  
  * **Legal:** No discriminatory language (e.g., "men only," "whites only"). No harmful or violent terms.  
  * **Brand Voice:** Avoid "get rich quick," "guaranteed," "miracle cure," "100% effective," or other false/scammy claims. Avoid overly aggressive sales language ("buy now," "limited time only"). Focus on quality, durability, and environmental mission.

---

### **Your Task: Generate the Codebase Plan**

Produce a single, comprehensive "Codebase Plan" that a developer will use to build this application. The plan must include the following sections:

#### **1\. High-Level Architecture**

A textual description of the application flow, from the user's interaction with Gradio to the final file being saved in storage.

* **Example Flow:**  
  1. User opens the Gradio app in their browser.  
  2. User (optional) uploads existing assets.  
  3. User uploads their campaign\_brief.yaml.  
  4. User clicks "Generate Campaign."  
  5. The Gradio app triggers the main Orchestrator function.  
  6. The Orchestrator...  
     a. Parses the YAML brief.  
     b. Calls the ComplianceAgent (using Gemini Flash) to validate the brief against legal and brand guidelines.  
     c. If it fails, logs are sent to the Gradio UI, and the process stops.  
     d. If it passes, the Orchestrator loops through each product in the brief.  
     e. For each product, it calls the StorageManager to find a matching asset (e.g., patagonia\_better\_sweater.jpg) in Dropbox or the local assets/ dir.  
     f. If an asset is found, it's used as the base image.  
     g. If an asset is not found, the ImageGenerator (using gemini-2.5-flash-image) is called to generate a new product image.  
     h. The CreativeEngine takes the base image and generates all 3 aspect ratios (1:1, 9:16, 16:9), resizing/cropping it and adding the campaign message as a text overlay.  
     i. The StorageManager saves these 3 final creatives to the output directory (Dropbox or local output/).  
  7. Logs, status updates, and a gallery of the final images are streamed to the Gradio UI.

#### **2\. Project File Structure (Tree)**

A file tree for the entire project.

creative-automation-poc/  
├── .env.example           \# Example for API keys  
├── .gitignore  
├── app.py                 \# Main Gradio application  
├── campaign\_brief.yaml    \# Example Patagonia campaign brief  
├── config.py              \# Loads and manages env variables  
├── modules/  
│   ├── \_\_init\_\_.py  
│   ├── orchestrator.py    \# Main business logic controller  
│   ├── storage\_manager.py \# Handles Dropbox/local file I/O  
│   ├── image\_generator.py \# Wraps Gemini 2.5 Flash Image API  
│   ├── creative\_engine.py \# Handles PIL/Pillow image ops (resize, text)  
│   └── compliance\_agent.py  \# Wraps Gemini Flash for QA/Legal/Brand  
└── README.md              \# Full documentation

#### **3\. Data Model: campaign\_brief.yaml**

Provide the full YAML structure for our "Patagonia" example campaign.

YAML

campaign\_id: "patagonia-q4-2025-launch"  
target\_region: "Global (English)"  
target\_audience: "Eco-conscious consumers, outdoor enthusiasts, and individuals (ages 25-55) who value quality, durability, and corporate responsibility."  
campaign\_message: "Built to endure. Designed to be repaired. Better for our home planet."

products:  
  \- name: "Patagonia Better Sweater"  
    description: "A warm, low-bulk full-zip jacket made of 100% recycled polyester fleece. Fair Trade Certified™ sewn."  
    \# Used by storage\_manager to find 'patagonia\_better\_sweater.jpg'  
    asset\_filename: "patagonia\_better\_sweater"

  \- name: "Patagonia Baggies Shorts"  
    description: "Durable, quick-drying shorts made from 100% recycled nylon with a DWR (durable water repellent) finish. Perfect for water and land."  
    \# Used by storage\_manager to find 'patagonia\_baggies\_shorts.jpg'  
    asset\_filename: "patagonia\_baggies\_shorts"

#### **4\. Module Specifications (The Core Blueprint)**

For *each* Python file (app.py, config.py, and all files in modules/), provide a detailed spec:

* **Purpose:** A 1-sentence description.  
* **Key Dependencies:** What other modules it imports (e.g., PIL, gradio, dropbox, google.genai).  
* **Classes & Functions:** A breakdown of its primary classes and public function signatures, including parameters and return types, with logic explanations.

**Example (for modules/storage\_manager.py):**

* **Purpose:** To abstract all file system operations, automatically choosing between Dropbox and local storage.  
* **Key Dependencies:** dropbox, os, pathlib, config  
* **Class: StorageManager**  
  * \_\_init\_\_(self, config: AppConfig):  
    * Tries to initialize dropbox.Dropbox(oauth2\_access\_token=...) using config.dropbox\_token.  
    * Sets self.mode \= "dropbox" or self.mode \= "local" based on success.  
    * Initializes self.dbx client if successful.  
    * Logs a warning if falling back to local mode.  
  * find\_asset(self, asset\_filename: str) \-\> bytes | None:  
    * Takes a clean name like "patagonia\_better\_sweater".  
    * Searches for patagonia\_better\_sweater.jpg, .png, etc.  
    * **If self.mode \== "dropbox":** Searches /apps/creative\_automation\_poc/assets/.  
    * **If self.mode \== "local":** Searches ./assets/.  
    * Returns the file content as bytes if found, else None.  
  * upload\_creative(self, campaign\_id: str, product\_name: str, aspect\_ratio: str, image\_data: bytes) \-\> str:  
    * Generates a structured path, e.g., patagonia-q4-2025-launch/patagonia\_better\_sweater/1x1.jpg.  
    * **If self.mode \== "dropbox":** Uploads image\_data to /apps/creative\_automation\_poc/output/ \+ path.  
    * **If self.mode \== "local":** Saves image\_data to ./output/ \+ path.  
    * Returns the final path of the saved file.

**(You must provide this level of detail for all 6 Python files.)**

#### **5\. Gradio app.py UI Flow**

Describe the components in the Gradio interface and the main function that ties them together.

* gr.Blocks() as the main layout.  
* **Row 1:** gr.Markdown("\#\# Creative Automation Pipeline (Patagonia Demo)")  
* **Row 2 (Inputs):**  
  * gr.File(label="Upload Campaign Brief (.yaml)") (required)  
  * gr.File(label="Upload Existing Assets (.zip, optional)")  
* **Row 3 (Action):**  
  * gr.Button("Generate Campaign", variant="primary")  
* **Row 4 (Outputs):**  
  * gr.Textbox(label="Campaign Logs", interactive=False, lines=15) (for streaming logs)  
  * gr.Gallery(label="Final Creatives", show\_label=True, columns=3)  
* **Main Function run\_campaign(brief\_file, assets\_zip):**  
  * This function will be triggered by the "Generate Campaign" button.  
  * It will parse the brief\_file (YAML).  
  * It will (if provided) unzip assets\_zip into the ./assets/ directory (or upload to Dropbox).  
  * It will create an instance of Orchestrator.  
  * It will use a gradio.Progress tracker and a log\_stream (a simple list of strings) to provide real-time feedback.  
  * It will call orchestrator.execute\_campaign(brief\_data, log\_callback)  
  * The log\_callback will update the gr.Textbox.  
  * On completion, it will return the final list of output file paths to the gr.Gallery and the full log to the gr.Textbox.

#### **6\. README.md Template**

Provide a complete, production-grade README.md file template. It must include:

* **Title:** \# Creative Automation Pipeline POC  
* **Status:** \> \*\*Note:\*\* This is a technical assessment proof-of-concept.  
* **Demo:** (A placeholder for the user to add their 2-3 minute demo video/gif).  
* **Features:** (List the key features: YAML briefs, GenAI image generation, Dropbox/local storage, 3 aspect ratios, agentic compliance checks).  
* **Tech Stack:** (List the mandatory stack: Gradio, Python UV, Gemini, Dropbox, PIL).  
* **Setup & Installation (Using Python UV):**  
  1. git clone ...  
  2. cd creative-automation-poc  
  3. uv venv (Create virtual env)  
  4. source .venv/bin/activate  
  5. uv pip install \-r requirements.txt (You'll need to list the requirements: gradio, google-genai, pyyaml, pillow, dropbox)  
  6. Create a .env file...  
* **Configuration:** (Explain how to create .env from .env.example with GEMINI\_API\_KEY and DROPBOX\_ACCESS\_TOKEN).  
* **How to Run:**  
  1. source .venv/bin/activate  
  2. gradio app.py  
  3. Open http://127.0.0.1:7860 in your browser.  
* **How to Use:** (Step-by-step: 1\. Upload campaign\_brief.yaml, 2\. (Optional) Upload assets, 3\. Click Generate, 4\. View results).  
* **Key Design Decisions:**  
  * **(You, the LLM, will write this section).**  
  * **Gradio vs. FastAPI:** "Chose Gradio for a self-contained, highly-demoable POC..."  
  * **Dropbox Abstraction:** "Created StorageManager to... demonstrate production-grade design..."  
  * **Agentic Compliance:** "Used Gemini Flash... to show the 'nice-to-have' features..."  
* **Assumptions & Limitations:**  
  * "Assumes assets are named according to asset\_filename in the brief."  
  * "Image generation is non-deterministic..."  
  * "Dropbox fallback to local storage is for demo robustness..."

