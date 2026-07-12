import os
import folder_paths
import nodes
import comfy.model_management

class NovAModelsLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        # Dynamically fetch available model files from ComfyUI directories
        unet_models = folder_paths.get_filename_list("diffusion_models") or folder_paths.get_filename_list("unet")
        clip_models = folder_paths.get_filename_list("clip")
        vae_models = folder_paths.get_filename_list("vae")

        # Dynamically extract supported precision types (dtypes) from ComfyUI core
        # Fallback to standard list if internal structure differs
        supported_dtypes = ["default"]
        if hasattr(comfy.model_management, "str_to_dtype"):
            supported_dtypes.extend(list(comfy.model_management.str_to_dtype.keys()))
        else:
            supported_dtypes.extend(["fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"])

        # Dynamically extract clip type strategies from the native CLIPLoader
        clip_types = ["stable_diffusion"]
        if hasattr(nodes, "CLIPLoader") and hasattr(nodes.CLIPLoader, "INPUT_TYPES"):
            try:
                native_clip_inputs = nodes.CLIPLoader.INPUT_TYPES()
                if "required" in native_clip_inputs and "type" in native_clip_inputs["required"]:
                    # Extract the list of types from the native tuple definition
                    clip_types = native_clip_inputs["required"]["type"][0]
            except Exception:
                # Safe fallback matching major architectures
                clip_types = ["sd3", "flux2"]

        return {
            "required": {
                "unet_name": (sorted(unet_models),),
                "weight_dtype": (supported_dtypes, {"default": "default"}),
                "clip_name": (sorted(clip_models),),
                "clip_type": (sorted(list(clip_types)), {"default": "stable_diffusion"}),
                "vae_name": (sorted(vae_models),),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_all_models"
    CATEGORY = "NovA Tools"

    def load_all_models(self, unet_name, weight_dtype, clip_name, clip_type, vae_name):
        # Instantiate core ComfyUI loaders to reuse memory management and caching logic
        unet_loader = nodes.UNETLoader()
        clip_loader = nodes.CLIPLoader()
        vae_loader = nodes.VAELoader()

        # Execute native loading methods
        model = unet_loader.load_unet(unet_name, weight_dtype)[0]
        
        try:
            clip = clip_loader.load_clip(clip_name, type=clip_type)[0]
        except TypeError:
            # Fallback for older ComfyUI signatures where type isn't a named argument
            clip = clip_loader.load_clip(clip_name)[0]
            
        vae = vae_loader.load_vae(vae_name)[0]

        return (model, clip, vae)

# Registration mapping for ComfyUI backend
NODE_CLASS_MAPPINGS = {"NovAModelsLoader": NovAModelsLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAModelsLoader": "NovA Models Loader"}