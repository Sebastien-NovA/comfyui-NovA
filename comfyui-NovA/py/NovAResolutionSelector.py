import math
import torch

class NovAResolutionSelector:
    # Supported aspect ratios and their mathematical multipliers (width / height)
    RATIOS = {
        "Landscape – 16:9": 16 / 9,
        "Portrait – 9:16": 9 / 16,
        "Square – 1:1": 1.0,
        "Portrait – 2:3": 2 / 3,
        "Landscape – 3:2": 3 / 2,
    }

    # Dynamically generate multiples of 64 between 4096 and 512 (inclusive)
    LENGTHS = [str(x) for x in range(4096, 511, -64)]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Format selection or Custom option
                "format": (["Custom Format"] + list(cls.RATIOS.keys()), {"default": "Landscape – 16:9"}),
                # Choice of the greatest length (defaults to 1024, optimal for SDXL/Turbo)
                "greatest_length": (cls.LENGTHS, {"default": "1024"}),
                
                # Fallback values if "Custom Format" is selected
                "custom_width": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "custom_height": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                
                # Added batch size input to match EmptySD3LatentImage functionality
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
            }
        }

    # Added LATENT output type
    RETURN_TYPES = ("INT", "INT", "FLOAT", "LATENT")
    # Added Latent to corresponding output names
    RETURN_NAMES = ("Width", "Height", "Optimised Shift", "Latent")
    FUNCTION = "get_resolution"
    CATEGORY = "NovA Tools"

    def get_resolution(self, format, greatest_length, custom_width, custom_height, batch_size):
        if format == "Custom Format":
            width = custom_width
            height = custom_height
        else:
            # Retrieve the maximum selected length (converted to integer)
            max_len = int(greatest_length)
            ratio = self.RATIOS[format]
            
            if ratio == 1.0:
                # Square Mode
                width = max_len
                height = max_len
            elif ratio > 1.0:
                # Landscape Mode (width is the greatest length)
                width = max_len
                # Calculate height and round to the nearest multiple of 64
                height = int(round((max_len / ratio) / 64) * 64)
            else:
                # Portrait Mode (height is the greatest length)
                height = max_len
                # Calculate width and round to the nearest multiple of 64
                width = int(round((max_len * ratio) / 64) * 64)
        
        # --- OPTIMISED SHIFT CALCULATION ---
        base_pixels = 1024 * 1024
        current_pixels = width * height
        
        pixel_ratio = current_pixels / base_pixels
        
        # Base Shift (3.0) + natural log of pixel ratio
        shift_opti = 3.0 + math.log(max(pixel_ratio, 1.0))
        shift_opti = round(shift_opti, 2)
        
        # --- GENERATE EMPTY SD3 LATENT TENSOR ---
        # SD3 uses 16 channels, compression factor of 8
        latent = torch.zeros([batch_size, 16, height // 8, width // 8])
            
        return (width, height, shift_opti, {"samples": latent})


NODE_CLASS_MAPPINGS = {
    "NovAResolutionSelector": NovAResolutionSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovAResolutionSelector": "NovA Resolution Selector"
}