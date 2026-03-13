import os
import time

from huggingface_hub import InferenceClient
from PIL import Image


class GenAIService:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN")
        if not self.token:
            raise ValueError("HF_TOKEN is missing from environment variables.")

        # Initialize the Inference Client
        self.client = InferenceClient(api_key=self.token)

        # FLUX.1-schnell for fast, high-quality images
        self.image_model = "black-forest-labs/FLUX.1-schnell"

        # It is highly reliable, natively supports chat_completion, and is excellent at localization.
        self.text_model = "Qwen/Qwen2.5-7B-Instruct"

    def generate_image(self, prompt: str, output_path: str, retries=2) -> str:
        """
        Generates a high-quality product image using FLUX.1 via Hugging Face.
        """
        for attempt in range(retries):
            try:
                image = self.client.text_to_image(prompt=prompt, model=self.image_model)

                if image.mode != "RGB":
                    image = image.convert("RGB")

                image.save(output_path, "JPEG", quality=95)
                print(f"Successfully generated image: {output_path}")
                return output_path

            except Exception as e:
                print(f"Hugging Face Image Gen attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                break

        # fallback image if genAI failed
        img = Image.new("RGB", (1024, 1024), color=(40, 44, 52))
        img.save(output_path, "JPEG")
        return output_path

    def localize_text(self, text: str, region: str) -> str:
        """
        Uses Qwen 2.5 on Hugging Face to adapt the ad copy.
        """
        try:
            # Simple, direct prompt for localization
            messages = [
                {
                    "role": "system",
                    "content": f"You are a marketing expert in {region}. Translate and adapt the text to be culturally relevant. Output ONLY the localized text, no explanations.",
                },
                {"role": "user", "content": text},
            ]

            response = self.client.chat_completion(
                model=self.text_model,
                messages=messages,
                max_tokens=100,
                temperature=0.7,  # allow LLM to be more creative and flexible
            )

            result = response.choices[0].message.content.strip()

            # Clean up potential AI chatter (like "Here is your translation:")
            return result.replace('"', "")

        except Exception as e:
            print(f"Text localization failed: {e}")
            return text
