import json

class NovAShowAny:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # Accept any data type
                "input_any": ("*",),
            },
            "optional": {
                # Declared natively to let ComfyUI 2.0 render the multiline textbox correctly.
                # dynamicPrompts is set to False to avoid pattern substitution errors on JSON strings.
                "text_display": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("TEXT",)
    FUNCTION = "show_any"
    CATEGORY = "️☣️ NovA Tools"
    OUTPUT_NODE = True

    def show_any(self, input_any, text_display="", unique_id=None):
        # Convert dictionaries and lists into neat indented JSON
        if isinstance(input_any, (dict, list)):
            try:
                text_out = json.dumps(input_any, indent=2, ensure_ascii=False)
            except Exception:
                text_out = str(input_any)
        else:
            text_out = str(input_any)

        # Return UI update payload and execute flow outputs
        return {"ui": {"text": [text_out]}, "result": (text_out,)}

# ComfyUI registry mappings for explicit dynamic discovery by the __init__.py
NODE_CLASS_MAPPINGS = {"NovAShowAny": NovAShowAny}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAShowAny": "NovA Show Any"}