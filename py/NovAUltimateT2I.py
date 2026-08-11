# ComfyUI\custom_nodes\comfyui-NovA\py\NovAUltimateT2I.py

import folder_paths
import comfy.samplers
import comfy.utils
import comfy.sd
from nodes import UNETLoader, CLIPLoader, VAELoader, LoraLoader, CLIPTextEncode, EmptyLatentImage, KSampler, VAEDecode

# Advanced helper dictionary to dynamically validate incoming UI widgets
class ContainsAnyDict(dict):
    def __contains__(self, key):
        return True
    def __getitem__(self, key):
        # Maps the suffix of dynamic fields to their proper ComfyUI types
        if key.endswith("_active"):
            return ("BOOLEAN",)
        elif key.endswith("_name"):
            # SYSTEM FIX: Dynamically load and map the list of system LoRAs
            return (folder_paths.get_filename_list("loras"),)
        elif key.endswith("_strength_model") or key.endswith("_strength_clip"):
            return ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01})
        return ("*",)

class NovA_Ultimate_T2I:
    def __init__(self):
        # PHASE 1 CACHE: Pristine Base Models (Loaded directly from disk)
        self.cached_base_state = None
        self.cached_base_model = None
        self.cached_base_clip = None
        self.cached_base_vae = None

        # PHASE 2 CACHE: Patched Models (LoRAs, Enhancers applied to clones)
        self.cached_patched_model_state = None
        self.cached_patched_model = None
        self.cached_patched_clip = None

        # PHASE 3 CACHE: Conditioning (Encoded text using the patched CLIP)
        self.cached_conditioning_state = None
        self.cached_cond = None
        self.cached_uncond = None

    @classmethod
    def INPUT_TYPES(cls):
        # Alphabetically sort the samplers and schedulers lists to organize the UI dropdowns
        sorted_samplers = sorted(list(comfy.samplers.KSampler.SAMPLERS))
        sorted_schedulers = sorted(list(comfy.samplers.KSampler.SCHEDULERS))

        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "diffusion_model": (folder_paths.get_filename_list("diffusion_models"),),
                "clip_name": (folder_paths.get_filename_list("text_encoders"),),
                "vae_name": (folder_paths.get_filename_list("vae"),),
                "image_length": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "image_height": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "sampler_name": (sorted_samplers,),
                "scheduler": (sorted_schedulers,),
                "cfg": ("FLOAT", {"default": 1.00, "min": 0.0, "max": 100.0, "step": 0.1}),
                "steps": ("INT", {"default": 8, "min": 1, "max": 10000}),
                "seed": ("INT", {"default": 1984, "min": 0, "max": 0xffffffffffffffff}),
            },
            # Allow frontend to dynamically inject any arbitrary number of LoRA parameters
            "optional": ContainsAnyDict()
        }

    # ComfyUI node metadata and execution configuration
    RETURN_TYPES = ("IMAGE", "CONDITIONING", "MODEL", "VAE", "LATENT")
    RETURN_NAMES = ("image", "conditioning", "model", "vae", "latent")
    CATEGORY = "️☣️ NovA/AllInOne Node"
    FUNCTION = "generate"

    def generate(self, prompt, diffusion_model, clip_name, vae_name,
                 sampler_name, scheduler, cfg, steps, seed, image_length, image_height, **kwargs):

        # Extract base models representation state key
        base_state = (diffusion_model, clip_name, vae_name)
        
        # Parse, sort, and construct deterministic state representation for dynamic LoRAs
        lora_indices = []
        for k in kwargs.keys():
            if k.startswith("lora") and k.endswith("_name"):
                idx_str = k.replace("lora", "").replace("_name", "")
                if idx_str.isdigit():
                    lora_indices.append(int(idx_str))

        lora_indices.sort()

        lora_state_list = []
        for i in lora_indices:
            is_active = kwargs.get(f"lora{i}_active", True)
            lora_name = kwargs.get(f"lora{i}_name", "None")
            strength_model = kwargs.get(f"lora{i}_strength_model", 1.0)
            strength_clip = kwargs.get(f"lora{i}_strength_clip", 1.0)
            lora_state_list.append((i, is_active, lora_name, strength_model, strength_clip))
        
        lora_state = tuple(lora_state_list)
        
        model_name = diffusion_model.lower()
        is_krea = "krea2" in model_name or "krea2" in clip_name.lower()
        patch_state = (is_krea, image_length, image_height)

        # Build downstream composite states
        patched_model_state = (base_state, lora_state, patch_state)
        conditioning_state = (patched_model_state, prompt)

        # -------------------------------------------------------------
        # PHASE 1: Load Pristine Base Models (Reload only if inputs change)
        # -------------------------------------------------------------
        if self.cached_base_state != base_state:
            print("[NovA_Ultimate_T2I] Info: Base model inputs changed. Invoking model loaders.")
            
            unet_loader = UNETLoader()
            base_model = unet_loader.load_unet(diffusion_model, "default")[0]

            clip_type = "krea2" if is_krea else "default"
            clip_loader = CLIPLoader()
            base_clip = clip_loader.load_clip(clip_name, clip_type)[0]

            vae_loader = VAELoader()
            base_vae = vae_loader.load_vae(vae_name)[0]

            self.cached_base_model = base_model
            self.cached_base_clip = base_clip
            self.cached_base_vae = base_vae
            self.cached_base_state = base_state

            # Clear subsequent caches to force recalculation
            self.cached_patched_model_state = None
            self.cached_conditioning_state = None
        else:
            print("[NovA_Ultimate_T2I] Info: Base model configuration unchanged. Reusing cached base.")
            base_model = self.cached_base_model
            base_clip = self.cached_base_clip
            base_vae = self.cached_base_vae

        # -------------------------------------------------------------
        # PHASE 2: Apply LoRAs and Enhancers (Reload only on dynamic config changes)
        # -------------------------------------------------------------
        if self.cached_patched_model_state != patched_model_state:
            print("[NovA_Ultimate_T2I] Info: Patches or LoRAs changed. Re-applying modifications.")
            
            # Clone to keep base caches unmodified in memory
            working_model = base_model.clone()
            working_clip = base_clip.clone()

            # Apply dynamic LoRA list conditionally
            lora_loader = LoraLoader()
            for idx, is_active, lora_name, strength_model, strength_clip in lora_state:
                if not is_active:
                    continue
                if lora_name == "None" or not lora_name:
                    continue
                if strength_model == 0.0 and strength_clip == 0.0:
                    continue

                working_model, working_clip = lora_loader.load_lora(
                    working_model, working_clip, lora_name, strength_model, strength_clip
                )

            # Apply Krea2T Enhancer Patch
            if is_krea:
                try:
                    import importlib
                    enhancer_module = importlib.import_module("custom_nodes.ComfyUI-Krea2T-Enhancer")
                    node_mappings = getattr(enhancer_module, "NODE_CLASS_MAPPINGS", {})
                    Krea2TEnhancerClass = node_mappings.get("Krea2T-Enhancer-Advanced")
                    
                    if Krea2TEnhancerClass is not None:
                        enhancer_instance = Krea2TEnhancerClass()
                        func_name = getattr(Krea2TEnhancerClass, "FUNCTION", "patch")
                        enhance_func = getattr(enhancer_instance, func_name)
                        
                        print("[NovA_Ultimate_T2I] Info: Applying Krea2T-Enhancer-Advanced patch.")
                        working_model = enhance_func(model=working_model, enabled=True, strength=1.0, text_scale=1.5, debug=False)[0]
                    else:
                        print("[NovA_Ultimate_T2I] Warning: Krea2T-Enhancer-Advanced class missing.")
                except Exception as e:
                    print(f"[NovA_Ultimate_T2I] Warning: Failed to import/apply Krea2T Enhancer: {e}")

            self.cached_patched_model = working_model
            self.cached_patched_clip = working_clip
            self.cached_patched_model_state = patched_model_state

            # Reset downstream conditioning cache
            self.cached_conditioning_state = None
        else:
            print("[NovA_Ultimate_T2I] Info: LoRA/patch config unchanged. Reusing cached patched model.")
            working_model = self.cached_patched_model
            working_clip = self.cached_patched_clip

        # -------------------------------------------------------------
        # PHASE 3: Text Conditioning (Reload only if prompt or CLIP changed)
        # -------------------------------------------------------------
        if self.cached_conditioning_state != conditioning_state:
            print("[NovA_Ultimate_T2I] Info: Prompt or CLIP changed. Encoding prompts.")
            
            clip_encoder = CLIPTextEncode()
            cond = clip_encoder.encode(working_clip, prompt)[0]
            uncond = clip_encoder.encode(working_clip, "")[0]

            self.cached_cond = cond
            self.cached_uncond = uncond
            self.cached_conditioning_state = conditioning_state
        else:
            print("[NovA_Ultimate_T2I] Info: Prompts and CLIP unchanged. Reusing cached conditioning.")
            cond = self.cached_cond
            uncond = self.cached_uncond

        # -------------------------------------------------------------
        # PHASE 4: Latent Generation, Sampling, and VAE Decoding
        # -------------------------------------------------------------
        print("[NovA_Ultimate_T2I] Info: Executing sampler and decoding latent.")
        
        # Instantiate and build empty latent image
        latent_generator = EmptyLatentImage()
        latent = latent_generator.generate(image_length, image_height, batch_size=1)[0]

        # Run KSampler
        sampler = KSampler()
        sampled_latent = sampler.sample(
            working_model, seed, steps, cfg, sampler_name, scheduler, cond, uncond, latent, denoise=1.0
        )[0]

        # Decode using VAE
        decoder = VAEDecode()
        decoded_image = decoder.decode(base_vae, sampled_latent)[0]

        return (decoded_image, cond, working_model, base_vae, sampled_latent)

NODE_CLASS_MAPPINGS = {"NovAUltimateT2I": NovA_Ultimate_T2I}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAUltimateT2I": "NovA Ultimate T2i"}