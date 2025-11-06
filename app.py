"""
FastAPI backend for Creative Automation Pipeline.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import yaml
import asyncio
import json
from datetime import datetime

from config import config
from modules import CampaignOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Creative Automation Pipeline API",
    description="Backend API for generating creative campaign assets",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = CampaignOrchestrator(config)

# Global storage for campaign status (in-memory, for demo purposes)
campaign_status_store: Dict[str, Dict] = {}

# Pydantic models
class ProductRequest(BaseModel):
    """Product information for campaign."""
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    asset_filename: str = Field(..., description="Asset filename for lookup")


class CampaignRequest(BaseModel):
    """Campaign generation request."""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    target_region: str = Field(..., description="Target geographic region")
    target_audience: str = Field(..., description="Target audience description")
    campaign_message: str = Field(..., max_length=200, description="Campaign message (max 200 chars)")
    products: List[ProductRequest] = Field(..., min_length=2, description="List of products (minimum 2)")


class CampaignResponse(BaseModel):
    """Campaign generation response."""
    campaign_id: str
    status: str  # "completed", "failed", "processing"
    logs: List[str] = []
    output_paths: Dict = {}
    errors: List[str] = []


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "service": "Creative Automation Pipeline API",
        "version": "1.0.0",
        "status": "healthy",
        "storage_mode": config.get_storage_mode()
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "storage_mode": config.get_storage_mode(),
        "gemini_api_configured": bool(config.GEMINI_API_KEY),
        "dropbox_configured": config.has_dropbox_credentials()
    }


@app.post("/api/v1/campaigns/generate")
async def generate_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks,
    locale: Optional[str] = None,
    ab_variant: Optional[str] = None
):
    """
    Generate campaign creatives from brief (async with status updates).
    
    Args:
        request: Campaign generation request with products and details
        background_tasks: FastAPI background tasks
        locale: Optional locale code (e.g., "en_US", "es_ES")
        ab_variant: Optional A/B test variant name
    
    Returns:
        Campaign ID for status tracking
    """
    try:
        # Convert request to dict
        brief_data = request.model_dump()
        campaign_id = brief_data.get("campaign_id", "unknown")
        
        # Initialize campaign status
        campaign_status_store[campaign_id] = {
            "status": "processing",
            "logs": [],
            "progress": 0,
            "output_paths": {},
            "errors": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Add background task
        background_tasks.add_task(
            process_campaign_async,
            campaign_id,
            brief_data,
            locale,
            ab_variant
        )
        
        return {
            "campaign_id": campaign_id,
            "status": "processing",
            "message": "Campaign generation started. Use /api/v1/campaigns/{campaign_id}/status for updates."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign generation failed: {str(e)}"
        )


async def process_campaign_async(campaign_id: str, brief_data: dict, 
                                 locale: Optional[str], ab_variant: Optional[str]):
    """Background task to process campaign with real-time updates."""
    try:
        def log_callback(message: str):
            """Callback to add logs in real-time."""
            if campaign_id in campaign_status_store:
                campaign_status_store[campaign_id]["logs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                })
                # Force update of progress if available
                if "progress" in campaign_status_store[campaign_id]:
                    pass  # Progress will be updated by orchestrator
        
        # Execute campaign generation
        results = orchestrator.execute_campaign(brief_data, log_callback, locale, ab_variant)
        
        # Update final status
        if campaign_id in campaign_status_store:
            # Update progress from results
            if "progress" in results:
                campaign_status_store[campaign_id]["progress"] = results["progress"]
            
            campaign_status_store[campaign_id].update({
                "status": results["status"],
                "output_paths": results.get("output_paths", {}),
                "errors": results.get("errors", []),
                "progress": results.get("progress", 100),
                "completed_at": datetime.now().isoformat()
            })
            
    except Exception as e:
        if campaign_id in campaign_status_store:
            campaign_status_store[campaign_id].update({
                "status": "failed",
                "errors": [str(e)],
                "progress": 0,
                "completed_at": datetime.now().isoformat()
            })


@app.get("/api/v1/campaigns/{campaign_id}/status")
async def get_campaign_status(campaign_id: str):
    """
    Get real-time status of a campaign.
    
    Args:
        campaign_id: Campaign identifier
    
    Returns:
        Campaign status with logs and progress
    """
    if campaign_id not in campaign_status_store:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return campaign_status_store[campaign_id]


@app.get("/api/v1/campaigns/{campaign_id}/outputs")
async def list_campaign_outputs(campaign_id: str):
    """
    List all output files for a campaign.
    
    Args:
        campaign_id: Campaign identifier
    
    Returns:
        List of output file paths
    """
    try:
        outputs = orchestrator.storage_manager.list_campaign_outputs(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "output_count": len(outputs),
            "outputs": outputs
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list outputs: {str(e)}"
        )


@app.post("/api/v1/assets/upload")
async def upload_assets(files: List[str]):
    """
    Upload user-provided asset files.
    
    Args:
        files: List of file paths to upload
    
    Returns:
        Upload results
    """
    try:
        results = orchestrator.storage_manager.upload_user_assets(files)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Asset upload failed: {str(e)}"
        )


@app.post("/api/v1/campaigns/parse-brief")
async def parse_brief(brief_data: dict):
    """
    Parse campaign brief and return available locales and A/B variants.
    
    Args:
        brief_data: Campaign brief dictionary
    
    Returns:
        Available locales and A/B variants
    """
    try:
        locales = orchestrator.get_available_locales(brief_data)
        ab_variants = orchestrator.get_available_ab_variants(brief_data)
        
        return {
            "locales": locales,
            "ab_variants": ab_variants,
            "default_message": brief_data.get("campaign_message", "")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse brief: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Starting Creative Automation Pipeline API")
    print("="*60)
    print(f"Storage Mode: {config.get_storage_mode()}")
    print(f"API Documentation: http://0.0.0.0:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
