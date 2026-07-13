import { app } from "../../../web/scripts/app.js";

app.registerExtension({
    name: "NovA.NovAKSampler",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAKSampler") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                // Create a persistent clone of the full widget array for structural filtering
                this.allWidgets = [...this.widgets];

                // Functional state controller using array filtering mutation
                const updateWidgetVisibility = () => {
                    const formatWidget = this.allWidgets.find(w => w.name === "format");
                    if (!formatWidget) return;

                    const isCustom = formatWidget.value === "Custom Format";

                    // Reconstruct the active widgets array based on context criteria
                    this.widgets = this.allWidgets.filter(w => {
                        if (w.name === "greatest_length") return !isCustom;
                        if (w.name === "custom_width" || w.name === "custom_height") return isCustom;
                        return true;
                    });

                    // Update internal layout positioning structures
                    this.setSize(this.computeSize());
                    app.canvas.setDirty(true, true);
                };

                // Bind visibility toggle action directly to the format field callback chain
                const formatField = this.widgets.find(w => w.name === "format");
                if (formatField) {
                    const baseCallback = formatField.callback;
                    formatField.callback = function (value) {
                        if (baseCallback) {
                            baseCallback.apply(this, arguments);
                        }
                        updateWidgetVisibility();
                    };
                }

                // Defer execution until the canvas environment finishes node assembly mapping
                setTimeout(() => {
                    updateWidgetVisibility();
                }, 1);
            };
        }
    }
});