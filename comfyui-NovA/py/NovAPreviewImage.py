import os
import torch
import numpy as np
from PIL import Image
import folder_paths
import secrets # Added for generating cryptographically secure unique short tokens

class NovAPreviewImage:
    def __init__(self):
        # Retrieve the dedicated ComfyUI temporary directory instead of output
        self.output_dir = folder_paths.get_temp_directory()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process_preview"
    CATEGORY = "NovA Tools"
    OUTPUT_NODE = True

    def process_preview(self, image):
        results = []
        
        for index, tensor in enumerate(image):
            array = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))
            
            # OPTIMIZATION: Generate a highly unique, random temporary filename
            # This aligns with standard ComfyUI behavior for native image downloads
            # while leaving the frontend "Save Image As..." logic completely unaffected.
            random_token = secrets.token_hex(4)
            temp_filename = f"ComfyUI_temp_{random_token}_{index}.png"
            
            filepath = os.path.join(self.output_dir, temp_filename)
            img.save(filepath, format="PNG")
            
            # Change type to "temp" so ComfyUI UI knows where to look
            results.append({
                "filename": temp_filename,
                "subfolder": "",
                "type": "temp"
            })
            
        return {"ui": {"images": results}, "result": (image,)}
        
# Register mappings for explicit dynamic discovery by the __init__.py engine
NODE_CLASS_MAPPINGS = {
    "NovAPreviewImage": NovAPreviewImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovAPreviewImage": "NovA Preview Image"
}