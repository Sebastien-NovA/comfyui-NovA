import json
import os
from pathlib import Path
from PIL import Image
import folder_paths

class NovAJsonExtractor:
    """
    Custom node to extract embedded workflow and prompt JSON metadata from PNG files.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # Fetch available images from ComfyUI input directory
        input_dir = folder_paths.get_input_directory()
        files = [
            f for f in os.listdir(input_dir) 
            if os.path.isfile(os.path.join(input_dir, f)) and f.lower().endswith(('.png', '.webp'))
        ]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
            },
            "optional": {
                "custom_file_path": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("workflow_json", "prompt_json")
    FUNCTION = "extract_json"
    CATEGORY = "️☣️ NovA/Utils"

    def extract_json(self, image: str, custom_file_path: str = ""):
        # Determine the image path based on user input
        if custom_file_path and custom_file_path.strip():
            target_path = Path(custom_file_path.strip()).resolve()
        else:
            input_dir = Path(folder_paths.get_input_directory()).resolve()
            target_path = (input_dir / image).resolve()

            # Security: Prevent path traversal attacks
            if not str(target_path).startswith(str(input_dir)):
                raise ValueError("⚠️ Security violation: Path traversal outside input directory is not allowed.")

        if not target_path.is_file():
            raise FileNotFoundError(f"Target image not found at path: {target_path}")

        workflow_json = "{}"
        prompt_json = "{}"

        # Extract embedded metadata safely from image headers
        with Image.open(target_path) as img:
            metadata = img.info
            
            if "workflow" in metadata:
                workflow_json = metadata["workflow"]
            
            if "prompt" in metadata:
                prompt_json = metadata["prompt"]

        return (workflow_json, prompt_json)

# Register node mappings for ComfyUI loader
NODE_CLASS_MAPPINGS = {
    "NovAJsonExtractor": NovAJsonExtractor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovAJsonExtractor": "NovA PNG JSON Metadata Extractor"
}