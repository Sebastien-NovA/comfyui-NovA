import os
import json
import sys
import subprocess
from aiohttp import web
import folder_paths
from server import PromptServer

class NovAUnusedModelsManager:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Toggle option to include or exclude standard model directories
                "include_models": ("BOOLEAN", {"default": True, "label_on": "Scan Models", "label_off": "Off"}),
                # Toggle option to include or exclude LoRAs directory
                "include_loras": ("BOOLEAN", {"default": False, "label_on": "Scan LoRAs", "label_off": "Off"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("unused_models_text",)
    CATEGORY = "️☣️ NovA/Utils"
    FUNCTION = "scan_unused_models"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, include_models, include_loras):
        # Force re-execution when any toggle state changes
        return (include_models, include_loras)

    def scan_unused_models(self, include_models, include_loras):
        # Early exit if both scanning options are disabled
        if not include_models and not include_loras:
            print("[NovA Models Manager] Scan skipped (both toggles are set to Off).")
            text_output = "Scan is turned OFF. Select 'include_models' and/or 'include_loras' to run."
            return {"ui": {"text": [text_output]}, "result": (text_output,)}

        print("[NovA Models Manager] Executing unused models scan...")

        workflows_dir = os.path.join(folder_paths.base_path, "user", "default", "workflows")
        used_model_names = set()

        # Parse JSON workflows to extract active model references
        if os.path.exists(workflows_dir):
            for root, _, files in os.walk(workflows_dir):
                for file in files:
                    if file.endswith(".json"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                self._extract_strings(data, used_model_names)
                        except Exception as e:
                            print(f"[NovA Models Manager] Error reading workflow {filepath}: {e}")

        # Build categories dictionary dynamically based on active toggle switches
        categories = {}

        if include_models:
            categories.update({
                "background_removal": "Background Removal",
                "checkpoints": "Checkpoints",
                "clip": "CLIP Model",
                "clip_vision": "CLIP Vision",
                "controlnet": "Controlnet",
                "diffusion_models": "Diffusion Model",
                "ipadapter": "IPAdapter",
                "latent_upscale_models": "Latent Upscale Models",
                "model_patches": "Model Patches",
                "text_encoders": "Text Encoders",
                "unet": "Unet Model",
                "upscale_models": "Upscale Models",
                "vae": "VAE Model"
            })

        if include_loras:
            categories["loras"] = "LoRA Model"

        result_lines = []
        scanned_paths = set()

        for folder_name, display_name in categories.items():
            models = folder_paths.get_filename_list(folder_name)
            unused_models = []

            for model in models:
                full_path = folder_paths.get_full_path(folder_name, model)
                if full_path and os.path.exists(full_path):
                    abs_path = os.path.abspath(full_path)
                    
                    if abs_path in scanned_paths:
                        continue
                        
                    if model not in used_model_names:
                        scanned_paths.add(abs_path)
                        size_bytes = os.path.getsize(abs_path)
                        size_str = self._format_size(size_bytes)
                        unused_models.append(f"  - {model} ({size_str})")

            if unused_models:
                result_lines.append(f"Unused [{display_name}]({folder_name}) ({len(unused_models)}):")
                result_lines.extend(unused_models)
                result_lines.append("")

        final_text = "\n".join(result_lines).strip()
        if not final_text:
            final_text = "No unused models found. All selected categories are actively used."

        return {"ui": {"text": [final_text]}, "result": (final_text,)}

    def _extract_strings(self, obj, string_set):
        """Recursively scan JSON data while ignoring payload from NovAModelsManager nodes."""
        if isinstance(obj, dict):
            # Ignore nodes of type NovAModelsManager or NovAUnusedModelsManager to prevent self-referencing false negatives
            if obj.get("type") in ("NovAModelsManager", "NovAUnusedModelsManager") or \
               obj.get("class_type") in ("NovAModelsManager", "NovAUnusedModelsManager"):
                return
            for val in obj.values():
                self._extract_strings(val, string_set)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_strings(item, string_set)
        elif isinstance(obj, str):
            string_set.add(obj)

    def _format_size(self, size_bytes):
        """Format file size into human-readable unit string."""
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024.0
            i += 1
            
        if size_name[i] == "GB":
            return f"{size_bytes:.1f} {size_name[i]}"
        return f"{int(size_bytes)} {size_name[i]}"


# Secure API endpoint for opening folder in native system file explorer
@PromptServer.instance.routes.post("/nova/open_folder")
async def open_folder_endpoint(request):
    try:
        data = await request.json()
        folder_name = data.get("folder_name")

        if not folder_name:
            return web.json_response({"status": "error", "message": "Missing folder_name"}, status=400)

        paths = folder_paths.get_folder_paths(folder_name)
        if not paths:
            return web.json_response({"status": "error", "message": "Folder category not found"}, status=404)

        target_dir = os.path.abspath(paths[0])
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        if sys.platform == "win32":
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target_dir])
        else:
            subprocess.Popen(["xdg-open", target_dir])

        return web.json_response({"status": "success"})

    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


NODE_CLASS_MAPPINGS = {"NovAUnusedModelsManager": NovAUnusedModelsManager}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAUnusedModelsManager": "NovA Unused Models Manager"}
