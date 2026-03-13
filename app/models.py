from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    description: str
    asset_filename: Optional[str] = None


class CampaignBrief(BaseModel):
    campaign_name: str
    # CHANGED: Require at least 2 products to match UI logic
    products: List[Product] = Field(..., min_length=2)
    target_region: str
    target_audience: str
    campaign_message: str
    brand_colors: Optional[List[str]] = ["#000000", "#FFFFFF"]


class CampaignResponse(BaseModel):
    id: str
    status: str
    message: str


class CampaignData(BaseModel):
    id: str
    status: str
    brief: CampaignBrief
    base_images: Dict[str, str] = {}
    generated_assets: Dict[str, List[str]] = {}
