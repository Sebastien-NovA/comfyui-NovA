import torch


class NovASwitchImage:
    """A ComfyUI custom node that swaps image inputs to outputs based on a boolean switch."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                # Boolean switch to toggle the connection mapping (disabled by default)
                "Swap_Image": ("BOOLEAN", {"default": False, "label_on": "Enabled", "label_off": "Disabled"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("IMAGE1", "IMAGE2")
    CATEGORY = "️☣️ NovA/Utils"
    FUNCTION = "switch_images"

    def switch_images(self, image1: torch.Tensor, image2: torch.Tensor, Swap_Image: bool = False):

        # Input validation to enforce tensor structure integrity
        if not isinstance(image1, torch.Tensor) or not isinstance(image2, torch.Tensor):
            raise TypeError("Inputs 'image1' and 'image2' must be torch.Tensor instances.")

        if Swap_Image:
            # Active state: Swap input routing to outputs
            return (image2, image1)
        
        # Default state: Standard input routing to outputs
        return (image1, image2)


# Mapping node classes for dynamic discovery by ComfyUI
NODE_CLASS_MAPPINGS = {
    "NovASwitchImage": NovASwitchImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovASwitchImage": "NovA Switch Images"
}