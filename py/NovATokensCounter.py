import re

class NovATokensCounter:
    """
    Custom node that calculates word count and exact CLIP token count 
    from an incoming prompt using the active CLIP tokenizer.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Receives incoming text/prompt from any connected output
                "prompt": ("*",),
                # Receives model CLIP instance for accurate tokenization
                "clip": ("CLIP",),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "count_tokens"
    OUTPUT_NODE = True
    CATEGORY = "️☣️ NovA/Utils"

    def count_tokens(self, prompt, clip):
        # Convert incoming input payload to standard string
        text = str(prompt) if prompt is not None else ""

        # Calculate word count via regex
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)

        # Calculate exact token count using the provided CLIP model tokenizer
        if text.strip() and clip is not None:
            tokens = clip.tokenize(text)
            # Flatten token tensors/lists returned by CLIP tokenizer
            token_count = sum(len(t) for sublist in tokens.values() for t in sublist)
        else:
            token_count = 0

        # Construct raw payload output for front-end rendering
        display_payload = f"Words Count: {word_count}\nTokens Count: {token_count}"

        return {"ui": {"text": [display_payload]}}


# Register class mappings
NODE_CLASS_MAPPINGS = {"NovATokensCounter": NovATokensCounter}
NODE_DISPLAY_NAME_MAPPINGS = {"NovATokensCounter": "NovA Tokens Counter"}