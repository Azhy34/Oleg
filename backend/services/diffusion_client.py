import replicate
import requests
from backend.core.config import settings

class DiffusionClient:
    """
    A client for interacting with the Replicate API for image generation.
    """
    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)

    def generate_wallpaper(
        self,
        original_image_path: str,
        mask_image_path: str,
        wallpaper_image_path: str
    ) -> str:
        """
        Calls the Replicate API to generate a new wallpaper by applying a pattern
        to a masked area of an original image.

        Args:
            original_image_path: Path to the original interior image.
            mask_image_path: Path to the mask image.
            wallpaper_image_path: Path to the wallpaper pattern image.

        Returns:
            The URL of the generated image.
        """
        print("Starting wallpaper generation via Replicate API...")
        
        # Using a model suitable for inpainting with a pattern (ControlNet Tile)
        model_version = "diffusers/controlnet-tile-sdxl-1.0:69958813b3d86c8837a5b6b2334a3e5013a5a0c8a39528774a9404e8504634d8"
        
        with open(original_image_path, "rb") as original_image, \
             open(mask_image_path, "rb") as mask_image, \
             open(wallpaper_image_path, "rb") as wallpaper_image:
            
            output = self.client.run(
                model_version,
                input={
                    "image": original_image,
                    "mask": mask_image,
                    "prompt": "Applying a new wallpaper pattern to the specified wall area",
                    "control_image": wallpaper_image,
                }
            )
        
        if not output or not isinstance(output, list) or not output[0]:
            raise Exception("Invalid response from Replicate API.")
            
        result_url = output[0]
        print(f"Generation finished. Result URL: {result_url}")

        return result_url

# Create a single instance of the client
diffusion_client = DiffusionClient(api_token=settings.REPLICATE_API_TOKEN)
