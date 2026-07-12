# Copyright 2026 Sebastien NovA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import sys
import importlib.util

__author__ = "Sebastien NovA"
__version__ = "1.0.0"

current_dir = Path(__file__).parent
nodes_dir = current_dir / "py"

# SECURITY & STABILITY: 
# This ensures that standard Python libraries and core ComfyUI modules retain their highest priority in the import resolution order.
# Prevent the custom node from accidentally shadowing or breaking fundamental dependencies.
if str(nodes_dir) not in sys.path:
    sys.path.append(str(nodes_dir))

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
# Custom .js files directory:
WEB_DIRECTORY = "./web"

def load_nodes():
    # OPTIMIZATION: 
    for file in nodes_dir.rglob("*.py"):
        
        # Ignore __init__.py file in folder py/
        if file.name == "__init__.py":
            continue
            
        try:
            # CLEAN DYNAMIC IMPORT
            spec = importlib.util.spec_from_file_location(file.stem, file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # MAPPING EXTRACTION
                if hasattr(module, "NODE_CLASS_MAPPINGS"):
                    NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                    NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
                    
        except Exception as e:
            # ERROR HANDLING
            print(f"[{__file__}] Error loading module {file.name}: {e}")

load_nodes()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]