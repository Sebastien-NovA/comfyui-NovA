import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.TokensCounter",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovATokensCounter") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            const onExecuted = nodeType.prototype.onExecuted;
            const onConfigure = nodeType.prototype.onConfigure;

            // Initialize dynamic DOM HTML widget container
            function ensureDisplayWidget(node) {
                let widget = node.widgets?.find(w => w.name === "tokens_display");
                if (!widget) {
                    const container = document.createElement("div");
                    container.className = "nova-tokens-display-container";
                    
                    // Styling for metric display box
                    container.style.cssText = `
                        background-color: var(--comfy-input-bg);
                        color: #ffffff;
                        font-family: monospace;
                        font-size: 13px;
                        padding: 1px;
                        border-radius: 4px;
                        border: 1px solid var(--border-color, #444);
                        box-sizing: border-box;
                        width: 100%;
                        height: 100%
                    `;

                    widget = node.addDOMWidget("tokens_display", "display", container, {
                        getValue: () => node.properties?.saved_display_text || "",
                        setValue: (val) => {
                            node.properties.saved_display_text = val;
                            updateWidgetContent(node, widget, val);
                        }
                    });

                    if (!node.properties) node.properties = {};
                }
                return widget;
            }

            // Convert backend metric updates into custom HTML markup
            function updateWidgetContent(node, widget, rawText) {
                if (!rawText) return;
                
                widget.element.innerHTML = renderMetricsToHTML(rawText);
            }

            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                ensureDisplayWidget(this);
				
				// Applying default Size
				this.size = [80, 80];
            };

            nodeType.prototype.onConfigure = function(serializedData) {
                onConfigure?.apply(this, arguments);
                const widget = ensureDisplayWidget(this);
                if (this.properties?.saved_display_text) {
                    updateWidgetContent(this, widget, this.properties.saved_display_text);
                }
            };

            nodeType.prototype.onExecuted = function(message) {
                onExecuted?.apply(this, arguments);
                
                if (message?.text) {
                    const textPayload = message.text[0];
                    const widget = ensureDisplayWidget(this);
                    
                    this.properties.saved_display_text = textPayload;
                    updateWidgetContent(this, widget, textPayload);
                }
            };

        }
    }
});

/**
 * Format string payload to HTML markup elements
 */
function renderMetricsToHTML(text) {
    const lines = text.split("\n");
    return lines.map(line => {
        // Sanitize string output against XSS injection
        const safeLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        if (safeLine.startsWith("Words Count:")) {
            const val = safeLine.replace("Words Count:", "").trim();
            return `<div style="margin-bottom:6px;"><span style="color: #77FF77; font-weight: bold;">Words Count:</span> <span style="color: #ffffff; font-weight: bold;">${val}</span></div>`;
        }
        if (safeLine.startsWith("Tokens Count:")) {
            const val = safeLine.replace("Tokens Count:", "").trim();
            return `<div style="margin-bottom: 6px;"><span style="color: #FFD500; font-weight: bold;">Tokens Count:</span> <span style="color: #ffffff; font-weight: bold;">${val}</span></div>`;
        }
        
        return `<div>${safeLine}</div>`;
    }).join("");
}