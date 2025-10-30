import numpy as np
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image
import io

class EmbeddingService:
    def __init__(self, checkpoint_path: str, model_type: str):
        """
        Initializes the EmbeddingService.

        Args:
            checkpoint_path (str): Path to the SAM model checkpoint.
            model_type (str): The type of the SAM model (e.g., 'vit_b').
        """
        print(f"Loading SAM model from {checkpoint_path}...")
        sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        sam.to(device='cpu')  # Or 'cuda' if you have a GPU
        self.predictor = SamPredictor(sam)
        print("SAM model loaded successfully.")

    def generate_embedding_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """
        Generates an embedding for a given image.

        Args:
            image_bytes (bytes): The image in bytes.

        Returns:
            np.ndarray: The image embedding as a NumPy array.
        """
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB")
        
        # SAM expects a BGR image, but PIL opens in RGB.
        # The predictor handles the conversion internally.
        # No need to convert to numpy array and swap channels manually.
        
        print("Generating image embedding...")
        self.predictor.set_image(np.array(image))
        image_embedding = self.predictor.get_image_embedding().cpu().numpy()
        print("Image embedding generated successfully.")
        
        return image_embedding

# Example of how to initialize and use the service (for later use in main.py)
#
# from .config import settings
#
# embedding_service = EmbeddingService(
#     checkpoint_path=settings.SAM_CHECKPOINT_PATH,
#     model_type=settings.SAM_MODEL_TYPE
# )
