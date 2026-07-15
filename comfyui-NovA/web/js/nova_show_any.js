import { app } from "/scripts/app.js";

app.registerExtension({
    name: "comfyui-NovA.ShowAny",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAShowAny") {
			
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                // Execute standard upstream callback chain safely
                onExecuted?.apply(this, arguments);
                
                if (message?.text) {
                    const value = message.text.join("\n");
                    // Search for the pre-defined native text widget 
                    const widget = this.widgets?.find(w => w.name === "text_display");
                    if (widget) {
                        widget.value = value;
                        // Safe null check for legacy environments rendering standard DOM inputs
                        if (widget.inputEl) {
                            widget.inputEl.value = value;
                        }
                    }
                }
				
		   };
		 
			const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
			// Applying default Size
            this.size = [40, 40];
            }; 
		 
        }
    }
});