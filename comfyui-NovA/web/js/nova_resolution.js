import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "NovA.ResolutionSelector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAResolutionSelector") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                this.size = [300, 300];
                //this.computeSize();
            };
        }
    }
});