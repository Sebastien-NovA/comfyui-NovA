import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.UltimateT2I",
    async nodeCreated(node) {
        if (node.comfyClass === "NovAUltimateT2I") {
			
            // Inject Open Prompt Button
            node.addWidget("button", "📂 Load Prompt", "Open", () => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = ".txt";
                
                // Handle file selection
                input.onchange = (e) => {
                    const file = e.target.files[0];
                    if (!file) return;
                    
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const content = event.target.result;
                        const promptWidget = node.widgets.find(w => w.name === "prompt");
                        if (promptWidget) {
                            promptWidget.value = content;
                            app.graph.setDirtyCanvas(true); // Trigger UI update
                        }
                    };
                    reader.readAsText(file);
                };
                input.click();
            });

            // Inject Save Prompt Button
            node.addWidget("button", "💾 Save Prompt", "Save", () => {
                const promptWidget = node.widgets.find(w => w.name === "prompt");
                if (promptWidget && promptWidget.value) {
                    // Create an ephemeral Blob and trigger standard OS download
                    const text = promptWidget.value;
                    const blob = new Blob([text], { type: "text/plain" });
                    const url = URL.createObjectURL(blob);
                    
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "NovA_Prompt.txt";
                    document.body.appendChild(a);
                    a.click();
                    
                    // Cleanup
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
            });

            // Defer execution to ensure Python-generated widgets are fully loaded
            setTimeout(() => {
                const modelWidget = node.widgets.find(w => w.name === "diffusion_model");
                const shiftWidget = node.widgets.find(w => w.name === "shift");

                if (modelWidget && shiftWidget) {
                    // Preserve any existing callback assigned by ComfyUI
                    const originalCallback = modelWidget.callback;
                    
                    // Inject custom callback on model change
                    modelWidget.callback = function (value, graphCanvas, nodeRef, pos, event) {
                        if (originalCallback) {
                            originalCallback.apply(this, arguments);
                        }

                        // Prevent overriding user-saved values during workflow load
                        if (app.configuringGraph) {
                            return;
                        }

                        if (typeof value === "string") {
                            const modelName = value.toLowerCase();
                            
                            // Dynamically adjust shift based on model architecture
                            if (modelName.includes("z-image") || modelName.includes("sd3")) {
                                shiftWidget.value = 3.0;
                            } else if (modelName.includes("flux") || modelName.includes("aura")) {
                                shiftWidget.value = 3.15;
                            } else {
								shiftWidget.value = 0.0; // shift disabled for unsupported models
							}
                            
                            // Force UI redraw to display the new shift value
                            app.graph.setDirtyCanvas(true);
                        }
                    };
                }
            }, 0);
        }
    }
});