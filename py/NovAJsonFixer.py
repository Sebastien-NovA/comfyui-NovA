import json
import os
from pathlib import Path
from PIL import Image, PngImagePlugin
from aiohttp import web

import folder_paths
from server import PromptServer


class NovAJsonFixer:
    """
    Custom node designed to repair corrupted or outdated ComfyUI JSON metadata 
    embedded in PNG files with automatic scope resolution and multi-input renaming support.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Fetch available PNG/WebP files from ComfyUI input directory
        input_dir = folder_paths.get_input_directory()
        files = [
            f for f in os.listdir(input_dir) 
            if os.path.isfile(os.path.join(input_dir, f)) and f.lower().endswith(('.png', '.webp'))
        ]

        return {
            "required": {
                "image": (
                    sorted(files), 
                    {
                        "image_upload": True,
                        "tooltip": "Select a PNG image file containing embedded ComfyUI workflow/prompt metadata."
                    }
                ),
                "output_suffix": (
                    "STRING",
                    {
                        "default": "_fixed",
                        "multiline": False,
                        "tooltip": "Suffix appended to the generated fixed PNG filename in the output directory."
                    }
                ),
            },
            "optional": {
                # Section 1: Class Type Renaming & Substitution
                "target_node_type": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Target class name as defined in NODE_CLASS_MAPPINGS (e.g., CLIPTextEncode). Leave empty to target all nodes."
                    }
                ),
                "target_node_id": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Target a specific numeric Node ID (e.g., '4'). Leave empty for all matching nodes."
                    }
                ),
                "old_class_type": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Deprecated or old node class name to replace."
                    }
                ),
                "new_class_type": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "New node class name replacing the deprecated class name."
                    }
                ),

                # Section 2: Input Parameter Renaming (Supports Comma-Separated Lists)
                "old_input_name": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Name or comma-separated list of obsolete inputs (e.g., input1, input2)."
                    }
                ),
                "new_input_name": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Name or comma-separated list of replacement inputs (e.g., new1, new2)."
                    }
                ),

                # Section 3: Widget Array Repair
                "widget_action": (
                    ["NONE", "REPLACE_INDEX", "INSERT_INDEX", "DELETE_INDEX", "CLEAR_ALL"],
                    {
                        "default": "NONE",
                        "tooltip": "Operation to perform on the widgets_values array."
                    }
                ),
                "widget_index": (
                    "INT", 
                    {
                        "default": -1, 
                        "min": -1, 
                        "max": 99,
                        "tooltip": "Target array index in widgets_values (0-based)."
                    }
                ),
                "new_widget_value": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Value to insert or replace at widget_index."
                    }
                ),

                # Section 4: Slot Index Re-mapping
                "slot_action": (
                    ["NONE", "REMAPPING"],
                    {
                        "default": "NONE",
                        "tooltip": "Enable re-mapping of connection slots (links)."
                    }
                ),
                "slot_type": (
                    ["INPUT", "OUTPUT"],
                    {
                        "default": "INPUT",
                        "tooltip": "Specify whether slot is INPUT or OUTPUT."
                    }
                ),
                "old_slot_index": (
                    "INT", 
                    {
                        "default": -1, 
                        "min": -1, 
                        "max": 99,
                        "tooltip": "Old slot index number that was displaced."
                    }
                ),
                "new_slot_index": (
                    "INT", 
                    {
                        "default": -1, 
                        "min": -1, 
                        "max": 99,
                        "tooltip": "New slot index number for the connection."
                    }
                ),

                # Section 5: Structure Mutation (Widget <-> Input Slot)
                "conversion_mode": (
                    ["NONE", "WIDGET_TO_INPUT", "INPUT_TO_WIDGET"],
                    {
                        "default": "NONE",
                        "tooltip": "Convert values between widget scalar array and named input slots."
                    }
                ),
                "mutation_key_name": (
                    "STRING", 
                    {
                        "default": "", 
                        "multiline": False,
                        "tooltip": "Key name of the input slot used in Widget <-> Input conversion."
                    }
                ),

                # Section 6: Missing Node Handling
                "missing_node_action": (
                    ["NONE", "BYPASS", "DELETE_NODE", "CONVERT_TO_PLACEHOLDER"],
                    {
                        "default": "NONE",
                        "tooltip": "Action to perform on missing or unresolvable nodes."
                    }
                ),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    OUTPUT_NODE = True
    FUNCTION = "repair_json"
    CATEGORY = "️☣️ NovA/Utils"

    def _process_repair(
        self, 
        image: str, 
        output_suffix: str = "_fixed",
        target_node_type: str = "",
        target_node_id: str = "",
        old_class_type: str = "",
        new_class_type: str = "",
        old_input_name: str = "",
        new_input_name: str = "",
        widget_action: str = "NONE",
        widget_index: int = -1,
        new_widget_value: str = "",
        slot_action: str = "NONE",
        slot_type: str = "INPUT",
        old_slot_index: int = -1,
        new_slot_index: int = -1,
        conversion_mode: str = "NONE",
        mutation_key_name: str = "",
        missing_node_action: str = "NONE",
        **kwargs
    ) -> str:
        # Resolve target image path safely to prevent Path Traversal vulnerabilities
        input_dir = Path(folder_paths.get_input_directory()).resolve()
        target_path = (input_dir / image).resolve()

        if not str(target_path).startswith(str(input_dir)):
            raise ValueError("Security violation: Path traversal attempt outside input directory.")

        if not target_path.is_file():
            raise FileNotFoundError(f"Target image not found at path: {target_path}")

        workflow_data = {}
        prompt_data = {}

        # Load metadata from PNG image headers
        with Image.open(target_path) as img:
            if "workflow" in img.info:
                workflow_data = json.loads(img.info["workflow"])
            if "prompt" in img.info:
                prompt_data = json.loads(img.info["prompt"])

        # Automatically determine modification scopes based on configured actions
        modify_workflow = False
        modify_prompt = False

        if old_class_type.strip() and new_class_type.strip():
            modify_workflow = True
            modify_prompt = True

        if old_input_name.strip() and new_input_name.strip():
            modify_workflow = True
            modify_prompt = True

        if widget_action != "NONE":
            modify_workflow = True

        if slot_action == "REMAPPING" and old_slot_index >= 0 and new_slot_index >= 0:
            modify_workflow = True

        if conversion_mode != "NONE" and mutation_key_name.strip():
            modify_workflow = True
            modify_prompt = True

        if missing_node_action != "NONE":
            modify_workflow = True
            if missing_node_action == "DELETE_NODE":
                modify_prompt = True

        # Default fallback: modify both if no specific operation triggers
        if not modify_workflow and not modify_prompt:
            modify_workflow = True
            modify_prompt = True

        # Helper function to check node targeting criteria
        def is_target_node(node_id_val, class_type_val):
            if target_node_id and target_node_id.strip() and str(node_id_val) != target_node_id.strip():
                return False
            if target_node_type and target_node_type.strip() and class_type_val != target_node_type.strip():
                return False
            return True

        # =====================================================================
        # SECTION 1: Class Type Renaming & Substitution
        # =====================================================================
        if old_class_type.strip() and new_class_type.strip():
            old_cls = old_class_type.strip()
            new_cls = new_class_type.strip()

            if modify_workflow and "nodes" in workflow_data:
                for node in workflow_data["nodes"]:
                    node_id = str(node.get("id"))
                    current_type = node.get("type")
                    if is_target_node(node_id, current_type) and current_type == old_cls:
                        node["type"] = new_cls

            if modify_prompt and isinstance(prompt_data, dict):
                for node_id, node_data in prompt_data.items():
                    current_type = node_data.get("class_type")
                    if is_target_node(node_id, current_type) and current_type == old_cls:
                        node_data["class_type"] = new_cls

        # =====================================================================
        # SECTION 2: Input Parameter Renaming (Multi-Input Support)
        # =====================================================================
        if old_input_name.strip() and new_input_name.strip():
            old_list = [x.strip() for x in old_input_name.split(",") if x.strip()]
            new_list = [x.strip() for x in new_input_name.split(",") if x.strip()]
            
            rename_map = dict(zip(old_list, new_list))

            if modify_workflow and "nodes" in workflow_data:
                for node in workflow_data["nodes"]:
                    node_id = str(node.get("id"))
                    current_type = node.get("type")
                    if is_target_node(node_id, current_type):
                        for inp in node.get("inputs", []):
                            if inp.get("name") in rename_map:
                                inp["name"] = rename_map[inp["name"]]

            if modify_prompt and isinstance(prompt_data, dict):
                for node_id, node_data in prompt_data.items():
                    current_type = node_data.get("class_type")
                    if is_target_node(node_id, current_type):
                        inputs = node_data.get("inputs", {})
                        for old_k, new_k in rename_map.items():
                            if old_k in inputs:
                                inputs[new_k] = inputs.pop(old_k)

        # =====================================================================
        # SECTION 3: Widget Array Repair
        # =====================================================================
        if widget_action != "NONE" and modify_workflow and "nodes" in workflow_data:
            for node in workflow_data["nodes"]:
                node_id = str(node.get("id"))
                current_type = node.get("type")
                if is_target_node(node_id, current_type):
                    widgets = node.setdefault("widgets_values", [])

                    if widget_action == "CLEAR_ALL":
                        node["widgets_values"] = []
                    elif widget_action == "REPLACE_INDEX" and 0 <= widget_index < len(widgets):
                        widgets[widget_index] = new_widget_value
                    elif widget_action == "INSERT_INDEX" and 0 <= widget_index <= len(widgets):
                        widgets.insert(widget_index, new_widget_value)
                    elif widget_action == "DELETE_INDEX" and 0 <= widget_index < len(widgets):
                        widgets.pop(widget_index)

        # =====================================================================
        # SECTION 4: Slot Index Re-mapping
        # =====================================================================
        if slot_action == "REMAPPING" and old_slot_index >= 0 and new_slot_index >= 0:
            if modify_workflow and "links" in workflow_data:
                for link in workflow_data["links"]:
                    if not link or len(link) < 5:
                        continue
                    
                    origin_id, origin_slot, target_id, target_slot = str(link[1]), link[2], str(link[3]), link[4]

                    if slot_type == "OUTPUT" and origin_slot == old_slot_index:
                        if is_target_node(origin_id, None):
                            link[2] = new_slot_index

                    elif slot_type == "INPUT" and target_slot == old_slot_index:
                        if is_target_node(target_id, None):
                            link[4] = new_slot_index

        # =====================================================================
        # SECTION 5: Structure Mutation (Widget <-> Input Slot)
        # =====================================================================
        if conversion_mode != "NONE" and mutation_key_name.strip():
            key_name = mutation_key_name.strip()

            if conversion_mode == "WIDGET_TO_INPUT":
                if modify_workflow and "nodes" in workflow_data:
                    for node in workflow_data["nodes"]:
                        node_id = str(node.get("id"))
                        current_type = node.get("type")
                        if is_target_node(node_id, current_type):
                            widgets = node.get("widgets_values", [])
                            if 0 <= widget_index < len(widgets):
                                widgets.pop(widget_index)
                                node.setdefault("inputs", []).append({"name": key_name, "type": "STRING", "link": None})

                if modify_prompt and isinstance(prompt_data, dict):
                    for node_id, node_data in prompt_data.items():
                        current_type = node_data.get("class_type")
                        if is_target_node(node_id, current_type):
                            inputs = node_data.setdefault("inputs", {})
                            inputs[key_name] = new_widget_value

            elif conversion_mode == "INPUT_TO_WIDGET":
                if modify_prompt and isinstance(prompt_data, dict):
                    for node_id, node_data in prompt_data.items():
                        current_type = node_data.get("class_type")
                        if is_target_node(node_id, current_type):
                            inputs = node_data.get("inputs", {})
                            if key_name in inputs:
                                extracted_val = inputs.pop(key_name)
                                if modify_workflow and "nodes" in workflow_data:
                                    for wf_node in workflow_data["nodes"]:
                                        if str(wf_node.get("id")) == str(node_id):
                                            wf_widgets = wf_node.setdefault("widgets_values", [])
                                            wf_widgets.append(str(extracted_val))

        # =====================================================================
        # SECTION 6: Missing Node Handling
        # =====================================================================
        if missing_node_action != "NONE":
            if missing_node_action == "BYPASS" and modify_workflow and "nodes" in workflow_data:
                for node in workflow_data["nodes"]:
                    node_id = str(node.get("id"))
                    current_type = node.get("type")
                    if is_target_node(node_id, current_type):
                        node["mode"] = 2  # Mode 2 represents Bypassed state in LiteGraph

            elif missing_node_action == "CONVERT_TO_PLACEHOLDER":
                if modify_workflow and "nodes" in workflow_data:
                    for node in workflow_data["nodes"]:
                        node_id = str(node.get("id"))
                        current_type = node.get("type")
                        if is_target_node(node_id, current_type):
                            node["type"] = "Note"
                            node["properties"] = node.get("properties", {})
                            node["properties"]["title"] = f"Placeholder ({current_type})"

            elif missing_node_action == "DELETE_NODE":
                if modify_workflow and "nodes" in workflow_data:
                    nodes_to_remove = [
                        node for node in workflow_data["nodes"]
                        if is_target_node(str(node.get("id")), node.get("type"))
                    ]
                    for n in nodes_to_remove:
                        workflow_data["nodes"].remove(n)

                if modify_prompt and isinstance(prompt_data, dict):
                    keys_to_remove = [
                        nid for nid, ndata in prompt_data.items()
                        if is_target_node(nid, ndata.get("class_type"))
                    ]
                    for k in keys_to_remove:
                        prompt_data.pop(k, None)

        # Convert structures back to JSON strings
        fixed_workflow_str = json.dumps(workflow_data, indent=2)
        fixed_prompt_str = json.dumps(prompt_data, indent=2)

        # =====================================================================
        # SECTION 7: Output Folder Path & Metadata Embedding
        # =====================================================================
        output_dir = Path(folder_paths.get_output_directory()).resolve()
        suffix = output_suffix.strip() if output_suffix else "_fixed"
        new_filename = f"{target_path.stem}{suffix}{target_path.suffix}"
        output_file_path = output_dir / new_filename

        with Image.open(target_path) as img:
            png_info = PngImagePlugin.PngInfo()
            
            for key, val in img.info.items():
                if key not in ["workflow", "prompt"]:
                    png_info.add_text(key, str(val))

            png_info.add_text("workflow", fixed_workflow_str)
            png_info.add_text("prompt", fixed_prompt_str)

            img.save(output_file_path, pnginfo=png_info)
            saved_file_path = str(output_file_path)

        return saved_file_path

    def repair_json(self, **kwargs):
        # Entry point for workflow execution graph
        self._process_repair(**kwargs)
        return ()


# Register server POST endpoint to handle frontend "Save Fixed Image" button click
@PromptServer.instance.routes.post("/nova/json_fixer/save")
async def save_fixed_image_endpoint(request):
    try:
        data = await request.json()
        fixer = NovAJsonFixer()
        saved_path = fixer._process_repair(**data)
        return web.json_response({"status": "success", "saved_path": saved_path})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)


# Node registration mapping for ComfyUI loader
NODE_CLASS_MAPPINGS = {
    "NovAJsonFixer": NovAJsonFixer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovAJsonFixer": "NovA JSON Metadata Fixer"
}