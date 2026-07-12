import { app } from "../../../scripts/app.js";

// Register extension within ComfyUI ecosystem
app.registerExtension({
    name: "NovA.ModelsLoader",
    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        // Target only the specific custom node
        if (nodeData.name === "NovAModelsLoader") {
            
            // Hook into the node creation lifecycle
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                // Sizing definition
                this.size = [400, 250];
            };
        }
    }
});