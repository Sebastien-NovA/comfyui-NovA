import folder_paths
import comfy.samplers
from nodes import UNETLoader, CLIPLoader, VAELoader, LoraLoader, CLIPTextEncode, EmptyLatentImage, KSampler, VAEDecode

class NovA_Ultimate_T2I:
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
    CATEGORY = "NovA Tools"

    def generate(self, prompt, diffusion_model, clip_name, vae_name,
                 active_lora_1, lora_1, lora1_strength_model, lora1_strength_clip,
                 active_lora_2, lora_2, lora2_strength_model, lora2_strength_clip,
                 active_lora_3, lora_3, lora3_strength_model, lora3_strength_clip,
                 sampler_name, scheduler, cfg, steps, shift, seed, image_length, image_height):

        # 1. Load Base Models via standard ComfyUI loaders
        unet_loader = UNETLoader()
        model = unet_loader.load_unet(diffusion_model, "default")[0]

        # Détection du type pour Krea2 Turbo
        model_name = diffusion_model.lower()
        clip_type = "default"
        if "krea2" in model_name or "krea2" in clip_name.lower():
            clip_type = "krea2"

        clip_loader = CLIPLoader()
        # On passe le type détecté ('default' ou 'krea2') au chargeur de CLIP
        clip = clip_loader.load_clip(clip_name, clip_type)[0]

        vae_loader = VAELoader()
        vae = vae_loader.load_vae(vae_name)[0]

        # 2. Apply LoRAs conditionally
        lora_loader = LoraLoader()
        if active_lora_1:
            model, clip = lora_loader.load_lora(model, clip, lora_1, lora1_strength_model, lora1_strength_clip)
        if active_lora_2:
            model, clip = lora_loader.load_lora(model, clip, lora_2, lora2_strength_model, lora2_strength_clip)
        if active_lora_3:
            model, clip = lora_loader.load_lora(model, clip, lora_3, lora3_strength_model, lora3_strength_clip)
        
        # 2. Apply LoRAs conditionally
        lora_loader = LoraLoader()
        if active_lora_1:
            model, clip = lora_loader.load_lora(model, clip, lora_1, lora1_strength_model, lora1_strength_clip)
        if active_lora_2:
            model, clip = lora_loader.load_lora(model, clip, lora_2, lora2_strength_model, lora2_strength_clip)
        if active_lora_3:
            model, clip = lora_loader.load_lora(model, clip, lora_3, lora3_strength_model, lora3_strength_clip)

        # 2b. Inject Krea2T-Enhancer-Advanced conditionally (Bypass safely if not found)
        if "krea2" in model_name:
            try:
                import importlib
                # Safely dynamic-import the external enhancer package
                enhancer_module = importlib.import_module("custom_nodes.ComfyUI-Krea2T-Enhancer")
                
                # Retrieve class from official NODE_CLASS_MAPPINGS dictionary to avoid root namespace omission
                node_mappings = getattr(enhancer_module, "NODE_CLASS_MAPPINGS", {})
                Krea2TEnhancerClass = node_mappings.get("Krea2T-Enhancer-Advanced")
                
                if Krea2TEnhancerClass is not None:
                    enhancer_instance = Krea2TEnhancerClass()
                    
                    # Dynamically look up execution function target defined in the class
                    func_name = getattr(Krea2TEnhancerClass, "FUNCTION", "patch")
                    enhance_func = getattr(enhancer_instance, func_name)
                    
                    # Apply the enhancement patch onto the model execution pipeline
                    print("[NovA_Ultimate_T2I] Info: Applying Krea2T-Enhancer-Advanced patch.")
                    model = enhance_func(model=model, enabled=True, strength=1.0, text_scale=1.5, debug=False)[0]
                else:
                    print("[NovA_Ultimate_T2I] Warning: Krea2T-Enhancer-Advanced key missing in NODE_CLASS_MAPPINGS. Bypassing.")
            except ImportError:
                print("[NovA_Ultimate_T2I] Info: ComfyUI-Krea2T-Enhancer repository not found. Bypassing optimizer.")
            except Exception as e:
                print(f"[NovA_Ultimate_T2I] Error during Krea2T enhancement processing: {e}")

        # 3. Apply Shift (Model Patcher mapping for Turbo architectures)
        if shift != 0.0:
            import nodes
            # Convert model name to lowercase for reliable substring matching
            model_name = diffusion_model.lower()
            
            try:
                # Route to ModelSamplingFlux
                if "flux" in model_name and hasattr(nodes, 'ModelSamplingFlux'):
                    sampling_node = nodes.ModelSamplingFlux()
                    # Flux node requires resolution parameters to compute shift scaling natively
                    model = sampling_node.patch(model, max_shift=shift, base_shift=0.5, width=image_length, height=image_height)[0]
                
                # Route to ModelSamplingSD3
                elif "sd3" in model_name and hasattr(nodes, 'ModelSamplingSD3'):
                    sampling_node = nodes.ModelSamplingSD3()
                    model = sampling_node.patch(model, shift)[0]
                
                # Route to ModelSamplingAuraFlow (Z-Image Turbo)
                elif ("z-image" in model_name or "aura" in model_name) and hasattr(nodes, 'ModelSamplingAuraFlow'):
                    sampling_node = nodes.ModelSamplingAuraFlow()
                    model = sampling_node.patch(model, shift)[0]
                
                # Fallback for unsupported models (e.g., Krea2 Turbo, SDXL)
                else:
                    print(f"[NovA_Ultimate_T2I] Info: No native shift patching required or supported for '{diffusion_model}'. Bypassing.")
            
            except Exception as e:
                print(f"[NovA_Ultimate_T2I] Warning: Shift patching failed. Error: {e}")

        # 4. Text Encoding
        text_encoder = CLIPTextEncode()
        cond = text_encoder.encode(clip, prompt)[0]
        uncond = text_encoder.encode(clip, "")[0] # Empty negative prompt optimized for Turbo

        # 5. Generate Empty Latent
        latent_node = EmptyLatentImage()
        latent = latent_node.generate(image_length, image_height, 1)[0]

        # 6. Sampling
        ksampler = KSampler()
        samples = ksampler.sample(model, seed, steps, cfg, sampler_name, scheduler, cond, uncond, latent, denoise=1.0)[0]

        # 7. VAE Decoding
        vae_decoder = VAEDecode()
        image = vae_decoder.decode(vae, samples)[0]

        return (image, cond, model, vae, samples)
    
NODE_CLASS_MAPPINGS = {"NovAUltimateT2I": NovA_Ultimate_T2I}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAUltimateT2I": "NovA Ultimate Text to Image"}
