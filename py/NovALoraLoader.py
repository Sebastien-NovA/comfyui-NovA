import folder_paths
import comfy.utils
import comfy.sd

# Dynamic dictionary mapping input types requested by the UI
class ContainsAnyDict(dict):
    def __contains__(self, key):
        return True
    def __getitem__(self, key):
        # Dynamically evaluate expected input types based on variable name
        if key.endswith("_active"):
            return ("BOOLEAN",)
        elif key.endswith("_name"):
            return ("COMBO",)
        elif key.endswith("_strength_model") or key.endswith("_strength_clip"):
            return ("FLOAT",)
        return ("*",)

class NovALoraLoader:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                # Primary default LoRA group
                "lora1_active": ("BOOLEAN", {"default": True}),
                "lora1_name": (folder_paths.get_filename_list("loras"),),
                "lora1_strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                "lora1_strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
            },
            # Handles dynamic inputs (lora2, lora3...) generated via JavaScript
            "optional": ContainsAnyDict()
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    CATEGORY = "️☣️ NovA/AllInOne Node"
    FUNCTION = "nova_load_lora"

    def nova_load_lora(self, model, clip, **kwargs):
        # Extract and sort all dynamic LoRA indices from keyword arguments
        lora_indices = []
        for k in kwargs.keys():
            if k.startswith("lora") and k.endswith("_name"):
                idx_str = k.replace("lora", "").replace("_name", "")
                if idx_str.isdigit():
                    lora_indices.append(int(idx_str))

        lora_indices.sort()

        current_model = model
        current_clip = clip

        # Iterate over sorted indices and chain active LoRAs sequentially
        for i in lora_indices:
            is_active = kwargs.get(f"lora{i}_active", True)
            if not is_active:
                continue

            lora_name = kwargs.get(f"lora{i}_name")
            if lora_name == "None" or not lora_name:
                continue

            strength_model = kwargs.get(f"lora{i}_strength_model", 1.0)
            strength_clip = kwargs.get(f"lora{i}_strength_clip", 1.0)

            # Skip execution if both strength values are set to zero
            if strength_model == 0.0 and strength_clip == 0.0:
                continue

            # Load weights and apply LoRA onto Model and CLIP
            lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)

            current_model, current_clip = comfy.sd.load_lora_for_models(
                current_model, current_clip, lora, strength_model, strength_clip
            )

        return (current_model, current_clip)

NODE_CLASS_MAPPINGS = {"NovALoraLoader": NovALoraLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"NovALoraLoader": "NovA LoRAs Loader"}