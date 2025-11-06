"""
Gradio UI for Creative Automation Pipeline.
"""

import gradio as gr
import requests
import yaml
import time
import os
from pathlib import Path
from typing import List, Tuple, Optional

# FastAPI backend URL - configurable via environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> bool:
    """Check if FastAPI backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        return response.status_code == 200
    except:
        return False


def run_campaign(brief_file, asset_files, locale_choice, ab_variant_choice, progress=gr.Progress()):
    """
    Run campaign generation workflow with real-time streaming updates.
    
    This is a generator function that yields intermediate results for real-time updates.
    
    Args:
        brief_file: Uploaded YAML brief file
        asset_files: Optional list of uploaded asset images
        locale_choice: Selected locale
        ab_variant_choice: Selected A/B variant
        progress: Gradio progress tracker
    
    Yields:
        Tuple of (logs_text, gallery_images) at each update
    """
    logs = []
    
    def add_log(message: str):
        """Add message to logs."""
        timestamp = time.strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {message}")
    
    try:
        # Check backend status
        add_log("Checking backend status...")
        yield "\n".join(logs), []
        
        if not check_backend_health():
            add_log("✗ ERROR: FastAPI backend is not running!")
            add_log("\nPlease start the backend server:")
            add_log("  Terminal 1: uv run uvicorn app:app --host 0.0.0.0 --port 8000")
            yield "\n".join(logs), []
            return
        
        add_log("✓ Backend is running\n")
        yield "\n".join(logs), []
        
        # Validate brief file
        if not brief_file:
            add_log("✗ ERROR: No campaign brief file uploaded")
            yield "\n".join(logs), []
            return
        
        add_log(f"Reading campaign brief: {Path(brief_file).name}")
        yield "\n".join(logs), []
        
        # Parse YAML brief
        try:
            with open(brief_file, 'r') as f:
                brief_data = yaml.safe_load(f)
            
            add_log(f"✓ Campaign ID: {brief_data.get('campaign_id', 'N/A')}")
            add_log(f"✓ Products: {len(brief_data.get('products', []))}")
            add_log("")
            yield "\n".join(logs), []
            
        except Exception as e:
            add_log(f"✗ ERROR parsing YAML: {str(e)}")
            yield "\n".join(logs), []
            return
        
        # Upload asset files if provided
        if asset_files:
            add_log(f"Uploading {len(asset_files)} asset files...")
            yield "\n".join(logs), []
            
            try:
                file_paths = [f.name if hasattr(f, 'name') else f for f in asset_files]
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/assets/upload",
                    json=file_paths,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    add_log(f"✓ Uploaded {result.get('uploaded_count', 0)} assets\n")
                else:
                    add_log(f"⚠ Asset upload warning: {response.status_code}\n")
                yield "\n".join(logs), []
            except Exception as e:
                add_log(f"⚠ Asset upload warning: {str(e)}\n")
                yield "\n".join(logs), []
        
        # Send campaign generation request
        add_log("="*60)
        add_log("Starting campaign generation...")
        add_log("="*60)
        yield "\n".join(logs), []
        
        # Add locale and A/B variant parameters
        params = {}
        if locale_choice and locale_choice != "Default":
            params["locale"] = locale_choice
            add_log(f"Using locale: {locale_choice}")
        if ab_variant_choice and ab_variant_choice != "Default":
            params["ab_variant"] = ab_variant_choice
            add_log(f"Using A/B variant: {ab_variant_choice}")
        
        if params:
            yield "\n".join(logs), []
        
        try:
            # Start campaign generation (async)
            response = requests.post(
                f"{BACKEND_URL}/api/v1/campaigns/generate",
                json=brief_data,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                add_log(f"✗ ERROR: Backend returned status {response.status_code}")
                add_log(f"Response: {response.text}")
                yield "\n".join(logs), []
                return
            
            result = response.json()
            campaign_id = result.get("campaign_id")
            
            add_log(f"Campaign started: {campaign_id}")
            add_log("Monitoring progress...\n")
            yield "\n".join(logs), []
            
            # Poll for status updates with real-time streaming
            max_polls = 600  # 5 minutes with 0.5s intervals
            poll_count = 0
            last_log_count = 0
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            while poll_count < max_polls:
                try:
                    status_response = requests.get(
                        f"{BACKEND_URL}/api/v1/campaigns/{campaign_id}/status",
                        timeout=15  # Increased from 5 to 15 seconds
                    )
                    
                    # Reset error counter on successful request
                    consecutive_errors = 0
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        campaign_status = status_data.get("status")
                        campaign_logs = status_data.get("logs", [])
                        
                        # Add new logs and yield immediately for real-time updates
                        new_logs_added = False
                        for log_entry in campaign_logs[last_log_count:]:
                            log_msg = log_entry.get("message", "")
                            add_log(log_msg)
                            new_logs_added = True
                        
                        # Yield if new logs were added for immediate UI update
                        if new_logs_added:
                            yield "\n".join(logs), []
                        
                        last_log_count = len(campaign_logs)
                        
                        # Update progress
                        progress_pct = status_data.get("progress", 0)
                        progress(progress_pct / 100, desc=f"Processing: {campaign_status}")
                        
                        # Check if complete
                        if campaign_status in ["completed", "failed"]:
                            if campaign_status == "completed":
                                add_log("\n" + "="*60)
                                add_log("✓ CAMPAIGN GENERATION COMPLETED!")
                                add_log("="*60)
                                
                                # Collect output images
                                output_paths = status_data.get("output_paths", {})
                                gallery_images = []
                                
                                for product_name, product_data in output_paths.items():
                                    creatives = product_data.get("creatives", {})
                                    for aspect_ratio, path in creatives.items():
                                        if Path(path).exists():
                                            gallery_images.append(str(path))
                                
                                add_log(f"\n✓ Generated {len(gallery_images)} total creatives")
                                add_log("\nCreatives are displayed in the gallery below.")
                                
                                yield "\n".join(logs), gallery_images
                                return
                            
                            else:  # failed
                                add_log("\n" + "="*60)
                                add_log("✗ CAMPAIGN GENERATION FAILED")
                                add_log("="*60)
                                
                                errors = status_data.get("errors", [])
                                if errors:
                                    add_log("\nErrors:")
                                    for error in errors:
                                        add_log(f"  - {error}")
                                
                                yield "\n".join(logs), []
                                return
                    
                    # Wait before next poll
                    time.sleep(0.5)
                    poll_count += 1
                    
                except requests.exceptions.Timeout:
                    consecutive_errors += 1
                    # Only log every 3rd timeout to avoid spam
                    if consecutive_errors % 3 == 1:
                        add_log(f"⚠ Backend is processing (timeout, attempt {consecutive_errors})...")
                        yield "\n".join(logs), []
                    
                    if consecutive_errors >= max_consecutive_errors:
                        add_log("\n✗ ERROR: Backend appears to be unresponsive")
                        add_log("The backend may still be processing. Check terminal logs.")
                        yield "\n".join(logs), []
                        return
                    
                    # Exponential backoff: wait longer after each timeout
                    wait_time = min(2 ** (consecutive_errors - 1), 10)
                    time.sleep(wait_time)
                    poll_count += 1
                    
                except requests.exceptions.RequestException as e:
                    consecutive_errors += 1
                    # Only log every 3rd error to avoid spam
                    if consecutive_errors % 3 == 1:
                        add_log(f"⚠ Connection issue (attempt {consecutive_errors}): {type(e).__name__}")
                        yield "\n".join(logs), []
                    
                    if consecutive_errors >= max_consecutive_errors:
                        add_log(f"\n✗ ERROR: Cannot connect to backend after {max_consecutive_errors} attempts")
                        add_log(f"Backend URL: {BACKEND_URL}")
                        yield "\n".join(logs), []
                        return
                    
                    # Exponential backoff
                    wait_time = min(2 ** (consecutive_errors - 1), 10)
                    time.sleep(wait_time)
                    poll_count += 1
            
            # Timeout
            add_log("\n✗ ERROR: Status polling timed out")
            add_log("The backend may still be processing. Check terminal output.")
            yield "\n".join(logs), []
            return
                
        except requests.exceptions.Timeout:
            add_log("\n✗ ERROR: Request timed out")
            yield "\n".join(logs), []
            return
            
        except Exception as e:
            add_log(f"\n✗ ERROR during generation: {str(e)}")
            yield "\n".join(logs), []
            return
    
    except Exception as e:
        add_log(f"\n✗ UNEXPECTED ERROR: {str(e)}")
        yield "\n".join(logs), []
        return


def parse_brief_options(brief_file):
    """Parse brief and return available locales and A/B variants."""
    if not brief_file:
        return gr.update(choices=["Default"], value="Default"), gr.update(choices=["Default"], value="Default")
    
    try:
        with open(brief_file, 'r') as f:
            brief_data = yaml.safe_load(f)
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/campaigns/parse-brief",
            json=brief_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            locales = ["Default"] + result.get("locales", [])
            ab_variants = ["Default"] + result.get("ab_variants", [])
            return gr.update(choices=locales, value="Default"), gr.update(choices=ab_variants, value="Default")
    except:
        pass
    
    return gr.update(choices=["Default"], value="Default"), gr.update(choices=["Default"], value="Default")


# Create Gradio interface
with gr.Blocks(
    title="Creative Automation Pipeline - Patagonia Demo",
    theme=gr.themes.Soft()
) as app:
    
    gr.Markdown("# 🎨 Creative Automation Pipeline")
    gr.Markdown("### Patagonia Demo - Generate Social Media Creatives with AI")
    gr.Markdown(
        "Upload a campaign brief (YAML) and optionally provide existing product assets. "
        "The system will generate creatives for three aspect ratios (1:1, 9:16, 16:9) "
        "with brand compliance checks."
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📤 Input")
            
            brief_file = gr.File(
                label="Campaign Brief (.yaml)",
                file_types=[".yaml", ".yml"],
                type="filepath"
            )
            
            asset_files = gr.File(
                label="Asset Images (optional)",
                file_count="multiple",
                file_types=["image"],
                type="filepath"
            )
            
            with gr.Row():
                locale_dropdown = gr.Dropdown(
                    label="Locale (Multi-language)",
                    choices=["Default"],
                    value="Default",
                    interactive=True
                )
                
                ab_variant_dropdown = gr.Dropdown(
                    label="A/B Test Variant",
                    choices=["Default"],
                    value="Default",
                    interactive=True
                )
            
            gr.Markdown(
                """
                **Tips:**
                - Upload `campaign_brief_patagonia.yaml` to get started
                - Asset images should be named to match the `asset_filename` in your brief
                - If no assets are provided, AI will generate product images
                - Select a locale for multi-language campaigns
                - Choose an A/B variant to test different messages
                """
            )
            
            generate_btn = gr.Button(
                "🚀 Generate Campaign",
                variant="primary",
                size="lg"
            )
            
            # Update dropdowns when brief is uploaded
            brief_file.change(
                fn=parse_brief_options,
                inputs=[brief_file],
                outputs=[locale_dropdown, ab_variant_dropdown]
            )
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Campaign Logs")
            
            log_output = gr.Textbox(
                label="",
                interactive=False,
                lines=20,
                max_lines=30,
                show_label=False,
                placeholder="Campaign logs will appear here..."
            )
    
    gr.Markdown("### 🖼️ Generated Creatives")
    
    gallery = gr.Gallery(
        label="",
        show_label=False,
        columns=3,
        rows=2,
        height="auto",
        object_fit="contain"
    )
    
    gr.Markdown(
        """
        ---
        
        **Storage Modes:**
        - **Dropbox Mode:** If configured, all assets and outputs are stored in Dropbox
        - **Local Mode:** If Dropbox is not configured, files are stored in `./assets/` and `./output/`
        
        **Requirements:**
        - FastAPI backend must be running on port 8000
        - Gemini API key must be configured in `.env`
        - See README.md for setup instructions
        """
    )
    
    # Event handler
    generate_btn.click(
        fn=run_campaign,
        inputs=[brief_file, asset_files, locale_dropdown, ab_variant_dropdown],
        outputs=[log_output, gallery]
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Creative Automation Pipeline - Gradio UI")
    print("="*60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print("Starting Gradio interface...")
    
    # Check if running in Docker
    in_docker = os.path.exists('/.dockerenv')
    
    if not in_docker:
        print("\nIMPORTANT: Make sure the FastAPI backend is running:")
        print("  Terminal 1: uv run uvicorn app:app --host 0.0.0.0 --port 8000")
        print("  Terminal 2: uv run python gradio_ui.py")
    else:
        print("\nRunning in Docker container mode")
    
    print("\n" + "="*60 + "\n")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        mcp_server=True
    )

