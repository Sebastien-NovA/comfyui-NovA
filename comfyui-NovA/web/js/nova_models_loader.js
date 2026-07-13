import { app } from "../../../scripts/app.js";

// Register extension within ComfyUI ecosystem
app.registerExtension({
    name: "NovA.ModelsLoader",
    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        if (nodeData.name === "NovAModelsLoader") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                // Sizing definition
                this.size = [500, 250];
            };
        }
    }
});