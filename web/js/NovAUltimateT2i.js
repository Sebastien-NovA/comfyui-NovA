import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.UltimateT2I",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAUltimateT2I") {
            
            // Fetch the system's registered LoRA filenames from standard object info endpoints
            let loraOptions = ["None"];
            try {
                const response = await fetch("/object_info/LoraLoader");
                if (response.ok) {
                    const info = await response.json();
                    // SYSTEM FIX: Correctly access dynamic options via the root 'LoraLoader' key
                    const choices = info?.LoraLoader?.input?.required?.lora_name?.[0];
                    if (choices && Array.isArray(choices)) {
                        loraOptions = choices;
                    }
                }
            } catch (err) {
                console.warn("[NovA.UltimateT2I] Standard LoraLoader lookup failed. Falling back to NovALoraLoader check...", err);
            }

            // Secondary Fallback check against custom NovALoraLoader endpoint
            if (loraOptions.length <= 1) {
                try {
                    const response = await fetch("/object_info/NovALoraLoader");
                    if (response.ok) {
                        const info = await response.json();
                        const choices = info?.NovALoraLoader?.input?.required?.lora1_name?.[0];
                        if (choices && Array.isArray(choices)) {
                            loraOptions = choices;
                        }
                    }
                } catch (err) {
                    console.error("[NovA.UltimateT2I] Failed to retrieve dynamic LoRA names from fallback:", err);
                }
            }

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                this.loraCount = 0; // Starts with absolutely no active LoRAs by default

                const strengthWidgetOptions = { min: -100.0, max: 100.0, step: 0.01, precision: 2 };

                // Inject Open Prompt Button
                const promptWidget = this.widgets.find(w => w.name === "prompt");
                if (promptWidget) {
                    this.addWidget("button", "📂 Load Prompt", "Open", () => {
                        const input = document.createElement("input");
                        input.type = "file";
                        input.accept = ".txt";
                        input.style.display = "none";
                        
                        input.onchange = (e) => {
                            const file = e.target.files[0];
                            if (!file) return;
                            
                            const reader = new FileReader();
                            reader.onload = (event) => {
                                promptWidget.value = event.target.result;
                                app.graph.setDirtyCanvas(true); // Redraw UI
                            };
                            reader.readAsText(file);
                        };

                        document.body.appendChild(input);
                        input.click();
                        document.body.removeChild(input);
                    });

                    // Inject Save Prompt Button
                    this.addWidget("button", "💾 Save Prompt", "Save", () => {
                        if (!promptWidget.value) return;
                        
                        const blob = new Blob([promptWidget.value], { type: "text/plain" });
                        const url = URL.createObjectURL(blob);
                        
                        const anchor = document.createElement("a");
                        anchor.href = url;
                        anchor.download = "NovA_Prompt.txt";
                        anchor.style.display = "none";
                        
                        document.body.appendChild(anchor);
                        anchor.click();
                        document.body.removeChild(anchor);
                        
                        URL.revokeObjectURL(url); // Clean browser memory allocation
                    });

                    // Reorder Prompt Actions immediately below prompt
                    const promptIndex = this.widgets.findIndex(w => w.name === "prompt");
                    if (promptIndex !== -1) {
                        const buttons = this.widgets.splice(-2, 2);
                        this.widgets.splice(promptIndex + 1, 0, ...buttons);
                    }
                }

                // Push Add/Remove action buttons to the absolute bottom of the widget list
                this.reorderWidgets = function() {
                    const btnAdd = this.widgets.find(w => w.name === "Add LoRA");
                    const btnRemove = this.widgets.find(w => w.name === "Remove Last LoRA");

                    if (btnAdd) this.widgets.push(this.widgets.splice(this.widgets.indexOf(btnAdd), 1)[0]);
                    if (btnRemove) this.widgets.push(this.widgets.splice(this.widgets.indexOf(btnRemove), 1)[0]);
                };

                // Inject next dynamic LoRA widget group
                this.addNovaLora = function() {
                    this.loraCount++;
                    const i = this.loraCount;
                    const widgetConfig = { forceInput: true, serialize: true };

                    // Instantiate graphical interface widgets with proper options list
                    const wActive = this.addWidget("toggle", `lora${i}_active`, true, () => {}, { ...widgetConfig, default: true });
                    const wName = this.addWidget("combo", `lora${i}_name`, loraOptions[0] || "None", () => {}, { ...widgetConfig, values: loraOptions });
                    const wModel = this.addWidget("number", `lora${i}_strength_model`, 1.0, () => {}, { ...strengthWidgetOptions, ...widgetConfig });
                    const wClip = this.addWidget("number", `lora${i}_strength_clip`, 1.0, () => {}, { ...strengthWidgetOptions, ...widgetConfig });

                    // Maintain serialization map while preventing duplication in workflows
                    const inputExists = this.inputs && this.inputs.find(inp => inp.name === `lora${i}_active`);
                    
                    if (!inputExists) {
                        this.addInput(`lora${i}_active`, "BOOLEAN", { widget: wActive });
                        this.addInput(`lora${i}_name`, "COMBO", { widget: wName });
                        this.addInput(`lora${i}_strength_model`, "FLOAT", { widget: wModel });
                        this.addInput(`lora${i}_strength_clip`, "FLOAT", { widget: wClip });
                    } else {
                        const updateRef = (name, w) => {
                            const inp = this.inputs.find(x => x.name === name);
                            if (inp) {
                                inp.widget = w;
                                if (!inp.extra_info) inp.extra_info = {};
                                inp.extra_info.widget = w;
                            }
                        };
                        updateRef(`lora${i}_active`, wActive);
                        updateRef(`lora${i}_name`, wName);
                        updateRef(`lora${i}_strength_model`, wModel);
                        updateRef(`lora${i}_strength_clip`, wClip);
                    }

                    this.reorderWidgets();
                    this.computeSize();
                    this.setDirtyCanvas(true, true);
                };

                // Safely remove the last dynamic LoRA widget group
                this.removeNovaLora = function() {
                    if (this.loraCount > 0) { 
                        const i = this.loraCount;
                        const prefixes = [`lora${i}_active`, `lora${i}_name`, `lora${i}_strength_model`, `lora${i}_strength_clip`];

                        for (let j = this.widgets.length - 1; j >= 0; j--) {
                            if (prefixes.includes(this.widgets[j].name)) {
                                this.widgets.splice(j, 1);
                            }
                        }

                        if (this.inputs) {
                            for (let j = this.inputs.length - 1; j >= 0; j--) {
                                if (prefixes.includes(this.inputs[j].name)) {
                                    this.removeInput(j);
                                }
                            }
                        }

                        this.loraCount--;
                        this.computeSize();
                        this.setDirtyCanvas(true, true);
                    }
                };

                // Render execution controls at bottom of node UI
                if (!this.widgets.find(w => w.name === "Add LoRA")) {
                    this.addWidget("button", "Add LoRA", "add", () => this.addNovaLora());
                    this.addWidget("button", "Remove Last LoRA", "remove", () => this.removeNovaLora());
                }

                this.reorderWidgets();
                this.computeSize();
            };

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function(info) {
                // Parse serialized elements to recreate custom LoRA counts from workflows
                let maxLora = 0;
                if (info && info.inputs) {
                    info.inputs.forEach(inp => {
                        const match = inp.name.match(/^lora(\d+)_/);
                        if (match) maxLora = Math.max(maxLora, parseInt(match[1], 10));
                    });
                }

                // Add missing UI widgets in order
                while (this.loraCount < maxLora) {
                    this.addNovaLora();
                }

                if (onConfigure) {
                    onConfigure.apply(this, arguments);
                }

                // Force layout restoration with setTimeout to bypass standard core overrides
                if (info && info.widgets_values) {
                    setTimeout(() => {
                        for (let i = 0; i < info.widgets_values.length; i++) {
                            if (this.widgets[i] && this.widgets[i].type !== "button") {
                                this.widgets[i].value = info.widgets_values[i];
                            }
                        }
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                    }, 10);
                }
            };
        }
    }
});