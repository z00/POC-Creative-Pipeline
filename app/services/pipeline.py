import os
import uuid

from PIL import Image

from app.models import CampaignBrief

from .checks import passes_legal_check
from .genai import GenAIService
from .image_utils import create_variations
from .storage import LocalStorage

# In-memory DB for tracking campaign state
CAMPAIGN_DB = {}


class CreativePipeline:
    def __init__(self):
        self.storage = LocalStorage()
        self.ai = GenAIService()

    async def process_campaign(self, campaign_id: str, brief: CampaignBrief):
        try:
            campaign_record = CAMPAIGN_DB[campaign_id]
            campaign_record.status = "processing"

            if not passes_legal_check(brief.campaign_message):
                campaign_record.status = "failed: legal check rejected message"
                return

            # 1. Localize the campaign message
            localized_msg = self.ai.localize_text(
                brief.campaign_message, brief.target_region
            )

            for product in brief.products:
                campaign_record.generated_assets[product.name] = []
                safe_prod_name = product.name.replace(" ", "_")

                # Define directory for this product's inputs
                prod_input_dir = os.path.join(
                    self.storage.input_dir, campaign_id, safe_prod_name
                )
                os.makedirs(prod_input_dir, exist_ok=True)

                # 2. Check if UI uploaded a base image; otherwise generate one
                base_image_path = campaign_record.base_images.get(product.name)

                if not base_image_path:
                    # Create the file path where GenAI should save the image (forcing .jpg)
                    temp_filename = f"gen_{uuid.uuid4().hex[:8]}.jpg"
                    target_gen_path = os.path.join(prod_input_dir, temp_filename)

                    prompt = (
                        f"Professional studio product shot of {product.name}. "
                        f"{product.description}. High resolution, commercial, sharp focus "
                        f"lighting, 4k quality, centered composition."
                    )

                    # Generate and get the path back
                    base_image_path = self.ai.generate_image(prompt, target_gen_path)
                    campaign_record.base_images[product.name] = base_image_path

                # Normalize the base image (handle PNG/RGBA uploads from UI)
                # This ensures create_variations always receives a readable file regardless of image format
                normalized_path = os.path.join(
                    prod_input_dir, f"normalized_{safe_prod_name}.jpg"
                )
                with Image.open(base_image_path) as b_img:
                    if b_img.mode in ("RGBA", "P"):
                        clean_img = Image.new("RGB", b_img.size, (255, 255, 255))
                        if b_img.mode == "RGBA":
                            clean_img.paste(b_img, mask=b_img.split()[3])
                        else:
                            clean_img.paste(b_img)
                        clean_img.save(normalized_path, "JPEG")
                        base_image_path = normalized_path
                    elif b_img.format != "JPEG":
                        b_img.convert("RGB").save(normalized_path, "JPEG")
                        base_image_path = normalized_path

                # 3. Create Variations (Outputs)
                product_output_dir = os.path.join(
                    self.storage.output_dir, campaign_id, safe_prod_name
                )
                os.makedirs(product_output_dir, exist_ok=True)

                variations = create_variations(
                    base_image_path, localized_msg, product.name, product_output_dir
                )

                campaign_record.generated_assets[product.name].extend(variations)

            campaign_record.status = "completed"

        except Exception as e:
            print(f"Pipeline Error: {e}")
            if campaign_id in CAMPAIGN_DB:
                CAMPAIGN_DB[campaign_id].status = f"failed: {str(e)}"
