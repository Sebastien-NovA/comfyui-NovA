import os
import sys
import json
import nodes
import folder_paths

class NovAUnusedNodesManager:
    """
    Custom node that scans registered custom nodes and compares them against
    saved JSON workflows to detect unused custom nodes grouped by package folder.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Primary toggle to execute or skip scanning
                "scan_trigger": ("BOOLEAN", {"default": True, "label_on": "Scan Now", "label_off": "Off"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("unused_nodes_text",)
    CATEGORY = "️☣️ NovA/Utils"
    FUNCTION = "scan_unused_nodes"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, scan_trigger):
        # Trigger execution when toggle state changes
        return (scan_trigger,)

    def scan_unused_nodes(self, scan_trigger):
        if not scan_trigger:
            print("[NovA Tools] Scan skipped (scan_trigger is set to Off).")
            text_output = "Scan is turned OFF. Set 'scan_trigger' to 'Scan Now' to run."
            return {"ui": {"text": [text_output]}, "result": (text_output,)}

        print("[NovA Tools] Executing unused custom nodes scan...")

        # Locate saved workflow JSON files
        workflows_dir = os.path.join(folder_paths.base_path, "user", "default", "workflows")
        used_node_types = set()

        # Parse JSON workflows to extract active node types
        if os.path.exists(workflows_dir):
            for root, _, files in os.walk(workflows_dir):
                for file in files:
                    if file.endswith(".json"):
                        filepath = os.path.abspath(os.path.join(root, file))
                        # Prevent directory traversal vulnerability
                        if not filepath.startswith(os.path.abspath(workflows_dir)):
                            continue
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                self._extract_node_types(data, used_node_types)
                        except Exception as e:
                            print(f"[NovA Tools] Error reading workflow {filepath}: {e}")

        # Map registered node class mappings to their parent custom_nodes package folder
        custom_nodes_base = os.path.abspath(os.path.join(folder_paths.base_path, "custom_nodes"))
        folder_to_nodes = {}

        for node_type, node_cls in nodes.NODE_CLASS_MAPPINGS.items():
            if node_type in ("NovAUnusedNodesManager", "NovAModelsManager"):
                continue

            module_name = getattr(node_cls, "__module__", None)
            if not module_name or module_name not in sys.modules:
                continue

            mod = sys.modules[module_name]
            file_path = getattr(mod, "__file__", None)
            if not file_path:
                continue

            abs_file_path = os.path.abspath(file_path)

            # Filter node classes originating from custom_nodes directory
            if abs_file_path.startswith(custom_nodes_base):
                rel_path = os.path.relpath(abs_file_path, custom_nodes_base)
                path_parts = rel_path.split(os.sep)
                if path_parts:
                    folder_name = path_parts[0]
                    if folder_name not in folder_to_nodes:
                        folder_to_nodes[folder_name] = []
                    folder_to_nodes[folder_name].append(node_type)

        # Build output text structure showing unused vs total node counts per directory
        result_lines = []
        for folder_name in sorted(folder_to_nodes.keys()):
            all_nodes = folder_to_nodes[folder_name]
            total_count = len(all_nodes)
            unused = [nt for nt in all_nodes if nt not in used_node_types]

            if unused:
                result_lines.append(f"{folder_name} ({len(unused)} unused / {total_count} total):")
                for node_name in sorted(unused):
                    result_lines.append(f"- {node_name}")
                result_lines.append("")

        final_text = "\n".join(result_lines).strip()
        if not final_text:
            final_text = "No unused custom nodes found. All custom nodes are used in your workflows."

        return {"ui": {"text": [final_text]}, "result": (final_text,)}

    def _extract_node_types(self, obj, used_node_types):
        """Recursively scan JSON data to extract active node class references."""
        if isinstance(obj, dict):
            node_type = obj.get("type") or obj.get("class_type")
            if node_type in ("NovAUnusedNodesManager", "NovAModelsManager"):
                return

            if "type" in obj and isinstance(obj["type"], str):
                used_node_types.add(obj["type"])
            if "class_type" in obj and isinstance(obj["class_type"], str):
                used_node_types.add(obj["class_type"])

            for val in obj.values():
                self._extract_node_types(val, used_node_types)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_node_types(item, used_node_types)


NODE_CLASS_MAPPINGS = {"NovAUnusedNodesManager": NovAUnusedNodesManager}
NODE_DISPLAY_NAME_MAPPINGS = {"NovAUnusedNodesManager": "NovA Unused Custom Nodes Manager"}