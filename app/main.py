import io
import os
import shutil
import uuid
import zipfile
from typing import List

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.models import CampaignBrief, CampaignData, CampaignResponse
from app.services.pipeline import CAMPAIGN_DB, CreativePipeline

# load API KEY from .env file
load_dotenv()

app = FastAPI(
    title="Creative Automation Pipeline API",
    description="PoC for generating localized social ad variations at scale.",
    version="1.0.0",
)

pipeline = CreativePipeline()

# Mount static directories so the UI can serve images natively
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.get("/campaigns/", response_model=List[CampaignData])
async def get_all_campaigns():
    """Returns all campaigns from memory for the UI dashboard."""
    return list(CAMPAIGN_DB.values())


@app.post("/campaigns/", response_model=CampaignResponse)
async def create_campaign(
    background_tasks: BackgroundTasks,
    campaign_data: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    campaign_id = str(uuid.uuid4())
    brief = CampaignBrief.model_validate_json(campaign_data)  # Pydantic v2 usage

    file_map = {f.filename: f for f in files if f.filename}
    base_images = {}

    for prod in brief.products:
        if prod.asset_filename and prod.asset_filename in file_map:
            upload_file = file_map[prod.asset_filename]
            # CRITICAL: Use safe names for BOTH the path and the dictionary key
            safe_prod_name = prod.name.replace(" ", "_")
            prod_dir = os.path.join("storage", "inputs", campaign_id, safe_prod_name)
            os.makedirs(prod_dir, exist_ok=True)

            file_path = os.path.join(prod_dir, upload_file.filename)
            # Ensure path uses forward slashes for the UI/Browser compatibility
            web_path = file_path.replace("\\", "/")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            # Map the product name to the consistent web path
            base_images[prod.name] = web_path

    CAMPAIGN_DB[campaign_id] = CampaignData(
        id=campaign_id,
        status="queued",
        brief=brief,
        base_images=base_images,
        generated_assets={},
    )

    background_tasks.add_task(pipeline.process_campaign, campaign_id, brief)

    return CampaignResponse(
        id=campaign_id, status="queued", message="Campaign processing started."
    )


@app.get("/campaigns/{campaign_id}", response_model=CampaignData)
async def get_campaign(campaign_id: str):
    if campaign_id not in CAMPAIGN_DB:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CAMPAIGN_DB[campaign_id]


@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign from memory and remove all associated files from disk."""
    if campaign_id not in CAMPAIGN_DB:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 1. Define paths to remove
    input_path = os.path.join("storage", "inputs", campaign_id)
    output_path = os.path.join("storage", "outputs", campaign_id)

    # 2. Remove folders from disk if they exist
    try:
        if os.path.exists(input_path):
            shutil.rmtree(input_path)
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
    except Exception as e:
        # We log the error but continue to remove the DB entry
        # to keep the UI in sync
        print(f"Error deleting storage for {campaign_id}: {e}")

    # 3. Remove from in-memory DB
    del CAMPAIGN_DB[campaign_id]

    return {"message": f"Campaign {campaign_id} and its assets deleted successfully."}


@app.get("/campaigns/{campaign_id}/download/{product_name}")
async def download_product_assets(campaign_id: str, product_name: str):
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    assets = campaign.generated_assets.get(product_name, [])
    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for this product")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for asset_path in assets:
            if os.path.exists(asset_path):
                # asset_path is like 'storage/outputs/id/name/file.jpg'
                arcname = os.path.basename(asset_path)
                zip_file.write(asset_path, arcname=arcname)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment; filename={product_name}_assets.zip"
        },
    )
