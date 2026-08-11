
import os
import random
import numpy as np
from PIL import Image
import folder_paths

class NovAPreviewImageNoData:
    """
    Custom node to preview images in the UI without embedding ComfyUI workflow metadata in the temporary PNG.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_"
        self.compress_level = 1

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "preview_images"
    OUTPUT_NODE = True
    CATEGORY = "️☣️ NovA/Utils"

    def preview_images(self, images):
        # Generate a unique random prefix for temporary preview files
        filename_prefix = "NovA_Preview" + self.prefix_append + ''.join(random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for _ in range(5))
        
        # Resolve temporary output directory paths and naming schemes
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[2], images[0].shape[1]
        )

        results = list()
        for batch_number, image in enumerate(images):
            # Convert tensor image format (normalized float) to uint8 numpy array
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Generate target filename
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05d}_.png"
            file_path = os.path.join(full_output_folder, file)

            # Save PNG to temp directory without providing any metadata (pnginfo parameter omitted)
            img.save(file_path, compress_level=self.compress_level)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return {"ui": {"images": results}}

NODE_CLASS_MAPPINGS = {"NovAPreviewImageNoData": NovAPreviewImageNoData}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAPreviewImageNoData": "Preview Image (No Metadata)"}