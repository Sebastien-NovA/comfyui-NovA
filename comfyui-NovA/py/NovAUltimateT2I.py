# ComfyUI\custom_nodes\comfyui-NovA\py\NovAUltimateT2I.py

import folder_paths
import comfy.samplers
from nodes import UNETLoader, CLIPLoader, VAELoader, LoraLoader, CLIPTextEncode, EmptyLatentImage, KSampler, VAEDecode

class NovA_Ultimate_T2I:
    def __init__(self):
        # PHASE 1 CACHE: Pristine Base Models (Loaded directly from disk/core cache)
        self.cached_base_state = None
        self.cached_base_model = None
        self.cached_base_clip = None
        self.cached_base_vae = None

        # PHASE 2 CACHE: Patched Models (LoRAs, Enhancers, Shifts applied to clones)
        self.cached_patched_model_state = None
        self.cached_patched_model = None
        self.cached_patched_clip = None

        # PHASE 3 CACHE: Conditioning (Encoded text using the patched CLIP)
        self.cached_conditioning_state = None
        self.cached_cond = None
        self.cached_uncond = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "diffusion_model": (folder_paths.get_filename_list("diffusion_models"),),
                "clip_name": (folder_paths.get_filename_list("text_encoders"),),
                "vae_name": (folder_paths.get_filename_list("vae"),),
                "active_lora_1": ("BOOLEAN", {"default": False}),
                "lora_1": (folder_paths.get_filename_list("loras"),),
                "lora1_strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora1_strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "active_lora_2": ("BOOLEAN", {"default": False}),
                "lora_2": (folder_paths.get_filename_list("loras"),),
                "lora2_strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora2_strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "active_lora_3": ("BOOLEAN", {"default": False}),
                "lora_3": (folder_paths.get_filename_list("loras"),),
                "lora3_strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "lora3_strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "cfg": ("FLOAT", {"default": 1.00, "min": 0.0, "max": 100.0, "step": 0.1}),
                "steps": ("INT", {"default": 8, "min": 1, "max": 10000}),
                "shift": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "seed": ("INT", {"default": 1984, "min": 0, "max": 0xffffffffffffffff}),
                "image_length": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "image_height": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
            }
        }

    RETURN_TYPES = ("IMAGE", "CONDITIONING", "MODEL", "VAE", "LATENT")
    RETURN_NAMES = ("image", "conditioning", "model", "vae", "latent")
    FUNCTION = "generate"
    CATEGORY = "️☣️ NovA Tools"

    def generate(self, prompt, diffusion_model, clip_name, vae_name,
                 active_lora_1, lora_1, lora1_strength_model, lora1_strength_clip,
                 active_lora_2, lora_2, lora2_strength_model, lora2_strength_clip,
                 active_lora_3, lora_3, lora3_strength_model, lora3_strength_clip,
                 sampler_name, scheduler, cfg, steps, shift, seed, image_length, image_height):

        # Extract independent state keys for granular cache-matching
        base_state = (diffusion_model, clip_name, vae_name)
        
        lora_state = (
            active_lora_1, lora_1, lora1_strength_model, lora1_strength_clip,
            active_lora_2, lora_2, lora2_strength_model, lora2_strength_clip,
            active_lora_3, lora_3, lora3_strength_model, lora3_strength_clip
        )
        
        model_name = diffusion_model.lower()
        is_krea = "krea2" in model_name or "krea2" in clip_name.lower()
        patch_state = (shift, is_krea, image_length, image_height)

        # Compound state definitions
        patched_model_state = (base_state, lora_state, patch_state)
        conditioning_state = (patched_model_state, prompt)

        # -------------------------------------------------------------
        # PHASE 1: Load Pristine Base Models (Only run if loaders change)
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

            # Cache the clean base wrappers
            self.cached_base_model = base_model
            self.cached_base_clip = base_clip
            self.cached_base_vae = base_vae
            self.cached_base_state = base_state

            # Force re-evaluation of downstream dependent states
            self.cached_patched_model_state = None
            self.cached_conditioning_state = None
        else:
            print("[NovA_Ultimate_T2I] Info: Base model configuration unchanged. Reusing cached base.")
            base_model = self.cached_base_model
            base_clip = self.cached_base_clip
            base_vae = self.cached_base_vae

        # -------------------------------------------------------------
        # PHASE 2: Apply LoRAs and Enhancers (Only run if LoRAs/patches change)
        # -------------------------------------------------------------
        if self.cached_patched_model_state != patched_model_state:
            print("[NovA_Ultimate_T2I] Info: Patches or LoRAs changed. Re-applying modifications.")
            
            # SAFE DESIGN: Clone the pristine bases so we do not mutate cached structures in memory
            working_model = base_model.clone()
            working_clip = base_clip.clone()

            # Apply LoRAs conditionally
            lora_loader = LoraLoader()
            if active_lora_1:
                working_model, working_clip = lora_loader.load_lora(working_model, working_clip, lora_1, lora1_strength_model, lora1_strength_clip)
            if active_lora_2:
                working_model, working_clip = lora_loader.load_lora(working_model, working_clip, lora_2, lora2_strength_model, lora2_strength_clip)
            if active_lora_3:
                working_model, working_clip = lora_loader.load_lora(working_model, working_clip, lora_3, lora3_strength_model, lora3_strength_clip)

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
                        print("[NovA_Ultimate_T2I] Warning: Krea2T-Enhancer-Advanced class missing. Bypassing.")
                except ImportError:
                    print("[NovA_Ultimate_T2I] Info: ComfyUI-Krea2T-Enhancer not found. Bypassing optimizer.")
                except Exception as e:
                    print(f"[NovA_Ultimate_T2I] Error during Krea2T enhancement processing: {e}")

            # Apply Shift Mapping
            if shift != 0.0:
                import nodes
                try:
                    if "flux" in model_name and hasattr(nodes, 'ModelSamplingFlux'):
                        sampling_node = nodes.ModelSamplingFlux()
                        working_model = sampling_node.patch(working_model, max_shift=shift, base_shift=0.5, width=image_length, height=image_height)[0]
                    elif "sd3" in model_name and hasattr(nodes, 'ModelSamplingSD3'):
                        sampling_node = nodes.ModelSamplingSD3()
                        working_model = sampling_node.patch(working_model, shift)[0]
                    elif ("z-image" in model_name or "aura" in model_name) and hasattr(nodes, 'ModelSamplingAuraFlow'):
                        sampling_node = nodes.ModelSamplingAuraFlow()
                        working_model = sampling_node.patch(working_model, shift)[0]
                    else:
                        print(f"[NovA_Ultimate_T2I] Info: No native shift patching required or supported for '{diffusion_model}'. Bypassing.")
                except Exception as e:
                    print(f"[NovA_Ultimate_T2I] Warning: Shift patching failed. Error: {e}")

            # Cache the modified/patched results
            self.cached_patched_model = working_model
            self.cached_patched_clip = working_clip
            self.cached_patched_model_state = patched_model_state

            # Force re-evaluation of downstream dependent states
            self.cached_conditioning_state = None
        else:
            print("[NovA_Ultimate_T2I] Info: Patches and LoRAs unchanged. Utilizing cached patched models.")
            working_model = self.cached_patched_model
            working_clip = self.cached_patched_clip

        # -------------------------------------------------------------
        # PHASE 3: Text Encoding (Only run if prompt or patched clip changes)
        # -------------------------------------------------------------
        if self.cached_conditioning_state != conditioning_state:
            print("[NovA_Ultimate_T2I] Info: Prompt or CLIP changed. Encoding text.")
            text_encoder = CLIPTextEncode()
            cond = text_encoder.encode(working_clip, prompt)[0]
            uncond = text_encoder.encode(working_clip, "")[0]
            
            # Cache the conditional targets
            self.cached_cond = cond
            self.cached_uncond = uncond
            self.cached_conditioning_state = conditioning_state
        else:
            print("[NovA_Ultimate_T2I] Info: Prompt and CLIP unchanged. Utilizing cached conditioning.")
            cond = self.cached_cond
            uncond = self.cached_uncond

        # -------------------------------------------------------------
        # PHASE 4: Processing Pipelines (Run continuously)
        # -------------------------------------------------------------
        latent_node = EmptyLatentImage()
        latent = latent_node.generate(image_length, image_height, 1)[0]

        ksampler = KSampler()
        samples = ksampler.sample(working_model, seed, steps, cfg, sampler_name, scheduler, cond, uncond, latent, denoise=1.0)[0]

        vae_decoder = VAEDecode()
        image = vae_decoder.decode(base_vae, samples)[0]

        return (image, cond, working_model, base_vae, samples)

NODE_CLASS_MAPPINGS = {"NovAUltimateT2I": NovA_Ultimate_T2I}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAUltimateT2I": "NovA Ultimate Text to Image"}