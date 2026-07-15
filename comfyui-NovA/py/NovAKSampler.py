import math
import torch
import nodes

class NovAKSampler:
    # Supported aspect ratios and their mathematical multipliers (width / height)
    RATIOS = {
        "Landscape – 16:9": 16 / 9,
        "Portrait – 9:16": 9 / 16,
        "Square – 1:1": 1.0,
        "Portrait – 2:3": 2 / 3,
        "Landscape – 3:2": 3 / 2,
    }

    # Dynamically generate multiples of 64 between 4096 and 512
    LENGTHS = [str(x) for x in range(4096, 511, -64)]

    @classmethod
    def INPUT_TYPES(s):
        # Fetch standard inputs from the core KSampler node
        base_inputs = nodes.KSampler.INPUT_TYPES()
        base_required = base_inputs["required"]
        
        # Explicitly delete the latent_image input from the base dictionary
        if "latent_image" in base_required:
            del base_required["latent_image"]
        
        # Reconstruct the dictionary to set the precise slot order and override defaults
        ordered_required = {}
        for key, value in base_required.items():
            # Apply user-requested default overrides for core sampling parameters
            if key == "seed" and isinstance(value, tuple):
                config = value[1].copy() if len(value) > 1 else {}
                config["default"] = 1984
                ordered_required[key] = (value[0], config)
            elif key == "steps" and isinstance(value, tuple):
                config = value[1].copy() if len(value) > 1 else {}
                config["default"] = 8
                ordered_required[key] = (value[0], config)
            elif key == "cfg" and isinstance(value, tuple):
                config = value[1].copy() if len(value) > 1 else {}
                config["default"] = 1.0
                ordered_required[key] = (value[0], config)
            else:
                ordered_required[key] = value

            # Inject the VAE input immediately after the model input
            if key == "model":
                ordered_required["vae"] = ("VAE",)
        
        # Append the custom resolution configuration inputs after denoise
        ordered_required["format"] = (["Custom Format"] + list(s.RATIOS.keys()), {"default": "Landscape – 16:9"})
        ordered_required["greatest_length"] = (s.LENGTHS, {"default": "1024"})
        ordered_required["custom_width"] = ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8})
        ordered_required["custom_height"] = ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8})
        ordered_required["batch_size"] = ("INT", {"default": 1, "min": 1, "max": 4096})
        
        return {
            "required": ordered_required,
            "optional": base_inputs.get("optional", {})
        }

    # Outputs for chaining nodes
    RETURN_TYPES = ("LATENT", "MODEL", "IMAGE")
    RETURN_NAMES = ("LATENT", "MODEL", "IMAGE")
    FUNCTION = "sample_and_decode"
    CATEGORY = "️☣️ NovA Tools"

    def sample_and_decode(self, model, vae, seed, steps, cfg, sampler_name, scheduler, positive, negative, denoise, format, greatest_length, custom_width, custom_height, batch_size):
        # 1. Calculate resolution based on selected format or custom values
        if format == "Custom Format":
            width = custom_width
            height = custom_height
        else:
            max_len = int(greatest_length)
            ratio = self.RATIOS[format]
            
            if ratio == 1.0:
                width = max_len
                height = max_len
            elif ratio > 1.0:
                width = max_len
                height = int(round((max_len / ratio) / 64) * 64)
            else:
                height = max_len
                width = int(round((max_len * ratio) / 64) * 64)
        
        # 2. Generate the internal 16-channel SD3 empty latent tensor (compression factor of 8)
        latent_tensor = torch.zeros([batch_size, 16, height // 8, width // 8])
        latent_image = {"samples": latent_tensor}

        # 3. Instantiate the core KSampler and execute latent generation
        ksampler = nodes.KSampler()
        latent_output = ksampler.sample(
            model=model, 
            seed=seed, 
            steps=steps, 
            cfg=cfg, 
            sampler_name=sampler_name, 
            scheduler=scheduler, 
            positive=positive, 
            negative=negative, 
            latent_image=latent_image, 
            denoise=denoise
        )[0]

        # 4. Instantiate the core VAEDecode node and decode the latent data into pixel space
        vae_decode = nodes.VAEDecode()
        image_output = vae_decode.decode(vae=vae, samples=latent_output)[0]

        # 5. Return the latent data, the original model reference for chaining, and decoded images
        return (latent_output, model, image_output)

# ComfyUI registry mappings for explicit dynamic discovery by the __init__.py
NODE_CLASS_MAPPINGS = {"NovAKSampler": NovAKSampler}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAKSampler": "NovA KSampler (with VAE)"}
