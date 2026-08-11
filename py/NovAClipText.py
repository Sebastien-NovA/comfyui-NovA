import nodes

class NovAClipText:
    
    @classmethod
    def INPUT_TYPES(cls):
        # Define base inputs
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
                "clip": ("CLIP", ),
            }
        }
    
    # ComfyUI node metadata and execution configuration
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING")
    RETURN_NAMES = ("CONDITIONING", "CONDITIONING ZERO", "PROMPT")
    CATEGORY = "️☣️ NovA/Text"
    FUNCTION = "encode"

    def encode(self, clip, text):
        # Encoding using ComfyUI core functionality
        conditioning = nodes.CLIPTextEncode().encode(clip, text)[0]
        
        # Generate zeroed conditioning natively using ComfyUI core functionality
        conditioning_zero = nodes.ConditioningZeroOut().zero_out(conditioning)[0]
        
        # Return conditioning, zeroed conditioning, and prompt as text
        return (conditioning, conditioning_zero, text)

# ComfyUI registry mappings for explicit dynamic discovery by the __init__.py
NODE_CLASS_MAPPINGS = {"NovAClipText": NovAClipText}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAClipText": "NovA CLIP Text Encoder"}
