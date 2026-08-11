# ComfyUI\custom_nodes\comfyui-NovA\py\NovASaveImage.py

class NovASaveImage:
    """
    Custom node to configure a dynamic hotkey shortcut and prefix for saving image previews.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Hotkey text input field
                "save_image_key": ("STRING", {
                    "default": "0",
                    "multiline": False
                }),
                # Optional prefix field
                "add_prefix": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "images": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "process_save_image"
    CATEGORY = "️☣️ NovA/Utils"
    OUTPUT_NODE = True

    def process_save_image(self, save_image_key, add_prefix="", images=None):
        return (images,)


NODE_CLASS_MAPPINGS = {"NovASaveImage": NovASaveImage}
NODE_DISPLAY_NAME_MAPPINGS = {"NovASaveImage": "NovA Save Image Manager"}