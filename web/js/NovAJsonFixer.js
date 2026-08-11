import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// Register custom extension compatible with LiteGraph and V2 Frontend
app.registerExtension({
    name: "NovA.JsonFixer",
    
    async nodeCreated(node) {
        if (node.comfyClass === "NovAJsonFixer") {
            // Append trigger button widget at the bottom of the node UI
            node.addWidget("button", "💾 Save Fixed Image", "save_btn", async () => {
                const widgetValues = {};

                // Filter valid parameters and ignore UI-only or action widgets
                if (node.widgets) {
                    for (const widget of node.widgets) {
                        if (
                            widget.name && 
                            widget.name !== "save_btn" && 
                            widget.type !== "button" && 
                            widget.name !== "upload"
                        ) {
                            widgetValues[widget.name] = widget.value;
                        }
                    }
                }

                try {
                    // Send node configuration parameters directly to Python endpoint
                    const response = await api.fetchApi("/nova/json_fixer/save", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(widgetValues)
                    });

                    const result = await response.json();

                    if (response.ok && result.status === "success") {
                        alert(`Success! Image saved to output directory:\n${result.saved_path}`);
                    } else {
                        alert(`Error saving fixed image: ${result.message || "Unknown error"}`);
                    }
                } catch (error) {
                    console.error("[NovAJsonFixer] Execution failed:", error);
                    alert(`Failed to execute save action: ${error.message}`);
                }
            });
        }
    }
});