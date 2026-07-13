class NovAText:
    @classmethod
    def INPUT_TYPES(cls):
        # Define base inputs
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
            }
        }
    
    # ComfyUI node metadata and execution configuration
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "novaPrompt"
    CATEGORY = "️☣️ NovA Tools"

    def novaPrompt(self, text):        
        # Return prompt as text
        return (text,)

# ComfyUI registry mappings for explicit dynamic discovery by the __init__.py
NODE_CLASS_MAPPINGS = {"NovAText": NovAText}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAText": "NovA Text"}
