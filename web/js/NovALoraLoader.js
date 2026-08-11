import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.LoraLoader",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovALoraLoader") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
				
                this.loraCount = 1;

                // Cache reference options from default lora1 widgets
                const loraNameWidget = this.widgets.find(w => w.name === "lora1_name");
                const loraOptions = loraNameWidget ? loraNameWidget.options.values : [];

                const baseStrengthWidget = this.widgets.find(w => w.name === "lora1_strength_model");
                const strengthWidgetOptions = baseStrengthWidget ? { ...baseStrengthWidget.options } : { min: -100.0, max: 100.0, step: 0.01, precision: 2 };

                // Keep action buttons at the bottom of the widget list
                this.reorderWidgets = function() {
                    const btnAdd = this.widgets.find(w => w.name === "Add LoRA");
                    const btnRemove = this.widgets.find(w => w.name === "Remove Last LoRA");

                    if (btnAdd) this.widgets.push(this.widgets.splice(this.widgets.indexOf(btnAdd), 1)[0]);
                    if (btnRemove) this.widgets.push(this.widgets.splice(this.widgets.indexOf(btnRemove), 1)[0]);
                };

                // Add a new dynamic set of LoRA widgets
                this.addNovaLora = function() {
                    this.loraCount++;
                    const i = this.loraCount;
                    const widgetConfig = { forceInput: true, serialize: true };

                    // 1. Create graphical widgets
                    const wActive = this.addWidget("toggle", `lora${i}_active`, true, () => {}, { ...widgetConfig, default: true });
                    const wName = this.addWidget("combo", `lora${i}_name`, loraOptions[0] || "None", () => {}, { ...widgetConfig, values: loraOptions });
                    const wModel = this.addWidget("number", `lora${i}_strength_model`, 1.0, () => {}, { ...strengthWidgetOptions, ...widgetConfig });
                    const wClip = this.addWidget("number", `lora${i}_strength_clip`, 1.0, () => {}, { ...strengthWidgetOptions, ...widgetConfig });

                    // 2. Prevent duplicating inputs if LiteGraph already restored them from JSON
                    const inputExists = this.inputs && this.inputs.find(inp => inp.name === `lora${i}_active`);
                    
                    if (!inputExists) {
                        this.addInput(`lora${i}_active`, "BOOLEAN", { widget: wActive });
                        this.addInput(`lora${i}_name`, "COMBO", { widget: wName });
                        this.addInput(`lora${i}_strength_model`, "FLOAT", { widget: wModel });
                        this.addInput(`lora${i}_strength_clip`, "FLOAT", { widget: wClip });
                    } else {
                        // Update internal widget references during workflow load
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

                // Remove the last set of dynamic LoRA widgets
                this.removeNovaLora = function() {
                    if (this.loraCount > 1) { 
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

                if (!this.widgets.find(w => w.name === "Add LoRA")) {
                    this.addWidget("button", "Add LoRA", "add", () => this.addNovaLora());
                    this.addWidget("button", "Remove Last LoRA", "remove", () => this.removeNovaLora());
                }

                this.reorderWidgets();
                this.computeSize();
            };

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function(info) {
                let maxLora = 1;

                // 1. Calculate saved LoRAs from node inputs if present
                if (info && info.inputs) {
                    info.inputs.forEach(inp => {
                        const match = inp.name.match(/^lora(\d+)_/);
                        if (match) maxLora = Math.max(maxLora, parseInt(match[1], 10));
                    });
                }

                // 2. Calculate saved LoRAs from image PNG metadata widgets_values array
                if (info && info.widgets_values && Array.isArray(info.widgets_values)) {
                    // Each LoRA group has 4 values, last 2 values are action buttons
                    const calculatedLoraCount = Math.floor((info.widgets_values.length - 2) / 4);
                    if (calculatedLoraCount > maxLora) {
                        maxLora = calculatedLoraCount;
                    }
                }

                // 3. Instantiate missing widgets BEFORE LiteGraph assigns widget values
                while (this.loraCount < maxLora) {
                    this.addNovaLora();
                }

                // 4. Execute original configuration
                if (onConfigure) {
                    onConfigure.apply(this, arguments);
                }

                // 5. Force inject values at the end of the event loop to bypass internal overrides
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